"""
Tests for playlist parsers.
"""
import os
import unittest

from televize import Media, PlaylistParser


class TestPlaylistParsers(unittest.TestCase):
    """Tests of playlist parsers."""
    def test_playlist(self):
        parser = PlaylistParser()

        with open(os.path.join(os.path.dirname(__file__), "data/playlist.m3u8")) as buff:
            playlist = parser.parse(buff, 'http://example.cz/')

        items = [Media(57481956, 'http://example.cz/1502/57481956.ts', 7.0),
                 Media(57481957, 'http://example.cz/1502/57481957.ts', 8.0),
                 Media(57481958, 'http://example.cz/1502/57481958.ts', 9.0)]
        self.assertEqual(list(playlist), items)
        self.assertFalse(playlist.end)

    def test_playlist_end(self):
        parser = PlaylistParser()

        with open(os.path.join(os.path.dirname(__file__), "data/playlist_end.m3u8")) as buff:
            playlist = parser.parse(buff, 'http://example.cz/')

        items = [Media(57481956, 'http://example.cz/1502/57481956.ts', 7.0),
                 Media(57481957, 'http://example.cz/1502/57481957.ts', 8.0),
                 Media(57481958, 'http://example.cz/1502/57481958.ts', 9.0)]
        self.assertEqual(list(playlist), items)
        self.assertTrue(playlist.end)

    def test_playlist_invalid(self):
        parser = PlaylistParser()

        with open(os.path.join(os.path.dirname(__file__), "data/invalid.m3u8")) as buff:
            with self.assertRaises(ValueError):
                parser.parse(buff, 'http://example.cz/')

        with open(os.path.join(os.path.dirname(__file__), "data/invalid_line.m3u8")) as buff:
            with self.assertRaises(ValueError):
                parser.parse(buff, 'http://example.cz/')
