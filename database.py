"""Storage for chart runs: one run per fetch, one row per chart entry.

Two backends with the same two functions, chosen by the STORAGE setting:
  csv    a plain CSV file (default). Git-friendly, so the daily job commits it.
  mysql  the `runs` and `entries` tables in schema.sql.
"""

import csv
import logging
import os
from contextlib import contextmanager
from datetime import datetime

import config

logger = logging.getLogger(__name__)

FIELDS = ["position", "item_id", "name", "artists", "kind", "genre", "release_date", "url"]
CSV_HEADER = ["run_id", "fetched_at", "source", "market", *FIELDS]

INSERT_RUN = "INSERT INTO runs (fetched_at, source, market) VALUES (%s, %s, %s)"
INSERT_ENTRY = (
    "INSERT INTO entries (run_id, position, item_id, name, artists, kind, genre, release_date, url) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
)
SELECT_RUNS = "SELECT id, fetched_at, source, market FROM runs ORDER BY fetched_at DESC, id DESC LIMIT %s"
SELECT_ENTRIES = (
    "SELECT run_id, position, item_id, name, artists, kind, genre, release_date, url "
    "FROM entries WHERE run_id IN ({}) ORDER BY run_id, position"
)


def save_run(rows, fetched_at, source, market):
    """Store one fetch. Returns the new run id, or None if storage failed."""
    if config.STORAGE == "mysql":
        return _mysql_save(rows, fetched_at, source, market)
    return _csv_save(rows, fetched_at, source, market)


def load_runs(last_n=2):
    """The most recent runs, oldest first: [{"id", "fetched_at", "source", "market", "rows": [...]}].
    last_n=None loads every run."""
    if config.STORAGE == "mysql":
        return _mysql_load(last_n)
    return _csv_load(last_n)


# ---------- CSV ----------

def _csv_save(rows, fetched_at, source, market, path=None):
    path = path or config.HISTORY_PATH
    existing = os.path.exists(path) and os.path.getsize(path) > 0
    run_id = 1
    if existing:
        with open(path, newline="", encoding="utf-8") as f:
            ids = [int(r["run_id"]) for r in csv.DictReader(f) if r.get("run_id")]
        run_id = max(ids, default=0) + 1
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    stamp = fetched_at.isoformat() if isinstance(fetched_at, datetime) else str(fetched_at)
    try:
        with open(path, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if not existing:
                w.writerow(CSV_HEADER)
            for r in rows:
                w.writerow([run_id, stamp, source, market, *(r.get(k, "") for k in FIELDS)])
    except OSError as e:
        logger.error("Error writing %s: %s", path, e)
        return None
    logger.info("Saved run %s with %d entries to %s", run_id, len(rows), path)
    return run_id


def _csv_load(last_n, path=None):
    path = path or config.HISTORY_PATH
    if not os.path.exists(path):
        return []
    runs = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rid = int(r["run_id"])
            run = runs.setdefault(rid, {"id": rid, "fetched_at": r["fetched_at"], "source": r["source"],
                                        "market": r["market"], "rows": []})
            run["rows"].append({k: (int(r[k]) if k == "position" else r[k]) for k in FIELDS})
    ordered = [runs[k] for k in sorted(runs)]
    return ordered if last_n is None else ordered[-last_n:]


# ---------- MySQL ----------

@contextmanager
def connection():
    import mysql.connector  # only needed for the MySQL backend
    db = None
    try:
        db = mysql.connector.connect(host=config.DB_HOST, user=config.DB_USER,
                                     password=config.DB_PASSWORD, database=config.DB_NAME)
        yield db
    finally:
        if db is not None and db.is_connected():
            db.close()


def _mysql_save(rows, fetched_at, source, market):
    from mysql.connector import Error
    try:
        with connection() as db:
            cur = db.cursor()
            cur.execute(INSERT_RUN, (fetched_at, source, market))
            run_id = cur.lastrowid
            cur.executemany(INSERT_ENTRY, [(run_id, *(r.get(k, "") for k in FIELDS)) for r in rows])
            db.commit()
            cur.close()
            logger.info("Saved run %s with %d entries", run_id, len(rows))
            return run_id
    except Error as e:
        logger.error("Error saving to database: %s", e)
        return None


def _mysql_load(last_n):
    from mysql.connector import Error
    try:
        with connection() as db:
            cur = db.cursor()
            cur.execute(SELECT_RUNS, (last_n or 1_000_000,))
            runs = [{"id": rid, "fetched_at": at, "source": src, "market": m, "rows": []}
                    for rid, at, src, m in cur.fetchall()]
            if runs:
                by_id = {r["id"]: r for r in runs}
                cur.execute(SELECT_ENTRIES.format(", ".join(["%s"] * len(runs))), tuple(by_id))
                for run_id, *values in cur.fetchall():
                    by_id[run_id]["rows"].append(dict(zip(FIELDS, values)))
            cur.close()
            runs.reverse()
            return runs
    except Error as e:
        logger.error("Error reading from database: %s", e)
        return []
