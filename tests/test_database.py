import os
import sys
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import INSERT_RELEASE, INSERT_RUN, load_runs, save_run

ROWS = [
    {"position": 1, "album_id": "alb1", "name": "First Album", "artists": "Artist One", "album_type": "album",
     "release_date": "2026-10-24", "total_tracks": 12, "url": "https://open.spotify.com/album/alb1"},
    {"position": 2, "album_id": "alb2", "name": "Single Two", "artists": "Artist Three", "album_type": "single",
     "release_date": "2026-10", "total_tracks": 1, "url": "https://open.spotify.com/album/alb2"},
]


class TestSaveRun(unittest.TestCase):

    @patch('database.mysql.connector.connect')
    def test_inserts_one_run_and_one_row_per_release(self, mock_connect):
        db, cur = MagicMock(), MagicMock()
        mock_connect.return_value = db
        db.cursor.return_value = cur
        cur.lastrowid = 7
        when = datetime(2026, 10, 30, 12, 0, 0)

        run_id = save_run(ROWS, when, "US")

        self.assertEqual(run_id, 7)
        cur.execute.assert_called_once_with(INSERT_RUN, (when, "US"))
        sql, values = cur.executemany.call_args.args
        self.assertEqual(sql, INSERT_RELEASE)
        self.assertEqual(values[0], (7, 1, "alb1", "First Album", "Artist One", "album", "2026-10-24", 12,
                                     "https://open.spotify.com/album/alb1"))
        self.assertEqual(len(values), 2)
        db.commit.assert_called_once()
        db.close.assert_called_once()

    @patch('database.mysql.connector.connect')
    def test_connection_failure_returns_none_instead_of_raising(self, mock_connect):
        from mysql.connector import Error
        mock_connect.side_effect = Error("cannot connect")
        self.assertIsNone(save_run(ROWS, datetime(2026, 10, 30), "US"))


class TestLoadRuns(unittest.TestCase):

    @patch('database.mysql.connector.connect')
    def test_groups_releases_by_run_oldest_first(self, mock_connect):
        db, cur = MagicMock(), MagicMock()
        mock_connect.return_value = db
        db.cursor.return_value = cur
        cur.fetchall.side_effect = [
            [(8, datetime(2026, 10, 30), "US"), (7, datetime(2026, 10, 29), "US")],
            [(7, 1, "alb1", "First Album", "Artist One", "album", "2026-10-24", 12, "u1"),
             (8, 1, "alb2", "Single Two", "Artist Three", "single", "2026-10", 1, "u2"),
             (8, 2, "alb1", "First Album", "Artist One", "album", "2026-10-24", 12, "u1")],
        ]

        runs = load_runs(2)

        self.assertEqual([r["id"] for r in runs], [7, 8])
        self.assertEqual([r["album_id"] for r in runs[0]["rows"]], ["alb1"])
        self.assertEqual([r["album_id"] for r in runs[1]["rows"]], ["alb2", "alb1"])
        self.assertEqual(runs[1]["rows"][1]["position"], 2)

    @patch('database.mysql.connector.connect')
    def test_empty_database(self, mock_connect):
        db, cur = MagicMock(), MagicMock()
        mock_connect.return_value = db
        db.cursor.return_value = cur
        cur.fetchall.return_value = []
        self.assertEqual(load_runs(5), [])


if __name__ == '__main__':
    unittest.main()
