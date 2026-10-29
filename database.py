"""MySQL storage: one row in `runs` per fetch, one row in `releases` per list entry."""

import logging
from contextlib import contextmanager

import mysql.connector
from mysql.connector import Error

from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INSERT_RUN = "INSERT INTO runs (fetched_at, market) VALUES (%s, %s)"
INSERT_RELEASE = (
    "INSERT INTO releases (run_id, position, album_id, name, artists, album_type, release_date, total_tracks, url) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
)
SELECT_RUNS = "SELECT id, fetched_at, market FROM runs ORDER BY fetched_at DESC, id DESC LIMIT %s"
SELECT_RELEASES = (
    "SELECT run_id, position, album_id, name, artists, album_type, release_date, total_tracks, url "
    "FROM releases WHERE run_id IN ({}) ORDER BY run_id, position"
)


@contextmanager
def connection():
    db = None
    try:
        db = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
        yield db
    finally:
        if db is not None and db.is_connected():
            db.close()


def save_run(rows, fetched_at, market):
    """Store one fetch. Returns the new run id, or None if the database could not be reached."""
    try:
        with connection() as db:
            cur = db.cursor()
            cur.execute(INSERT_RUN, (fetched_at, market))
            run_id = cur.lastrowid
            cur.executemany(INSERT_RELEASE, [
                (run_id, r["position"], r["album_id"], r["name"], r["artists"], r["album_type"],
                 r["release_date"], r["total_tracks"], r["url"])
                for r in rows
            ])
            db.commit()
            cur.close()
            logger.info("Saved run %s with %d releases", run_id, len(rows))
            return run_id
    except Error as e:
        logger.error("Error saving to database: %s", e)
        return None


def load_runs(last_n=2):
    """Return the most recent runs, oldest first, each as {"id", "fetched_at", "market", "rows": [...]}."""
    try:
        with connection() as db:
            cur = db.cursor()
            cur.execute(SELECT_RUNS, (last_n,))
            runs = [{"id": rid, "fetched_at": at, "market": m, "rows": []} for rid, at, m in cur.fetchall()]
            if runs:
                by_id = {r["id"]: r for r in runs}
                placeholders = ", ".join(["%s"] * len(runs))
                cur.execute(SELECT_RELEASES.format(placeholders), tuple(by_id))
                for run_id, position, album_id, name, artists, album_type, release_date, total_tracks, url in cur.fetchall():
                    by_id[run_id]["rows"].append({
                        "position": position, "album_id": album_id, "name": name, "artists": artists,
                        "album_type": album_type, "release_date": release_date,
                        "total_tracks": total_tracks, "url": url,
                    })
            cur.close()
            runs.reverse()
            return runs
    except Error as e:
        logger.error("Error reading from database: %s", e)
        return []
