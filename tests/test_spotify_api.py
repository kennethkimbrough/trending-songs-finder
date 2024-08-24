
import unittest
from unittest.mock import patch
import sys
import os

# Add the parent directory to the sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spotify_api import authenticate, get_recommendations

class TestSpotifyAPI(unittest.TestCase):

    @patch('spotify_api.requests.post')
    def test_authenticate(self, mock_post):
        mock_post.return_value.json.return_value = {'access_token': 'test_token'}
        mock_post.return_value.raise_for_status = lambda: None
        token = authenticate()
        self.assertEqual(token, 'test_token')

    @patch('spotify_api.requests.get')
    def test_get_recommendations(self, mock_get):
        mock_get.return_value.json.return_value = {
            'tracks': [
                {'name': 'Song1', 'href': 'url1', 'duration_ms': 300000},
                {'name': 'Song2', 'href': 'url2', 'duration_ms': 250000}
            ]
        }
        mock_get.return_value.raise_for_status = lambda: None
        recommendations = get_recommendations('test_token')
        self.assertEqual(len(recommendations), 2)
        self.assertEqual(recommendations[0], ['Song1', 'url1', 300000])

if __name__ == '__main__':
    unittest.main()
