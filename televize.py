#!/usr/bin/env python
"""
Play Czech television stream in mplayer.
"""
import argparse
from collections import namedtuple, OrderedDict
import json
import sys
import time
from urlparse import urljoin
from urllib import urlencode
import urllib2


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
PARSER.add_argument('channel', choices=CHANNEL_NAMES.keys(), help="channel to stream")
PARSER.add_argument('--debug', action='store_true', help="print debug messages")


def setup_http(debug):
    "Set up HTTP handlers."
    if debug:
        debuglevel = 1
    else:
        debuglevel = 0
    handlers = [urllib2.HTTPHandler(debuglevel=debuglevel), urllib2.HTTPSHandler(debuglevel=debuglevel)]
    opener = urllib2.build_opener(*handlers)
    urllib2.install_opener(opener)


################################################################################
# Extended M3U playlists
#
# Based on Apple Playlist specification, see https://developer.apple.com/library/ios/technotes/tn2288/_index.html.
#
Media = namedtuple('Media', ('sequence', 'location', 'duration'))
Stream = namedtuple('Stream', ('location', 'bandwidth'))


class VariantPlaylist(object):
    """Represents a playlist with variations of the same video in different quality."""
    def __init__(self):
        self._streams = {}

    def __getitem__(self, key):
        return self._streams[key]

    def add(self, stream):
        self._streams[stream.bandwidth] = stream


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


class VariantPlaylistParser(object):
    """
    Parser of the variant playlists.
    """
    def parse(self, data):
        "Parses file-like `data` object and returns `VariantPlaylist` object."
        first_line = next(data, None)
        if first_line.strip() != '#EXTM3U':
            raise ValueError('Invalid playlist')

        playlist = VariantPlaylist()
        for line in data:
            line = line.strip()
            if line.startswith('#EXT-X-STREAM-INF'):
                # Parse stream tag
                stream = self._parse_stream(line, data)
                playlist.add(stream)
            else:
                raise ValueError("Invalid playlist - unknown data: %s" % line)
        return playlist

    def _parse_stream(self, line, data):
        "Parses `EXT-X-STREAM-INF` tag."
        attributes = line[18:]
        bandwidth = None
        for chunk in attributes.split(','):
            key, value = chunk.split('=')
            if key == 'BANDWIDTH':
                bandwidth = int(value)
        if bandwidth is None:
            raise ValueError("Invalid playlist - required BANDWIDTH attribute not found in EXT-X-STREAM-INF tag: %s" %
                             line)
        location = next(data)
        location = location.strip()
        return Stream(location, bandwidth)


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


def print_streams(playlist, urlbase):
    """Print streams from playlist to the stdout."""
    while playlist:
        media = playlist.pop()
        sys.stdout.write(media.location)
        sys.stdout.write('\n')
        sys.stdout.flush()


def main():
    args = PARSER.parse_args()
    setup_http(args.debug)

# from lxml import etree
#
#     response = urllib2.urlopen(LINK_CT24)
#
#     parser = etree.HTMLParser()
#     tree = etree.parse(response, parser)
#     player_src = tree.xpath('//div[@id="programmePlayer"]//iframe/@src')
#     player_src = player_src[0]
#
#     response = urllib2.urlopen(urljoin(LINK_CT24, player_src))
#     content = response.read()
#
#TODO: We shold parse the `content` from the flash player to find playlist data from `getPlaylistUrl` calls.

    # First get the custom client playlist URL
    post_data = {
        'playlist[0][id]': CHANNEL_NAMES[args.channel],
        'playlist[0][type]': "channel",
        'requestUrl': '/ivysilani/embed/iFramePlayerCT24.php',
        'requestSource': "iVysilani",
        'addCommercials': 0,
        'type': "html"
    }
    req = urllib2.Request(PLAYLIST_LINK, urlencode(post_data), {'x-addr': '127.0.0.1'})
    response = urllib2.urlopen(req)
    client_playlist = json.load(response)

    # Get the custom playlist URL to get playlist JSON meta data (including playlist URL)
    response = urllib2.urlopen(urljoin(PLAYLIST_LINK, client_playlist["url"]))
    playlist_metadata = json.load(response)
    stream_playlist_url = playlist_metadata['playlist'][0]['streamUrls']['main']

    # Use playlist URL to get the M3U playlist with streams
    var_parser = VariantPlaylistParser()
    response = urllib2.urlopen(urljoin(PLAYLIST_LINK, stream_playlist_url))
    variant_playlist = var_parser.parse(response)
    # Use the first stream found
    live_stream = variant_playlist[500000]

    playlist_parser = PlaylistParser()
    # Iteratively download the stream playlists
    response = urllib2.urlopen(live_stream.location)
    live_playlist = playlist_parser.parse(response, live_stream.location)

    while not live_playlist.end:
        print_streams(live_playlist, live_stream.location)

        # Wait playlist duration. New media item should appear on the playlist.
        time.sleep(live_playlist.duration)
        # Get new part of the playlist
        response = urllib2.urlopen(live_stream.location)
        live_chunk = playlist_parser.parse(response, live_stream.location)
        live_playlist.update(live_chunk)

    print_streams(live_playlist, live_stream.location)


if __name__ == '__main__':
    main()
