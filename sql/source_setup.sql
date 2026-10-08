CREATE SCHEMA IF NOT EXISTS source;
CREATE TABLE IF NOT EXISTS source.grammy (
    source_row_id integer PRIMARY KEY,
    year text, title text, published_at text, updated_at text,
    category text, nominee text, artist text, workers text, img text, winner text
);
CREATE TABLE IF NOT EXISTS source.import_manifest (
    source_name text PRIMARY KEY, sha256 text NOT NULL,
    row_count integer NOT NULL, imported_at timestamptz NOT NULL DEFAULT now()
);
