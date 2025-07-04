import unittest
from unittest import TestCase
from unittest.mock import call, patch, sentinel

import responses
from responses.matchers import query_param_matcher
from testfixtures import OutputCapture

from televize import (
    CHANNELS_LINK,
    Channel,
    get_channels,
    get_ivysilani_playlist,
    get_live_playlist,
    play_ivysilani,
    play_live,
    print_channels,
    run_player,
)


class GetChannelsTest(TestCase):
    def test_empty(self):
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, CHANNELS_LINK, json={'data': []}),

            channels = tuple(get_channels())

        self.assertEqual(channels, ())

    def test_live_current(self):
        channel_data = {
            "__typename": "LiveBroadcast", "id": "CT-42",
            "current": {"channelSettings": {"channelName": "ČT 42"}, "slug": "ct42", "title": "Great question"}}
        channel = Channel(id="CT-42", name="ČT 42", slug="ct42", title="Great question")
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, CHANNELS_LINK, json={'data': [channel_data]})

            channels = tuple(get_channels())

        self.assertEqual(channels, (channel, ))

    def test_live_next(self):
        channel_data = {
            "__typename": "LiveBroadcast", "id": "CT-42",
            "next": {"channelSettings": {"channelName": "ČT 42"}, "slug": "ct42", "title": "Great question"}}
        channel = Channel(id="CT-42", name="ČT 42", slug="ct42", title="Great question")
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, CHANNELS_LINK, json={'data': [channel_data]})

            channels = tuple(get_channels())

        self.assertEqual(channels, (channel, ))

    def test_live_empty(self):
        # Test live brodcast without current or next record.
        channel_data = {"__typename": "LiveBroadcast", "id": "CT-42"}
        channel = Channel(id="CT-42", name="", slug="", title=None)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, CHANNELS_LINK, json={'data': [channel_data]})

            channels = tuple(get_channels())

        self.assertEqual(channels, (channel, ))


class PrintChannelsTest(TestCase):
    def test_empty(self):
        with OutputCapture(separate=True) as output:
            print_channels(())

        output.compare(stdout="", stderr="")

    def test(self):
        channel = Channel(id="CT-42", name="ČT 42", slug="ct42", title="Great question")
        with OutputCapture(separate=True) as output:
            print_channels((channel, ))

        output.compare(stdout="ct42: ČT 42 - Great question", stderr="")


class GetLivePlaylistTest(TestCase):
    def test_channel_not_found(self):
        with patch("televize.get_channels", autospec=True) as channels_mock:
            channels_mock.return_value = ()

            with self.assertRaisesRegex(ValueError, "Channel ct42 not found."):
                get_live_playlist("ct42", "1080p")

    def test(self):
        channel = Channel(id="CT-42", name="ČT 42", slug="ct42", title="Great question")
        playlist_data = {"streamUrls": {"main": "https://playlist.example.org/"}}
        with patch("televize.get_channels", autospec=True) as channels_mock:
            channels_mock.return_value = (channel, )

            with responses.RequestsMock() as rsps:
                query_matcher = query_param_matcher({"quality": "1080p"})
                rsps.add(responses.GET,
                         "https://api.ceskatelevize.cz/video/v1/playlist-live/v1/stream-data/channel/CT-42",
                         match=[query_matcher], json=playlist_data)

                self.assertEqual(get_live_playlist("ct42", "1080p"), "https://playlist.example.org/")


class GetIvysilaniPlaylistTest(TestCase):
    def test(self):
        playlist_data = {"streams": [{"url": "https://playlist.example.org/"}]}
        with responses.RequestsMock() as rsps:
            query_matcher = query_param_matcher({"quality": "1080p"})
            rsps.add(responses.GET,
                     "https://api.ceskatelevize.cz/video/v1/playlist-vod/v1/stream-data/media/external/42",
                     match=[query_matcher], json=playlist_data)

            self.assertEqual(get_ivysilani_playlist("42", "1080p"), "https://playlist.example.org/")


class TestRunPlayer(unittest.TestCase):
    def setUp(self):
        call_patcher = patch('televize.subprocess.call')
        self.addCleanup(call_patcher.stop)
        self.call_mock = call_patcher.start()

    def test_run_player_live(self):
        playlist_uri = 'http://example.cz/path/playlist.m3u8'

        run_player(playlist_uri, 'my_player "Custom Argument"')

        self.assertEqual(self.call_mock.mock_calls, [call(['my_player', 'Custom Argument', playlist_uri])])


class PlayLiveTest(TestCase):
    def test(self):
        with patch("televize.get_live_playlist", autospec=True, return_value=sentinel.playlist_url) as get_mock:
            with patch("televize.run_player", autospec=True) as run_mock:
                play_live({"<channel>": sentinel.channel, "--player": sentinel.player, "--quality": sentinel.quality})

        self.assertEqual(get_mock.mock_calls, [call(sentinel.channel, sentinel.quality)])
        self.assertEqual(run_mock.mock_calls, [call(sentinel.playlist_url, sentinel.player)])


class PlayIvysilaniTest(TestCase):
    def test_program_page(self):
        url = "https://www.ceskatelevize.cz/porady/11276561613-kosmo/"
        with self.assertRaisesRegex(ValueError, "Video not found"):
            play_ivysilani({"<url>": url})

    def test_episode(self):
        url = "https://www.ceskatelevize.cz/porady/11276561613-kosmo/215512121020005/"
        with patch("televize.get_ivysilani_playlist", autospec=True, return_value=sentinel.playlist_url) as get_mock:
            with patch("televize.run_player", autospec=True) as run_mock:
                play_ivysilani({"<url>": url, "--player": sentinel.player, "--quality": sentinel.quality})

        self.assertEqual(get_mock.mock_calls, [call("215512121020005", sentinel.quality)])
        self.assertEqual(run_mock.mock_calls, [call(sentinel.playlist_url, sentinel.player)])
