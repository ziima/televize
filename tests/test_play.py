"""
Test live streaming
"""
import unittest
from unittest.mock import call, patch

from m3u8.model import Playlist

from televize import play


class TestPlay(unittest.TestCase):
    """Test `play` function"""
    def setUp(self):
        call_patcher = patch('televize.subprocess.call')
        self.addCleanup(call_patcher.stop)
        self.call_mock = call_patcher.start()

    def test_play_live(self):
        playlist_uri = 'http://example.cz/path/playlist.m3u8'
        playlist = Playlist(playlist_uri, {'bandwidth': 500000}, None, None)

        play(playlist, 'my_player "Custom Argument"')

        self.assertEqual(self.call_mock.mock_calls, [call(['my_player', 'Custom Argument', playlist_uri])])
