import os

# Where each fetch is stored: "csv" (a plain file, the default, used by the daily job) or "mysql".
STORAGE = os.getenv('STORAGE', 'csv')
HISTORY_PATH = os.getenv('HISTORY_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'history.csv'))

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'dbspotify')

# Which chart to track: "apple" (Apple Music Top Songs, no account needed) or "spotify"
# (Spotify New Releases; needs an app that still has access, see README).
SOURCE = os.getenv('CHART_SOURCE', 'apple')
# Two-letter country code, and how many entries to keep per run (Apple up to 100, Spotify up to 50).
MARKET = os.getenv('CHART_MARKET', os.getenv('SPOTIFY_MARKET', 'US'))
LIMIT = int(os.getenv('CHART_LIMIT', '100'))

CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', '')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', '')
