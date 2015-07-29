"""
Tests for playlist parsers.
"""
import os
import unittest

from televize import Media, PlaylistParser, Stream, VariantPlaylistParser


class TestPlaylistParsers(unittest.TestCase):
    """Tests of playlist parsers."""
    def test_variant_playlist(self):
        parser = VariantPlaylistParser()

        with open(os.path.join(os.path.dirname(__file__), "data/variants.m3u8")) as buff:
            playlist = parser.parse(buff)

        self.assertEqual(playlist[500000], Stream('http://example.cz/path/to/playlist-1.m3u8', 500000))
        self.assertEqual(playlist[1032000], Stream('http://example.cz/path/to/playlist-2.m3u8', 1032000))
        self.assertEqual(playlist[2048000], Stream('http://example.cz/path/to/playlist-3.m3u8', 2048000))
        self.assertEqual(playlist[3584000], Stream('http://example.cz/path/to/playlist-4.m3u8', 3584000))

    def test_variant_playlist_invalid(self):
        parser = VariantPlaylistParser()

        with open(os.path.join(os.path.dirname(__file__), "data/invalid.m3u8")) as buff:
            with self.assertRaises(ValueError):
                parser.parse(buff)

        with open(os.path.join(os.path.dirname(__file__), "data/invalid_line.m3u8")) as buff:
            with self.assertRaises(ValueError):
                parser.parse(buff)

    def test_playlist(self):
        parser = PlaylistParser()

        with open(os.path.join(os.path.dirname(__file__), "data/playlist.m3u8")) as buff:
            playlist = parser.parse(buff)

        items = [Media(57481956, '1502/57481956.ts', 7.0), Media(57481957, '1502/57481957.ts', 8.0),
                 Media(57481958, '1502/57481958.ts', 9.0)]
        self.assertEqual(list(playlist), items)
        self.assertFalse(playlist.end)

    def test_playlist_end(self):
        parser = PlaylistParser()

        with open(os.path.join(os.path.dirname(__file__), "data/playlist_end.m3u8")) as buff:
            playlist = parser.parse(buff)

        items = [Media(57481956, '1502/57481956.ts', 7.0), Media(57481957, '1502/57481957.ts', 8.0),
                 Media(57481958, '1502/57481958.ts', 9.0)]
        self.assertEqual(list(playlist), items)
        self.assertTrue(playlist.end)

    def test_playlist_invalid(self):
        parser = PlaylistParser()

        with open(os.path.join(os.path.dirname(__file__), "data/invalid.m3u8")) as buff:
            with self.assertRaises(ValueError):
                parser.parse(buff)

        with open(os.path.join(os.path.dirname(__file__), "data/invalid_line.m3u8")) as buff:
            with self.assertRaises(ValueError):
                parser.parse(buff)
