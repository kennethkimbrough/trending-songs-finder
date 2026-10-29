import os
import sys
import unittest
from unittest.mock import patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import spotify_api
from spotify_api import SpotifyError, authenticate, get_new_releases, parse_new_releases

SAMPLE = {
    "albums": {
        "items": [
            {"id": "alb1", "name": "First Album", "album_type": "album", "release_date": "2026-10-24",
             "total_tracks": 12, "external_urls": {"spotify": "https://open.spotify.com/album/alb1"},
             "artists": [{"name": "Artist One"}, {"name": "Artist Two"}]},
            {"id": "alb2", "name": "Single Two", "album_type": "single", "release_date": "2026-10",
             "total_tracks": 1, "external_urls": {"spotify": "https://open.spotify.com/album/alb2"},
             "artists": [{"name": "Artist Three"}]},
            None,
            {"id": "", "name": "no id"},
        ]
    }
}


class TestAuthenticate(unittest.TestCase):

    @patch('spotify_api.CLIENT_ID', 'id')
    @patch('spotify_api.CLIENT_SECRET', 'secret')
    @patch('spotify_api.requests.post')
    def test_returns_the_access_token(self, mock_post):
        mock_post.return_value.json.return_value = {'access_token': 'test_token'}
        mock_post.return_value.raise_for_status = lambda: None
        self.assertEqual(authenticate(), 'test_token')

    @patch('spotify_api.CLIENT_ID', '')
    @patch('spotify_api.CLIENT_SECRET', '')
    @patch('spotify_api.requests.post')
    def test_missing_credentials_do_not_call_spotify(self, mock_post):
        self.assertIsNone(authenticate())
        mock_post.assert_not_called()


class TestNewReleases(unittest.TestCase):

    def test_parse_flattens_albums_and_skips_bad_items(self):
        rows = parse_new_releases(SAMPLE)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], {
            "position": 1, "album_id": "alb1", "name": "First Album", "artists": "Artist One, Artist Two",
            "album_type": "album", "release_date": "2026-10-24", "total_tracks": 12,
            "url": "https://open.spotify.com/album/alb1",
        })
        self.assertEqual(rows[1]["position"], 2)
        self.assertEqual(rows[1]["artists"], "Artist Three")

    @patch('spotify_api.requests.get')
    def test_get_new_releases_passes_market_and_limit(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = SAMPLE
        mock_get.return_value.raise_for_status = lambda: None
        rows = get_new_releases('tok', market='GB', limit=20)
        self.assertEqual(len(rows), 2)
        url = mock_get.call_args.args[0]
        self.assertIn("country=GB", url)
        self.assertIn("limit=20", url)
        self.assertEqual(mock_get.call_args.kwargs["headers"]["Authorization"], "Bearer tok")

    @patch('spotify_api.requests.get')
    def test_restricted_endpoint_raises_a_clear_error(self, mock_get):
        mock_get.return_value.status_code = 403
        mock_get.return_value.text = "forbidden"
        with self.assertRaises(SpotifyError):
            get_new_releases('tok')


if __name__ == '__main__':
    unittest.main()
