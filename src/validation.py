"""GX 1.x suites and explicit Validation Definitions, with severity-based gates."""
import json
from pathlib import Path

import great_expectations as gx
import pandas as pd

from src.common import LOG, write_json
from src.profiling import CATEGORIES
from src.transform import PREPARED_COLUMNS


class QualityError(ValueError):
    pass


def expectation(name, rule, severity='Critical', **kwargs):
    return getattr(gx.expectations, name)(meta={'rule_id': rule, 'severity': severity}, **kwargs)


def rules(layer, frame, expected_rows=None):
    e = expectation
    checks = [e('ExpectTableRowCountToBeBetween', f'{layer}-NONEMPTY', min_value=1)]
    if layer == 'spotify_raw':
        checks += [e('ExpectColumnValuesToNotBeNull', 'S02', column='track_id'),
                   e('ExpectColumnValuesToMatchRegex', 'S02-format', column='track_id', regex=r'^[A-Za-z0-9]{22}$'),
                   e('ExpectColumnValuesToBeUnique', 'S03', 'Warning', column='track_id')]
        for col in ['track_name', 'artists']:
            checks += [e('ExpectColumnValuesToNotBeNull', f'S04-{col}', 'Warning', column=col)]
        for col, maximum in [('popularity', 100), ('energy', 1), ('danceability', 1)]:
            checks += [e('ExpectColumnValuesToNotBeNull', f'S05-{col}-complete', column=col),
                       e('ExpectColumnValuesToBeBetween', f'S05-{col}', column=col, min_value=0, max_value=maximum)]
    elif layer == 'grammy_raw':
        checks += [e('ExpectColumnValuesToBeUnique', 'G02-id', column='source_row_id'),
                   e('ExpectColumnValuesToNotBeNull', 'G02-complete', column='source_row_id'),
                   e('ExpectColumnValuesToMatchRegex', 'G03', column='year', regex=r'^(19[5-9][0-9]|20[0-9]{2})$'),
                   e('ExpectColumnValuesToNotBeNull', 'G03-complete', column='year'),
                   e('ExpectColumnValuesToNotBeNull', 'G04-complete', column='category'),
                   e('ExpectColumnValuesToMatchRegex', 'G04', column='category', regex=r'\S'),
                   e('ExpectColumnValuesToBeInSet', 'G05', column='_scope_identity_valid', value_set=[True]),
                   e('ExpectColumnUniqueValueCountToBeBetween', 'G06', 'Warning', column='winner', min_value=2, max_value=2)]
    elif layer == 'prepared':
        checks += [e('ExpectTableRowCountToEqual', 'P02', value=expected_rows),
                   e('ExpectColumnValuesToBeUnique', 'P03', column='entry_key'),
                   e('ExpectColumnValuesToBeInSet', 'P04', column='category', value_set=CATEGORIES),
                   e('ExpectColumnValuesToBeBetween', 'P05', column='year', min_value=1950, max_value=2099),
                   e('ExpectColumnValuesToBeInSet', 'P06', column='match_status', value_set=['matched', 'unmatched', 'ambiguous']),
                   e('ExpectColumnValuesToBeInSet', 'P07', column='_link_valid', value_set=[True]),
                   e('ExpectColumnValuesToBeInSet', 'P08', column='_measures_valid', value_set=[True]),
                   e('ExpectColumnSumToBeBetween', 'P09', column='matched', min_value=1),
                   e('ExpectColumnValuesToBeInSet', 'P10', 'Warning', column='match_status', value_set=['matched'])]
        for col in ['entry_key', 'source_row_id', 'year', 'category', 'nominee', 'artist', 'candidate_count', 'matched', 'match_status']:
            checks += [e('ExpectColumnValuesToNotBeNull', f'P11-{col}', column=col)]
    else:
        raise ValueError(f'Unknown layer {layer}')
    return checks


