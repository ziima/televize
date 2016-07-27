"""
Tests for playlist objects.
"""
import unittest

from televize import Media, Playlist


class TestPlaylist(unittest.TestCase):
    """Tests of `Playlist` object"""
    def test_bool(self):
        self.assertFalse(Playlist())

        playlist = Playlist()
        playlist.add(Media(42, 'http://example.cz/1', 8.0))
        self.assertTrue(playlist)

    def test_add(self):
        playlist = Playlist()

        playlist.add(Media(42, 'http://example.cz/1', 8.0))
        playlist.add(Media(43, 'http://example.cz/2', 9.0))
        # Check skips are allowed
        playlist.add(Media(47, 'http://example.cz/67', 7.0))

        items = [Media(42, 'http://example.cz/1', 8.0), Media(43, 'http://example.cz/2', 9.0),
                 Media(47, 'http://example.cz/67', 7.0)]
        self.assertEqual(list(playlist), items)

        # Check sequence number can not be added twice
        with self.assertRaises(ValueError):
            playlist.add(Media(43, 'http://example.cz/3', 7.0))

    def test_pop(self):
        playlist = Playlist()

        # Empty playlist returns None
        self.assertIsNone(playlist.pop())

        playlist.add(Media(42, 'http://example.cz/1', 8.0))
        playlist.add(Media(43, 'http://example.cz/2', 9.0))
        playlist.add(Media(44, 'http://example.cz/3', 7.0))
        playlist.add(Media(47, 'http://example.cz/4', 8.0))

        # Check items are returned in correct order
        self.assertEqual(playlist.pop(), Media(42, 'http://example.cz/1', 8.0))
        self.assertEqual(playlist.pop(), Media(43, 'http://example.cz/2', 9.0))
        self.assertEqual(playlist.pop(), Media(44, 'http://example.cz/3', 7.0))
        self.assertEqual(playlist.pop(), Media(47, 'http://example.cz/4', 8.0))
        self.assertIsNone(playlist.pop())

    def test_update(self):
        playlist = Playlist()
        playlist.add(Media(42, '/path-1', 7.0))
        playlist.add(Media(43, '/path-2', 8.0))
        playlist.add(Media(44, '/path-3', 9.0))
        other = Playlist()
        other.add(Media(43, '/path-2', 8.0))
        other.add(Media(44, '/path-3', 9.0))
        other.add(Media(45, '/path-4', 7.0))
        other.add(Media(46, '/path-5', 8.0))

        playlist.update(other)

        items = [Media(42, '/path-1', 7.0), Media(43, '/path-2', 8.0), Media(44, '/path-3', 9.0),
                 Media(45, '/path-4', 7.0), Media(46, '/path-5', 8.0)]
        self.assertEqual(list(playlist), items)
        self.assertFalse(playlist.end)

    def test_update_end(self):
        # Check playlist updated with finished playlist
        playlist = Playlist()
        other = Playlist()
        other.add(Media(42, '/path-1', 7.0))
        other.add(Media(43, '/path-2', 8.0))
        other.end = True

        playlist.update(other)

        self.assertEqual(list(playlist), [Media(42, '/path-1', 7.0), Media(43, '/path-2', 8.0)])
        self.assertTrue(playlist.end)

    def test_update_ended(self):
        # Check playlist can be updated if already ended
        playlist = Playlist()
        playlist.end = True
        with self.assertRaises(ValueError):
            playlist.update(Playlist())
