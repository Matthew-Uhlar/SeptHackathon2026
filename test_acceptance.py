"""Acceptance tests for SignalReady written by the testing team.

They encode the four completion checks from proposal slide 10 and walk the demo path the
way a user would: flawed sample / included sample / train / Model comparison / downloads /
What drove the model / save / refresh / reload / Try a prediction / batch scoring / Compare
saved runs. Edge cases found during exploratory testing are covered at the end.

- Everything runs through streamlit.testing.v1.AppTest (no browser) with default_timeout=60.
- Every test points SIGNALREADY_MODEL_DIR at a temporary folder. ./models is never touched.
- Bugs B1-B6 from TEST_REPORT.md are fixed. Their tests now run as ordinary regression tests.
  When a bug is fixed the test starts passing and strict mode fails the run as a reminder to
  remove the marker.
- The one browser test is opt-in: set SIGNALREADY_BROWSER_TESTS=1 with Playwright and Chromium
  installed (SIGNALREADY_CHROMIUM overrides the browser path / SIGNALREADY_TEST_PORT the port).
"""
import io
import json
import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import joblib
import numpy as np
import pandas as pd
import pytest
import streamlit.testing.v1.app_test as app_test_module
from streamlit.runtime.memory_media_file_storage import MemoryMediaFileStorage
from streamlit.testing.v1 import AppTest

import core
from completion_checks import clean_frame
from inference import model_score, score_batch

ROOT = Path(__file__).parent
APP = str(ROOT / 'app.py')
SAMPLE_BYTES = (ROOT / 'data' / 'ai4i2020.csv').read_bytes()
NEW_READINGS_BYTES = (ROOT / 'data' / 'new_readings.csv').read_bytes()
TAB_RESULTS = '2  Model comparison'
SLIDE_10_CHECKS = ['Known bad inputs receive clear warnings', 'Answer columns never enter training',
                   'Both models use the same final examples', 'Reloading preserves predictions']
ANSWER_COLUMNS = ['UDI', 'Product ID', 'TWF', 'HDF', 'PWF', 'OSF', 'RNF']
DEFAULT_READING = {'Type': 'L', 'Air temperature [K]': 300.0, 'Process temperature [K]': 310.0,
                   'Rotational speed [rpm]': 1500.0, 'Torque [Nm]': 40.0, 'Tool wear [min]': 100.0}


# ---------------------------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------------------------

DOWNLOADS = {}


class _RecordingStorage(MemoryMediaFileStorage):
    """AppTest keeps download bytes in a throwaway media store. Record them so tests can read them."""

    def load_and_get_id(self, path_or_data, mimetype, kind, filename=None):
        file_id = super().load_and_get_id(path_or_data, mimetype, kind, filename)
        DOWNLOADS[file_id] = path_or_data
        return file_id


@pytest.fixture(scope='module', autouse=True)
def _record_downloads():
    patch = pytest.MonkeyPatch()
    patch.setattr(app_test_module, 'MemoryMediaFileStorage', _RecordingStorage)
    yield
    patch.undo()


def new_session():
    """A fresh AppTest session is the equivalent of refreshing the browser page."""
    app = AppTest.from_file(APP, default_timeout=60).run(timeout=60)
    assert not app.exception
    return app


def click(app, label, where=None, timeout=90):
    next(b for b in (where or app).button if b.label == label).click().run(timeout=timeout)
    assert not app.exception, [e.value for e in app.exception]
    return app


def button(app, label, where=None):
    return next(b for b in (where or app).button if b.label == label)


def choose_source(app, source):
    app.sidebar.radio[0].set_value(source).run(timeout=60)
    assert not app.exception
    return app


def upload_training_file(app, name, data):
    choose_source(app, 'Upload a CSV')
    uploader = next(u for u in app.file_uploader if u.label == 'Equipment readings')
    uploader.set_value((name, data, 'text/csv')).run(timeout=60)
    assert not app.exception, [e.value for e in app.exception]
    return app


def upload_batch(app, name, data):
    uploader = next(u for u in app.tabs[2].file_uploader if u.label == 'Readings to score')
    uploader.set_value((name, data, 'text/csv')).run(timeout=60)
    assert not app.exception, [e.value for e in app.exception]
    return app


