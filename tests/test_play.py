"""
Test live streaming
"""
import unittest
from unittest.mock import call, patch

import responses
from m3u8.model import Playlist

from televize import play, run_player

from .utils import get_path


class TestRunPlayer(unittest.TestCase):
    """Test `run_player` function"""
    def setUp(self):
        call_patcher = patch('televize.subprocess.call')
        self.addCleanup(call_patcher.stop)
        self.call_mock = call_patcher.start()

    def test_run_player_live(self):
        playlist_uri = 'http://example.cz/path/playlist.m3u8'
        playlist = Playlist(playlist_uri, {'bandwidth': 500000}, None, None)

        run_player(playlist, 'my_player "Custom Argument"')

        self.assertEqual(self.call_mock.mock_calls, [call(['my_player', 'Custom Argument', playlist_uri])])


class TestPlay(unittest.TestCase):
    """Test `play` function"""

    def setUp(self):
        call_patcher = patch('televize.subprocess.call')
        self.addCleanup(call_patcher.stop)
        self.call_mock = call_patcher.start()

    def test_play_live(self):
        options = {'live': True, '<channel>': '24', '--player': 'mpv', '--quality': 'min'}
        playlist_url = 'http://www.ceskatelevize.cz/ivysilani/client-playlist/?key=df365c9c2ea8b36f76dfa29e3b16d245'

        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, 'http://www.ceskatelevize.cz/ivysilani/ajax/get-client-playlist',
                     json={'url': playlist_url}),
            rsps.add(responses.GET, 'http://www.ceskatelevize.cz/ivysilani/client-playlist/',
                     body=open(get_path(__file__, 'data/play_live/client_playlist.json')).read())
            rsps.add(responses.GET, 'http://80.188.65.18:80/cdn/uri/get/',
                     body=open(get_path(__file__, 'data/play_live/stream_playlist.m3u')).read())
            play(options)

        stream_url = ('http://80.188.78.151:80/atip/fd2eccaa99022586e14694df91068915/1449324471384/'
                      '3616440c710a1d7e3f54761a6d940c64/2402-tv-pc/1502.m3u8')
        self.assertEqual(self.call_mock.mock_calls, [call(['mpv', stream_url])])

    def test_play_live_unknown(self):
        options = {'live': True, '<channel>': 'unknown', '--quality': 'min'}

        with self.assertRaisesRegexp(ValueError, "^Unknown live channel 'unknown'$"):
            play(options)

    def test_play_ivysilani(self):
        options = {'live': False, 'ivysilani': True, '<url>': 'http://www.ceskatelevize.cz/ivysilani/kosmo.html',
                   '--player': 'mpv', '--quality': 'min'}
        playlist_url = 'http://www.ceskatelevize.cz/ivysilani/client-playlist/?key=df365c9c2ea8b36f76dfa29e3b16d245'

        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, 'http://www.ceskatelevize.cz/ivysilani/kosmo.html',
                     body=open(get_path(__file__, 'data/ivysilani.html'), mode='r').read())
            rsps.add(responses.POST, 'http://www.ceskatelevize.cz/ivysilani/ajax/get-client-playlist',
                     json={'url': playlist_url}),
            rsps.add(responses.GET, 'http://www.ceskatelevize.cz/ivysilani/client-playlist/',
                     body=open(get_path(__file__, 'data/play_live/client_playlist.json')).read())
            rsps.add(responses.GET, 'http://80.188.65.18:80/cdn/uri/get/',
                     body=open(get_path(__file__, 'data/play_live/stream_playlist.m3u')).read())
            play(options)

        stream_url = ('http://80.188.78.151:80/atip/fd2eccaa99022586e14694df91068915/1449324471384/'
                      '3616440c710a1d7e3f54761a6d940c64/2402-tv-pc/1502.m3u8')
        self.assertEqual(self.call_mock.mock_calls, [call(['mpv', stream_url])])
