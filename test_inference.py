"""Tests for per-reading scores with what-if checks and batch scoring."""
import copy
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import core
import inference

ROOT = Path(__file__).parent
DEFAULT_ROW = {'Type': 'L', 'Air temperature [K]': 300.0, 'Process temperature [K]': 310.0,
               'Rotational speed [rpm]': 1500.0, 'Torque [Nm]': 40.0, 'Tool wear [min]': 100.0}
MODEL_NAMES = ['Logistic regression', 'Random forest']


@pytest.fixture(scope='module')
def sample():
    return core.read_csv((ROOT / 'data/ai4i2020.csv').read_bytes())


@pytest.fixture(scope='module')
def run(sample):
    return core.train(sample, source_label='UCI AI4I generated sample')


def _estimator(name):
    if name == 'Logistic regression':
        return LogisticRegression(max_iter=1500, class_weight='balanced', random_state=core.SEED)
    return RandomForestClassifier(n_estimators=120, max_depth=12, min_samples_leaf=2, class_weight='balanced',
                                  n_jobs=2, random_state=core.SEED)


@pytest.fixture(scope='module')
def runs(run, sample):
    """Both model types trained on the same training rows as the sample run."""
    clean = sample.copy()
    clean[core.NUMERIC] = clean[core.NUMERIC].apply(pd.to_numeric)
    clean[core.TARGET] = pd.to_numeric(clean[core.TARGET]).astype(int)
    clean = clean.drop_duplicates(subset=core.FEATURES + [core.TARGET]).reset_index(drop=True)
    training = clean.loc[run['split_indices']['training']]
    result = {}
    for name in MODEL_NAMES:
        if name == run['winner']:
            result[name] = run
            continue
        other = copy.copy(run)
        preprocessing = ColumnTransformer([('numbers', StandardScaler(), core.NUMERIC),
                                           ('type', OneHotEncoder(categories=[['L', 'M', 'H']], handle_unknown='error'), ['Type'])])
        other['model'] = Pipeline([('prepare', preprocessing), ('model', _estimator(name))]).fit(training[core.FEATURES], training[core.TARGET])
        other['winner'] = name
        result[name] = other
    assert isinstance(result['Logistic regression']['model'].named_steps['model'], LogisticRegression)
    assert isinstance(result['Random forest']['model'].named_steps['model'], RandomForestClassifier)
    return result


def _rows(sample, count=200):
    picked = sample.sample(n=count, random_state=7)
    # Include every failure row among the first picks so both flags appear.
    failures = sample[sample[core.TARGET] == 1].head(40)
    return pd.concat([failures, picked]).reset_index(drop=True)


# --- model_score and score_band ---------------------------------------------

@pytest.mark.parametrize('name', MODEL_NAMES)
def test_model_score_matches_core_predict(runs, sample, name):
    run = runs[name]
    for _, record in _rows(sample, 20).iterrows():
        row = {c: record[c] for c in core.FEATURES}
        result = inference.model_score(run, row)
        flag, outside = core.predict(run, row)
        assert result['flag'] == flag
        assert result['outside'] == outside
        assert 0.0 <= result['score'] <= 1.0
        # Flag and score agree about the side of the threshold.
        assert (result['score'] > 0.5) == bool(flag) or np.isclose(result['score'], 0.5)
        band = inference.score_band(result['score'], result['flag'])
        if flag:
            assert band != 'Well below the 0.5 threshold'
        else:
            assert band != 'Well above the 0.5 threshold'


def test_model_score_shape(run):
    result = inference.model_score(run, DEFAULT_ROW)
    assert set(result) == {'flag', 'score', 'outside'}
    assert type(result['flag']) is int and type(result['score']) is float and isinstance(result['outside'], list)


@pytest.mark.parametrize('score,flag,expected', [
    (0.05, 0, 'Well below the 0.5 threshold'),
    (0.4, 0, 'Well below the 0.5 threshold'),
    (0.45, 0, 'Near the 0.5 threshold'),
    (0.5, 0, 'Near the 0.5 threshold'),
    (0.5, 1, 'Near the 0.5 threshold'),
    (0.55, 1, 'Near the 0.5 threshold'),
    (0.6, 1, 'Well above the 0.5 threshold'),
    (0.97, 1, 'Well above the 0.5 threshold'),
    # Contradictory inputs never produce a band that contradicts the flag.
    (0.9, 0, 'Near the 0.5 threshold'),
    (0.1, 1, 'Near the 0.5 threshold'),
])
def test_score_band(score, flag, expected):
    assert inference.score_band(score, flag) == expected


@pytest.mark.parametrize('bad', [
    {'Type': 'X'}, {'Type': None}, {'Torque [Nm]': -1.0}, {'Tool wear [min]': float('nan')},
    {'Rotational speed [rpm]': float('inf')},
])
def test_model_score_rejects_invalid_rows_like_core(run, bad):
    row = {**DEFAULT_ROW, **bad}
    with pytest.raises(ValueError) as expected:
        core.predict(run, row)
    with pytest.raises(ValueError) as actual:
        inference.model_score(run, row)
    assert str(actual.value) == str(expected.value)
    with pytest.raises(ValueError):
        inference.what_if(run, row)


