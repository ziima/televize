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


Media = namedtuple('Media', ('location', ))
Stream = namedtuple('Stream', ('location', 'bandwidth'))


class M3uPlaylist(object):
    """
    Represents a playlist contents

    @ivar sequence: Id of the first item in `items`.
    """
    def __init__(self):
        self.items = []
        self.duration = None
        self.sequence = 0
        self.end = False

    def update_live(self, other):
        """
        Update live playlist with data from other part of the live playlist.
        """
        if self.end:
            # This playlist already ended.
            return

        new_items = enumerate(other.items, start=other.sequence)
        # Filter items not yet present in this playlist
        last_id = self.sequence + len(self.items) - 1
        new_items = [(i, s) for i, s in new_items if i > last_id]

        if not new_items:
            # No new items
            return

        # Update sequence if needed
        if not self.items:
            self.sequence = new_items[0][0]
        self.items.extend(s for i, s in new_items)
        # Check the end flag
        if other.end:
            self.end = True

    def pop(self):
        if not self.items:
            return

        first = self.items.pop(0)
        self.sequence += 1
        return first


class M3uPlaylistParser(object):
    """
    Parser of the M3U playlists.

    Based on Apple Playlist specification, see https://developer.apple.com/library/ios/technotes/tn2288/_index.html.
    """
    def parse(self, data):
        "Parses file-like `data` object and returns `M3uPlaylist` object."
        first_line = next(data, None)
        if first_line.strip() != '#EXTM3U':
            raise ValueError('Not a valid playlist')

        playlist = M3uPlaylist()
        for line in data:
            line = line.strip()
            # Interesting headers
            if line.startswith('#EXT-X-TARGETDURATION'):
                playlist.duration = float(line[22:])
            elif line.startswith('#EXT-X-MEDIA-SEQUENCE'):
                playlist.sequence = int(line[22:])
            elif line.startswith('#EXT-X-STREAM-INF'):
                # Parse stream tag
                stream = self._parse_stream(line, data)
                playlist.items.append(stream)
            elif line.startswith('#EXTINF'):
                # Parse media line
                media = self._parse_media(line, data)
                playlist.items.append(media)
            # And ignore any other lines
        return playlist

    def _parse_media(self, line, data):
        "Parses `EXTINF` tag."
        location = next(data)
        location = location.strip()
        return Media(location)

    def _parse_stream(self, line, data):
        "Parses `EXT-X-STREAM-INF` tag."
        attributes = line[18:]
        bandwidth = None
        for chunk in attributes.split(','):
            key, value = chunk.split('=')
            if key == 'BANDWIDTH':
                bandwidth = int(value)
        location = next(data)
        location = location.strip()
        return Stream(location, bandwidth)


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
    m3u_parser = M3uPlaylistParser()
    response = urllib2.urlopen(urljoin(PLAYLIST_LINK, stream_playlist_url))
    streams_playlist = m3u_parser.parse(response)
    # Use the first stream found
    live_stream = streams_playlist.items[0]

    # Iteratively download the stream playlists
    response = urllib2.urlopen(live_stream.location)
    live_playlist = m3u_parser.parse(response)

    while not live_playlist.end:
        while live_playlist.items:
            media = live_playlist.pop()
            sys.stdout.write(media.location)
            sys.stdout.write('\n')
            sys.stdout.flush()

        # Wait playlist duration. New media item appears in the playlist.
        time.sleep(live_playlist.duration)
        # Get new part of the playlist
        response = urllib2.urlopen(live_stream.location)
        live_chunk = m3u_parser.parse(response)
        live_playlist.update_live(live_chunk)

    while live_playlist.items:
        media = live_playlist.pop()
        sys.stdout.write(media.location)
        sys.stdout.write('\n')
        sys.stdout.flush()


if __name__ == '__main__':
    main()
