import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from report import diff_runs, format_report, format_rows, staying_power


def row(position, album_id):
    return {"position": position, "album_id": album_id, "name": f"Album {album_id}", "artists": "Someone",
            "album_type": "album", "release_date": "2026-10-24", "total_tracks": 10, "url": ""}


PREVIOUS = [row(1, "a"), row(2, "b"), row(3, "c")]
LATEST = [row(1, "c"), row(2, "a"), row(3, "d")]


class TestDiffRuns(unittest.TestCase):

    def test_entered_dropped_and_movers(self):
        d = diff_runs(PREVIOUS, LATEST)
        self.assertEqual([r["album_id"] for r in d["entered"]], ["d"])
        self.assertEqual([r["album_id"] for r in d["dropped"]], ["b"])
        # c climbed from 3 to 1 (+2), a fell from 1 to 2 (-1)
        self.assertEqual([(r["album_id"], change) for r, change in d["movers"]], [("c", 2), ("a", -1)])

    def test_identical_runs(self):
        d = diff_runs(PREVIOUS, PREVIOUS)
        self.assertEqual(d["entered"], [])
        self.assertEqual(d["dropped"], [])
        self.assertTrue(all(change == 0 for _, change in d["movers"]))


class TestStayingPower(unittest.TestCase):

    def test_counts_runs_per_album(self):
        runs = [{"rows": PREVIOUS}, {"rows": LATEST}, {"rows": [row(1, "a")]}]
        ranked = staying_power(runs)
        self.assertEqual([(r["album_id"], n) for r, n in ranked][:2], [("a", 3), ("c", 2)])
        # the row kept is the latest appearance, so a's position is 1 from the third run
        self.assertEqual(ranked[0][0]["position"], 1)


class TestFormatting(unittest.TestCase):

    def test_report_mentions_each_section(self):
        runs = [
            {"id": 1, "fetched_at": "2026-10-29 12:00:00", "market": "US", "rows": PREVIOUS},
            {"id": 2, "fetched_at": "2026-10-30 12:00:00", "market": "US", "rows": LATEST},
        ]
        text = format_report(runs)
        self.assertIn("Run 2 fetched 2026-10-30 12:00:00 (US), 3 releases", text)
        self.assertIn("entered the list: 1", text)
        self.assertIn("dropped off: 1", text)
        self.assertIn("+2  #1   Album c", text)
        self.assertIn("Staying power over the last 2 runs", text)

    def test_empty_report_and_dry_run_table(self):
        self.assertIn("No runs stored", format_report([]))
        table = format_rows(LATEST)
        self.assertTrue(table.startswith("  #  Released    Type    Album / Artists"))
        self.assertTrue(table.endswith("3 releases\n"))


if __name__ == '__main__':
    unittest.main()
