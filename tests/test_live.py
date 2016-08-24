"""
Test live streaming
"""
import os.path
import unittest
from cStringIO import StringIO

from mock import Mock, call
from requests import Response

from televize import play_live


def _make_response(content):
    response = Response()
    response.raw = StringIO(content)
    return response


class TestPlayLive(unittest.TestCase):
    """Test `play_live` function"""
    def test_play_live(self):
        requests_mock = Mock()
        get_responses = [
            _make_response(open(os.path.join(os.path.dirname(__file__), "data/play_live/client_playlist.json")).read()),
            _make_response(open(os.path.join(os.path.dirname(__file__), "data/play_live/stream_playlist.m3u")).read()),
            _make_response(open(os.path.join(os.path.dirname(__file__), "data/play_live/playlist_1.m3u")).read()),
            _make_response(open(os.path.join(os.path.dirname(__file__), "data/play_live/playlist_2.m3u")).read()),
        ]
        post_responses = [_make_response(r'{"url":"http:\/\/www.ceskatelevize.cz\/ivysilani\/client-playlist\/'
                                         r'?key=df365c9c2ea8b36f76dfa29e3b16d245"}')]
        requests_mock.get.side_effect = lambda *args, **kwargs: get_responses.pop(0)
        requests_mock.post.side_effect = lambda *args, **kwargs: post_responses.pop(0)
        sleep_mock = Mock()
        output = StringIO()

        play_live('24', output, _client=requests_mock, _sleep=sleep_mock)

        self.assertEqual(output.getvalue(),
                         open(os.path.join(os.path.dirname(__file__), "data/play_live/output")).read())
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
            call.get('http://80.188.78.151:80/atip/fd2eccaa99022586e14694df91068915/1449324471384/'
                     '3616440c710a1d7e3f54761a6d940c64/2402-tv-pc/1502.m3u8'),
            call.get('http://80.188.78.151:80/atip/fd2eccaa99022586e14694df91068915/1449324471384/'
                     '3616440c710a1d7e3f54761a6d940c64/2402-tv-pc/1502.m3u8'),
        ]
        self.assertEqual(requests_mock.mock_calls, calls)
        self.assertEqual(sleep_mock.mock_calls, [call(8.0)])