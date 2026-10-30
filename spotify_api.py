"""Spotify Web API calls: client-credentials auth and the new-releases list.

Spotify removed /browse/new-releases from Development Mode apps in February 2026, so
only apps with extended access can use this source; the default source is Apple Music.
"""

import base64
import logging
from urllib.parse import urlencode

import requests

from config import CLIENT_ID, CLIENT_SECRET

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN_URL = "https://accounts.spotify.com/api/token"
NEW_RELEASES_URL = "https://api.spotify.com/v1/browse/new-releases"
RECOMMENDATIONS_URL = "https://api.spotify.com/v1/recommendations"


class SpotifyError(Exception):
    """Raised when Spotify refuses a request (bad credentials, restricted endpoint, rate limit)."""


def authenticate():
    """Exchange the client ID and secret for an access token. Returns None on failure."""
    if not CLIENT_ID or not CLIENT_SECRET:
        logger.error("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set")
        return None
    try:
        creds = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
        req = requests.post(TOKEN_URL, data={"grant_type": "client_credentials"},
                            headers={"Authorization": f"Basic {creds}"}, timeout=15)
        req.raise_for_status()
        token = req.json()["access_token"]
        logger.info("Authenticated with Spotify")
        return token
    except requests.exceptions.RequestException as e:
        logger.error("Error during authentication: %s", e)
        return None


def get_new_releases(access_token, market="US", limit=50):
    """Return the current new-releases list for a market as a list of dicts, ordered as Spotify ranks them.

    Each row: position (1-based), item_id (the album id), name, artists, kind (album type), genre (empty:
    the endpoint gives none), release_date, url.
    """
    params = urlencode({"country": market, "limit": min(max(limit, 1), 50)})
    res = requests.get(f"{NEW_RELEASES_URL}?{params}",
                       headers={"Authorization": f"Bearer {access_token}"}, timeout=15)
    if res.status_code in (401, 403, 404, 429):
        raise SpotifyError(f"Spotify returned HTTP {res.status_code}: {res.text[:200]}"
                           + (" (New Releases is not available to Development Mode apps since February 2026)"
                              if res.status_code in (403, 404) else ""))
    res.raise_for_status()
    return parse_new_releases(res.json())


def parse_new_releases(payload):
    """Flatten the /browse/new-releases JSON into rows. Pure function, so it is tested without the network."""
    rows = []
    for position, album in enumerate(payload.get("albums", {}).get("items", []), start=1):
        if not album or not album.get("id"):
            continue
        rows.append({
            "position": position,
            "item_id": album["id"],
            "name": album.get("name", ""),
            "artists": ", ".join(a.get("name", "") for a in album.get("artists", []) if a),
            "kind": album.get("album_type", ""),
            "genre": "",
            "release_date": album.get("release_date", ""),
            "url": (album.get("external_urls") or {}).get("spotify", ""),
        })
    logger.info("Fetched %d new releases", len(rows))
    return rows


def get_recommendations(access_token, seed_genres="r-n-b,hip-hop"):
    """The original data source. Spotify restricted this endpoint to existing apps in November 2024,
    so new developer apps receive 403; it is kept for apps that still have access."""
    params = urlencode({"seed_genres": seed_genres})
    res = requests.get(f"{RECOMMENDATIONS_URL}?{params}",
                       headers={"Authorization": f"Bearer {access_token}"}, timeout=15)
    if res.status_code == 403:
        raise SpotifyError("The Recommendations endpoint is not available to this app (HTTP 403)")
    res.raise_for_status()
    return [[t["name"], t["href"], t["duration_ms"]] for t in res.json().get("tracks", [])]
