"""Check staged publication payload, original bytes and local secret exclusion."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def main():
    names = [s.decode('utf-8') for s in git('ls-files', '-z').split(b'\0') if s]
    if not names:
        raise ValueError('Stage intended files before checking the release')
    for name in names:
        if name == '.env' or name.startswith(('.venv/', 'logs/', 'data/runs/')) or '__pycache__/' in name:
            raise ValueError(f'Local-only path in index: {name}')
    secrets = []
    env = ROOT / '.env'
    if env.exists():
        for line in env.read_text(encoding='utf-8').splitlines():
            key, sep, value = line.partition('=')
            if sep and key in {'POSTGRES_PASSWORD', 'AIRFLOW_JWT_SECRET'} and len(value) >= 16:
                secrets.append(value.encode())
    total = 0
    for name in names:
        content = git('show', ':' + name)
        total += len(content)
        if any(secret in content for secret in secrets):
            raise ValueError(f'Local secret found in staged file: {name}')
        if len(content) >= 100 * 1024 * 1024:
            raise ValueError(f'File exceeds GitHub normal Git size limit: {name}')
    manifest = json.loads(git('show', ':docs/evidence/input_manifest.json'))
    for entry in manifest:
        content = git('show', ':data/input/' + entry['file'])
        if len(content) != entry['bytes'] or hashlib.sha256(content).hexdigest() != entry['sha256']:
            raise ValueError(f'Staged original bytes changed: {entry["file"]}')
    print(f'Release index OK: {len(names)} files, {total / 1024 / 1024:.2f} MiB; original hashes match; local secrets excluded.')


if __name__ == '__main__':
    main()
