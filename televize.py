#!/usr/bin/env python3
"""
Plays Czech television stream in custom player

Usage: televize.py [options] <channel>
       televize.py -h | --help
       televize.py --version

Channels:
  1                    CT1
  2                    CT2
  24                   CT24
  sport                CTsport
  D                    CT:D
  art                  CTart

Options:
  -h, --help           show this help message and exit
  --version            show program's version number and exit
  -p, --player=PLAYER  player command [default: mpv -]
  -d, --debug          print debug messages
"""
import logging
import shlex
import sys
import time
from collections import OrderedDict
from subprocess import PIPE, Popen
from urllib.parse import urljoin

import m3u8
import requests
from docopt import docopt
from lxml import etree

__version__ = '0.1a1'


PLAYLIST_LINK = 'http://www.ceskatelevize.cz/ivysilani/ajax/get-client-playlist'
CHANNEL_NAMES = OrderedDict((
    ('1', 1),
    ('2', 2),
    ('24', 24),
    ('sport', 4),
    ('D', 5),
    ('art', 6),
))
PLAYLIST_TYPE_CHANNEL = 'channel'
PLAYLIST_TYPE_EPISODE = 'episode'


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

    def __bool__(self):
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
# Playlist functions

def get_playlist(playlist_id, playlist_type):
    """
    Extract the playlist for CT video.

    @param playlist_id: ID of playlist
    @param playlist_type: Type of playlist
    """
    assert playlist_type in (PLAYLIST_TYPE_CHANNEL, PLAYLIST_TYPE_EPISODE)
    # First get the custom client playlist URL
    post_data = {
        'playlist[0][id]': playlist_id,
        'playlist[0][type]': playlist_type,
        'requestUrl': '/ivysilani/',
        'requestSource': "iVysilani",
        'addCommercials': 0,
        'type': "html"
    }
    response = requests.post(PLAYLIST_LINK, post_data, headers={'x-addr': '127.0.0.1'})
    client_playlist = response.json()

    # Get the custom playlist URL to get playlist JSON meta data (including playlist URL)
    response = requests.get(urljoin(PLAYLIST_LINK, client_playlist["url"]))
    playlist_metadata = response.json()
    stream_playlist_url = playlist_metadata['playlist'][0]['streamUrls']['main']

    # Use playlist URL to get the M3U playlist with streams
    response = requests.get(urljoin(PLAYLIST_LINK, stream_playlist_url))
    logging.debug("Variant playlist: %s", response.text)
    variant_playlist = m3u8.loads(response.text)
    # Use the first stream found
    # TODO: Select variant based on requested quality
    return variant_playlist.playlists[0]


def get_ivysilani_playlist(url):
    """
    Extract the playlist for ivysilani page.

    @param url: URL of the web page
    """
    response = requests.get(url)
    page = etree.HTML(response.text)
    play_button = page.find('.//a[@class="programmeToPlaylist"]')
    item = play_button.get('rel')
    return get_playlist(item, PLAYLIST_TYPE_EPISODE)


def get_live_playlist(channel):
    """
    Extract the playlist for live CT channel.

    @param channel: Name of the channel
    """
    return get_playlist(CHANNEL_NAMES[channel], PLAYLIST_TYPE_CHANNEL)


################################################################################
def feed_stream(stream, base_url, player):
    """
    Feed segments from stream to the player.

    @param stream: Stream to be played
    @type stream: `LiveStream`
    @param base_url: Base URL for segment URIs
    @param player: Process with player
    @type player: `subprocess.Popen`
    """
    while stream:
        segment = stream.pop()
        url = urljoin(base_url, segment.uri)
        logging.debug("URL: %s", url)
        chunk = requests.get(url)
        player.stdin.write(chunk.content)


def play_live(playlist, player_cmd, _sleep=time.sleep):
    """
    Play live CT channel

    @param channel: Name of the channel
    @param player_cmd: Additional player arguments
    @type player_cmd: str
    @param _sleep: Sleep function
    """
    # Initialize the stream
    stream = LiveStream()
    response = requests.get(playlist.uri)
    logging.debug("Stream playlist: %s", response.text)
    stream.update(m3u8.loads(response.text))

    cmd = shlex.split(player_cmd)
    logging.debug("Player cmd: %s", cmd)
    player = Popen(cmd, stdin=PIPE)

    # Iteratively download the stream playlists
    while not stream.end:
        feed_stream(stream, playlist.uri, player)

        # Wait playlist duration. New media item should appear on the playlist.
        _sleep(stream.last_played.duration)

        # Get new part of the stream
        response = requests.get(playlist.uri)
        logging.debug("Stream playlist: %s", response.text)
        stream.update(m3u8.loads(response.text))

    feed_stream(stream, playlist.uri, player)


def main():
    options = docopt(__doc__, version=__version__)
    if options['<channel>'] not in CHANNEL_NAMES:
        exit("Unknown channel")
    if options['--debug']:
        level = logging.DEBUG
    else:
        level = logging.WARNING
    logging.basicConfig(stream=sys.stderr, level=level, format='%(asctime)s %(levelname)s:%(funcName)s:%(message)s')
    logging.getLogger('iso8601').setLevel(logging.WARN)

    playlist = get_playlist(options['<channel>'])
    play_live(playlist, options['--player'])


if __name__ == '__main__':
    main()
