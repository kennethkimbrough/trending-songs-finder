import os
import sys
import tempfile
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib.util

import config
import database
from database import INSERT_ENTRY, INSERT_RUN, load_runs, save_run

ROWS = [
    {"position": 1, "item_id": "111", "name": "First Song", "artists": "Artist One", "kind": "song",
     "genre": "Pop", "release_date": "2026-10-15", "url": "https://music.apple.com/x"},
    {"position": 2, "item_id": "222", "name": "Second, \"quoted\" Song", "artists": "Artist Two", "kind": "song",
     "genre": "", "release_date": "2026-09-01", "url": ""},
]


class TestCsvStorage(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "sub", "history.csv")
        self.patches = [patch.object(config, "STORAGE", "csv"), patch.object(config, "HISTORY_PATH", self.path)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.dir.cleanup()

    def test_round_trip_and_run_ids(self):
        self.assertEqual(load_runs(5), [])
        self.assertEqual(save_run(ROWS, datetime(2026, 10, 29, 10, 0), "apple", "US"), 1)
        self.assertEqual(save_run(ROWS[::-1], datetime(2026, 10, 30, 10, 0), "apple", "US"), 2)
        runs = load_runs(5)
        self.assertEqual([r["id"] for r in runs], [1, 2])
        self.assertEqual(runs[0]["fetched_at"], "2026-10-29T10:00:00")
        self.assertEqual(runs[0]["rows"][1]["name"], 'Second, "quoted" Song')
        self.assertEqual(runs[0]["rows"][1]["position"], 2)
        self.assertEqual(runs[1]["source"], "apple")

    def test_last_n_and_all(self):
        for day in range(1, 5):
            save_run(ROWS, datetime(2026, 10, day), "apple", "US")
        self.assertEqual([r["id"] for r in load_runs(2)], [3, 4])
        self.assertEqual(len(load_runs(None)), 4)


@unittest.skipUnless(importlib.util.find_spec("mysql"), "mysql-connector-python is not installed")
class TestMysqlStorage(unittest.TestCase):

    def setUp(self):
        self.patch = patch.object(config, "STORAGE", "mysql")
        self.patch.start()

    def tearDown(self):
        self.patch.stop()

    @patch('mysql.connector.connect')
    def test_inserts_one_run_and_one_row_per_entry(self, mock_connect):
        db, cur = MagicMock(), MagicMock()
        mock_connect.return_value = db
        db.cursor.return_value = cur
        cur.lastrowid = 7
        when = datetime(2026, 10, 30, 12, 0, 0)

        self.assertEqual(save_run(ROWS, when, "apple", "US"), 7)
        cur.execute.assert_called_once_with(INSERT_RUN, (when, "apple", "US"))
        sql, values = cur.executemany.call_args.args
        self.assertEqual(sql, INSERT_ENTRY)
        self.assertEqual(values[0], (7, 1, "111", "First Song", "Artist One", "song", "Pop", "2026-10-15",
                                     "https://music.apple.com/x"))
        db.commit.assert_called_once()
        db.close.assert_called_once()

    @patch('mysql.connector.connect')
    def test_connection_failure_returns_none_instead_of_raising(self, mock_connect):
        from mysql.connector import Error
        mock_connect.side_effect = Error("cannot connect")
        self.assertIsNone(save_run(ROWS, datetime(2026, 10, 30), "apple", "US"))

    @patch('mysql.connector.connect')
    def test_groups_entries_by_run_oldest_first(self, mock_connect):
        db, cur = MagicMock(), MagicMock()
        mock_connect.return_value = db
        db.cursor.return_value = cur
        cur.fetchall.side_effect = [
            [(8, datetime(2026, 10, 30), "apple", "US"), (7, datetime(2026, 10, 29), "apple", "US")],
            [(7, 1, "111", "First Song", "Artist One", "song", "Pop", "2026-10-15", "u1"),
             (8, 1, "222", "Second Song", "Artist Two", "song", "", "2026-09-01", "u2"),
             (8, 2, "111", "First Song", "Artist One", "song", "Pop", "2026-10-15", "u1")],
        ]
        runs = load_runs(2)
        self.assertEqual([r["id"] for r in runs], [7, 8])
        self.assertEqual([r["item_id"] for r in runs[1]["rows"]], ["222", "111"])
        self.assertEqual(runs[1]["rows"][1]["position"], 2)


if __name__ == '__main__':
    unittest.main()