def downloaded(app, label):
    button_element = next(b for b in app.get('download_button') if b.proto.label == label)
    data = DOWNLOADS[button_element.proto.url.rsplit('/', 1)[-1].split('.')[0]]
    return data.decode('utf-8') if isinstance(data, bytes) else data


def expander(where, label):
    return next(e for e in where.expander if e.label == label)


def checks_table(app):
    # Shown with st.table (index Check / columns Result and Detail) so the evidence wraps on screen.
    table = expander(app.tabs[1], 'Completion checks').table[0].value
    return table.reset_index().rename(columns={'Result': 'Passed'})


def giveaway_lines(tab):
    return [m.value[2:] for m in tab.markdown if m.value.startswith('- Possible answer giveaway')]


def run_completion_checks(app):
    click(app, 'Run completion checks', app.tabs[1], timeout=120)
    return dict(zip(*checks_table(app)[['Check', 'Passed']].to_dict('list').values()))


def visible_text(app):
    kinds = ['title', 'header', 'subheader', 'markdown', 'caption', 'info', 'warning', 'error', 'success']
    return [element.value for kind in kinds for element in getattr(app, kind)]


def predict_in_app(app, **changes):
    tab = app.tabs[2]
    for label, value in changes.items():
        if label == 'Type':
            next(s for s in tab.selectbox if s.label == 'Product quality type').set_value(value)
        else:
            next(n for n in tab.number_input if n.label == label).set_value(value)
    click(app, 'Check these readings', tab, timeout=60)
    return app.tabs[2]


def sample_frame():
    return pd.read_csv(io.BytesIO(SAMPLE_BYTES))


def csv_bytes(frame):
    return frame.to_csv(index=False).encode('utf-8')


@pytest.fixture
def model_dir(tmp_path, monkeypatch):
    folder = tmp_path / 'models'
    monkeypatch.setenv('SIGNALREADY_MODEL_DIR', str(folder))
    return folder


@pytest.fixture(scope='module')
def sample_run():
    return core.train(core.read_csv(SAMPLE_BYTES), source_label='UCI AI4I generated sample')


# ---------------------------------------------------------------------------------------------
# Demo path (one browser-like session shared by the tests below)
# ---------------------------------------------------------------------------------------------

@pytest.fixture(scope='module')
def demo(tmp_path_factory):
    folder = tmp_path_factory.mktemp('acceptance_models')
    patch = pytest.MonkeyPatch()
    patch.setenv('SIGNALREADY_MODEL_DIR', str(folder))
    app = new_session()
    choose_source(app, 'Try a flawed sample')
    tab = app.tabs[0]
    flawed = SimpleNamespace(
        errors=[e.value for e in tab.error], warnings=[w.value for w in tab.warning],
        metrics={m.label: m.value for m in tab.metric},
        corrections=expander(tab, 'Where to correct the file').dataframe[0].value,
        balance=next(m.value for m in tab.markdown if m.value.startswith('Outcome balance')),
        train_disabled=button(app, 'Check and compare models').disabled)
    choose_source(app, 'Included sample')
    included = SimpleNamespace(errors=[e.value for e in app.tabs[0].error],
                               warnings=[w.value for w in app.tabs[0].warning],
                               giveaways=giveaway_lines(app.tabs[0]),
                               captions=[c.value for c in app.tabs[0].caption],
                               balance=next(m.value for m in app.tabs[0].markdown if m.value.startswith('Outcome balance')))
    started = time.perf_counter()
    click(app, 'Check and compare models', timeout=120)
    train_seconds = time.perf_counter() - started
    yield SimpleNamespace(app=app, folder=folder, flawed=flawed, included=included, train_seconds=train_seconds,
                          run=app.session_state['run'], active_tab=app.session_state['active_tab'],
                          notices=[s.value for s in app.success])
    patch.undo()


@pytest.fixture(scope='module')
def reloaded(demo):
    """Save the demo run / refresh the page / reload the saved run from the sidebar."""
    click(demo.app, 'Save selected model locally')
    saved = sorted(demo.folder.glob('*.joblib'))
    assert len(saved) == 1
    patch = pytest.MonkeyPatch()
    patch.setenv('SIGNALREADY_MODEL_DIR', str(demo.folder))
    app = new_session()
    assert 'run' not in app.session_state
    click(app, 'Reload saved model', app.sidebar)
    yield SimpleNamespace(app=app, saved=saved[0], original=demo.run)
    patch.undo()


