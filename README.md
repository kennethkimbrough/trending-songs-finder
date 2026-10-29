# Trending Songs Finder

[![Tests](https://github.com/kennethkimbrough/trending-songs-finder/actions/workflows/tests.yml/badge.svg)](https://github.com/kennethkimbrough/trending-songs-finder/actions/workflows/tests.yml)

Tracks Spotify's new-releases list for a country over time. Each run stores
the current list in MySQL; the report compares the latest run with the one
before it and shows what entered, what dropped off, what moved, and which
releases have stayed on the list longest.

## What it does

`fetch` authenticates with the Spotify Web API (client-credentials flow),
pulls the [new releases](https://developer.spotify.com/documentation/web-api/reference/get-new-releases)
for a market (default `US`, up to 50 entries), and stores one row in `runs`
plus one row per release in `releases`, keeping each release's position.

`report` loads the last few runs and prints:

```
Run 12 fetched 2026-10-30 09:00:00 (US), 50 releases

Compared with run 11 (2026-10-29 09:00:00)
  entered the list: 4
    #1   <album> — <artists>
    ...
  dropped off: 4
    was #38  <album> — <artists>
  biggest moves: 31 changed position
    +12  #3   <album> — <artists>
    ...

Staying power over the last 5 runs
    5 runs  <album> — <artists>
    ...
```

`fetch --dry-run` prints the fetched list as a table and writes nothing, so
you can try it with just Spotify credentials and no database.

> The project originally used Spotify's Recommendations endpoint. Spotify
> restricted that endpoint to existing apps in November 2024, so new apps
> get `403`. `spotify_api.get_recommendations` is still there for apps that
> have access, but the tracker is built on New Releases, which remains open.

## Run it

Requires Python 3.10+, a Spotify developer app (client ID and secret), and
for storage a MySQL server.

```sh
pip install -r requirements.txt

export SPOTIFY_CLIENT_ID='your_client_id'
export SPOTIFY_CLIENT_SECRET='your_client_secret'
python main.py fetch --dry-run            # no database needed

mysql -u root -p -e 'CREATE DATABASE dbspotify'
mysql -u root -p dbspotify < schema.sql   # creates runs and releases
export DB_HOST=localhost DB_USER=root DB_PASSWORD='' DB_NAME=dbspotify
python main.py fetch                      # stores a run
python main.py report --runs 5 --top 10
```

`--market GB` (or `SPOTIFY_MARKET`) changes the country; `--limit`
(or `SPOTIFY_LIMIT`) caps the entries per run. Run `fetch` on a schedule
(cron, a container, or a workflow with secrets) to build up history; the
report only gets interesting from the second run.

With Docker, the image takes all settings from the environment and runs
`fetch` by default:

```sh
docker build -t trending-songs-finder .
docker run --rm -e SPOTIFY_CLIENT_ID=... -e SPOTIFY_CLIENT_SECRET=... \
  -e DB_HOST=host.docker.internal trending-songs-finder
docker run --rm ... trending-songs-finder report
```

## Tests

```sh
python -m unittest discover -s tests
```

The tests mock the HTTP client and the MySQL driver, so they run with no
credentials, network or database: response parsing, the SQL issued for a
run, grouping of loaded runs, and the diff and staying-power calculations.
They run on every push through GitHub Actions.

## Layout

```
main.py                 command line: fetch, report
spotify_api.py          auth, new releases, response parsing
database.py             MySQL: save_run, load_runs
report.py               pure functions: diff between runs, staying power, text formatting
config.py               settings from environment variables
schema.sql              the two tables
databaseManipulation.py the original entry point, now a shim for `fetch`
tests/                  unittest + mock
legacy/                 earlier editor backups of the first version
```

## Tech stack

Python, `requests`, `mysql-connector-python`, `unittest`, Docker, GitHub Actions.

## License

MIT
