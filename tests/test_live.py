"""
Test live streaming
"""
import os.path
import unittest
from io import BytesIO
from subprocess import PIPE
from unittest.mock import Mock, call, patch, sentinel

from m3u8.model import Playlist
from requests import Response

from televize import get_playlist, play_live


def _make_response(content):
    response = Response()
    response.raw = BytesIO(content)
    return response


class TestGetPlaylist(unittest.TestCase):
    """Test `get_playlist` function"""
    def setUp(self):
        patcher = patch('televize.requests')
        self.addCleanup(patcher.stop)
        self.requests_mock = patcher.start()

    def test_get_playlist(self):
        get_responses = [
            _make_response(
                open(os.path.join(os.path.dirname(__file__), "data/play_live/client_playlist.json"), mode='rb').read(),
            ),
            _make_response(
                open(os.path.join(os.path.dirname(__file__), "data/play_live/stream_playlist.m3u"), mode='rb').read(),
            ),
        ]
        post_responses = [_make_response(b'{"url":"http:\/\/www.ceskatelevize.cz\/ivysilani\/client-playlist\/'
                                         b'?key=df365c9c2ea8b36f76dfa29e3b16d245"}')]
        self.requests_mock.get.side_effect = get_responses
        self.requests_mock.post.side_effect = post_responses

        playlist = get_playlist('24')

        self.assertIsInstance(playlist, Playlist)
        playlist_uri = 'http://80.188.78.151:80/atip/fd2eccaa99022586e14694df91068915/1449324471384/' \
                       '3616440c710a1d7e3f54761a6d940c64/2402-tv-pc/1502.m3u8'
        self.assertEqual(playlist.uri, playlist_uri)
        self.assertEqual(playlist.stream_info.bandwidth, 500000)
        calls = [
            call.post('http://www.ceskatelevize.cz/ivysilani/ajax/get-client-playlist',
                      {'type': 'html', 'requestUrl': '/ivysilani/embed/iFramePlayerCT24.php',
                       'playlist[0][type]': 'channel', 'playlist[0][id]': 24, 'requestSource': 'iVysilani',
                       'addCommercials': 0},
                      headers={'x-addr': '127.0.0.1'}),
            call.get('http://www.ceskatelevize.cz/ivysilani/client-playlist/?key=df365c9c2ea8b36f76dfa29e3b16d245'),
            call.get('http://80.188.65.18:80/cdn/uri/get/?token=fa8a25eb4f77fafdf17a3f3ced84fcfcc76e4ac2&contentType'
                     '=live&expiry=1449327687&id=2402&playerType=flash&quality=web&region=1&skipIpAddressCheck=false'
                     '&userId=823c8699-a1d0-41e2-aabc-1101c128cdab'),
        ]
        self.assertEqual(self.requests_mock.mock_calls, calls)


class TestPlayLive(unittest.TestCase):
    """Test `play_live` function"""
    def setUp(self):
        patcher = patch('televize.requests')
        self.addCleanup(patcher.stop)
        self.requests_mock = patcher.start()

        popen_patcher = patch('televize.Popen')
        self.addCleanup(popen_patcher.stop)
        self.popen_mock = popen_patcher.start()

    def test_play_live(self):
        get_responses = [
            _make_response(
                open(os.path.join(os.path.dirname(__file__), "data/play_live/playlist_1.m3u"), mode='rb').read(),
            ),
            Mock(content=sentinel.data_1),
            Mock(content=sentinel.data_2),
            Mock(content=sentinel.data_3),
            _make_response(
                open(os.path.join(os.path.dirname(__file__), "data/play_live/playlist_2.m3u"), mode='rb').read(),
            ),
            Mock(content=sentinel.data_4),
        ]
        self.requests_mock.get.side_effect = get_responses
        sleep_mock = Mock()
        playlist_uri = 'http://80.188.78.151:80/atip/fd2eccaa99022586e14694df91068915/1449324471384/' \
                       '3616440c710a1d7e3f54761a6d940c64/2402-tv-pc/1502.m3u8'
        playlist = Playlist(playlist_uri, {'bandwidth': 500000}, None, None)

        play_live(playlist, 'my_player "Custom Argument" --', _sleep=sleep_mock)

        calls = [
            call.get('http://80.188.78.151:80/atip/fd2eccaa99022586e14694df91068915/1449324471384/'
                     '3616440c710a1d7e3f54761a6d940c64/2402-tv-pc/1502.m3u8'),
            call.get('http://80.188.78.151:80/atip/fd2eccaa99022586e14694df91068915/1449324471384/'
                     '3616440c710a1d7e3f54761a6d940c64/2402-tv-pc/1502/58877187.ts'),
            call.get('http://80.188.78.151:80/atip/fd2eccaa99022586e14694df91068915/1449324471384/'
                     '3616440c710a1d7e3f54761a6d940c64/2402-tv-pc/1502/58877188.ts'),
            call.get('http://80.188.78.151:80/atip/fd2eccaa99022586e14694df91068915/1449324471384/'
                     '3616440c710a1d7e3f54761a6d940c64/2402-tv-pc/1502/58877189.ts'),
            call.get('http://80.188.78.151:80/atip/fd2eccaa99022586e14694df91068915/1449324471384/'
                     '3616440c710a1d7e3f54761a6d940c64/2402-tv-pc/1502.m3u8'),
            call.get('http://80.188.78.151:80/atip/fd2eccaa99022586e14694df91068915/1449324471384/'
                     '3616440c710a1d7e3f54761a6d940c64/2402-tv-pc/1502/58877190.ts'),
        ]
        self.assertEqual(self.requests_mock.mock_calls, calls)
        self.assertEqual(sleep_mock.mock_calls, [call(8.0)])
        popen_calls = [call(['my_player', 'Custom Argument', '--'], stdin=PIPE),
                       call().stdin.write(sentinel.data_1),
                       call().stdin.write(sentinel.data_2),
                       call().stdin.write(sentinel.data_3),
                       call().stdin.write(sentinel.data_4)]
        self.assertEqual(self.popen_mock.mock_calls, popen_calls)
