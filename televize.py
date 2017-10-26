#!/usr/bin/env python3
"""
Plays Czech television stream in custom player

Usage: televize.py [options] live <channel>
       televize.py [options] ivysilani <url>
       televize.py -h | --help
       televize.py --version

Subcommands:
  live                 play live channel
  ivysilani            play video from ivysilani archive

Live channels:
  1                    CT1
  2                    CT2
  24                   CT24
  sport                CTsport
  D                    CT:D
  art                  CTart

Options:
  -h, --help           show this help message and exit
  --version            show program's version number and exit
  -p, --player=PLAYER  player command [default: mpv]
  -d, --debug          print debug messages
"""
import logging
import shlex
import subprocess
import sys
from collections import OrderedDict
from urllib.parse import urljoin

import m3u8
import requests
from docopt import docopt
from lxml import etree

__version__ = '0.1'


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
def play(playlist, player_cmd):
    """
    Play CT playlist

    @param playlist: Playlist to be played
    @type playlist: m3u8.model.Playlist
    @param player_cmd: Additional player arguments
    @type player_cmd: str
    """
    cmd = shlex.split(player_cmd) + [playlist.uri]
    logging.debug("Player cmd: %s", cmd)
    subprocess.call(cmd)


def main():
    options = docopt(__doc__, version=__version__)

    # Set up logging
    if options['--debug']:
        level = logging.DEBUG
    else:
        level = logging.WARNING
    logging.basicConfig(stream=sys.stderr, level=level, format='%(asctime)s %(levelname)s:%(funcName)s:%(message)s')
    logging.getLogger('iso8601').setLevel(logging.WARN)

    if options['live']:
        if options['<channel>'] not in CHANNEL_NAMES:
            exit("Unknown live channel")
        playlist = get_live_playlist(options['<channel>'])
    elif options['ivysilani']:
        playlist = get_ivysilani_playlist(options['<url>'])
    play(playlist, options['--player'])


if __name__ == '__main__':
    main()
