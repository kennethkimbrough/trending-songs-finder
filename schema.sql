-- MySQL schema for trending-songs-finder.
--   mysql -u root -p dbspotify < schema.sql

CREATE TABLE IF NOT EXISTS runs (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  fetched_at  DATETIME     NOT NULL,
  market      CHAR(2)      NOT NULL
);

CREATE TABLE IF NOT EXISTS releases (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  run_id       INT          NOT NULL,
  position     SMALLINT     NOT NULL,
  album_id     VARCHAR(32)  NOT NULL,
  name         VARCHAR(255) NOT NULL,
  artists      VARCHAR(512) NOT NULL,
  album_type   VARCHAR(16)  NOT NULL,
  release_date VARCHAR(10)  NOT NULL,   -- Spotify gives YYYY, YYYY-MM or YYYY-MM-DD
  total_tracks SMALLINT     NOT NULL,
  url          VARCHAR(255) NOT NULL,
  CONSTRAINT fk_releases_run FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE,
  INDEX idx_releases_album (album_id),
  INDEX idx_releases_run_position (run_id, position)
);
