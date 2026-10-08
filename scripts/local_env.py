"""Local notebook connection configuration; never print credentials."""
import os
from pathlib import Path
from sqlalchemy.engine import URL


def configure():
    if 'MUSIC_DB_URL' not in os.environ:
        root = Path(__file__).resolve().parents[1]
        values = dict(line.split('=', 1) for line in (root / '.env').read_text().splitlines()
                      if line and not line.startswith('#') and '=' in line)
        os.environ['MUSIC_DB_URL'] = URL.create('postgresql+psycopg2', username='workshop',
            password=values['POSTGRES_PASSWORD'], host='localhost', port=5434, database='music').render_as_string(hide_password=False)
