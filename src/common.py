import hashlib
import json
import logging
import os
from pathlib import Path

from sqlalchemy import create_engine

ROOT = Path(os.environ.get('PROJECT_ROOT', Path(__file__).resolve().parents[1]))
LOG = logging.getLogger('music_pipeline')


def engine():
    return create_engine(os.environ['MUSIC_DB_URL'], pool_pre_ping=True)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str), encoding='utf-8')


def batch_dir(run_id):
    # Stable, filesystem-safe run namespace (different runs never overwrite each other).
    return ROOT / 'data/runs' / hashlib.sha256(run_id.encode()).hexdigest()[:24]


def save_frame(frame, directory, name):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f'{name}.parquet'
    frame.to_parquet(path, index=False)
    LOG.info('%s rows=%s artifact=%s', name, len(frame), path)
    return str(path)