REQUIRED = {
    'spotify_raw': ['track_id', 'track_name', 'artists', 'popularity', 'energy', 'danceability'],
    'grammy_raw': ['source_row_id', 'year', 'category', 'nominee', 'artist', 'winner'],
    'prepared': PREPARED_COLUMNS,
}


def evaluate(frame, layer, output, expected_rows=None):
    context = gx.get_context(mode='ephemeral')
    datasource = context.data_sources.add_pandas(name='music')
    asset = datasource.add_dataframe_asset(name=layer)
    definition = asset.add_batch_definition_whole_dataframe('whole_batch')
    missing = set(REQUIRED[layer]) - set(frame.columns)
    checks = [expectation('ExpectTableColumnsToMatchSet', f'{layer}-SCHEMA',
                         column_set=REQUIRED[layer], exact_match=(layer == 'prepared'))]
    evaluated = frame.copy()
    if not missing:
        if layer == 'grammy_raw':
            eligible = frame.category.isin(CATEGORIES)
            identity = frame[['nominee', 'artist']].fillna('').apply(lambda s: s.astype(str).str.strip().ne('')).all(axis=1)
            evaluated['_scope_identity_valid'] = ~eligible | identity
        if layer == 'prepared':
            # Diagnostics are evaluated by GX; original columns remain untouched.
            matched = frame.match_status.eq('matched')
            metrics = ['popularity', 'energy', 'danceability']
            track_fields = ['track_id', 'track_name', 'spotify_artists']
            evaluated['_link_valid'] = (
                (matched & frame.candidate_count.eq(1) & frame.matched.eq(1) & frame[track_fields].notna().all(axis=1))
                | (frame.match_status.eq('unmatched') & frame.candidate_count.eq(0) & frame.matched.eq(0) & frame[track_fields].isna().all(axis=1))
                | (frame.match_status.eq('ambiguous') & frame.candidate_count.gt(1) & frame.matched.eq(0) & frame[track_fields].isna().all(axis=1)))
            evaluated['_measures_valid'] = ((matched & frame.popularity.between(0, 100)
                & frame.energy.between(0, 1) & frame.danceability.between(0, 1))
                | (~matched & frame[metrics].isna().all(axis=1)))
            # Include diagnostic columns in the expected evaluated schema.
            checks[0] = expectation('ExpectTableColumnsToMatchSet', 'prepared-SCHEMA',
                column_set=PREPARED_COLUMNS + ['_link_valid', '_measures_valid'], exact_match=True)
        checks += rules(layer, evaluated, expected_rows)
    suite = context.suites.add(gx.ExpectationSuite(name=layer, expectations=checks))
    validation = context.validation_definitions.add(gx.ValidationDefinition(name=layer, data=definition, suite=suite))
    result = validation.run(batch_parameters={'dataframe': evaluated}, result_format={'result_format': 'SUMMARY'})
    details = result.to_json_dict()
    failed_critical = []
    for item in details['results']:
        meta = item['expectation_config']['meta']
        if not item['success']:
            LOG.warning('GX layer=%s rule=%s severity=%s result=%s', layer, meta['rule_id'], meta['severity'], item['result'])
            if meta['severity'] == 'Critical':
                failed_critical.append(meta['rule_id'])
    report = {'layer': layer, 'rows': len(frame), 'gx_success': details['success'],
              'policy_success': not failed_critical, 'critical_failures': failed_critical,
              'validation_definition': layer, 'suite': suite.to_json_dict(), 'gx_result': details}
    write_json(output, report)  # Persist even when rejecting the batch.
    if failed_critical:
        raise QualityError(f'{layer}: Critical rules failed {failed_critical}; evidence={output}')
    LOG.info('GX layer=%s accepted rows=%s report=%s', layer, len(frame), output)
    return report


def validate(path, layer):
    path = Path(path)
    expected = None
    if layer == 'prepared':
        expected = json.loads((path.parent / 'reconciliation.json').read_text())['prepared_rows']
    evaluate(pd.read_parquet(path), layer, path.parent / f'gx_{layer}.json', expected)
    return str(path)
