from datetime import timedelta

import pendulum
from airflow.sdk import Param, dag, get_current_context, task


@dag(dag_id='reliable_music_pipeline', schedule=None,
     start_date=pendulum.datetime(2026, 1, 1, tz='UTC'), catchup=False,
     max_active_runs=1, default_args={'retries': 0},
     params={'scenario': Param('normal', enum=['normal', 'invalid_popularity'])},
     tags=['workshop2', 'spotify', 'grammy', 'gx'])
def reliable_music_pipeline():
    @task
    def extract_spotify():
        from src.extract import spotify
        ctx = get_current_context()
        return spotify(ctx['run_id'], ctx['params']['scenario'])

    @task(retries=2, retry_delay=timedelta(seconds=20), retry_exponential_backoff=True)
    def extract_grammys():
        from airflow.exceptions import AirflowFailException
        from sqlalchemy.exc import OperationalError
        from src.extract import grammys
        try:
            return grammys(get_current_context()['run_id'])
        except OperationalError:
            raise
        except Exception as exc:
            raise AirflowFailException(str(exc)) from exc

    @task
    def validate_spotify_raw(path):
        from src.validation import validate
        return validate(path, 'spotify_raw')

    @task
    def validate_grammys_raw(path):
        from src.validation import validate
        return validate(path, 'grammy_raw')

    @task
    def transform_and_integrate(spotify_path, grammy_path):
        from src.transform import transform
        return transform(spotify_path, grammy_path)

    @task
    def validate_prepared(path):
        from src.validation import validate
        return validate(path, 'prepared')

    @task(retries=2, retry_delay=timedelta(seconds=20), retry_exponential_backoff=True)
    def load_dw(path):
        from airflow.exceptions import AirflowFailException
        from sqlalchemy.exc import OperationalError
        from src.load import load
        try:
            return load(path, get_current_context()['run_id'])
        except OperationalError:
            raise
        except Exception as exc:
            raise AirflowFailException(str(exc)) from exc

    spotify = validate_spotify_raw(extract_spotify())
    grammy = validate_grammys_raw(extract_grammys())
    prepared = transform_and_integrate(spotify, grammy)
    load_dw(validate_prepared(prepared))


reliable_music_pipeline()
