"""Data readiness tab shows where to correct a file and the outcome balance."""
from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = Path(__file__).parent / 'app.py'


def _app(tmp_path, monkeypatch, source):
    monkeypatch.setenv('SIGNALREADY_MODEL_DIR', str(tmp_path))
    app = AppTest.from_file(str(APP)).run(timeout=30)
    app.sidebar.radio[0].set_value(source).run(timeout=30)
    assert not app.exception
    return app


def test_flawed_sample_locates_missing_reading(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch, 'Try a flawed sample')
    tab = app.tabs[0]
    guide = next(e for e in tab.expander if e.label == 'Where to correct the file')
    table = guide.dataframe[0].value
    assert list(table.columns) == ['Data row', 'Column', 'Problem']
    assert len(table) >= 1
    assert table['Problem'].str.contains('Missing value').any()
    assert any('Outcome balance' in m.value for m in tab.markdown)
    assert next(b for b in tab.button if b.label == 'Check and compare models').disabled


def test_clean_sample_shows_balance_without_correction_table(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch, 'Included sample')
    tab = app.tabs[0]
    assert not any(e.label == 'Where to correct the file' for e in tab.expander)
    balance = next(m.value for m in tab.markdown if 'Outcome balance' in m.value)
    assert 'failure examples' in balance and 'no-failure examples' in balance
    assert not next(b for b in tab.button if b.label == 'Check and compare models').disabled
