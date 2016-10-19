import os
import unittest

import m3u8

from televize import LiveStream, feed_stream

try:
    from unittest.mock import Mock, call, patch, sentinel  # Python3
except ImportError:
    from mock import Mock, call, patch, sentinel  # Python2


class TestFeedStream(unittest.TestCase):
    """Tests of `feed_stream` function"""
    def setUp(self):
        patcher = patch('televize.requests')
        self.addCleanup(patcher.stop)
        self.requests_mock = patcher.start()

    def test_empty(self):
        empty = LiveStream()
        feed_stream(empty, sentinel.base_url, sentinel.mplayer)
        self.assertEqual(self.requests_mock.mock_calls, [])

    def test_feed(self):
        stream = LiveStream()
        data = open(os.path.join(os.path.dirname(__file__), 'data', 'playlist.m3u8')).read()
        stream.update(m3u8.loads(data))
        self.requests_mock.get.side_effect = [Mock(content=sentinel.data_1), Mock(content=sentinel.data_2),
                                              Mock(content=sentinel.data_3)]
        mplayer_mock = Mock()

        feed_stream(stream, 'http://example.com/', mplayer_mock)

        self.assertIsNone(stream.pop())
        self.assertEqual(self.requests_mock.mock_calls, [call.get('http://example.com/1502/57481956.ts'),
                                                         call.get('http://example.com/1502/57481957.ts'),
                                                         call.get('http://example.com/1502/57481958.ts')])
        self.assertEqual(mplayer_mock.mock_calls, [call.stdin.write(sentinel.data_1), call.stdin.write(sentinel.data_2),
                                                   call.stdin.write(sentinel.data_3)])