def test_demo_flawed_sample_is_caught_before_training(demo):
    flawed = demo.flawed
    assert flawed.train_disabled
    assert flawed.metrics['Blocking issues'] == str(len(flawed.errors)) and flawed.errors
    assert any('empty' in e for e in flawed.errors)
    assert flawed.metrics['Repeated examples'] == '1'
    assert any('repeated' in w for w in flawed.warnings)
    first = flawed.corrections.iloc[0]
    assert (int(first['Data row']), first['Column']) == (10, 'Air temperature [K]')
    assert 'Missing value' in first['Problem']
    # DEMO_SCRIPT reference: 13 failure examples (23.6%) and 42 no-failure examples.
    assert '13 failure examples (23.6%' in flawed.balance and '42 no-failure examples' in flawed.balance


def test_demo_included_sample_is_ready_and_flags_giveaways(demo):
    included = demo.included
    assert not included.errors
    flagged = {w.split('Possible answer giveaway: ')[1].split(' ')[0] for w in included.giveaways}
    assert flagged == {'TWF', 'HDF', 'PWF', 'OSF'}
    excluded = next(c for c in included.captions if c.startswith('Excluded columns: '))
    assert set(excluded.removeprefix('Excluded columns: ').split(', ')) == set(ANSWER_COLUMNS)
    assert '339 failure examples (3.4%' in included.balance


def test_demo_training_opens_model_comparison(demo):
    assert demo.active_tab == TAB_RESULTS
    assert any('Comparison ready' in n for n in demo.notices)
    assert demo.run['source_label'] == 'UCI AI4I generated sample'
    assert demo.train_seconds < 60


def test_demo_model_comparison_matches_the_run(demo):
    tab, run = demo.app.tabs[1], demo.run
    stats = run['test'][run['winner']]
    assert {m.label: int(m.value) for m in tab.metric} == {k: stats[k] for k in ['Failures found', 'Failures missed', 'False alarms']}
    table = tab.dataframe[0].value
    assert list(table.index) == ['Logistic regression', 'Random forest', 'Always no failure']
    assert table.loc['Always no failure', 'Failures found'] == 0
    summary = next(m.value for m in tab.markdown if m.value.startswith('- '))
    assert f"found {stats['Failures found']} of the" in summary and f"missed {stats['Failures missed']}" in summary
    assert 'always predicts no failure' in summary


def test_demo_how_this_run_was_checked(demo):
    how = expander(demo.app.tabs[1], 'How this run was checked')
    assert any(m.value == 'Data source: UCI AI4I generated sample' for m in how.markdown)
    details = json.loads(how.get('json')[0].proto.body)
    assert details['dataset fingerprint'] == demo.run['fingerprint']
    assert details['approved inputs'] == core.FEATURES
    assert details['rows'] == {'training': 6000, 'selection': 2000, 'final check': 2000}


def test_demo_downloads_match_the_screen(demo):
    run, tab = demo.app.session_state['run'], demo.app.tabs[1]
    report = json.loads(downloaded(demo.app, 'Download results report'))
    assert report == json.loads(json.dumps(core.public_report(run)))
    assert 'model' not in report and 'split_indices' not in report
    text = downloaded(demo.app, 'Download results report (readable)')
    assert f"Dataset fingerprint: {run['fingerprint']}" in text
    assert f"Selected model: {run['winner']}" in text
    table = tab.dataframe[0].value
    for name in table.index:
        line = next(l for l in text.splitlines() if l.startswith(name))
        found, missed, alarms, correct = (int(v) for v in line[len(name):].split()[:4])
        assert (found, missed, alarms, correct) == tuple(int(table.loc[name, c]) for c in
                                                         ['Failures found', 'Failures missed', 'False alarms', 'Correct no-failure readings'])
    assert 'Limitations:' in text and 'calibrated failure probabilities' in text


