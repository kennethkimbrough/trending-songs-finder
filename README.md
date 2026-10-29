# Trending Songs Finder

A small Python service that fetches track recommendations from the Spotify
Web API and stores them in a MySQL table.

## What it does

1. Authenticates with Spotify using the client-credentials flow
   (`spotify_api.authenticate`).
2. Calls the Recommendations endpoint seeded with the `r-n-b` and `hip-hop`
   genres and extracts each track's name, API URL and duration
   (`spotify_api.get_recommendations`).
3. Inserts one row per track into a `records` table
   (`database.save`).

`databaseManipulation.py` runs those three steps in order. Credentials and
database settings come from environment variables (`config.py`); nothing is
hardcoded.

> **Spotify API note.** In November 2024 Spotify restricted the
> Recommendations endpoint to apps that already had extended quota access.
> A developer app created after that date may receive `403` from step 2; the
> code is unchanged, but the data source may not be available to new apps.

## Run it

Requires Python 3.10+ and a MySQL server with a database containing:

```sql
CREATE TABLE records (
  name     VARCHAR(255),
  url      VARCHAR(255),
  duration INT
);
```

```bash
pip install -r requirements.txt

export SPOTIFY_CLIENT_ID='your_client_id'
export SPOTIFY_CLIENT_SECRET='your_client_secret'
export DB_HOST='localhost'
export DB_USER='root'
export DB_PASSWORD=''
export DB_NAME='dbspotify'

python databaseManipulation.py
```

Or with Docker (the image reads the same environment variables; override them
with `-e`):

```bash
docker build -t trending-songs-finder .
docker run --rm -e SPOTIFY_CLIENT_ID=... -e SPOTIFY_CLIENT_SECRET=... \
  -e DB_HOST=host.docker.internal trending-songs-finder
```

## Tests

The unit tests mock the HTTP client and the MySQL driver, so they run without
network access or a database:

```bash
python -m unittest discover -s tests
```

They run on every push through GitHub Actions.

## Layout

```
config.py                 environment-variable configuration
spotify_api.py            Spotify auth and recommendations
database.py               MySQL insert
databaseManipulation.py   entry point
tests/                    unit tests (unittest + mock)
legacy/                   earlier editor backups of the files above, kept for reference
```

## Tech stack

Python, `requests`, `mysql-connector-python`, `unittest`, Docker, GitHub Actions.

## License

MIT
