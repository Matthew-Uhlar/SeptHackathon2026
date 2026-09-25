"""Exercise failed reloads without obscuring the identity of an active model."""
from pathlib import Path
import joblib
from streamlit.testing.v1 import AppTest

APP = Path(__file__).parent / 'app.py'

def test_failed_reload_retains_active_identity_and_persistent_error(tmp_path, monkeypatch):
    monkeypatch.setenv('SIGNALREADY_MODEL_DIR', str(tmp_path))
    joblib.dump({'winner': 'not a compatible run'}, tmp_path / 'broken.joblib')
    app = AppTest.from_file(str(APP), default_timeout=60).run(timeout=30)
    next(b for b in app.button if b.label == 'Check and compare models').click().run(timeout=60)
    original = app.session_state['run']['fingerprint']
    assert app.session_state['run']['source_label'] == 'UCI AI4I generated sample'
    assert any('Data source: UCI AI4I generated sample' in m.value for m in app.markdown)
    next(b for b in app.sidebar.button if b.label == 'Reload saved model').click().run()
    assert not app.exception
    assert app.session_state['run']['fingerprint'] == original
    assert any('previously active model remains selected' in e.value for e in app.error)
    app.run()
    assert any('previously active model remains selected' in e.value for e in app.error)
    assert any(original[:12] in c.value and 'Active model' in c.value for c in app.caption)

def test_clear_active_model_does_not_delete_saved_files(tmp_path, monkeypatch):
    monkeypatch.setenv('SIGNALREADY_MODEL_DIR', str(tmp_path))
    sentinel = tmp_path / 'existing.joblib'
    sentinel.write_bytes(b'existing user artifact')
    app = AppTest.from_file(str(APP), default_timeout=60).run(timeout=30)
    next(b for b in app.button if b.label == 'Check and compare models').click().run(timeout=60)
    app.run()
    next(b for b in app.sidebar.button if b.label == 'Clear active model').click().run()
    assert not app.exception
    assert app.session_state.get('run') is None
    assert sentinel.read_bytes() == b'existing user artifact'
    assert not app.tabs[1].metric

def test_first_save_immediately_populates_sidebar(tmp_path, monkeypatch):
    monkeypatch.setenv('SIGNALREADY_MODEL_DIR', str(tmp_path))
    app = AppTest.from_file(str(APP), default_timeout=60).run(timeout=30)
    assert not app.sidebar.selectbox
    next(b for b in app.button if b.label == 'Check and compare models').click().run(timeout=60)
    next(b for b in app.button if b.label == 'Save selected model locally').click().run(timeout=30)
    assert not app.exception
    saved = list(tmp_path.glob('*.joblib'))
    assert len(saved) == 1
    # No extra app.run(): the Save action itself must refresh the available runs.
    picker = next(s for s in app.sidebar.selectbox if s.label == 'Saved local runs')
    assert picker.value == saved[0]
    assert any(b.label == 'Reload saved model' for b in app.sidebar.button)
    assert any('Saved' in s.value for s in app.success)

def test_second_save_selects_newest_run_and_keeps_first(tmp_path, monkeypatch):
    monkeypatch.setenv('SIGNALREADY_MODEL_DIR', str(tmp_path))
    app = AppTest.from_file(str(APP), default_timeout=60).run(timeout=30)
    next(b for b in app.button if b.label == 'Check and compare models').click().run(timeout=60)
    next(b for b in app.button if b.label == 'Save selected model locally').click().run(timeout=30)
    first = set(tmp_path.glob('*.joblib'))
    next(b for b in app.button if b.label == 'Save selected model locally').click().run(timeout=30)
    assert not app.exception
    saved = set(tmp_path.glob('*.joblib'))
    assert first < saved and len(saved) == 2
    picker = next(s for s in app.sidebar.selectbox if s.label == 'Saved local runs')
    assert picker.value == (saved - first).pop()
    assert len(picker.options) == 2

def test_training_switches_to_model_comparison_with_notice(tmp_path, monkeypatch):
    monkeypatch.setenv('SIGNALREADY_MODEL_DIR', str(tmp_path))
    app = AppTest.from_file(str(APP), default_timeout=60).run(timeout=30)
    next(b for b in app.button if b.label == 'Check and compare models').click().run(timeout=60)
    assert not app.exception
    assert app.session_state['active_tab'] == '2  Model comparison'
    assert 'switch_tab' not in app.session_state
    assert any('Comparison ready' in s.value for s in app.success)
    app.run()
    assert not any('Comparison ready' in s.value for s in app.success)
