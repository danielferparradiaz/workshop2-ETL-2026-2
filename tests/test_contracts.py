import json

import pandas as pd
import pytest

from src.transform import integrate
from src.validation import QualityError, evaluate


def spotify():
    return pd.DataFrame([dict(track_id='a'*22, track_name='Song', artists='Artist', popularity=50, energy=.5, danceability=.6)])


def grammy():
    return pd.DataFrame([dict(source_row_id=1, year='2019', category='Record Of The Year', nominee=' song ', artist='ARTIST', winner='True')])


def test_repeated_genres_do_not_multiply_and_versions_are_ambiguous():
    s = spotify()
    p, _, r, _ = integrate(pd.concat([s, s]), grammy())
    assert len(p) == 1 and p.iloc[0].matched == 1
    assert r['collapsed_repeated_rows'] == 1
    other = s.copy()
    other['track_id'] = 'b'*22
    p, _, _, _ = integrate(pd.concat([s, other]), grammy())
    assert p.iloc[0].match_status == 'ambiguous'
    assert p.iloc[0].candidate_count == 2
    assert p.iloc[0].track_id is None and p.iloc[0].popularity is None


def test_conflicting_id_is_quarantined_not_arbitrarily_selected():
    s = spotify()
    other = s.copy()
    other['popularity'] = 90
    p, quarantine, r, _ = integrate(pd.concat([s, other]), grammy())
    assert len(quarantine) == 2 and r['conflicting_track_ids'] == 1
    assert p.iloc[0].match_status == 'unmatched'


def test_raw_critical_failure_persists_gx_evidence(tmp_path):
    s = spotify()
    s.loc[0, 'popularity'] = 101
    output = tmp_path / 'failed.json'
    with pytest.raises(QualityError, match='S05-popularity'):
        evaluate(s, 'spotify_raw', output)
    report = json.loads(output.read_text(encoding='utf-8'))
    assert not report['policy_success']
    assert 'S05-popularity' in report['critical_failures']


def test_warning_does_not_block_grammy(tmp_path):
    report = evaluate(grammy(), 'grammy_raw', tmp_path / 'warning.json')
    assert report['policy_success'] and not report['gx_success']


def test_missing_schema_reports_rule_instead_of_keyerror(tmp_path):
    with pytest.raises(QualityError, match='spotify_raw-SCHEMA'):
        evaluate(spotify().drop(columns='popularity'), 'spotify_raw', tmp_path / 'schema.json')


def test_prepared_rejects_measure_on_unmatched_row(tmp_path):
    p, _, _, _ = integrate(spotify(), grammy())
    evaluate(p, 'prepared', tmp_path / 'ok.json', expected_rows=1)
    p.loc[0, ['matched', 'candidate_count', 'match_status']] = [0, 0, 'unmatched']
    p.loc[0, ['track_id', 'track_name', 'spotify_artists']] = None
    with pytest.raises(QualityError, match='P08'):
        evaluate(p, 'prepared', tmp_path / 'bad.json', expected_rows=1)
