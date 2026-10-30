"""Command line: fetch a chart and store it, report on the stored runs, or export them for the web page.

    python main.py fetch [--source apple|spotify] [--market US] [--limit 100] [--dry-run]
    python main.py report [--runs 5] [--top 10]
    python main.py export [--out site/chart.json]
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone

import config
from database import load_runs, save_run
from report import chart_summary, format_report, format_rows

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def fetch_rows(source, market, limit):
    """Rows for the chosen chart, or raises with a readable message."""
    if source == "apple":
        from apple_music import get_top_songs
        return get_top_songs(market, limit)
    if source == "spotify":
        from spotify_api import SpotifyError, authenticate, get_new_releases
        token = authenticate()
        if token is None:
            raise SpotifyError("Could not authenticate with Spotify")
        return get_new_releases(token, market=market, limit=min(limit, 50))
    raise ValueError(f"Unknown source {source!r}: use apple or spotify")


def fetch(args):
    try:
        rows = fetch_rows(args.source, args.market, args.limit)
    except Exception as e:  # network and API errors all end the run the same way
        print(e, file=sys.stderr)
        return 1
    if args.dry_run:
        print(format_rows(rows), end="")
        return 0
    run_id = save_run(rows, datetime.now(timezone.utc).replace(microsecond=0), args.source, args.market.upper())
    if run_id is None:
        return 1
    print(f"Saved run {run_id}: {len(rows)} entries from {args.source} ({args.market.upper()})")
    return 0


def report(args):
    print(format_report(load_runs(args.runs), top=args.top), end="")
    return 0


def export(args):
    summary = chart_summary(load_runs(None), history_runs=args.history)
    if summary is None:
        print("No runs stored yet.", file=sys.stderr)
        return 1
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, separators=(",", ":"), default=str)
    print(f"Wrote {args.out}: {len(summary['entries'])} entries from {summary['run_count']} runs")
    return 0


def build_parser():
    p = argparse.ArgumentParser(description="Track a music chart over time.")
    sub = p.add_subparsers(dest="command", required=True)

    f = sub.add_parser("fetch", help="fetch the current chart and store it (or print it with --dry-run)")
    f.add_argument("--source", default=config.SOURCE, choices=["apple", "spotify"],
                   help="apple: Apple Music Top Songs (default, no account); spotify: Spotify New Releases")
    f.add_argument("--dry-run", action="store_true", help="print the chart instead of storing it")
    f.add_argument("--market", default=config.MARKET, help="two-letter country code (default US)")
    f.add_argument("--limit", type=int, default=config.LIMIT, help="entries to keep (Apple up to 100, Spotify 50)")
    f.set_defaults(func=fetch)

    r = sub.add_parser("report", help="compare the latest run with the previous one")
    r.add_argument("--runs", type=int, default=5, help="how many recent runs to load for staying power")
    r.add_argument("--top", type=int, default=10, help="rows to show per section")
    r.set_defaults(func=report)

    e = sub.add_parser("export", help="write the summary the web page reads")
    e.add_argument("--out", default="site/chart.json", help="output file (default site/chart.json)")
    e.add_argument("--history", type=int, default=30, help="runs of position history per entry")
    e.set_defaults(func=export)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
