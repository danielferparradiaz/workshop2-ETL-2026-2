"""Read-only source profiling; preserves input values, includes cross-source risks."""
import json
from pathlib import Path

import pandas as pd

CATEGORIES = ['Record Of The Year', 'Best Pop Solo Performance']


def profile_frame(df):
    result = {'rows': len(df), 'columns': list(df), 'dtypes': df.dtypes.astype(str).to_dict(),
              'missing': df.isna().sum().to_dict(),
              'missing_pct': (df.isna().mean() * 100).to_dict(),
              'distinct': df.nunique().to_dict(),
              'exact_duplicate_rows': int(df.duplicated().sum()), 'frequencies': {}, 'numeric': {}}
    for col in df:
        if pd.api.types.is_numeric_dtype(df[col]) and not pd.api.types.is_bool_dtype(df[col]):
            result['numeric'][col] = df[col].describe().to_dict()
        else:
            result['frequencies'][col] = df[col].fillna('<NULL>').astype(str).value_counts().head(15).to_dict()
    return result


def profile_sources(spotify, grammy):
    s, g = profile_frame(spotify), profile_frame(grammy)
    s['duplicate_track_ids'] = int(spotify.duplicated('track_id').sum())
    s['duplicates_without_export_index'] = int(spotify.drop(columns=['Unnamed: 0'], errors='ignore').duplicated().sum())
    s['conflicting_track_ids'] = int((spotify.groupby('track_id')[['track_name', 'artists', 'popularity', 'energy', 'danceability']].nunique(dropna=False).max(axis=1) > 1).sum())
    g['year_coverage'] = sorted(grammy.year.dropna().unique().tolist())
    for col in ['published_at', 'updated_at']:
        dates = pd.to_datetime(grammy[col], errors='coerce', utc=True)
        g[col + '_parse'] = {'invalid_or_missing': int(dates.isna().sum()), 'min': str(dates.min()), 'max': str(dates.max())}
    selected = grammy[grammy.category.isin(CATEGORIES)]
    g['scope_rows'] = len(selected)
    g['scope_category_counts'] = selected.category.value_counts().to_dict()
    g['winner_counts'] = grammy.winner.astype(str).value_counts().to_dict()
    g['scope_groups_multiple_true'] = int((selected.groupby(['year', 'category']).winner.sum() > 1).sum())
    g['scope_missing_artist'] = int(selected.artist.isna().sum())
    g['scope_business_key_duplicates'] = int(selected.duplicated(['year', 'category', 'nominee', 'artist']).sum())
    return {'spotify': s, 'grammy': g}


def main():
    root = Path(__file__).resolve().parents[1]
    s = pd.read_csv(root / 'data/input/spotify_dataset.csv')
    g = pd.read_csv(root / 'data/input/the_grammy_awards.csv')
    result = profile_sources(s, g)
    target = root / 'docs/evidence/profile.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, default=str), encoding='utf-8')
    print(json.dumps({k: {a: b for a, b in v.items() if a not in ['frequencies', 'numeric', 'distinct', 'dtypes']} for k, v in result.items()}, indent=2))


if __name__ == '__main__':
    main()
