import os

CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', '')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', '')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'dbspotify')

# Two-letter country code for the new-releases chart, and how many entries to keep per run (max 50).
MARKET = os.getenv('SPOTIFY_MARKET', 'US')
LIMIT = int(os.getenv('SPOTIFY_LIMIT', '50'))
