"""Verify original datasets after checkout, without third-party dependencies."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify():
    manifest = json.loads((ROOT / 'docs/evidence/input_manifest.json').read_text(encoding='utf-8'))
    expected = {'spotify_dataset.csv', 'the_grammy_awards.csv'}
    if {entry['file'] for entry in manifest} != expected or len(manifest) != 2:
        raise ValueError('Input manifest must contain exactly the two supplied datasets')
    for entry in manifest:
        path = ROOT / 'data/input' / entry['file']
        content = path.read_bytes()
        if len(content) != entry['bytes'] or hashlib.sha256(content).hexdigest() != entry['sha256']:
            raise ValueError(f'Original dataset differs from manifest: {path.name}')
        print(f'OK {path.name}: {len(content):,} bytes, SHA-256 matches', flush=True)


if __name__ == '__main__':
    verify()