def test_out_of_range_reading_is_reported(run):
    row = {**DEFAULT_ROW, 'Torque [Nm]': 500.0}
    result = inference.model_score(run, row)
    assert result['outside'] == ['Torque [Nm]']
    assert inference.model_score(run, DEFAULT_ROW)['outside'] == []


def test_type_absent_from_training(run):
    limited = copy.copy(run)
    limited['observed_types'] = ['L', 'M']
    row = {**DEFAULT_ROW, 'Type': 'H'}
    with pytest.raises(ValueError, match='absent from the training examples'):
        core.predict(limited, row)
    with pytest.raises(ValueError, match='absent from the training examples'):
        inference.model_score(limited, row)
    compared = [r['Compared with'] for r in inference.what_if(limited, DEFAULT_ROW) if r['Input'] == 'Type']
    assert compared == ['type M']
    frame = pd.DataFrame([DEFAULT_ROW, row, {**DEFAULT_ROW, 'Type': 'M'}])
    results, problems = inference.score_batch(limited, frame)
    assert list(results['Data row']) == [1, 3]
    assert problems == [{'Data row': 2, 'Problem': 'This product type was absent from the training examples.'}]


# --- what_if ----------------------------------------------------------------

@pytest.mark.parametrize('name', MODEL_NAMES)
def test_what_if_rows(runs, name):
    run = runs[name]
    row = {**DEFAULT_ROW, 'Torque [Nm]': 65.0, 'Tool wear [min]': 210.0}
    base = inference.model_score(run, row)
    rows = inference.what_if(run, row)
    assert len(rows) == len(core.NUMERIC) + len(run['observed_types']) - 1
    assert [set(r) for r in rows] == [{'Input', 'Current value', 'Compared with', 'Score change', 'Flag would change'}] * len(rows)
    changes = [abs(r['Score change']) for r in rows]
    assert changes == sorted(changes, reverse=True)
    means = dict(zip(core.NUMERIC, run['model'].named_steps['prepare'].named_transformers_['numbers'].mean_))
    for r in rows:
        changed = dict(row)
        if r['Input'] == 'Type':
            changed['Type'] = r['Compared with'].removeprefix('type ')
            assert r['Current value'] == 'L'
        else:
            changed[r['Input']] = means[r['Input']]
            assert r['Compared with'] == f"training average {means[r['Input']]:.1f}"
        other = inference.model_score(run, changed)
        assert r['Score change'] == pytest.approx(base['score'] - other['score'])
        assert r['Flag would change'] == (other['flag'] != base['flag'])


def test_what_if_means_come_from_training_rows_only(run, sample):
    clean = sample.copy()
    clean = clean.drop_duplicates(subset=core.FEATURES + [core.TARGET]).reset_index(drop=True)
    training = clean.loc[run['split_indices']['training'], core.NUMERIC].astype(float)
    scaler_means = run['model'].named_steps['prepare'].named_transformers_['numbers'].mean_
    assert np.allclose(scaler_means, training.mean().to_numpy())


def test_what_if_type_falls_back_to_encoder_categories(run):
    legacy = copy.copy(run)
    legacy.pop('observed_types')
    compared = sorted(r['Compared with'] for r in inference.what_if(legacy, DEFAULT_ROW) if r['Input'] == 'Type')
    assert compared == ['type H', 'type M']


# --- score_batch ------------------------------------------------------------

@pytest.mark.parametrize('name', MODEL_NAMES)
def test_batch_matches_per_row_predictions(runs, sample, name):
    run = runs[name]
    rows = _rows(sample)
    results, problems = inference.score_batch(run, rows)
    assert problems == []
    assert list(results.columns) == ['Data row', 'UDI', 'Product ID'] + core.FEATURES + ['Model flag', 'Model score', 'Outside training range']
    assert list(results['Data row']) == list(range(1, len(rows) + 1))
    assert list(results['UDI']) == list(rows['UDI'])
    frames = []
    for position, record in rows.iterrows():
        row = {c: record[c] for c in core.FEATURES}
        flag, outside = core.predict(run, row)
        out = results.iloc[position]
        assert out['Model flag'] == ('Failure pattern' if flag else 'No failure pattern')
        assert out['Outside training range'] == ', '.join(outside)
        frames.append(pd.DataFrame([row], columns=core.FEATURES))
    single_scores = run['model'].predict_proba(pd.concat(frames, ignore_index=True))[:, 1]
    assert list(results['Model score']) == [round(float(s), 3) for s in single_scores]
    assert (results['Model flag'] == 'Failure pattern').any()
    assert (results['Model flag'] == 'No failure pattern').any()


