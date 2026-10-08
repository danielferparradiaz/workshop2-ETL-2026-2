CREATE SCHEMA IF NOT EXISTS dw;
CREATE TABLE IF NOT EXISTS dw.dim_year (year_key integer PRIMARY KEY CHECK(year_key BETWEEN 1950 AND 2099));
CREATE TABLE IF NOT EXISTS dw.dim_category (category_key integer PRIMARY KEY, category text UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS dw.dim_artist (artist_key integer PRIMARY KEY, artist text UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS dw.dim_track (
    track_key integer PRIMARY KEY, track_id text UNIQUE NOT NULL,
    track_name text NOT NULL, spotify_artists text NOT NULL
);
CREATE TABLE IF NOT EXISTS dw.fact_grammy_catalog (
    entry_key text PRIMARY KEY, source_row_id integer UNIQUE NOT NULL,
    year_key integer NOT NULL REFERENCES dw.dim_year,
    category_key integer NOT NULL REFERENCES dw.dim_category,
    artist_key integer NOT NULL REFERENCES dw.dim_artist,
    track_key integer NOT NULL REFERENCES dw.dim_track,
    nominee text NOT NULL,
    match_status text NOT NULL CHECK(match_status IN ('matched','unmatched','ambiguous')),
    candidate_count integer NOT NULL CHECK(candidate_count >= 0),
    matched integer NOT NULL CHECK(matched IN (0,1)),
    popularity double precision CHECK(popularity BETWEEN 0 AND 100),
    energy double precision CHECK(energy BETWEEN 0 AND 1),
    danceability double precision CHECK(danceability BETWEEN 0 AND 1),
    CHECK ((matched=1 AND match_status='matched' AND candidate_count=1 AND track_key<>0
            AND popularity IS NOT NULL AND energy IS NOT NULL AND danceability IS NOT NULL)
        OR (matched=0 AND track_key=0 AND popularity IS NULL AND energy IS NULL AND danceability IS NULL
            AND ((match_status='unmatched' AND candidate_count=0) OR (match_status='ambiguous' AND candidate_count>1))))
);
CREATE TABLE IF NOT EXISTS dw.load_audit (
    run_id text PRIMARY KEY, loaded_at timestamptz NOT NULL DEFAULT now(),
    fact_count integer NOT NULL, matched_count integer NOT NULL,
    popularity_sum double precision NOT NULL, energy_sum double precision NOT NULL
);
CREATE OR REPLACE VIEW dw.v_entries AS
SELECT f.entry_key, f.source_row_id, y.year_key AS year, c.category, a.artist,
       f.nominee, t.track_id, t.track_name, f.match_status, f.candidate_count,
       f.matched, f.popularity, f.energy, f.danceability
FROM dw.fact_grammy_catalog f
JOIN dw.dim_year y USING(year_key)
JOIN dw.dim_category c USING(category_key)
JOIN dw.dim_artist a USING(artist_key)
JOIN dw.dim_track t USING(track_key);
CREATE OR REPLACE VIEW dw.v_kpis AS
SELECT COUNT(*) AS entries, SUM(matched) AS matched_entries,
       100.0*AVG(matched) AS coverage_pct, AVG(popularity) AS avg_popularity,
       AVG(energy) AS avg_energy FROM dw.fact_grammy_catalog;
CREATE OR REPLACE VIEW dw.v_coverage AS
SELECT year, category, COUNT(*) AS entries, SUM(matched) AS matched_entries,
       100.0*AVG(matched) AS coverage_pct FROM dw.v_entries GROUP BY year, category;
CREATE OR REPLACE VIEW dw.v_category_metrics AS
SELECT category, COUNT(*) AS entries, SUM(matched) AS matched_entries,
       AVG(popularity) AS avg_popularity, AVG(energy) AS avg_energy,
       AVG(danceability) AS avg_danceability FROM dw.v_entries GROUP BY category;
