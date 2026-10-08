"""Exercise real scheduled Airflow runs and preserve observed, not simulated, states."""
import hashlib
import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, text

from src.common import ROOT, batch_dir, engine, sha256, write_json
from src.load import SUMMARY_SQL

DAG = 'reliable_music_pipeline'


def airflow(*args):
    result = subprocess.run(['airflow', *args], check=True, text=True, capture_output=True)
    return result.stdout


def snapshot():
    with engine().connect() as conn:
        summary = dict(conn.execute(text(SUMMARY_SQL)).mappings().one())
        rows = [dict(x) for x in conn.execute(text('SELECT * FROM dw.v_entries ORDER BY entry_key')).mappings()]
    summary['content_sha256'] = hashlib.sha256(json.dumps(rows, sort_keys=True, default=str).encode()).hexdigest()
    return summary


def run_case(meta, run_id, scenario, evidence):
    airflow('dags', 'trigger', DAG, '--run-id', run_id, '--conf', json.dumps({'scenario': scenario}))
    deadline = time.monotonic() + 900
    state = None
    while time.monotonic() < deadline:
        with meta.connect() as conn:
            state = conn.execute(text('SELECT state FROM dag_run WHERE dag_id=:dag AND run_id=:run'), {'dag': DAG, 'run': run_id}).scalar()
        if state in ['success', 'failed']:
            break
        time.sleep(5)
    if state not in ['success', 'failed']:
        raise TimeoutError(f'Run did not finish: {run_id} state={state}')
    with meta.connect() as conn:
        tasks = [dict(x) for x in conn.execute(text('''SELECT task_id,state,try_number,start_date,end_date
            FROM task_instance WHERE dag_id=:dag AND run_id=:run ORDER BY task_id'''), {'dag': DAG, 'run': run_id}).mappings()]
    output = evidence / run_id
    output.mkdir(parents=True, exist_ok=True)
    for artifact in batch_dir(run_id).glob('*.json'):
        shutil.copyfile(artifact, output / artifact.name)
    logdir = Path('/opt/airflow/logs') / f'dag_id={DAG}' / f'run_id={run_id}'
    if logdir.exists():
        shutil.copytree(logdir, output / 'task_logs', dirs_exist_ok=True)
    result = {'run_id': run_id, 'scenario': scenario, 'dag_state': state, 'tasks': tasks,
              'artifact_directory': str(batch_dir(run_id))}
    write_json(output / 'airflow_states.json', result)
    print(json.dumps(result, default=str), flush=True)
    return result


def main():
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    evidence = ROOT / 'docs/evidence' / stamp
    evidence.mkdir(parents=True, exist_ok=True)
    original_hash = sha256(ROOT / 'data/input/spotify_dataset.csv')
    meta = create_engine(os.environ['AIRFLOW__DATABASE__SQL_ALCHEMY_CONN'])
    airflow('dags', 'unpause', DAG)
    baseline = run_case(meta, f'baseline_{stamp}', 'normal', evidence)
    assert baseline['dag_state'] == 'success', baseline
    before = snapshot()
    failure = run_case(meta, f'failure_{stamp}', 'invalid_popularity', evidence)
    states = {x['task_id']: x['state'] for x in failure['tasks']}
    assert failure['dag_state'] == 'failed' and states['validate_spotify_raw'] == 'failed'
    assert states['extract_spotify'] == 'success'
    for task in ['transform_and_integrate', 'validate_prepared', 'load_dw']:
        assert states[task] == 'upstream_failed', states
    after_failure = snapshot()
    assert before == after_failure, 'Failed quality batch changed the warehouse'
    rerun = run_case(meta, f'rerun_{stamp}', 'normal', evidence)
    assert rerun['dag_state'] == 'success'
    after_rerun = snapshot()
    assert before == after_rerun, 'Same-source rerun changed counts, measures or content'
    assert original_hash == sha256(ROOT / 'data/input/spotify_dataset.csv')
    with engine().connect() as conn:
        kpis = dict(conn.execute(text('SELECT * FROM dw.v_kpis')).mappings().one())
    result = {'airflow_version': airflow('version').strip(), 'baseline': baseline['run_id'],
              'failure': failure['run_id'], 'rerun': rerun['run_id'], 'before': before,
              'after_failure': after_failure, 'after_rerun': after_rerun,
              'unchanged_original': True, 'kpis': kpis, 'evidence_directory': str(evidence)}
    write_json(evidence / 'reliability_summary.json', result)
    write_json(ROOT / 'docs/evidence/latest_reliability.json', result)
    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
