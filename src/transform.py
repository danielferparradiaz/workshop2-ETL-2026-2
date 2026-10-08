"""Conservative, auditable linkage; never choose an arbitrary recording version."""
import hashlib
import json
import unicodedata
from collections import defaultdict
from pathlib import Path

import pandas as pd

from src.common import save_frame, write_json
from src.profiling import CATEGORIES

SPOTIFY_FIELDS = ['track_name', 'artists', 'popularity', 'energy', 'danceability']
PREPARED_COLUMNS = ['entry_key', 'source_row_id', 'year', 'category', 'nominee', 'artist',
                    'match_status', 'candidate_count', 'matched', 'track_id', 'track_name',
                    'spotify_artists', 'popularity', 'energy', 'danceability']


def normalize(value):
    if pd.isna(value):
        return ''
    return ' '.join(unicodedata.normalize('NFKC', str(value)).casefold().split())


def integrate(spotify, grammy):
    # Export index and genre must not multiply the track grain. Conflicting IDs
    # have no documented latest observation, so none of their versions is chosen.
    conflicts = spotify.groupby('track_id')[SPOTIFY_FIELDS].nunique(dropna=False).max(axis=1)
    conflict_ids = set(conflicts[conflicts > 1].index)
    missing = spotify[['track_id', 'track_name', 'artists']].isna().any(axis=1)
    blank = spotify[['track_id', 'track_name', 'artists']].fillna('').astype(str).apply(lambda s: s.str.strip().eq('')).any(axis=1)
    rejected = spotify[missing | blank | spotify.track_id.isin(conflict_ids)].copy()
    rejected['reason'] = 'missing_matching_key_or_conflicting_track_id'
    valid = spotify[~(missing | blank | spotify.track_id.isin(conflict_ids))].copy()
    tracks = valid.drop_duplicates('track_id').set_index('track_id')
    lookup = defaultdict(set)
    for track_id, row in tracks.iterrows():
        for artist in str(row.artists).split(';'):
            key = (normalize(row.track_name), normalize(artist))
            if all(key):
                lookup[key].add(track_id)
    scoped = grammy[grammy.category.isin(CATEGORIES)].copy()
    unique = scoped.drop_duplicates(['year', 'category', 'nominee', 'artist'])
    rows = []
    candidates_log = []
    for row in unique.itertuples(index=False):
        key = hashlib.sha256(json.dumps([str(row.year), row.category, row.nominee, row.artist], ensure_ascii=False).encode()).hexdigest()
        candidates = sorted(lookup[(normalize(row.nominee), normalize(row.artist))])
        count = len(candidates)
        result = dict.fromkeys(PREPARED_COLUMNS)
        result.update(entry_key=key, source_row_id=int(row.source_row_id), year=int(row.year),
                      category=row.category, nominee=row.nominee, artist=row.artist,
                      candidate_count=count, matched=int(count == 1),
                      match_status='matched' if count == 1 else ('ambiguous' if count > 1 else 'unmatched'))
        if count == 1:
            track = tracks.loc[candidates[0]]
            result.update(track_id=candidates[0], track_name=track.track_name, spotify_artists=track.artists,
                          popularity=float(track.popularity), energy=float(track.energy), danceability=float(track.danceability))
        rows.append(result)
        candidates_log.append({'entry_key': key, 'candidate_track_ids': candidates})
    prepared = pd.DataFrame(rows, columns=PREPARED_COLUMNS)
    reconciliation = {'spotify_raw_rows': len(spotify), 'quarantined_rows': len(rejected),
                      'conflicting_track_ids': len(conflict_ids), 'eligible_unique_tracks': len(tracks),
                      'collapsed_repeated_rows': len(valid) - len(tracks),
                      'grammy_raw_rows': len(grammy), 'out_of_scope': len(grammy) - len(scoped),
                      'scope_rows': len(scoped), 'collapsed_grammy_duplicates': len(scoped) - len(unique),
                      'prepared_rows': len(prepared), 'match_states': prepared.match_status.value_counts().to_dict()}
    assert len(spotify) == len(rejected) + len(tracks) + reconciliation['collapsed_repeated_rows']
    assert len(grammy) == reconciliation['out_of_scope'] + reconciliation['collapsed_grammy_duplicates'] + len(prepared)
    return prepared, rejected, reconciliation, candidates_log


def transform(spotify_path, grammy_path):
    folder = Path(spotify_path).parent
    prepared, quarantine, reconciliation, candidates = integrate(pd.read_parquet(spotify_path), pd.read_parquet(grammy_path))
    save_frame(quarantine, folder, 'spotify_quarantine')
    write_json(folder / 'reconciliation.json', reconciliation)
    write_json(folder / 'match_candidates.json', candidates)
    return save_frame(prepared, folder, 'prepared')
