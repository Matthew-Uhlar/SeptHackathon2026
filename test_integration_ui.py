"""UI integration of the profiling / narrative / completion-check / inference modules."""
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).parent / 'app.py'


@pytest.fixture(scope='module')
def trained(tmp_path_factory):
    folder = tmp_path_factory.mktemp('models')
    mp = pytest.MonkeyPatch()
    mp.setenv('SIGNALREADY_MODEL_DIR', str(folder))
    app = AppTest.from_file(str(APP), default_timeout=90).run(timeout=60)
    next(b for b in app.button if b.label == 'Check and compare models').click().run(timeout=90)
    assert not app.exception
    yield app, folder
    mp.undo()


def test_data_tab_flags_giveaway_columns_and_profiles_columns(trained):
    app, _ = trained
    tab = app.tabs[0]
    giveaways = [m.value for m in tab.markdown if m.value.startswith('- Possible answer giveaway')]
    assert any('may give away the answer' in i.value for i in tab.info)
    assert {name for name in ['TWF', 'HDF', 'PWF', 'OSF'] if any(name in w for w in giveaways)} == {'TWF', 'HDF', 'PWF', 'OSF'}
    assert not any('UDI' in w or 'RNF' in w for w in giveaways)
    profile = next(e for e in tab.expander if e.label == 'Column profile').dataframe[0].value
    assert set(profile['Role']) == {'Input', 'Target', 'Excluded'}


def test_results_tab_explains_results_and_runs_completion_checks(trained):
    app, _ = trained
    tab = app.tabs[1]
    assert any(s.value == 'What these results mean' for s in tab.subheader)
    summary = next(m.value for m in tab.markdown if m.value.startswith('- '))
    assert 'Random forest' in summary or 'Logistic regression' in summary
    assert ', and' not in summary
    next(b for b in tab.button if b.label == 'Run completion checks').click().run(timeout=90)
    assert not app.exception
    checks = next(e for e in app.tabs[1].expander if e.label == 'Completion checks').table[0].value
    assert len(checks) == 6
    assert set(checks['Result']) == {'Passed'}
    app.run()
    assert next(e for e in app.tabs[1].expander if e.label == 'Completion checks').table


def test_prediction_tab_shows_uncalibrated_score_and_what_if(trained):
    app, _ = trained
    tab = app.tabs[2]
    next(b for b in tab.button if b.label == 'Check these readings').click().run(timeout=60)
    assert not app.exception
    tab = app.tabs[2]
    metric = next(m for m in tab.metric if m.label == 'Model score (uncalibrated)')
    assert 0 <= float(metric.value) <= 1
    assert any('not the chance' in c.value for c in tab.caption)
    assert any(s.value == 'How the score responds to each reading' for s in tab.subheader)
    assert not any('probability' in m.value.lower() for m in tab.markdown)


def test_saved_runs_can_be_compared(trained):
    app, folder = trained
    next(b for b in app.button if b.label == 'Save selected model locally').click().run(timeout=60)
    assert not app.exception
    assert len(list(folder.glob('*.joblib'))) == 1
    table = next(e for e in app.tabs[1].expander if e.label == 'Compare saved runs').dataframe[0].value
    assert len(table) == 1
    assert table['Data source'].iloc[0] == 'UCI AI4I generated sample'


def test_deleted_saved_run_is_reported_instead_of_silently_switching(tmp_path, monkeypatch):
    monkeypatch.setenv('SIGNALREADY_MODEL_DIR', str(tmp_path))
    app = AppTest.from_file(str(APP), default_timeout=90).run(timeout=60)
    next(b for b in app.button if b.label == 'Check and compare models').click().run(timeout=90)
    for _ in range(2):
        next(b for b in app.button if b.label == 'Save selected model locally').click().run(timeout=60)
    chosen = next(s for s in app.sidebar.selectbox if s.label == 'Saved local runs').value
    chosen.unlink()
    # AppTest would resend the stale widget value itself, so start a session that remembers the deleted file.
    fresh = AppTest.from_file(str(APP), default_timeout=90)
    fresh.session_state['saved_run_choice'] = chosen
    fresh.run(timeout=60)
    assert not fresh.exception
    assert any('no longer in the model folder' in w.value for w in fresh.sidebar.warning)
    picker = next(s for s in fresh.sidebar.selectbox if s.label == 'Saved local runs')
    assert picker.value != chosen and picker.value.exists()


def test_completion_checks_are_marked_stale_after_the_file_changes(tmp_path, monkeypatch):
    monkeypatch.setenv('SIGNALREADY_MODEL_DIR', str(tmp_path))
    app = AppTest.from_file(str(APP), default_timeout=90).run(timeout=60)
    next(b for b in app.button if b.label == 'Check and compare models').click().run(timeout=90)
    next(b for b in app.button if b.label == 'Save selected model locally').click().run(timeout=60)
    next(b for b in app.sidebar.button if b.label == 'Reload saved model').click().run(timeout=60)
    assert app.session_state['active_tab'] == '2  Model comparison'
    next(b for b in app.tabs[1].button if b.label == 'Run completion checks').click().run(timeout=90)
    assert next(e for e in app.tabs[1].expander if e.label == 'Completion checks').table
    app.sidebar.radio[0].set_value('Try a flawed sample').run(timeout=60)
    assert not app.exception
    checks = next(e for e in app.tabs[1].expander if e.label == 'Completion checks')
    assert not checks.table
    assert any('changed since the last check' in c.value for c in checks.caption)
