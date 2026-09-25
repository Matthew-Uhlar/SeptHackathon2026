from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import core
from profiling import (PROFILE_COLUMNS, RUN_TABLE_COLUMNS, answer_giveaway_columns, profile_columns,
                       saved_run_table)

SAMPLE = Path(__file__).parent / 'data' / 'ai4i2020.csv'


@pytest.fixture(scope='module')
def sample():
    return pd.read_csv(SAMPLE)


@pytest.fixture(scope='module')
def trained_run(sample):
    return core.train(sample, source_label='UCI AI4I generated sample')


def _flagged(df):
    return {item['Column']: item for item in answer_giveaway_columns(df)}


def _no_comma_and(text):
    assert ', and' not in str(text)


# ---- profile_columns ----

def test_profile_clean_sample(sample):
    profile = profile_columns(sample)
    assert list(profile.columns) == PROFILE_COLUMNS
    assert list(profile['Column']) == list(sample.columns)
    roles = dict(zip(profile['Column'], profile['Role']))
    assert all(roles[c] == 'Input' for c in core.FEATURES)
    assert roles[core.TARGET] == 'Target'
    assert roles['UDI'] == roles['Product ID'] == roles['TWF'] == 'Excluded'
    torque = profile.set_index('Column').loc['Torque [Nm]']
    assert torque['Missing'] == 0
    assert torque['Min'] == sample['Torque [Nm]'].min()
    assert torque['Median'] == sample['Torque [Nm]'].median()
    assert torque['Max'] == sample['Torque [Nm]'].max()
    product = profile.set_index('Column').loc['Product ID']
    assert product['Unique values'] == 10000
    assert product['Min'] is None and product['Max'] is None
    assert profile.set_index('Column').loc['Type', 'Median'] is None


def test_profile_messy_values_do_not_leak_text():
    df = pd.DataFrame({'Torque [Nm]': ['40', '41.5', 'secret-note', None, 'inf'] + ['42'] * 95,
                       'Notes': ['confidential text'] * 50 + [None] * 50,
                       'Empty': [None] * 100,
                       'Machine failure': [0, 1, 'x', None] + [0] * 96})
    profile = profile_columns(df).set_index('Column')
    assert profile.loc['Torque [Nm]', 'Missing'] == 1
    assert profile.loc['Torque [Nm]', 'Min'] == 40.0
    assert profile.loc['Torque [Nm]', 'Max'] == 42.0
    assert profile.loc['Empty', 'Missing'] == 100
    assert profile.loc['Empty', 'Unique values'] == 0
    assert profile.loc['Empty', 'Min'] is None
    assert profile.loc['Notes', 'Min'] is None
    text = profile.to_csv()
    assert 'secret-note' not in text and 'confidential' not in text


def test_profile_missing_required_columns():
    df = pd.DataFrame({'Type': ['L', 'M'], 'Extra': [1, 2]})
    profile = profile_columns(df)
    assert list(profile['Role']) == ['Input', 'Excluded']
    assert core.TARGET not in set(profile['Column'])


def test_profile_empty_frame_with_headers():
    df = pd.DataFrame(columns=core.FEATURES + [core.TARGET, 'UDI'])
    profile = profile_columns(df)
    assert len(profile) == 8
    assert (profile['Missing'] == 0).all()
    assert profile['Min'].isna().all()
    assert profile_columns(pd.DataFrame()).columns.tolist() == PROFILE_COLUMNS


# ---- answer_giveaway_columns ----

def test_ai4i_failure_mode_columns_flagged(sample):
    flagged = _flagged(sample)
    assert {'TWF', 'HDF', 'PWF', 'OSF'} <= set(flagged)
    assert 'RNF' not in flagged  # random failures mostly carry a no-failure label in this file
    for item in flagged.values():
        assert 'already excluded from training' in item['Evidence']
        assert 'records the answer rather than a reading taken beforehand' in item['Evidence']
        assert 'cause' not in item['Evidence'].replace('proof of a cause', '')
        _no_comma_and(item['Evidence'])
    strengths = [item['Strength'] for item in answer_giveaway_columns(sample)]
    assert strengths == sorted(strengths, reverse=True)


def test_ids_not_flagged(sample):
    flagged = _flagged(sample)
    assert 'UDI' not in flagged
    assert 'Product ID' not in flagged
    for column in core.FEATURES + [core.TARGET]:
        assert column not in flagged


