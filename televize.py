#!/usr/bin/env python3
"""Play Czech television stream in custom player.

Usage: televize.py [options] channels
       televize.py [options] live <channel>
       televize.py [options] ivysilani <url>
       televize.py -h | --help
       televize.py --version

Subcommands:
  channels             print a list of available channels
  live                 play live channel
  ivysilani            play video from ivysilani archive

Options:
  -h, --help           show this help message and exit
  --version            show program's version number and exit
  -q, --quality=QUAL   select stream quality [default: 540p]. Commonly available are 180p, 360p, 540p, 720p and 1080p.
  -p, --player=PLAYER  player command [default: mpv]
  -d, --debug          print debug messages
"""
import logging
import re
import shlex
import subprocess  # nosec
import sys
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional
from urllib.parse import urljoin, urlsplit

import requests
from docopt import docopt

__version__ = '0.6.0'


################################################################################
# Channels API

CHANNELS_LINK = "https://ct24.ceskatelevize.cz/api/live"


@dataclass
class Channel:
    """Represents a TV channel.

    Attributes:
        id: Channel ID
        name: Channel name
        slug: Channel slug
        title: Current or next programme title
    """
    id: str
    name: str
    slug: str
    title: Optional[str] = None


def get_channels() -> Iterable[Channel]:
    """Iterate over available channels."""
    response = requests.get(CHANNELS_LINK, timeout=10)
    logging.debug("Channels response[%s]: %s", response.status_code, response.text)
    response.raise_for_status()
    for channel_data in response.json()["data"]:
        if not channel_data.get("__typename") == "LiveBroadcast":
            # Skip non-live channels
            continue
        if current := channel_data.get('current'):
            name = current['channelSettings']['channelName']
            slug = current['slug']
            title = current['title']
        elif next := channel_data.get('next'):
            name = next['channelSettings']['channelName']
            slug = next['slug']
            title = next['title']
        else:
            name = ''
            slug = ''
            title = None

        yield Channel(id=channel_data['id'], name=name, slug=slug, title=title)


def print_channels(channels: Iterable[Channel]) -> None:
    """List available channels."""
    for channel in channels:
        print(f"{channel.slug}: {channel.name} - {channel.title}")


################################################################################
# Playlist functions
LIVE_PLAYLIST_LINK = "https://api.ceskatelevize.cz/video/v1/playlist-live/v1/stream-data/channel/"


def get_live_playlist(channel: str, quality: str) -> str:
    """Return playlist URL for live CT channel.

    @param channel: Channel slug
    @param quality: Requested quality
    """
    channels = {c.slug: c for c in get_channels()}
    if channel not in channels:
        raise ValueError(f"Channel {channel} not found.")
    channel_obj = channels[channel]

    data = {'quality': quality}
    response = requests.get(urljoin(LIVE_PLAYLIST_LINK, channel_obj.id), data, timeout=10)
    logging.debug("Live playlist response[%s]: %s", response.status_code, response.text)
    response.raise_for_status()

    playlist_data = response.json()
    return playlist_data["streamUrls"]["main"]


IVYSILANI_PLAYLIST_LINK = "https://api.ceskatelevize.cz/video/v1/playlist-vod/v1/stream-data/media/external/"


def get_ivysilani_playlist(program_id: str, quality: str) -> str:
    """Return playlist URL for ivysilani.

    @param program_id: Program ID
    @param quality: Requested quality
    """
    data = {'quality': quality}
    response = requests.get(urljoin(IVYSILANI_PLAYLIST_LINK, program_id), data, timeout=10)
    logging.debug("Ivysilani playlist response[%s]: %s", response.status_code, response.text)
    response.raise_for_status()

    playlist_data = response.json()
    return playlist_data["streams"][0]["url"]


################################################################################
def run_player(playlist: str, player_cmd: str) -> None:
    """Run the video player.

    @param playlist: Playlist URL to be played
    @param player_cmd: Player command
    """
    cmd = shlex.split(player_cmd) + [playlist]
    logging.debug("Player cmd: %s", cmd)
    subprocess.call(cmd)  # nosec


def play_live(options: Dict[str, Any]) -> None:
    """Play live channel."""
    playlist = get_live_playlist(options['<channel>'], options['--quality'])
    run_player(playlist, options['--player'])


PORADY_PATH_PATTERN = re.compile(r'^/porady/[^/]+/(?P<playlist_id>\d+)(-[^/]*)?/?$')


def play_ivysilani(options: Dict[str, Any]) -> None:
    """Play live channel.

    Raises:
        ValueError: Program not found.
    """
    # Porady pages have playlist ID in URL
    split = urlsplit(options["<url>"])
    match = PORADY_PATH_PATTERN.match(split.path)
    if match:
        playlist_id = match.group('playlist_id')
        playlist = get_ivysilani_playlist(playlist_id, options['--quality'])
        run_player(playlist, options['--player'])

    if not match:
        # TODO: Fetch porady page and play the most recent video.
        raise ValueError("Video not found.")


def main() -> None:
    """Play Czech television stream in custom player."""
    options = docopt(__doc__, version=__version__)

    # Set up logging
    if options['--debug']:
        level = logging.DEBUG
    else:
        level = logging.WARNING
    logging.basicConfig(stream=sys.stderr, level=level, format='%(asctime)s %(levelname)s:%(funcName)s: %(message)s')
    logging.getLogger('iso8601').setLevel(logging.WARN)

    try:
        channels = get_channels()
        if options['channels']:
            print_channels(channels)
        elif options['live']:
            play_live(options)
        else:
            assert options['ivysilani']  # nosec
            play_ivysilani(options)
    except Exception as error:
        if level == logging.DEBUG:
            logging.exception("An error occured:")
        else:
            logging.warning("An error occured: %s", error)
        exit(1)
    except KeyboardInterrupt:
        # User killed the program, silence the exception
        exit(0)


if __name__ == '__main__':
    main()
