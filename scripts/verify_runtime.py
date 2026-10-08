"""Check authoring dependencies, selective retries and warehouse constraints."""
import importlib.metadata
import runpy

from sqlalchemy import text

from src.common import ROOT, engine, write_json

namespace = runpy.run_path('/opt/airflow/dags/reliable_music_pipeline.py')
dag = namespace['reliable_music_pipeline']()
expected = {
    'extract_spotify': {'validate_spotify_raw'},
    'extract_grammys': {'validate_grammys_raw'},
    'validate_spotify_raw': {'transform_and_integrate'},
    'validate_grammys_raw': {'transform_and_integrate'},
    'transform_and_integrate': {'validate_prepared'},
    'validate_prepared': {'load_dw'},
    'load_dw': set(),
}
assert set(dag.task_ids) == set(expected)
tasks = []
for task in dag.tasks:
    assert task.downstream_task_ids == expected[task.task_id]
    assert task.retries == (2 if task.task_id in ['extract_grammys', 'load_dw'] else 0)
    assert task.trigger_rule == 'all_success'
    tasks.append({'task': task.task_id, 'downstream': sorted(task.downstream_task_ids),
                  'retries': task.retries, 'trigger_rule': task.trigger_rule})
with engine().connect() as conn:
    constraints = [dict(x) for x in conn.execute(text('''SELECT conname, pg_get_constraintdef(oid) AS definition
        FROM pg_constraint WHERE conrelid='dw.fact_grammy_catalog'::regclass ORDER BY conname''')).mappings()]
    counts = {name: conn.execute(text(f'SELECT COUNT(*) FROM dw.{name}')).scalar_one()
              for name in ['dim_year', 'dim_category', 'dim_artist', 'dim_track', 'fact_grammy_catalog']}
    metrics = [dict(x) for x in conn.execute(text('SELECT * FROM dw.v_category_metrics ORDER BY category')).mappings()]
result = {'versions': {p: importlib.metadata.version(p) for p in ['apache-airflow', 'great-expectations', 'pandas', 'SQLAlchemy']},
          'dag_tasks': tasks, 'fact_constraints': constraints, 'dw_counts': counts, 'category_metrics': metrics}
write_json(ROOT / 'docs/evidence/runtime_checks.json', result)
print(result)
