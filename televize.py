#!/usr/bin/env python
"""
Play Czech television stream in mplayer.
"""
import argparse
import logging
import sys
import time
from collections import OrderedDict
from datetime import timedelta
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
class LiveStream(object):
    """
    Handles live stream segments from playlists.

    @ivar end: Whether the live stream ended.
    """
    # Max number of old segments
    _history = 10

    def __init__(self):
        # Segments to be played
        self._segments = []
        self.end = False
        # Segments already played
        self._old_segments = []
        # EXT-X-MEDIA-SEQUENCE of the last item in the live stream
        self._last_media_sequence = None

    def __nonzero__(self):
        return bool(self._segments)

    @property
    def last_played(self):
        """
        Returns the last played segment.
        """
        if not self._old_segments:
            return None
        return self._old_segments[-1]

    def pop(self):
        """
        Pops the first segment.
        """
        if not self._segments:
            return None

        seg = self._segments.pop(0)
        self._old_segments.append(seg)
        self._old_segments = self._old_segments[-self._history:]
        return seg

    def update(self, playlist):
        """
        Updates live stream with segments from playlist.
        """
        if self.end:
            raise ValueError("This stream already ended.")

        new_segments = playlist.segments

        # Add only segments which were not part of the stream
        if self._last_media_sequence:
            new_segments = (s for i, s in enumerate(new_segments, start=playlist.media_sequence)
                            if i > self._last_media_sequence)

        self._segments.extend(new_segments)

        # Update `_last_media_sequence` to the index of the last item in `playlist`
        if new_segments:
            self._last_media_sequence = playlist.media_sequence + len(playlist.segments) - 1

        # Mark the stream as ended if required
        if playlist.is_endlist:
            self.end = True


################################################################################
def print_streams(stream, base_url, output=sys.stdout):
    """
    Print streams from playlist to the output.

    @param playlist: Playlist do be printed
    @param base_url: Base URL for segment URIs
    @param output: File-like object to write into
    """
    while stream:
        segment = stream.pop()
        url = urljoin(base_url, segment.uri)
        logging.debug("URL: %s", url)
        output.write(url)
        output.write('\n')
        output.flush()


def _fix_extinf(content):
    """
    Append the comma at the end of EXTINF tag if its missing.
    """
    output = []
    for line in content.split('\n'):
        if line.startswith(m3u8.protocol.extinf) and not line.endswith(','):
            output.append(line + ',')
        else:
            output.append(line)
    return '\n'.join(output)


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
    logging.debug("Variant playlist: %s", response.content)
    variant_playlist = m3u8.loads(response.content)
    # Use the first stream found
    live_playlist = variant_playlist.playlists[0]

    # Initialize the stream
    stream = LiveStream()
    response = _client.get(live_playlist.uri)
    logging.debug("Stream playlist: %s", response.content)
    stream.update(m3u8.loads(_fix_extinf(response.content)))

    # Iteratively download the stream playlists
    while not stream.end:
        print_streams(stream, live_playlist.uri, output)

        # Wait playlist duration. New media item should appear on the playlist.
        _sleep(stream.last_played.duration)

        # Get new part of the stream
        response = _client.get(live_playlist.uri)
        logging.debug("Stream playlist: %s", response.content)
        stream.update(m3u8.loads(_fix_extinf(response.content)))

    print_streams(stream, live_playlist.uri, output)


def main():
    args = PARSER.parse_args()
    if args.debug:
        level = logging.DEBUG
    else:
        level = logging.WARNING
    logging.basicConfig(stream=sys.stderr, level=level)
    logging.getLogger('iso8601').setLevel(logging.WARN)

    play_live(args.channel)


if __name__ == '__main__':
    main()
