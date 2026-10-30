"""Pure functions that compare runs of a chart. No storage or network here."""


def diff_runs(previous, latest):
    """Compare two lists of chart rows.

    Returns a dict with:
      entered  - rows in `latest` that were not in `previous`
      dropped  - rows in `previous` that are gone from `latest`
      movers   - (row, change) for entries in both, with change = previous position - latest position
                 (positive means it climbed), sorted by biggest climb first
    """
    prev_pos = {r["item_id"]: r["position"] for r in previous}
    latest_ids = {r["item_id"] for r in latest}
    entered = [r for r in latest if r["item_id"] not in prev_pos]
    dropped = [r for r in previous if r["item_id"] not in latest_ids]
    movers = [(r, prev_pos[r["item_id"]] - r["position"]) for r in latest if r["item_id"] in prev_pos]
    movers.sort(key=lambda m: (-m[1], m[0]["position"]))
    return {"entered": entered, "dropped": dropped, "movers": movers}


def staying_power(runs):
    """How many of the given runs each entry appeared in, best first.

    Returns a list of (row from the entry's latest appearance, run_count).
    """
    counts = {}
    latest_row = {}
    for run in runs:
        for r in run["rows"]:
            counts[r["item_id"]] = counts.get(r["item_id"], 0) + 1
            latest_row[r["item_id"]] = r
    ranked = [(latest_row[a], n) for a, n in counts.items()]
    ranked.sort(key=lambda x: (-x[1], x[0]["position"]))
    return ranked


def chart_summary(runs, history_runs=30):
    """Everything the web page shows, computed from all stored runs (oldest first).

    For each entry on the latest chart: its previous position (None if new), peak position and
    the number of runs it has appeared in across the whole history, the run it first appeared in,
    and its positions over the last `history_runs` runs (None where it was off the chart).
    Also the entries that dropped off since the previous run.
    """
    if not runs:
        return None
    latest = runs[-1]
    previous = runs[-2] if len(runs) >= 2 else None
    prev_pos = {r["item_id"]: r["position"] for r in previous["rows"]} if previous else {}
    peak, appearances, first = {}, {}, {}
    for run in runs:
        for r in run["rows"]:
            i = r["item_id"]
            peak[i] = min(peak.get(i, r["position"]), r["position"])
            appearances[i] = appearances.get(i, 0) + 1
            first.setdefault(i, run["fetched_at"])
    recent = runs[-history_runs:]
    recent_pos = [{r["item_id"]: r["position"] for r in run["rows"]} for run in recent]
    entries = []
    for r in latest["rows"]:
        i = r["item_id"]
        entries.append({
            **{k: r[k] for k in ("position", "name", "artists", "genre", "release_date", "url")},
            "previous": prev_pos.get(i) if previous else None,
            "new": bool(previous) and i not in prev_pos,
            "peak": peak[i],
            "runs": appearances[i],
            "first_seen": first[i],
            "history": [p.get(i) for p in recent_pos],
        })
    dropped = diff_runs(previous["rows"], latest["rows"])["dropped"] if previous else []
    return {
        "source": latest["source"],
        "market": latest["market"],
        "fetched_at": latest["fetched_at"],
        "previous_fetched_at": previous["fetched_at"] if previous else None,
        "run_count": len(runs),
        "first_fetched_at": runs[0]["fetched_at"],
        "history_dates": [run["fetched_at"] for run in recent],
        "entries": entries,
        "dropped": [{k: r[k] for k in ("position", "name", "artists", "url")} for r in dropped],
    }


def format_report(runs, top=10):
    """Plain-text summary of the last run against the one before, plus staying power across all given runs."""
    if not runs:
        return "No runs stored yet. Run `python main.py fetch` first.\n"
    latest = runs[-1]
    lines = [f"Run {latest['id']} fetched {latest['fetched_at']} ({latest['source']}, {latest['market']}), "
             f"{len(latest['rows'])} entries"]

    if len(runs) >= 2:
        previous = runs[-2]
        d = diff_runs(previous["rows"], latest["rows"])
        lines.append(f"\nCompared with run {previous['id']} ({previous['fetched_at']})")
        lines.append(f"  entered the chart: {len(d['entered'])}")
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
    lines = [f"{'#':>3}  {'Released':10}  {'Kind':6}  Title / Artists"]
    for r in rows:
        lines.append(f"{r['position']:3d}  {str(r['release_date']):10}  {r['kind']:6}  {_label(r)}")
    lines.append(f"{len(rows)} entries")
    return "\n".join(lines) + "\n"


def _label(r):
    return f"{r['name']} by {r['artists']}"