def test_demo_what_drove_the_model_uses_only_approved_inputs(demo):
    tab = demo.app.tabs[3]
    assert tab.get('vega_lite_chart'), 'importance chart missing'
    contributions = expander(tab, 'View all approved-feature contributions').dataframe[0].value
    inputs = set(contributions['Input'])
    assert inputs == set(core.NUMERIC) | {'Product type L', 'Product type M', 'Product type H'}
    assert list(contributions['Input'])[:2] == ['Torque [Nm]', 'Rotational speed [rpm]']  # DEMO_SCRIPT section 5
    assert any('cause' in c.value for c in tab.caption)


def test_demo_completion_checks_all_pass_on_the_trained_run(demo):
    results = run_completion_checks(demo.app)
    assert len(results) == 6
    assert set(SLIDE_10_CHECKS) <= set(results)
    assert set(results.values()) == {'Passed'}, results


# ---------------------------------------------------------------------------------------------
# Proposal slide 10 completion checks
# ---------------------------------------------------------------------------------------------

BAD_UPLOADS = {
    'not UTF-8': (b'Type,Air temperature [K]\nL,29\xe9\n', 'UTF-8'),
    'ragged row': (b'a,b\n1,2\n3\n', 'Row 3 has 1 fields'),
    'repeated header': (b'a,a\n1,2\n', 'Column names repeat'),
    'blank header': (b'a,,b\n1,2,3\n', 'Every column needs a name'),
    'some columns only': (csv_bytes(sample_frame()[['Type', 'Air temperature [K]', 'Machine failure']].head(300)),
                          'Missing required columns: Process temperature [K], Rotational speed [rpm], Torque [Nm], Tool wear [min]'),
    'text in a number': (csv_bytes(sample_frame().head(300).astype({'Torque [Nm]': object}).assign(
        **{'Torque [Nm]': lambda d: d['Torque [Nm]'].where(d.index != 5, 'forty')})), 'Torque [Nm] must contain finite numbers'),
    'negative reading': (csv_bytes(sample_frame().head(300).assign(
        **{'Tool wear [min]': lambda d: d['Tool wear [min]'].where(d.index != 3, -5)})), 'negative readings'),
    'unknown type': (csv_bytes(sample_frame().head(300).assign(Type=lambda d: d['Type'].str.lower())), 'Type must be L or M or H'),
    'label not 0 or 1': (csv_bytes(sample_frame().head(300).assign(
        **{'Machine failure': lambda d: d['Machine failure'].where(d.index != 3, 2)})), '0 for no failure or 1 for failure'),
    'too few rows': (csv_bytes(sample_frame().head(20)), 'between 50 and 50000 rows'),
    'conflicting labels': (csv_bytes(pd.concat([sample_frame().head(300), sample_frame().head(1).assign(
        **{'Machine failure': 1, 'UDI': 99999})], ignore_index=True)), 'conflicting failure labels'),
}


@pytest.mark.parametrize('case', list(BAD_UPLOADS), ids=list(BAD_UPLOADS))
def test_slide10_known_bad_inputs_receive_clear_warnings(case, model_dir):
    data, expected = BAD_UPLOADS[case]
    app = upload_training_file(new_session(), case + '.csv', data)
    errors = [e.value for e in app.tabs[0].error]
    assert any(expected in e for e in errors), errors
    train = [b for b in app.button if b.label == 'Check and compare models']
    assert not train or train[0].disabled
    assert 'run' not in app.session_state


def test_slide10_answer_columns_never_enter_training(model_dir):
    frame = sample_frame().head(3000)
    frame['Failure copy'] = frame['Machine failure']  # an extra column identical to the answer
    app = upload_training_file(new_session(), 'with_copy.csv', csv_bytes(frame))
    giveaways = giveaway_lines(app.tabs[0])
    assert any(w.startswith('Possible answer giveaway: Failure copy') for w in giveaways), giveaways
    assert not button(app, 'Check and compare models').disabled
    click(app, 'Check and compare models', timeout=120)
    run = app.session_state['run']
    assert run['features'] == core.FEATURES
    assert list(run['model'].feature_names_in_) == core.FEATURES
    assert not set(run['model'].feature_names_in_) & set(ANSWER_COLUMNS + ['Failure copy', core.TARGET])
    assert run['source_label'] == 'Uploaded CSV (origin not verified)'
    assert run_completion_checks(app)['Answer columns never enter training'] == 'Passed'


