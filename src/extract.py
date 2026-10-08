from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.common import ROOT, batch_dir, engine, save_frame, sha256, write_json


def spotify(run_id, scenario='normal'):
    folder = batch_dir(run_id)
    path = ROOT / 'data/input/spotify_dataset.csv'
    df = pd.read_csv(path)  # Only CSV parsing; no dropping, filtering or repairs.
    if scenario == 'invalid_popularity':
        df.loc[0, 'popularity'] = 101  # Fault injection in this run's copy only.
    elif scenario != 'normal':
        raise ValueError(f'Unknown test scenario: {scenario}')
    artifact = save_frame(df, folder, 'spotify_raw')
    write_json(folder / 'spotify_extract.json', {'run_id': run_id, 'source': str(path),
               'source_sha256': sha256(path), 'rows': len(df), 'scenario': scenario})
    return artifact


def grammys(run_id):
    folder = batch_dir(run_id)
    with engine().connect().execution_options(isolation_level='REPEATABLE READ') as conn:
        with conn.begin():
            df = pd.read_sql(text('SELECT * FROM source.grammy ORDER BY source_row_id'), conn)
            manifest = dict(conn.execute(text("SELECT * FROM source.import_manifest WHERE source_name='grammy'")).mappings().one())
    artifact = save_frame(df, folder, 'grammy_raw')
    write_json(folder / 'grammy_extract.json', {'run_id': run_id, 'source': 'PostgreSQL/music/source.grammy',
               'query': 'SELECT * FROM source.grammy ORDER BY source_row_id', 'rows': len(df), 'import': manifest})
    return artifact
