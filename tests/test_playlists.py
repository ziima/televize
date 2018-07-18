"""
Test playlist functions
"""
import unittest
from unittest.mock import call, patch, sentinel

import responses
from m3u8.model import Playlist

from televize import (PLAYLIST_TYPE_CHANNEL, PLAYLIST_TYPE_EPISODE, get_ivysilani_playlist, get_live_playlist,
                      get_playlist, parse_quality)

from .utils import get_content, get_path


class TestParseQuality(unittest.TestCase):
    """Test `parse_quality` function."""

    def test_keywords(self):
        self.assertEqual(parse_quality('min'), 0)
        self.assertEqual(parse_quality('max'), -1)

    def test_conversion(self):
        self.assertEqual(parse_quality('0'), 0)
        self.assertEqual(parse_quality('1'), 1)
        self.assertEqual(parse_quality('2'), 2)
        self.assertEqual(parse_quality('3'), 3)
        self.assertEqual(parse_quality('-1'), -1)
        self.assertEqual(parse_quality('-2'), -2)
        self.assertEqual(parse_quality('-3'), -3)

    def test_invalid(self):
        with self.assertRaisesRegex(ValueError, "^Quality 'invalid' is not a valid value.$"):
            parse_quality('invalid')


class TestGetPlaylist(unittest.TestCase):
    """Test `get_playlist` function"""

    def test_get_playlist(self):
        playlist_url = 'https://www.ceskatelevize.cz/ivysilani/client-playlist/?key=df365c9c2ea8b36f76dfa29e3b16d245'
        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, 'https://www.ceskatelevize.cz/ivysilani/ajax/get-client-playlist/',
                     json={'url': playlist_url}),
            rsps.add(responses.GET, 'https://www.ceskatelevize.cz/ivysilani/client-playlist/',
                     body=get_content(get_path(__file__, 'data/play_live/client_playlist.json')))
            rsps.add(responses.GET, 'http://80.188.65.18:80/cdn/uri/get/',
                     body=get_content(get_path(__file__, 'data/play_live/stream_playlist.m3u')))

            playlist = get_playlist(sentinel.playlist_id, PLAYLIST_TYPE_CHANNEL, 0)

        self.assertIsInstance(playlist, Playlist)
        playlist_uri = 'http://80.188.78.151:80/atip/fd2eccaa99022586e14694df91068915/1449324471384/' \
                       '3616440c710a1d7e3f54761a6d940c64/2402-tv-pc/1502.m3u8'
        self.assertEqual(playlist.uri, playlist_uri)
        self.assertEqual(playlist.stream_info.bandwidth, 500000)

    def test_get_playlist_invalid_quality(self):
        playlist_url = 'https://www.ceskatelevize.cz/ivysilani/client-playlist/?key=df365c9c2ea8b36f76dfa29e3b16d245'
        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, 'https://www.ceskatelevize.cz/ivysilani/ajax/get-client-playlist/',
                     json={'url': playlist_url}),
            rsps.add(responses.GET, 'https://www.ceskatelevize.cz/ivysilani/client-playlist/',
                     body=get_content(get_path(__file__, 'data/play_live/client_playlist.json')))
            rsps.add(responses.GET, 'http://80.188.65.18:80/cdn/uri/get/',
                     body=get_content(get_path(__file__, 'data/play_live/stream_playlist.m3u')))

            with self.assertRaisesRegex(ValueError, "Requested quality 42 is not available."):
                get_playlist(sentinel.playlist_id, PLAYLIST_TYPE_CHANNEL, 42)


class TestGetIvysilaniPlaylist(unittest.TestCase):
    """Test `get_ivysilani_playlist` function"""
    def setUp(self):
        patcher = patch('televize.get_playlist')
        self.addCleanup(patcher.stop)
        self.get_playlist_mock = patcher.start()

    def test_get_ivysilani_playlist(self):
        self.get_playlist_mock.return_value = sentinel.playlist

        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, 'https://www.ceskatelevize.cz/ivysilani/11276561613-kosmo/',
                     body=get_content(get_path(__file__, 'data/ivysilani.html')))

            self.assertEqual(get_ivysilani_playlist('https://www.ceskatelevize.cz/ivysilani/11276561613-kosmo/', 0),
                             sentinel.playlist)

        self.assertEqual(self.get_playlist_mock.mock_calls, [call('987650004321', PLAYLIST_TYPE_EPISODE, 0)])

    def test_get_ivysilani_playlist_no_button(self):
        self.get_playlist_mock.return_value = sentinel.playlist

        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, 'https://www.ceskatelevize.cz/ivysilani/11276561613-kosmo/',
                     body=get_content(get_path(__file__, 'data/ivysilani_no_button.html')))

            with self.assertRaisesRegex(ValueError, "Can't find playlist on the ivysilani page."):
                get_ivysilani_playlist('https://www.ceskatelevize.cz/ivysilani/11276561613-kosmo/', 0)

    def test_get_ivysilani_playlist_no_rel(self):
        self.get_playlist_mock.return_value = sentinel.playlist

        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, 'https://www.ceskatelevize.cz/ivysilani/11276561613-kosmo/',
                     body=get_content(get_path(__file__, 'data/ivysilani_no_rel.html')))

            with self.assertRaisesRegex(ValueError, "Can't find playlist on the ivysilani page."):
                get_ivysilani_playlist('https://www.ceskatelevize.cz/ivysilani/11276561613-kosmo/', 0)

    def test_get_ivysilani_playlist_porady(self):
        self.get_playlist_mock.return_value = sentinel.playlist
        self.assertEqual(
            get_ivysilani_playlist('https://www.ceskatelevize.cz/porady/11276561613-kosmo/215512121020005-triumf', 0),
            sentinel.playlist)
        self.assertEqual(self.get_playlist_mock.mock_calls, [call('215512121020005', PLAYLIST_TYPE_EPISODE, 0)])


class TestGetLivePlaylist(unittest.TestCase):
    """Test `get_live_playlist` function"""
    def setUp(self):
        patcher = patch('televize.get_playlist')
        self.addCleanup(patcher.stop)
        self.get_playlist_mock = patcher.start()

    def test_get_live_playlist(self):
        self.get_playlist_mock.return_value = sentinel.playlist
        self.assertEqual(get_live_playlist('24', 0), sentinel.playlist)
        self.assertEqual(self.get_playlist_mock.mock_calls, [call(24, PLAYLIST_TYPE_CHANNEL, 0)])