def test_slide10_both_models_use_the_same_final_examples(demo):
    run = demo.run
    size = run['counts']['final check']
    final = set(run['split_indices']['final'])
    assert len(final) == size
    assert not final & set(run['split_indices']['training']) and not final & set(run['split_indices']['selection'])
    totals = {name: sum(stats[k] for k in ['Failures found', 'Failures missed', 'False alarms', 'Correct no-failure readings'])
              for name, stats in run['test'].items()}
    assert set(totals.values()) == {size} and len(totals) == 3
    assert len({stats['Failures found'] + stats['Failures missed'] for stats in run['test'].values()}) == 1
    # The winner's recorded results come from exactly the stored final rows.
    clean = clean_frame(core.read_csv(SAMPLE_BYTES))
    rows = clean.loc[run['split_indices']['final']]
    assert core.metrics(rows[core.TARGET], run['model'].predict(rows[core.FEATURES])) == run['test'][run['winner']]


def test_slide10_reloading_preserves_predictions(reloaded):
    app, original = reloaded.app, reloaded.original
    run = app.session_state['run']
    assert app.session_state['loaded'] is True
    assert (run['fingerprint'], run['winner'], run['test'], run['counts']) == \
           (original['fingerprint'], original['winner'], original['test'], original['counts'])
    clean = clean_frame(core.read_csv(SAMPLE_BYTES))
    rows = clean.loc[original['split_indices']['final'], core.FEATURES]
    assert np.array_equal(run['model'].predict(rows), original['model'].predict(rows))
    assert np.allclose(run['model'].predict_proba(rows), original['model'].predict_proba(rows))
    assert any('Active model' in c.value and original['fingerprint'][:12] in c.value for c in app.caption)
    assert any('Showing a saved run' in i.value for i in app.tabs[1].info)
    assert set(run_completion_checks(app).values()) == {'Passed'}


# ---------------------------------------------------------------------------------------------
# Try a prediction / batch scoring / saved runs on the reloaded run
# ---------------------------------------------------------------------------------------------

def test_prediction_defaults_are_not_flagged_and_match_the_saved_model(reloaded):
    tab = predict_in_app(reloaded.app)
    assert any('does not flag a failure pattern' in i.value for i in tab.info)
    score = next(m for m in tab.metric if m.label == 'Model score (uncalibrated)')
    assert float(score.value) == pytest.approx(model_score(reloaded.original, DEFAULT_READING)['score'], abs=5e-4)


@pytest.mark.parametrize('changes', [{'Rotational speed [rpm]': 1300.0, 'Torque [Nm]': 65.0},
                                     {'Torque [Nm]': 65.0, 'Tool wear [min]': 210.0}],
                         ids=['speed1300_torque65', 'torque65_toolwear210'])
def test_prediction_high_torque_is_flagged(reloaded, changes):
    tab = predict_in_app(reloaded.app, **{**DEFAULT_READING, **changes})
    assert any('flags a failure pattern' in w.value for w in tab.warning)
    expected = model_score(reloaded.original, {**DEFAULT_READING, **changes})
    assert expected['flag'] == 1
    assert float(next(m for m in tab.metric if m.label == 'Model score (uncalibrated)').value) == pytest.approx(expected['score'], abs=5e-4)
    changes_table = tab.dataframe[0].value
    assert changes_table.iloc[0]['Input'] == 'Torque [Nm]' and bool(changes_table.iloc[0]['Flag would change'])


def test_prediction_outside_training_range_warns(reloaded):
    tab = predict_in_app(reloaded.app, **{**DEFAULT_READING, 'Air temperature [K]': 310.0})
    assert any(w.value.startswith('Outside the training range: Air temperature [K].') for w in tab.warning)


