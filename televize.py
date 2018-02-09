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
  -q, --quality=QUAL   select stream quality [default: min]. Possible values are integers, 'min' and 'max'.
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

__version__ = '0.2'


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
def parse_quality(value: str) -> int:
    """Return quality selector parsed from user input value.

    @raises ValueError: If value is not a valid quality selector.
    """
    # Special keywords
    if value == 'min':
        return 0
    elif value == 'max':
        return -1
    try:
        return int(value)
    except ValueError:
        raise ValueError("Quality '{}' is not a valid value.".format(value))


def get_playlist(playlist_id, playlist_type, quality: int):
    """
    Extract the playlist for CT video.

    @param playlist_id: ID of playlist
    @param playlist_type: Type of playlist
    @param quality: Quality selector
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

    # Select stream based on quality
    playlists = sorted(variant_playlist.playlists, key=lambda p: p.stream_info.bandwidth)
    try:
        return playlists[quality]
    except IndexError:
        raise ValueError("Requested quality {} is not available.".format(quality))


def get_ivysilani_playlist(url, quality: int):
    """
    Extract the playlist for ivysilani page.

    @param url: URL of the web page
    @param quality: Quality selector
    """
    response = requests.get(url)
    page = etree.HTML(response.text)
    play_button = page.find('.//a[@class="programmeToPlaylist"]')
    item = play_button.get('rel')
    return get_playlist(item, PLAYLIST_TYPE_EPISODE, quality)


def get_live_playlist(channel, quality: int):
    """
    Extract the playlist for live CT channel.

    @param channel: Name of the channel
    @param quality: Quality selector
    """
    return get_playlist(CHANNEL_NAMES[channel], PLAYLIST_TYPE_CHANNEL, quality)


################################################################################
def run_player(playlist: m3u8.model.Playlist, player_cmd: str):
    """Run the video player

    @param playlist: Playlist to be played
    @param player_cmd: Additional player arguments
    """
    cmd = shlex.split(player_cmd) + [playlist.uri]
    logging.debug("Player cmd: %s", cmd)
    subprocess.call(cmd)


def play(options):
    """Play televize.

    @raises ValueError: In case of an invalid options.
    """
    quality = parse_quality(options['--quality'])
    if options['live']:
        if options['<channel>'] not in CHANNEL_NAMES:
            raise ValueError("Unknown live channel '{}'".format(options['<channel>']))
        playlist = get_live_playlist(options['<channel>'], quality)
    else:
        assert options['ivysilani']
        playlist = get_ivysilani_playlist(options['<url>'], quality)
    run_player(playlist, options['--player'])


def main():
    """Main script."""
    options = docopt(__doc__, version=__version__)

    # Set up logging
    if options['--debug']:
        level = logging.DEBUG
    else:
        level = logging.WARNING
    logging.basicConfig(stream=sys.stderr, level=level, format='%(asctime)s %(levelname)s:%(funcName)s: %(message)s')
    logging.getLogger('iso8601').setLevel(logging.WARN)

    try:
        play(options)
    except Exception as error:
        if level == logging.DEBUG:
            logging.exception("An error occured:")
        else:
            logging.warn("An error occured: %s", error)
        exit(1)
    except KeyboardInterrupt:
        # User killed the program, silence the exception
        exit(0)


if __name__ == '__main__':
    main()
