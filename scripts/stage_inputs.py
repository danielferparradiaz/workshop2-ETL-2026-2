"""Copy supplied originals with byte-level reconciliation."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-dir', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    target = root / 'data/input'
    target.mkdir(parents=True, exist_ok=True)
    records = []
    for name in ['spotify_dataset.csv', 'the_grammy_awards.csv']:
        source = args.source_dir / name
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        destination = target / name
        if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest() != digest:
            raise ValueError(f'Refusing to overwrite different original: {destination}')
        if source.resolve() != destination.resolve():
            shutil.copyfile(source, destination)
        assert hashlib.sha256(destination.read_bytes()).hexdigest() == digest
        records.append({'file': name, 'bytes': destination.stat().st_size, 'sha256': digest})
    evidence = root / 'docs/evidence'
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / 'input_manifest.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
    print(json.dumps(records, indent=2))


if __name__ == '__main__':
    main()