def test_batch_scoring_new_readings_matches_download(reloaded):
    app = upload_batch(reloaded.app, 'new_readings.csv', NEW_READINGS_BYTES)
    tab = app.tabs[2]
    metrics = {m.label: int(m.value.replace(',', '')) for m in tab.metric if m.label in ('Rows scored', 'Flagged', 'Outside training range')}
    expected, problems = score_batch(reloaded.original, core.read_csv(NEW_READINGS_BYTES))
    scored = pd.read_csv(io.StringIO(downloaded(app, 'Download scored readings')))
    assert len(scored) == metrics['Rows scored'] == len(expected) == 29
    assert (scored['Model flag'] == 'Failure pattern').sum() == metrics['Flagged']
    assert scored['Outside training range'].notna().sum() == metrics['Outside training range']
    assert list(scored.columns[:len(expected.columns)]) == list(expected.columns)
    assert scored['Training dataset fingerprint'].eq(reloaded.original['fingerprint']).all()
    audit = pd.read_csv(io.StringIO(downloaded(app, 'Download batch audit')))
    assert audit['Data row'].tolist() == list(range(1, 32))
    assert audit['Status'].value_counts().to_dict() == {'Scored': 29, 'Skipped': 2}
    assert any(e.label == '2 rows were skipped' for e in tab.expander) and [p['Data row'] for p in problems] == [30, 31]
    # DEMO_SCRIPT section 7 reference values.
    assert (metrics['Flagged'], metrics['Outside training range']) == (4, 3)


def _batch(frame):
    return csv_bytes(frame)


NEW_FRAME = pd.read_csv(io.BytesIO(NEW_READINGS_BYTES))
BATCH_EDGES = {
    'missing column': (_batch(NEW_FRAME.drop(columns=['Torque [Nm]'])), 'error', 'Missing required columns: Torque [Nm]'),
    'more than 5000 rows': (csv_bytes(sample_frame().head(5001)), 'error', 'at most 5000 rows'),
    'not UTF-8': (NEW_READINGS_BYTES.replace(b'NR-001', b'NR-\xff01'), 'error', 'UTF-8'),
    'all rows invalid': (_batch(NEW_FRAME.assign(Type='X')), 'skipped', 31),
    'text numbers': (_batch(NEW_FRAME.astype(str).assign(**{'Torque [Nm]': lambda d: d['Torque [Nm]'].where(d.index != 2, 'forty')})), 'skipped', 3),
    'exactly 5000 rows': (csv_bytes(sample_frame().head(5000)), 'scored', 5000),
}


@pytest.mark.parametrize('case', list(BATCH_EDGES), ids=list(BATCH_EDGES))
def test_batch_scoring_edge_cases(reloaded, case):
    data, kind, expected = BATCH_EDGES[case]
    tab = upload_batch(reloaded.app, case + '.csv', data).tabs[2]
    if kind == 'error':
        assert any(expected in e.value for e in tab.error), [e.value for e in tab.error]
        assert not any(m.label == 'Rows scored' for m in tab.metric)
    elif kind == 'skipped':
        assert any(e.label == f'{expected} rows were skipped' for e in tab.expander), [e.label for e in tab.expander]
    else:
        assert next(m.value for m in tab.metric if m.label == 'Rows scored') == f'{expected:,}'


def test_completion_checks_on_reloaded_run_with_a_different_file(reloaded):
    app = choose_source(reloaded.app, 'Try a flawed sample')
    assert app.session_state['run']['fingerprint'] == reloaded.original['fingerprint']
    results = run_completion_checks(app)
    assert results['Repeat run gives the same results'] == 'Not checked'
    assert {k: v for k, v in results.items() if k != 'Repeat run gives the same results'} == \
           {k: 'Passed' for k in results if k != 'Repeat run gives the same results'}
    choose_source(app, 'Upload a CSV')
    assert run_completion_checks(app)['Repeat run gives the same results'] == 'Not checked'
    choose_source(app, 'Included sample')


def test_compare_saved_runs_lists_the_saved_run(reloaded, demo):
    table = expander(reloaded.app.tabs[1], 'Compare saved runs').dataframe[0].value
    assert len(table) == 1
    row = table.iloc[0]
    assert row['Data source'] == 'UCI AI4I generated sample' and row['Dataset'] == demo.run['fingerprint'][:12]
    assert int(row['Failures missed']) == demo.run['test'][demo.run['winner']]['Failures missed']