def test_copy_of_target_flagged_noise_not(sample):
    df = sample.copy()
    rng = np.random.default_rng(0)
    df['Copy of label'] = df[core.TARGET]
    df['Inverted label'] = 1 - df[core.TARGET]
    df['Noise'] = rng.normal(size=len(df))
    df['Noise flag'] = rng.integers(0, 2, size=len(df))
    flagged = _flagged(df)
    assert flagged['Copy of label']['Strength'] == 1.0
    assert 'Inverted label' in flagged
    assert 'Noise' not in flagged and 'Noise flag' not in flagged


def test_text_mapping_flagged_without_repeating_values(sample):
    df = sample.copy()
    df['Status note'] = np.where(df[core.TARGET] == 1, 'stopped-XYZ', 'running-XYZ')
    df['Mixed text'] = np.where(np.arange(len(df)) % 2 == 0, 'even', 'odd')
    flagged = _flagged(df)
    assert flagged['Status note']['Strength'] == 1.0
    assert 'XYZ' not in flagged['Status note']['Evidence']
    assert 'Mixed text' not in flagged
    _no_comma_and(flagged['Status note']['Evidence'])


def test_giveaway_handles_bad_or_missing_labels(sample):
    assert answer_giveaway_columns(sample.drop(columns=[core.TARGET])) == []
    no_labels = sample.copy()
    no_labels[core.TARGET] = 'unknown'
    assert answer_giveaway_columns(no_labels) == []
    one_class = sample.copy()
    one_class[core.TARGET] = 0
    assert answer_giveaway_columns(one_class) == []
    assert answer_giveaway_columns(pd.DataFrame(columns=sample.columns)) == []
    assert answer_giveaway_columns(pd.DataFrame()) == []


def test_giveaway_messy_values_and_partial_labels(sample):
    df = sample.head(2000).copy().astype(object)
    df.loc[0, 'HDF'] = 'oops'
    df.loc[1, core.TARGET] = 'x'
    df.loc[2, core.TARGET] = None
    df['All missing'] = None
    df['Infinite'] = np.inf
    flagged = _flagged(df)
    assert 'All missing' not in flagged and 'Infinite' not in flagged
    assert 'oops' not in str(answer_giveaway_columns(df))


# ---- saved_run_table ----

def test_saved_run_table_empty_and_missing(tmp_path):
    for folder in [tmp_path, tmp_path / 'absent']:
        table = saved_run_table(folder)
        assert table.empty and list(table.columns) == RUN_TABLE_COLUMNS


def test_saved_run_table_two_runs_and_corrupt(tmp_path, trained_run):
    older = dict(trained_run, metadata=dict(trained_run['metadata'], trained_at_utc='2026-01-01T00:00:00+00:00'))
    newer = dict(trained_run, metadata=dict(trained_run['metadata'], trained_at_utc='2026-06-01T12:30:00+00:00'),
                 source_label='Uploaded CSV (origin not verified)')
    core.save_run(older, tmp_path)
    core.save_run(newer, tmp_path)
    (tmp_path / 'broken.joblib').write_bytes(b'not a joblib file')
    table = saved_run_table(tmp_path)
    assert list(table.columns) == RUN_TABLE_COLUMNS
    assert len(table) == 3
    assert list(table['Trained (UTC)'][:2]) == ['2026-06-01 12:30:00', '2026-01-01 00:00:00']
    assert table.iloc[0]['Data source'] == 'Uploaded CSV (origin not verified)'
    assert table.iloc[2]['Data source'] == 'Could not be loaded'
    first = table.iloc[0]
    winner = trained_run['winner']
    assert first['Selected model'] == winner
    assert first['Selection F1'] == round(trained_run['validation'][winner]['F1'], 3)
    assert first['Final-check F1'] == round(trained_run['test'][winner]['F1'], 3)
    assert first['Failures found'] == trained_run['test'][winner]['Failures found']
    assert first['Dataset'] == trained_run['fingerprint'][:12]
    for value in table.astype(str).to_numpy().ravel():
        _no_comma_and(value)


def test_saved_run_table_rejects_incompatible_run(tmp_path, trained_run):
    core.save_run(dict(trained_run, features=['Torque [Nm]']), tmp_path)
    table = saved_run_table(tmp_path)
    assert list(table['Data source']) == ['Could not be loaded']
