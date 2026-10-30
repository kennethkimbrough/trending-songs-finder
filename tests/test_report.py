import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from report import chart_summary, diff_runs, format_report, format_rows, staying_power


def row(position, item_id):
    return {"position": position, "item_id": item_id, "name": f"Song {item_id}", "artists": "Someone",
            "kind": "song", "genre": "Pop", "release_date": "2026-10-24", "url": ""}


PREVIOUS = [row(1, "a"), row(2, "b"), row(3, "c")]
LATEST = [row(1, "c"), row(2, "a"), row(3, "d")]


class TestDiffRuns(unittest.TestCase):

    def test_entered_dropped_and_movers(self):
        d = diff_runs(PREVIOUS, LATEST)
        self.assertEqual([r["item_id"] for r in d["entered"]], ["d"])
        self.assertEqual([r["item_id"] for r in d["dropped"]], ["b"])
        # c climbed from 3 to 1 (+2), a fell from 1 to 2 (-1)
        self.assertEqual([(r["item_id"], change) for r, change in d["movers"]], [("c", 2), ("a", -1)])

    def test_identical_runs(self):
        d = diff_runs(PREVIOUS, PREVIOUS)
        self.assertEqual(d["entered"], [])
        self.assertEqual(d["dropped"], [])
        self.assertTrue(all(change == 0 for _, change in d["movers"]))


class TestStayingPower(unittest.TestCase):

    def test_counts_runs_per_entry(self):
        runs = [{"rows": PREVIOUS}, {"rows": LATEST}, {"rows": [row(1, "a")]}]
        ranked = staying_power(runs)
        self.assertEqual([(r["item_id"], n) for r, n in ranked][:2], [("a", 3), ("c", 2)])
        # the row kept is the latest appearance, so a's position is 1 from the third run
        self.assertEqual(ranked[0][0]["position"], 1)


class TestFormatting(unittest.TestCase):

    def test_report_mentions_each_section(self):
        runs = [
            {"id": 1, "fetched_at": "2026-10-29 12:00:00", "source": "apple", "market": "US", "rows": PREVIOUS},
            {"id": 2, "fetched_at": "2026-10-30 12:00:00", "source": "apple", "market": "US", "rows": LATEST},
        ]
        text = format_report(runs)
        self.assertIn("Run 2 fetched 2026-10-30 12:00:00 (apple, US), 3 entries", text)
        self.assertIn("entered the chart: 1", text)
        self.assertIn("dropped off: 1", text)
        self.assertIn("+2  #1   Song c", text)
        self.assertIn("Staying power over the last 2 runs", text)

    def test_empty_report_and_dry_run_table(self):
        self.assertIn("No runs stored", format_report([]))
        table = format_rows(LATEST)
        self.assertTrue(table.startswith("  #  Released    Kind    Title / Artists"))
        self.assertTrue(table.endswith("3 entries\n"))


class TestChartSummary(unittest.TestCase):

    def runs(self):
        return [
            {"id": 1, "fetched_at": "d1", "source": "apple", "market": "US", "rows": [row(1, "a"), row(2, "b"), row(3, "c")]},
            {"id": 2, "fetched_at": "d2", "source": "apple", "market": "US", "rows": [row(1, "b"), row(2, "a"), row(3, "d")]},
            {"id": 3, "fetched_at": "d3", "source": "apple", "market": "US", "rows": [row(1, "c"), row(2, "a"), row(3, "b")]},
        ]

    def test_latest_entries_with_previous_peak_and_history(self):
        s = chart_summary(self.runs(), history_runs=3)
        by = {e["name"]: e for e in s["entries"]}
        # c: off the chart in run 2, so it counts as new against the previous run; peak 1 from run 3
        self.assertEqual((by["Song c"]["previous"], by["Song c"]["new"], by["Song c"]["peak"], by["Song c"]["runs"]),
                         (None, True, 1, 2))
        self.assertEqual(by["Song c"]["history"], [3, None, 1])
        self.assertEqual(by["Song c"]["first_seen"], "d1")
        # b: 1 -> 3, peak 1 from run 2, on all three runs
        self.assertEqual((by["Song b"]["previous"], by["Song b"]["peak"], by["Song b"]["runs"]), (1, 1, 3))
        self.assertEqual([d["name"] for d in s["dropped"]], ["Song d"])
        self.assertEqual((s["run_count"], s["previous_fetched_at"], s["history_dates"]), (3, "d2", ["d1", "d2", "d3"]))

    def test_first_run_has_no_comparison(self):
        s = chart_summary(self.runs()[:1])
        self.assertTrue(all(e["previous"] is None and not e["new"] for e in s["entries"]))
        self.assertEqual(s["dropped"], [])
        self.assertIsNone(chart_summary([]))


if __name__ == '__main__':
    unittest.main()
