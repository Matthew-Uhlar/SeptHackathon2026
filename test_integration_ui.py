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
    giveaways = [w.value for w in tab.warning if w.value.startswith('Possible answer giveaway')]
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
    checks = next(e for e in app.tabs[1].expander if e.label == 'Completion checks').dataframe[0].value
    assert len(checks) == 6
    assert set(checks['Passed']) == {'Passed'}
    app.run()
    assert next(e for e in app.tabs[1].expander if e.label == 'Completion checks').dataframe


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