def test_ui_text_makes_no_probability_cause_or_forecast_claim(reloaded, demo):
    predict_in_app(reloaded.app, **{**DEFAULT_READING, 'Torque [Nm]': 65.0, 'Tool wear [min]': 210.0})
    forbidden = re.compile(r'probabilit|chance|likelihood|confidence|will fail|will break|root cause|caused by|'
                           r'time to failure|remaining useful life|days? before|hours? before', re.I)
    negation = re.compile(r"\b(not|no|never|without|cannot|doesn't|don't)\b", re.I)
    violations = []
    for text in visible_text(reloaded.app) + visible_text(demo.app):
        for sentence in re.split(r'(?<=[.!?])\s+', text):
            if forbidden.search(sentence) and not negation.search(sentence):
                violations.append(sentence)
    assert not violations, violations


# ---------------------------------------------------------------------------------------------
# Session state edge cases
# ---------------------------------------------------------------------------------------------

def test_switching_data_source_keeps_unsaved_and_reloaded_runs(model_dir, sample_run):
    app = click(new_session(), 'Check and compare models', timeout=120)
    assert app.session_state['run']
    choose_source(app, 'Try a flawed sample')
    assert app.session_state['run']
    assert app.tabs[1].metric
    assert any('active model has been kept' in i.value for i in app.info)
    core.save_run(sample_run, model_dir)
    app = click(new_session(), 'Reload saved model')
    choose_source(app, 'Try a flawed sample')
    assert app.session_state['run']['fingerprint'] == sample_run['fingerprint']
    assert any('Showing a saved run' in i.value for i in app.tabs[1].info)


def test_clear_active_model_keeps_saved_files(model_dir, sample_run):
    path = core.save_run(sample_run, model_dir)
    app = click(new_session(), 'Reload saved model')
    click(app, 'Clear active model', app.sidebar)
    assert 'run' not in app.session_state or app.session_state['run'] is None
    assert path.exists()
    assert any('Train or reload a saved model' in m.value for m in app.tabs[2].markdown)
    assert not app.tabs[1].metric


def test_repeated_saves_keep_every_run_and_select_the_newest(model_dir):
    app = click(new_session(), 'Check and compare models', timeout=120)
    for _ in range(3):
        click(app, 'Save selected model locally')
    saved = sorted(model_dir.glob('*.joblib'))
    assert len(saved) == 3
    picker = next(s for s in app.sidebar.selectbox if s.label == 'Saved local runs')
    assert picker.value == max(saved, key=lambda p: p.stat().st_mtime) and len(picker.options) == 3
    assert len(expander(app.tabs[1], 'Compare saved runs').dataframe[0].value) == 3


def test_corrupt_saved_files_do_not_break_the_app(model_dir, sample_run):
    model_dir.mkdir(parents=True)
    (model_dir / 'aaa-garbage.joblib').write_bytes(b'not a pickle')
    joblib.dump({'winner': 'not a run'}, model_dir / 'bbb-dict.joblib')
    (model_dir / 'ccc-folder.joblib').mkdir()
    good = core.save_run(sample_run, model_dir)
    app = new_session()
    table = expander(app.tabs[1], 'Compare saved runs').dataframe[0].value
    assert (table['Data source'] == 'Could not be loaded').sum() == 3
    assert (table['Data source'] == 'UCI AI4I generated sample').sum() == 1
    picker = next(s for s in app.sidebar.selectbox if s.label == 'Saved local runs')
    picker.set_value(model_dir / 'aaa-garbage.joblib').run()
    click(app, 'Reload saved model', app.sidebar)
    assert any('could not be loaded' in e.value for e in app.error)
    assert 'run' not in app.session_state or app.session_state['run'] is None
    next(s for s in app.sidebar.selectbox if s.label == 'Saved local runs').set_value(good).run()
    click(app, 'Reload saved model', app.sidebar)
    assert app.session_state['run']['fingerprint'] == sample_run['fingerprint']
    assert not any('could not be loaded' in e.value for e in app.error)


# ---------------------------------------------------------------------------------------------
# Regression tests for bugs B1-B6 in TEST_REPORT.md. They were strict xfail tests until fixed.
# ---------------------------------------------------------------------------------------------

