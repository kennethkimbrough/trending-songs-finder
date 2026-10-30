import os
import sys
import unittest
from unittest.mock import patch

import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apple_music import ChartError, get_top_songs, parse_top_songs

# Shaped like rss.marketingtools.apple.com/api/v2/us/music/most-played/N/songs.json (invented songs).
SAMPLE = {"feed": {"title": "Top Songs", "country": "us", "results": [
    {"artistName": "Artist One", "id": "111", "name": "First Song", "releaseDate": "2026-10-15", "kind": "songs",
     "genres": [{"genreId": "14", "name": "Pop"}, {"genreId": "34", "name": "Music"}],
     "url": "https://music.apple.com/us/album/first/1?i=111"},
    {"artistName": "Artist Two & Artist Three", "id": "222", "name": "Second Song", "releaseDate": "2026-09-01",
     "kind": "songs", "genres": [{"genreId": "34", "name": "Music"}], "url": "https://music.apple.com/x"},
    None,
    {"artistName": "No Id", "name": "skipped"},
]}}


class TestParse(unittest.TestCase):

    def test_flattens_songs_in_chart_order(self):
        rows = parse_top_songs(SAMPLE)
        self.assertEqual(rows[0], {
            "position": 1, "item_id": "111", "name": "First Song", "artists": "Artist One", "kind": "song",
            "genre": "Pop", "release_date": "2026-10-15", "url": "https://music.apple.com/us/album/first/1?i=111",
        })
        self.assertEqual(len(rows), 2)

    def test_ignores_the_generic_music_genre(self):
        self.assertEqual(parse_top_songs(SAMPLE)[1]["genre"], "")

    def test_empty_feed(self):
        self.assertEqual(parse_top_songs({}), [])


class TestFetch(unittest.TestCase):

    @patch('apple_music.requests.get')
    def test_builds_the_url_for_country_and_limit(self, mock_get):
        mock_get.return_value.json.return_value = SAMPLE
        mock_get.return_value.raise_for_status = lambda: None
        self.assertEqual(len(get_top_songs("GB", 250)), 2)
        self.assertIn("/gb/music/most-played/100/songs.json", mock_get.call_args.args[0])

    @patch('apple_music.requests.get')
    def test_network_errors_and_empty_charts_raise(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError("down")
        with self.assertRaises(ChartError):
            get_top_songs()
        mock_get.side_effect = None
        mock_get.return_value.json.return_value = {"feed": {"results": []}}
        mock_get.return_value.raise_for_status = lambda: None
        with self.assertRaises(ChartError):
            get_top_songs()


if __name__ == '__main__':
    unittest.main()
