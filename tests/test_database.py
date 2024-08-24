
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import save

class TestDatabase(unittest.TestCase):

    @patch('database.mysql.connector.connect')
    def test_save(self, mock_connect):
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_db
        mock_db.cursor.return_value = mock_cursor

        data = [
            ['Song1', 'url1', 300000],
            ['Song2', 'url2', 250000]
        ]
        save(data)

        self.assertEqual(mock_cursor.execute.call_count, 2)
        self.assertEqual(mock_db.commit.call_count, 1)

if __name__ == '__main__':
    unittest.main()
