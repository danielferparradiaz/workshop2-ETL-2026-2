"""Cross-platform setup and real reliability experiment from a fresh clone."""
import subprocess
import sys
from pathlib import Path

from scripts.verify_inputs import verify

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    print('\n> ' + ' '.join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def main():
    verify()
    run('docker', 'info', '--format', '{{.OSType}}')
    run('docker', 'compose', 'version')
    if not (ROOT / '.env').exists():
        run(sys.executable, '-m', 'scripts.configure')
    for folder in ['logs', 'data/runs']:
        (ROOT / folder).mkdir(parents=True, exist_ok=True)
    run('docker', 'compose', 'config', '--quiet')
    run('docker', 'compose', 'build')
    run('docker', 'compose', 'up', '-d')
    for module in ['wait_ready', 'prepare_source', 'reliability', 'verify_runtime']:
        run('docker', 'compose', 'exec', '-T', 'airflow-scheduler', 'python', '-m', f'scripts.{module}')
    print('\nReady: Airflow http://localhost:8082 | Dashboard http://localhost:8502')
    print('Success, controlled failure and rerun evidence: docs/evidence/latest_reliability.json')


if __name__ == '__main__':
    main()
