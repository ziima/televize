"""
Tests for `LiveStream`.
"""
import os
import unittest

import m3u8

from televize import LiveStream

from .utils import get_path


class TestLiveStream(unittest.TestCase):
    """Tests of `LiveStream` object"""
    def get_playlist(self, filename):
        data = open(get_path(__file__, os.path.join('data', filename))).read()
        return m3u8.loads(data)

    def test_bool(self):
        self.assertFalse(LiveStream())

        stream = LiveStream()
        stream.update(self.get_playlist('playlist.m3u8'))
        self.assertTrue(stream)

    def test_last_played_empty(self):
        stream = LiveStream()
        self.assertIsNone(stream.last_played)

    def test_pop_empty(self):
        stream = LiveStream()

        # Empty playlist returns None
        self.assertIsNone(stream.pop())

    def test_usage(self):
        # Test `pop()` and `last_played` attribute
        stream = LiveStream()
        stream.update(self.get_playlist('playlist.m3u8'))

        self.assertFalse(stream.end)

        seg1 = stream.pop()
        self.assertEqual(seg1.uri, '1502/57481956.ts')
        self.assertEqual(stream.last_played, seg1)
        seg2 = stream.pop()
        self.assertEqual(seg2.uri, '1502/57481957.ts')
        self.assertEqual(stream.last_played, seg2)
        seg3 = stream.pop()
        self.assertEqual(seg3.uri, '1502/57481958.ts')
        self.assertEqual(stream.last_played, seg3)
        # No more segments
        self.assertIsNone(stream.pop())
        self.assertEqual(stream.last_played, seg3)

    def test_update_twice(self):
        stream = LiveStream()
        stream.update(self.get_playlist('playlist.m3u8'))
        stream.update(self.get_playlist('playlist.m3u8'))

        self.assertFalse(stream.end)

        self.assertEqual(stream.pop().uri, '1502/57481956.ts')
        self.assertEqual(stream.pop().uri, '1502/57481957.ts')
        self.assertEqual(stream.pop().uri, '1502/57481958.ts')
        self.assertIsNone(stream.pop())

    def test_update_played(self):
        # The duplicates are removed even if the segments have already been played
        stream = LiveStream()
        stream.update(self.get_playlist('playlist.m3u8'))
        stream.pop()
        stream.pop()
        stream.pop()
        stream.update(self.get_playlist('playlist.m3u8'))

        self.assertFalse(stream.end)
        self.assertIsNone(stream.pop())

    def test_update_join(self):
        stream = LiveStream()
        stream.update(self.get_playlist(os.path.join('play_live', 'playlist_1.m3u')))
        stream.update(self.get_playlist(os.path.join('play_live', 'playlist_2.m3u')))

        self.assertEqual(stream.pop().uri, '1502/58877187.ts')
        self.assertEqual(stream.pop().uri, '1502/58877188.ts')
        self.assertEqual(stream.pop().uri, '1502/58877189.ts')
        self.assertEqual(stream.pop().uri, '1502/58877190.ts')
        self.assertIsNone(stream.pop())

    def test_update_end(self):
        # Check playlist updated with finished playlist
        stream = LiveStream()
        stream.update(self.get_playlist('playlist.m3u8'))
        stream.update(self.get_playlist('playlist_end.m3u8'))

        self.assertTrue(stream.end)

        self.assertEqual(stream.pop().uri, '1502/57481956.ts')
        self.assertEqual(stream.pop().uri, '1502/57481957.ts')
        self.assertEqual(stream.pop().uri, '1502/57481958.ts')
        self.assertIsNone(stream.pop())

    def test_update_ended(self):
        # Check playlist can be updated if already ended
        stream = LiveStream()
        stream.end = True
        with self.assertRaises(ValueError):
            stream.update(self.get_playlist('playlist.m3u8'))

    def test_update_date_time_shift(self):
        # Check playlist updated with playlist with EXT-X-PROGRAM-DATE-TIME shifted from previous playlist
        stream = LiveStream()
        stream.update(self.get_playlist(os.path.join('date_time_shift', 'playlist_1.m3u8')))
        stream.update(self.get_playlist(os.path.join('date_time_shift', 'playlist_2.m3u8')))
        stream.update(self.get_playlist(os.path.join('date_time_shift', 'playlist_3.m3u8')))

        self.assertEqual(stream.pop().uri, '1502/61784492.ts')
        self.assertEqual(stream.pop().uri, '1502/61784493.ts')
        self.assertEqual(stream.pop().uri, '1502/61784494.ts')
        self.assertEqual(stream.pop().uri, '1502/61784495.ts')
        self.assertEqual(stream.pop().uri, '1502/61784496.ts')
        self.assertIsNone(stream.pop())
