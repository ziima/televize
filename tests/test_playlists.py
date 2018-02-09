"""
Test playlist functions
"""
import unittest
from unittest.mock import call, patch, sentinel

from m3u8.model import Playlist

from televize import (PLAYLIST_TYPE_CHANNEL, PLAYLIST_TYPE_EPISODE, get_ivysilani_playlist, get_live_playlist,
                      get_playlist, parse_quality)

from .utils import get_path, make_response


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
        with self.assertRaisesRegexp(ValueError, "^Quality 'invalid' is not a valid value.$"):
            parse_quality('invalid')


class TestGetPlaylist(unittest.TestCase):
    """Test `get_playlist` function"""
    def setUp(self):
        patcher = patch('televize.requests')
        self.addCleanup(patcher.stop)
        self.requests_mock = patcher.start()

    def test_get_playlist(self):
        self.requests_mock.get.side_effect = [
            make_response(open(get_path(__file__, 'data/play_live/client_playlist.json'), mode='rb').read()),
            make_response(open(get_path(__file__, 'data/play_live/stream_playlist.m3u'), mode='rb').read()),
        ]
        post_responses = [make_response(b'{"url":"http:\/\/www.ceskatelevize.cz\/ivysilani\/client-playlist\/'
                                        b'?key=df365c9c2ea8b36f76dfa29e3b16d245"}')]
        self.requests_mock.post.side_effect = post_responses

        playlist = get_playlist(sentinel.playlist_id, PLAYLIST_TYPE_CHANNEL, 0)

        self.assertIsInstance(playlist, Playlist)
        playlist_uri = 'http://80.188.78.151:80/atip/fd2eccaa99022586e14694df91068915/1449324471384/' \
                       '3616440c710a1d7e3f54761a6d940c64/2402-tv-pc/1502.m3u8'
        self.assertEqual(playlist.uri, playlist_uri)
        self.assertEqual(playlist.stream_info.bandwidth, 500000)
        calls = [
            call.post('http://www.ceskatelevize.cz/ivysilani/ajax/get-client-playlist',
                      {'playlist[0][id]': sentinel.playlist_id, 'playlist[0][type]': PLAYLIST_TYPE_CHANNEL,
                       'requestUrl': '/ivysilani/', 'requestSource': 'iVysilani', 'addCommercials': 0, 'type': 'html'},
                      headers={'x-addr': '127.0.0.1'}),
            call.get('http://www.ceskatelevize.cz/ivysilani/client-playlist/?key=df365c9c2ea8b36f76dfa29e3b16d245'),
            call.get('http://80.188.65.18:80/cdn/uri/get/?token=fa8a25eb4f77fafdf17a3f3ced84fcfcc76e4ac2&contentType'
                     '=live&expiry=1449327687&id=2402&playerType=flash&quality=web&region=1&skipIpAddressCheck=false'
                     '&userId=823c8699-a1d0-41e2-aabc-1101c128cdab'),
        ]
        self.assertEqual(self.requests_mock.mock_calls, calls)

    def test_get_playlist_invalid_quality(self):
        self.requests_mock.get.side_effect = [
            make_response(open(get_path(__file__, 'data/play_live/client_playlist.json'), mode='rb').read()),
            make_response(open(get_path(__file__, 'data/play_live/stream_playlist.m3u'), mode='rb').read()),
        ]
        post_responses = [make_response(b'{"url":"http:\/\/www.ceskatelevize.cz\/ivysilani\/client-playlist\/'
                                        b'?key=df365c9c2ea8b36f76dfa29e3b16d245"}')]
        self.requests_mock.post.side_effect = post_responses

        with self.assertRaisesRegexp(ValueError, "Requested quality 42 is not available."):
            get_playlist(sentinel.playlist_id, PLAYLIST_TYPE_CHANNEL, 42)


class TestGetIvysilaniPlaylist(unittest.TestCase):
    """Test `get_ivysilani_playlist` function"""
    def setUp(self):
        patcher = patch('televize.requests')
        self.addCleanup(patcher.stop)
        self.requests_mock = patcher.start()

        patcher = patch('televize.get_playlist')
        self.addCleanup(patcher.stop)
        self.get_playlist_mock = patcher.start()

    def test_get_ivysilani_playlist(self):
        get_responses = [make_response(open(get_path(__file__, 'data/ivysilani.html'), mode='rb').read())]
        self.requests_mock.get.side_effect = get_responses
        self.get_playlist_mock.return_value = sentinel.playlist
        self.assertEqual(get_ivysilani_playlist(sentinel.url, 0), sentinel.playlist)
        self.assertEqual(self.get_playlist_mock.mock_calls, [call('987650004321', PLAYLIST_TYPE_EPISODE, 0)])


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
