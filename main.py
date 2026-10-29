"""Command line: fetch the new-releases list into MySQL, or report on the stored runs.

    python main.py fetch [--dry-run] [--market US] [--limit 50]
    python main.py report [--runs 5] [--top 10]
"""

import argparse
import sys
from datetime import datetime, timezone

import config
from database import load_runs, save_run
from report import format_report, format_rows
from spotify_api import SpotifyError, authenticate, get_new_releases


def fetch(args):
    token = authenticate()
    if token is None:
        return 1
    try:
        rows = get_new_releases(token, market=args.market, limit=args.limit)
    except SpotifyError as e:
        print(e, file=sys.stderr)
        return 1
    if args.dry_run:
        print(format_rows(rows), end="")
        return 0
    run_id = save_run(rows, datetime.now(timezone.utc).replace(microsecond=0), args.market)
    if run_id is None:
        return 1
    print(f"Saved run {run_id}: {len(rows)} releases for {args.market}")
    return 0


def report(args):
    print(format_report(load_runs(args.runs), top=args.top), end="")
    return 0


def build_parser():
    p = argparse.ArgumentParser(description="Track Spotify's new-releases list over time.")
    sub = p.add_subparsers(dest="command", required=True)

    f = sub.add_parser("fetch", help="fetch the current list and store it (or print it with --dry-run)")
    f.add_argument("--dry-run", action="store_true", help="print the list instead of writing to MySQL")
    f.add_argument("--market", default=config.MARKET, help="two-letter country code (default from SPOTIFY_MARKET)")
    f.add_argument("--limit", type=int, default=config.LIMIT, help="entries to keep, max 50")
    f.set_defaults(func=fetch)

    r = sub.add_parser("report", help="compare the latest run with the previous one")
    r.add_argument("--runs", type=int, default=5, help="how many recent runs to load for staying power")
    r.add_argument("--top", type=int, default=10, help="rows to show per section")
    r.set_defaults(func=report)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
