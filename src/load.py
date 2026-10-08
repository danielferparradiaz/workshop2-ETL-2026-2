import json
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.common import LOG, ROOT, engine, write_json

SUMMARY_SQL = '''SELECT COUNT(*) AS fact_count, COALESCE(SUM(matched),0) AS matched_count,
    COALESCE(SUM(popularity),0) AS popularity_sum, COALESCE(SUM(energy),0) AS energy_sum
    FROM dw.fact_grammy_catalog'''


def load(path, run_id):
    from src.validation import validate
    # Defensive revalidation also protects direct callers and altered artifacts.
    validate(path, 'prepared')
    frame = pd.read_parquet(path)
    categories = pd.DataFrame({'category': sorted(frame.category.unique())})
    categories.insert(0, 'category_key', range(1, len(categories) + 1))
    artists = pd.DataFrame({'artist': sorted(frame.artist.unique())})
    artists.insert(0, 'artist_key', range(1, len(artists) + 1))
    years = pd.DataFrame({'year_key': sorted(frame.year.unique())})
    tracks = frame.loc[frame.matched.eq(1), ['track_id', 'track_name', 'spotify_artists']].drop_duplicates('track_id').sort_values('track_id')
    tracks.insert(0, 'track_key', range(1, len(tracks) + 1))
    unknown = pd.DataFrame([{'track_key': 0, 'track_id': '__UNASSIGNED__', 'track_name': 'Sin asignar', 'spotify_artists': 'Sin asignar'}])
    tracks = pd.concat([unknown, tracks], ignore_index=True)
    facts = frame.merge(categories, on='category', validate='many_to_one').merge(artists, on='artist', validate='many_to_one')
    facts = facts.merge(tracks[['track_id', 'track_key']], on='track_id', how='left', validate='many_to_one')
    facts['track_key'] = facts.track_key.fillna(0).astype(int)
    facts = facts.rename(columns={'year': 'year_key'})
    facts = facts[['entry_key', 'source_row_id', 'year_key', 'category_key', 'artist_key', 'track_key',
                   'nominee', 'match_status', 'candidate_count', 'matched', 'popularity', 'energy', 'danceability']]
    with engine().begin() as conn:
        conn.execute(text('SELECT pg_advisory_xact_lock(202602)'))
        conn.execute(text((ROOT / 'sql/dw_schema.sql').read_text()))
        before = dict(conn.execute(text(SUMMARY_SQL)).mappings().one())
        conn.execute(text('TRUNCATE dw.fact_grammy_catalog, dw.dim_year, dw.dim_category, dw.dim_artist, dw.dim_track'))
        for table, data in [('dim_year', years), ('dim_category', categories), ('dim_artist', artists), ('dim_track', tracks), ('fact_grammy_catalog', facts)]:
            data.to_sql(table, conn, schema='dw', if_exists='append', index=False, method='multi', chunksize=500)
        after = dict(conn.execute(text(SUMMARY_SQL)).mappings().one())
        if after['fact_count'] != len(frame):
            raise ValueError('DW row reconciliation failed')
        conn.execute(text('''INSERT INTO dw.load_audit(run_id,fact_count,matched_count,popularity_sum,energy_sum)
            VALUES (:run_id,:fact_count,:matched_count,:popularity_sum,:energy_sum)
            ON CONFLICT(run_id) DO UPDATE SET loaded_at=now(), fact_count=excluded.fact_count,
            matched_count=excluded.matched_count, popularity_sum=excluded.popularity_sum, energy_sum=excluded.energy_sum'''),
            {'run_id': run_id, **after})
    report = {'run_id': run_id, 'before': before, 'after': after, 'strategy': 'transactional_full_snapshot'}
    write_json(Path(path).parent / 'load_summary.json', report)
    LOG.info('DW committed %s', json.dumps(report))
    return report
