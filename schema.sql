-- MySQL schema for trending-songs-finder (used when STORAGE=mysql; the default is a CSV file).
--   mysql -u root -p dbspotify < schema.sql

CREATE TABLE IF NOT EXISTS runs (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  fetched_at  DATETIME     NOT NULL,
  source      VARCHAR(16)  NOT NULL,   -- apple or spotify
  market      CHAR(2)      NOT NULL
);

CREATE TABLE IF NOT EXISTS entries (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  run_id       INT          NOT NULL,
  position     SMALLINT     NOT NULL,
  item_id      VARCHAR(32)  NOT NULL,   -- Apple song id or Spotify album id
  name         VARCHAR(255) NOT NULL,
  artists      VARCHAR(512) NOT NULL,
  kind         VARCHAR(16)  NOT NULL,   -- song, album, single, ...
  genre        VARCHAR(64)  NOT NULL,
  release_date VARCHAR(10)  NOT NULL,   -- YYYY, YYYY-MM or YYYY-MM-DD
  url          VARCHAR(255) NOT NULL,
  CONSTRAINT fk_entries_run FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE,
  INDEX idx_entries_item (item_id),
  INDEX idx_entries_run_position (run_id, position)
);
