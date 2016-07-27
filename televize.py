#!/usr/bin/env python
"""
Play Czech television stream in mplayer.
"""
import argparse
import logging
import sys
import time
from collections import OrderedDict, namedtuple
from urlparse import urljoin

import m3u8
import requests

PLAYLIST_LINK = 'http://www.ceskatelevize.cz/ivysilani/ajax/get-client-playlist'
CHANNEL_NAMES = OrderedDict((
    ('1', 1),
    ('2', 2),
    ('24', 24),
    ('sport', 4),
    ('D', 5),
    ('art', 6),
))

PARSER = argparse.ArgumentParser(description="Dumps Czech television stream locations")
PARSER.add_argument('--debug', action='store_true', help="print debug messages")

LIVE_SUBPARSERS = PARSER.add_subparsers(help="CT live", dest="channel")
for channel in CHANNEL_NAMES:
    LIVE_SUBPARSERS.add_parser(channel, description="CT%s live" % channel, help="CT%s live" % channel)


################################################################################
# Extended M3U playlists
#
# Based on Apple Playlist specification, see https://developer.apple.com/library/ios/technotes/tn2288/_index.html.
#
Media = namedtuple('Media', ('sequence', 'location', 'duration'))


class Playlist(object):
    """Represents a playlist contents

    @ivar duration: Maximum media file duration.
    """
    def __init__(self):
        self.duration = None
        self._items = OrderedDict()
        self._last_item = None
        self.end = False

    def __nonzero__(self):
        return bool(self._items)

    def __iter__(self):
        for item in self._items.values():
            yield item

    def add(self, media):
        """Add Media item into playlist"""
        if media.sequence in self._items:
            raise ValueError("Media can't be added to playlist - sequence number already used.")
        self._items[media.sequence] = media
        self._last_item = media

    def pop(self):
        if not self._items:
            return

        return self._items.popitem(last=False)[1]

    def update(self, other):
        """
        Update playlist with data from other playlist.
        """
        if self.end:
            raise ValueError("This playlist already ended.")

        for media in other:
            # Playlists' items may overlay - skip items from other playlist which matches items in this playlist.
            if self._last_item is not None and media.sequence <= self._last_item.sequence:
                continue
            self.add(media)

        # Update the end flag
        if other.end:
            self.end = True


class PlaylistParser(object):
    """
    Parser of the M3U playlists.

    Based on Apple Playlist specification, see https://developer.apple.com/library/ios/technotes/tn2288/_index.html.
    """
    def parse(self, data, playlist_url):
        """
        Parses file-like `data` object and returns `Playlist` object.

        @param playlist_url: URL where the playlist is downloaded from
        """
        first_line = next(data, None)
        if first_line.strip() != '#EXTM3U':
            raise ValueError('Invalid playlist')

        playlist = Playlist()
        sequence = None
        for line in data:
            line = line.strip()
            if line.startswith('#EXT-X-TARGETDURATION'):
                playlist.duration = float(line[22:])
            elif line.startswith('#EXT-X-MEDIA-SEQUENCE'):
                sequence = int(line[22:])
            elif line.startswith('#EXT-X-PROGRAM-DATE-TIME'):
                pass
            elif line.startswith('#EXTINF'):
                # Parse media line
                media = self._parse_media(line, data, sequence, playlist_url)
                playlist.add(media)
                sequence += 1
            elif line == '#EXT-X-ENDLIST':
                playlist.end = True
            else:
                raise ValueError("Invalid playlist - unknown data: %s" % line)
        return playlist

    def _parse_media(self, line, data, sequence, playlist_url):
        "Parses `EXTINF` tag."
        if sequence is None:
            raise ValueError("Invalid playlist - required EXT-X-MEDIA-SEQUENCE tag not found: %s" % line)
        location = next(data)
        location = location.strip()
        duration = float(line[8:])
        return Media(sequence, urljoin(playlist_url, location), duration)
################################################################################


def print_streams(playlist, output=sys.stdout):
    """
    Print streams from playlist to the output.

    @param playlist: Playlist do be printed
    @param output: File-like object to write into
    """
    while playlist:
        media = playlist.pop()
        output.write(media.location)
        output.write('\n')
        output.flush()


def play_live(channel, output=sys.stdout, _client=requests, _sleep=time.sleep):
    """
    Play live CT channel

    @param channel: Name of the channel
    @param _client: HTTP client. Used by tests
    @param _sleep: Sleep function
    """
    # TODO: We shold parse the `content` from the flash player to find playlist data from `getPlaylistUrl` calls.
    # from lxml import etree
    #
    # response = urllib2.urlopen(LINK_CT24)
    #
    # parser = etree.HTMLParser()
    # tree = etree.parse(response, parser)
    # player_src = tree.xpath('//div[@id="programmePlayer"]//iframe/@src')
    # player_src = player_src[0]
    #
    # response = urllib2.urlopen(urljoin(LINK_CT24, player_src))
    # content = response.read()

    # First get the custom client playlist URL
    post_data = {
        'playlist[0][id]': CHANNEL_NAMES[channel],
        'playlist[0][type]': "channel",
        'requestUrl': '/ivysilani/embed/iFramePlayerCT24.php',
        'requestSource': "iVysilani",
        'addCommercials': 0,
        'type': "html"
    }
    response = _client.post(PLAYLIST_LINK, post_data, headers={'x-addr': '127.0.0.1'})
    client_playlist = response.json()

    # Get the custom playlist URL to get playlist JSON meta data (including playlist URL)
    response = _client.get(urljoin(PLAYLIST_LINK, client_playlist["url"]))
    playlist_metadata = response.json()
    stream_playlist_url = playlist_metadata['playlist'][0]['streamUrls']['main']

    # Use playlist URL to get the M3U playlist with streams
    response = _client.get(urljoin(PLAYLIST_LINK, stream_playlist_url))
    variant_playlist = m3u8.loads(response.content)
    # Use the first stream found
    live_stream = variant_playlist.playlists[0]

    playlist_parser = PlaylistParser()
    # Iteratively download the stream playlists
    response = _client.get(live_stream.uri)
    live_playlist = playlist_parser.parse(response.iter_lines(), live_stream.uri)

    while not live_playlist.end:
        print_streams(live_playlist, output)

        # Wait playlist duration. New media item should appear on the playlist.
        _sleep(live_playlist.duration)
        # Get new part of the playlist
        response = _client.get(live_stream.uri)
        live_chunk = playlist_parser.parse(response.iter_lines(), live_stream.uri)
        live_playlist.update(live_chunk)

    print_streams(live_playlist, output)


def main():
    args = PARSER.parse_args()
    if args.debug:
        level = logging.DEBUG
    else:
        level = logging.WARNING
    logging.basicConfig(stream=sys.stderr, level=level)

    play_live(args.channel)


if __name__ == '__main__':
    main()