def test_bool_labels_do_not_produce_contradictory_messages(model_dir):
    frame = sample_frame().head(600)
    frame['Machine failure'] = frame['Machine failure'].astype(bool)
    app = upload_training_file(new_session(), 'bool_labels.csv', csv_bytes(frame))
    balance = next(m.value for m in app.tabs[0].markdown if m.value.startswith('Outcome balance'))
    failures = int(re.search(r'([\d,]+) failure examples', balance).group(1).replace(',', ''))
    assert failures >= 10
    assert not any('At least 10 unique examples of each outcome' in e.value for e in app.tabs[0].error)


def test_single_repeated_example_warning_is_grammatical(demo):
    assert any(w.startswith('1 repeated example will be removed') for w in demo.flawed.warnings), demo.flawed.warnings


def test_failed_reload_explains_the_reason(model_dir, sample_run):
    run = dict(sample_run)
    run['metadata'] = {**sample_run['metadata'], 'dependencies': {**sample_run['metadata']['dependencies'], 'scikit-learn': '0.0.1'}}
    core.save_run(run, model_dir)
    app = click(new_session(), 'Reload saved model')
    assert any('scikit-learn version' in e.value for e in app.error), [e.value for e in app.error]


def test_failed_reload_without_active_model_does_not_mention_one(model_dir):
    model_dir.mkdir(parents=True)
    (model_dir / 'broken.joblib').write_bytes(b'not a pickle')
    app = click(new_session(), 'Reload saved model')
    assert app.error
    assert not any('previously active model remains selected' in e.value for e in app.error)


def test_issue_locator_is_fast_on_the_largest_allowed_file():
    frame = pd.concat([sample_frame()] * 5, ignore_index=True)
    frame.loc[49_999, 'Torque [Nm]'] = np.nan
    started = time.perf_counter()
    issues = core.data_issue_examples(frame, limit=20)
    elapsed = time.perf_counter() - started
    assert issues == [{'Data row': 50_000, 'Column': 'Torque [Nm]', 'Problem': 'Missing value. Fill in this required reading or label.'}]
    assert elapsed < 3.0, f'{elapsed:.1f} s'


BROWSER = os.environ.get('SIGNALREADY_BROWSER_TESTS') == '1'
CHROMIUM = os.environ.get('SIGNALREADY_CHROMIUM', '/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
PORT = int(os.environ.get('SIGNALREADY_TEST_PORT', '8540'))


@pytest.mark.skipif(not BROWSER, reason='Browser check is opt-in: set SIGNALREADY_BROWSER_TESTS=1 (needs Playwright and Chromium)')
def test_browser_save_right_after_training_shows_one_tab_bar(tmp_path):
    sync_api = pytest.importorskip('playwright.sync_api')
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1', PORT)) == 0:
            pytest.skip(f'port {PORT} is busy')
    env = dict(os.environ, SIGNALREADY_MODEL_DIR=str(tmp_path / 'models'))
    server = subprocess.Popen([sys.executable, '-m', 'streamlit', 'run', APP, '--server.address', '127.0.0.1',
                               '--server.port', str(PORT), '--server.headless', 'true', '--browser.gatherUsageStats', 'false'],
                              cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    idle = "() => !document.querySelector('[data-testid=\"stStatusWidget\"]')"
    try:
        with sync_api.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=CHROMIUM)
            page = browser.new_page(viewport={'width': 1400, 'height': 1000})
            for _ in range(60):
                try:
                    page.goto(f'http://127.0.0.1:{PORT}/')
                    break
                except Exception:
                    time.sleep(1)
            page.get_by_text('Is the data ready?').wait_for(timeout=60_000)
            page.get_by_role('button', name='Check and compare models').click()
            page.get_by_text('What these results mean').wait_for(timeout=120_000)
            page.wait_for_function(idle, timeout=120_000)
            page.get_by_role('button', name='Save selected model locally').click()
            page.get_by_text('Saved. This run').wait_for(timeout=60_000)
            page.wait_for_function(idle, timeout=60_000)
            time.sleep(2)
            bars = page.locator('[data-testid="stTabs"]').count()
            browser.close()
        assert bars == 1, f'{bars} tab bars on the page after saving'
    finally:
        server.terminate()
        server.wait(timeout=20)
