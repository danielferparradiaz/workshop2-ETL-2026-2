"""Source preparation only: preserve CSV strings and reconcile all imported values."""
import pandas as pd
from sqlalchemy import text
from src.common import ROOT, engine, sha256, write_json


def main():
    path = ROOT / 'data/input/the_grammy_awards.csv'
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df.insert(0, 'source_row_id', range(1, len(df) + 1))
    db = engine()
    with db.begin() as conn:
        conn.execute(text((ROOT / 'sql/source_setup.sql').read_text()))
        conn.execute(text('TRUNCATE source.grammy'))
        df.to_sql('grammy', conn, schema='source', if_exists='append', index=False, method='multi', chunksize=500)
        loaded = pd.read_sql(text('SELECT * FROM source.grammy ORDER BY source_row_id'), conn)
        pd.testing.assert_frame_equal(df, loaded, check_dtype=False)
        conn.execute(text('''INSERT INTO source.import_manifest(source_name, sha256, row_count)
            VALUES ('grammy', :hash, :count) ON CONFLICT(source_name) DO UPDATE SET
            sha256=excluded.sha256, row_count=excluded.row_count, imported_at=now()'''),
            {'hash': sha256(path), 'count': len(df)})
    result = {'csv_rows': len(df), 'db_rows': len(loaded), 'all_values_equal': True,
              'sha256': sha256(path), 'table': 'source.grammy', 'database': 'music'}
    write_json(ROOT / 'docs/evidence/source_import.json', result)
    print(result)


if __name__ == '__main__':
    main()
