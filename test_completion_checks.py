import copy
from pathlib import Path

import pytest
from sklearn.base import clone

import core
import completion_checks as cc
from completion_checks import completion_checks, data_fingerprint, clean_frame

ROOT = Path(__file__).parent
NAMES = ['Answer columns never enter training', 'Both models use the same final examples', 'Final check kept separate',
         'Repeat run gives the same results', 'Reloading preserves predictions', 'Known bad inputs receive clear warnings']


@pytest.fixture(scope='module')
def df():
    return core.read_csv((ROOT / 'data/ai4i2020.csv').read_bytes())


@pytest.fixture(scope='module')
def run(df):
    return core.train(df, source_label='UCI AI4I generated sample')


@pytest.fixture(scope='module')
def fresh_results(df, run):
    return completion_checks(df, run)


def by_name(results):
    return {r['Check']: r for r in results}


def test_shape_and_all_pass_on_fresh_run(fresh_results):
    assert [r['Check'] for r in fresh_results] == NAMES
    for r in fresh_results:
        assert set(r) == {'Check', 'Passed', 'Detail'}
        assert r['Passed'] is True, r
        assert isinstance(r['Detail'], str) and r['Detail'] and ', and' not in r['Detail']
    assert 'all 2000 final-check readings' in by_name(fresh_results)['Reloading preserves predictions']['Detail']


def test_fingerprint_matches_core(df, run):
    assert data_fingerprint(df) == run['fingerprint']
    assert data_fingerprint(df.head(500)) != run['fingerprint']
    assert data_fingerprint(df.drop(columns=['Torque [Nm]'])) is None
    assert len(clean_frame(df)) == sum(run['counts'].values())


def test_checks_do_not_mutate_run(df, run):
    before = copy.deepcopy({k: v for k, v in run.items() if k != 'model'})
    completion_checks(df, run, repeat=False)
    assert {k: v for k, v in run.items() if k != 'model'} == before


def test_tampered_features_fail(df, run):
    bad = copy.deepcopy(run)
    bad['features'] = core.FEATURES + ['TWF']
    result = by_name(completion_checks(df, bad, repeat=False))['Answer columns never enter training']
    assert result['Passed'] is False and 'TWF' in result['Detail']


def test_tampered_counts_fail(df, run):
    bad = copy.deepcopy(run)
    bad['counts']['final check'] += 1
    results = by_name(completion_checks(df, bad, repeat=False))
    assert results['Both models use the same final examples']['Passed'] is False
    assert results['Final check kept separate']['Passed'] is False


def test_tampered_confusion_counts_fail(df, run):
    bad = copy.deepcopy(run)
    stats = bad['test']['Always no failure']
    stats['Failures missed'] -= 1
    stats['Correct no-failure readings'] += 1
    result = by_name(completion_checks(df, bad, repeat=False))['Both models use the same final examples']
    assert result['Passed'] is False and 'different numbers of actual failures' in result['Detail']


def test_overlapping_split_indices_fail(df, run):
    bad = copy.deepcopy(run)
    bad['split_indices']['final'][0] = bad['split_indices']['training'][0]
    result = by_name(completion_checks(df, bad, repeat=False))['Final check kept separate']
    assert result['Passed'] is False and 'more than one group' in result['Detail']


def test_swapped_model_fails(df, run):
    bad = copy.deepcopy(run)
    clean = clean_frame(df)
    rows = run['split_indices']['training'][:1500]
    other = clone(run['model']).set_params(model__n_estimators=3, model__max_depth=2)
    bad['model'] = other.fit(clean.loc[rows, core.FEATURES], clean.loc[rows, core.TARGET])
    results = by_name(completion_checks(df, bad))
    assert results['Answer columns never enter training']['Passed'] is True
    assert results['Repeat run gives the same results']['Passed'] is False
    assert results['Reloading preserves predictions']['Passed'] is False


def test_mismatched_fingerprint_skips_repeat(df, run):
    other = df.head(3000)
    results = by_name(completion_checks(other, run))
    repeat = results['Repeat run gives the same results']
    assert repeat['Passed'] is None and repeat['Detail'] == "Not checked: the selected file differs from this run's data."
    reload = results['Reloading preserves predictions']
    assert reload['Passed'] is True and 'recorded training ranges' in reload['Detail']


def test_no_data_and_repeat_disabled(run):
    results = by_name(completion_checks(None, run, repeat=True))
    assert results['Repeat run gives the same results']['Passed'] is None
    assert results['Reloading preserves predictions']['Passed'] is True
    skipped = by_name(completion_checks(None, run, repeat=False))['Repeat run gives the same results']
    assert skipped['Passed'] is None and 'skipped' in skipped['Detail']


def test_loaded_run_path(df, run, tmp_path):
    loaded = core.load_run(core.save_run(run, tmp_path))
    assert all(r['Passed'] is True for r in completion_checks(df, loaded))


def test_legacy_run_without_split_indices(df, run):
    legacy = copy.deepcopy(run)
    del legacy['split_indices']
    legacy.pop('metadata')
    results = by_name(completion_checks(df, legacy, repeat=False))
    assert results['Final check kept separate']['Passed'] is None
    assert results['Reloading preserves predictions']['Passed'] is True
    assert 'all 2000 final-check readings' in results['Reloading preserves predictions']['Detail']


def test_bad_sample_missing_is_not_checked(run, monkeypatch, tmp_path):
    monkeypatch.setattr(cc, 'BAD_SAMPLE', tmp_path / 'absent.csv')
    result = cc.check_bad_inputs()
    assert result['Passed'] is None


def test_bad_sample_without_errors_fails(monkeypatch, tmp_path):
    good = tmp_path / 'good.csv'
    good.write_bytes((ROOT / 'data/ai4i2020.csv').read_bytes())
    monkeypatch.setattr(cc, 'BAD_SAMPLE', good)
    assert cc.check_bad_inputs()['Passed'] is False


def test_broken_run_reports_failure_instead_of_crashing(df, run):
    bad = copy.deepcopy(run)
    del bad['test']
    results = by_name(completion_checks(df, bad, repeat=False))
    assert results['Both models use the same final examples']['Passed'] is False
    assert 'could not complete' in results['Both models use the same final examples']['Detail']
