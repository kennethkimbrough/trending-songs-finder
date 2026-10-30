"""Pure functions that compare runs of the new-releases list. No database or network here."""


def diff_runs(previous, latest):
    """Compare two lists of release rows.

    Returns a dict with:
      entered  - rows in `latest` that were not in `previous`
      dropped  - rows in `previous` that are gone from `latest`
      movers   - (row, change) for albums in both, with change = previous position - latest position
                 (positive means it climbed), sorted by biggest climb first
    """
    prev_pos = {r["album_id"]: r["position"] for r in previous}
    latest_ids = {r["album_id"] for r in latest}
    entered = [r for r in latest if r["album_id"] not in prev_pos]
    dropped = [r for r in previous if r["album_id"] not in latest_ids]
    movers = [(r, prev_pos[r["album_id"]] - r["position"]) for r in latest if r["album_id"] in prev_pos]
    movers.sort(key=lambda m: (-m[1], m[0]["position"]))
    return {"entered": entered, "dropped": dropped, "movers": movers}


def staying_power(runs):
    """How many of the given runs each album appeared in, best first.

    Returns a list of (row from the album's latest appearance, run_count).
    """
    counts = {}
    latest_row = {}
    for run in runs:
        for r in run["rows"]:
            counts[r["album_id"]] = counts.get(r["album_id"], 0) + 1
            latest_row[r["album_id"]] = r
    ranked = [(latest_row[a], n) for a, n in counts.items()]
    ranked.sort(key=lambda x: (-x[1], x[0]["position"]))
    return ranked


def format_report(runs, top=10):
    """Plain-text summary of the last run against the one before, plus staying power across all given runs."""
    if not runs:
        return "No runs stored yet. Run `python main.py fetch` first.\n"
    latest = runs[-1]
    lines = [f"Run {latest['id']} fetched {latest['fetched_at']} ({latest['market']}), "
             f"{len(latest['rows'])} releases"]

    if len(runs) >= 2:
        previous = runs[-2]
        d = diff_runs(previous["rows"], latest["rows"])
        lines.append(f"\nCompared with run {previous['id']} ({previous['fetched_at']})")
        lines.append(f"  entered the list: {len(d['entered'])}")
        lines += [f"    #{r['position']:<3} {_label(r)}" for r in d["entered"][:top]]
        lines.append(f"  dropped off: {len(d['dropped'])}")
        lines += [f"    was #{r['position']:<3} {_label(r)}" for r in d["dropped"][:top]]
        climbers = [m for m in d["movers"] if m[1] != 0]
        lines.append(f"  biggest moves: {len(climbers)} changed position")
        lines += [f"    {change:+4d}  #{r['position']:<3} {_label(r)}" for r, change in climbers[:top]]

    lines.append(f"\nStaying power over the last {len(runs)} run{'s' if len(runs) != 1 else ''}")
    for r, n in staying_power(runs)[:top]:
        lines.append(f"  {n:3d} run{'s' if n != 1 else ' '}  {_label(r)}")
    return "\n".join(lines) + "\n"


def format_rows(rows):
    """A simple table of one run's rows, for --dry-run."""
    lines = [f"{'#':>3}  {'Released':10}  {'Type':6}  Album / Artists"]
    for r in rows:
        lines.append(f"{r['position']:3d}  {str(r['release_date']):10}  {r['album_type']:6}  {_label(r)}")
    lines.append(f"{len(rows)} releases")
    return "\n".join(lines) + "\n"


def _label(r):
    return f"{r['name']} by {r['artists']}"
