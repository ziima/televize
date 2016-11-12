"""
Test live streaming
"""
import unittest
from subprocess import PIPE
from unittest.mock import Mock, call, patch, sentinel

from m3u8.model import Playlist

from televize import play_live

from .utils import get_path, make_response


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
        self.requests_mock.get.side_effect = [
            make_response(open(get_path(__file__, "data/play_live/playlist_1.m3u"), mode='rb').read()),
            Mock(content=sentinel.data_1),
            Mock(content=sentinel.data_2),
            Mock(content=sentinel.data_3),
            make_response(open(get_path(__file__, "data/play_live/playlist_2.m3u"), mode='rb').read()),
            Mock(content=sentinel.data_4),
        ]
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
