"""Apple Music's public Top Songs chart (the "most played" feed). No account or key needed."""

import logging

import requests

logger = logging.getLogger(__name__)

TOP_SONGS_URL = "https://rss.marketingtools.apple.com/api/v2/{country}/music/most-played/{limit}/songs.json"


class ChartError(Exception):
    """Raised when the feed cannot be read."""


def get_top_songs(country="US", limit=100):
    """Return the current Top Songs chart for a country, in chart order."""
    url = TOP_SONGS_URL.format(country=country.lower(), limit=min(max(limit, 1), 100))
    try:
        res = requests.get(url, timeout=20)
        res.raise_for_status()
        payload = res.json()
    except (requests.exceptions.RequestException, ValueError) as e:
        raise ChartError(f"Could not read the Apple Music chart: {e}") from e
    rows = parse_top_songs(payload)
    if not rows:
        raise ChartError("The Apple Music chart came back empty")
    return rows


def parse_top_songs(payload):
    """Flatten the feed JSON into rows. Pure function, so it is tested without the network.

    Each row: position, item_id, name, artists, kind, genre, release_date, url.
    """
    rows = []
    for position, song in enumerate((payload.get("feed") or {}).get("results") or [], start=1):
        if not song or not song.get("id"):
            continue
        genres = [g.get("name", "") for g in song.get("genres") or [] if g and g.get("name") != "Music"]
        rows.append({
            "position": position,
            "item_id": str(song["id"]),
            "name": song.get("name", ""),
            "artists": song.get("artistName", ""),
            "kind": "song",
            "genre": genres[0] if genres else "",
            "release_date": song.get("releaseDate", ""),
            "url": song.get("url", ""),
        })
    logger.info("Fetched %d songs", len(rows))
    return rows