def test_batch_skips_invalid_rows_without_echoing_values(run):
    frame = pd.DataFrame([
        DEFAULT_ROW,
        {**DEFAULT_ROW, 'Type': 'Q'},
        {**DEFAULT_ROW, 'Torque [Nm]': -3.5},
        {**DEFAULT_ROW, 'Tool wear [min]': None},
        {**DEFAULT_ROW, 'Air temperature [K]': 'warm'},
        {**DEFAULT_ROW, 'Rotational speed [rpm]': float('inf')},
        {**DEFAULT_ROW, 'Torque [Nm]': 900.0},
    ])
    frame['Machine failure'] = 0
    results, problems = inference.score_batch(run, frame)
    assert list(results['Data row']) == [1, 7]
    assert [p['Data row'] for p in problems] == [2, 3, 4, 5, 6]
    assert 'Machine failure' not in results.columns
    for p in problems:
        assert set(p) == {'Data row', 'Problem'}
        for raw in ['Q', '-3.5', 'warm', 'inf', 'None', 'nan']:
            assert raw not in p['Problem']
    assert results.iloc[1]['Outside training range'] == 'Torque [Nm]'
    assert results.iloc[0]['Outside training range'] == ''
    # Every skipped row is also rejected by core.predict.
    for p in problems:
        record = frame.iloc[p['Data row'] - 1]
        with pytest.raises(ValueError):
            core.predict(run, {c: record[c] for c in core.FEATURES})
    summary = inference.batch_summary(results)
    assert summary == {'Rows scored': 2, 'Flagged': int((results['Model flag'] == 'Failure pattern').sum()),
                       'Outside training range': 1}


def test_batch_missing_columns_and_row_limit(run, sample):
    with pytest.raises(ValueError, match=r'Missing required columns: Torque \[Nm\], Tool wear \[min\]'):
        inference.score_batch(run, sample.drop(columns=['Torque [Nm]', 'Tool wear [min]']))
    with pytest.raises(ValueError, match='at most 100 rows'):
        inference.score_batch(run, sample.head(101), limit=100)
    with pytest.raises(ValueError, match='at most 5000 rows'):
        inference.score_batch(run, sample)
    with pytest.raises(ValueError):
        inference.score_batch(run, sample.head(5), limit=0)


def test_batch_all_invalid_and_empty(run):
    results, problems = inference.score_batch(run, pd.DataFrame([{**DEFAULT_ROW, 'Type': 'Z'}]))
    assert results.empty and len(problems) == 1
    assert inference.batch_summary(results) == {'Rows scored': 0, 'Flagged': 0, 'Outside training range': 0}
    results, problems = inference.score_batch(run, pd.DataFrame(columns=core.FEATURES))
    assert results.empty and problems == []


def test_batch_without_ids_and_from_csv_bytes(run, sample):
    raw = sample.head(30)[core.FEATURES].to_csv(index=False).encode()
    results, problems = inference.score_batch(run, core.read_csv(raw))
    assert problems == [] and len(results) == 30
    assert 'UDI' not in results.columns and 'Product ID' not in results.columns


def test_batch_of_5000_rows_is_fast(run, sample):
    start = time.perf_counter()
    results, problems = inference.score_batch(run, sample.head(5000))
    assert len(results) + len(problems) == 5000
    assert time.perf_counter() - start < 10


# --- persistence and wording ------------------------------------------------

def test_save_reload_gives_identical_scores(run, sample, tmp_path):
    path = core.save_run(run, tmp_path)
    assert path.parent == tmp_path
    loaded = core.load_run(path)
    assert inference.model_score(loaded, DEFAULT_ROW) == inference.model_score(run, DEFAULT_ROW)
    assert inference.what_if(loaded, DEFAULT_ROW) == inference.what_if(run, DEFAULT_ROW)
    before, _ = inference.score_batch(run, sample.head(300))
    after, _ = inference.score_batch(loaded, sample.head(300))
    pd.testing.assert_frame_equal(before, after)


def test_texts_are_plain_and_honest(run):
    texts = [inference.SCORE_NOTE, inference.WHAT_IF_NOTE]
    texts += [inference.score_band(s, f) for s in (0.1, 0.5, 0.9) for f in (0, 1)]
    texts += [r['Compared with'] for r in inference.what_if(run, DEFAULT_ROW)]
    _, problems = inference.score_batch(run, pd.DataFrame([{**DEFAULT_ROW, 'Type': 'Z'}, {**DEFAULT_ROW, 'Torque [Nm]': -1}, {**DEFAULT_ROW, 'Torque [Nm]': None}]))
    texts += [p['Problem'] for p in problems]
    for text in texts:
        assert ', and' not in text
    note = inference.SCORE_NOTE.lower()
    assert 'uncalibrated' in note and '0.5' in note and 'balanced class weighting' in note and 'not the chance' in note
    assert 'training average' in inference.WHAT_IF_NOTE and 'not a physical cause' in inference.WHAT_IF_NOTE
    assert 'interact' in inference.WHAT_IF_NOTE
    for text in [inference.SCORE_NOTE, inference.WHAT_IF_NOTE]:
        lowered = text.lower()
        assert 'probability' not in lowered and 'time to failure' not in lowered and 'calibrated probab' not in lowered
