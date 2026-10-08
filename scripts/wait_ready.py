"""Wait inside Airflow for healthy services and a parsed workshop DAG."""
import json
import os
import time
import urllib.error
import urllib.request

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


def main():
    meta = create_engine(os.environ['AIRFLOW__DATABASE__SQL_ALCHEMY_CONN'], pool_pre_ping=True)
    deadline = time.monotonic() + 300
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen('http://airflow-api-server:8080/api/v2/monitor/health', timeout=5) as response:
                health = json.load(response)
            services_ready = all(health.get(service, {}).get('status') == 'healthy'
                                 for service in ['metadatabase', 'scheduler', 'dag_processor'])
            with meta.connect() as conn:
                parsed = conn.execute(text('SELECT COUNT(*) FROM dag WHERE dag_id=:dag'),
                                      {'dag': 'reliable_music_pipeline'}).scalar_one() == 1
            if services_ready and parsed:
                print('Airflow API, metadata, scheduler and DAG processor ready; workshop DAG discovered.')
                return
        except (urllib.error.URLError, TimeoutError, SQLAlchemyError, ValueError):
            pass
        time.sleep(5)
    raise TimeoutError('Airflow not ready after 300 s. Inspect docker compose logs and airflow dags list-import-errors.')


if __name__ == '__main__':
    main()
