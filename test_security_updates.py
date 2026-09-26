"""Regression coverage for privacy controls and traceable batch exports."""
from pathlib import Path
import hashlib
import tomllib

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

import core
from exports import batch_export_tables
from inference import safe_text, score_batch

ROOT = Path(__file__).parent


@pytest.fixture(scope='module')
def run():
    return core.train(core.read_csv((ROOT / 'data/ai4i2020.csv').read_bytes()))


@pytest.mark.parametrize('value', ['=1+1', '+1', '-1', '@SUM(A1)', '\t=1', '\r=1', '\n=1', '  =1', ' \n@SUM(A1)'])
def test_formula_like_identifiers_are_literal_text(value):
    assert safe_text(value) == "'" + value
    assert safe_text('NR-001') == 'NR-001'


def test_wide_upload_is_rejected_before_dataframe_parsing():
    raw = (','.join('c' + str(i) for i in range(65)) + '\n').encode()
    with pytest.raises(ValueError, match='at most 64 columns'):
        core.read_csv(raw)


def test_batch_audit_accounts_for_every_row_without_rejected_values(run):
    raw = (ROOT / 'data/new_readings.csv').read_bytes()
    frame = core.read_csv(raw)
    frame.loc[0, 'Product ID'] = '\n=HYPERLINK("private")'
    results, problems = score_batch(run, frame)
    scored, audit = batch_export_tables(run, results, problems, hashlib.sha256(raw).hexdigest())
    assert audit['Data row'].tolist() == list(range(1, len(frame) + 1))
    assert audit['Data row'].is_unique
    assert set(audit['Status']) == {'Scored', 'Skipped'}
    assert audit.loc[audit['Status'] == 'Skipped', 'Problem'].str.len().gt(0).all()
    assert audit.loc[audit['Status'] == 'Skipped', 'Model flag'].eq('').all()
    assert 'Product ID' not in audit and 'Type' not in audit
    assert scored['Product ID'].iloc[0].startswith("'\n=")
    assert scored['Training dataset fingerprint'].eq(run['fingerprint']).all()
    assert audit['Scored file fingerprint'].eq(hashlib.sha256(raw).hexdigest()).all()
    assert 'Selected model' not in results  # export metadata does not mutate scoring results


def test_clear_session_removes_uploaded_file_and_active_results_but_keeps_saved_run(tmp_path, monkeypatch):
    monkeypatch.setenv('SIGNALREADY_MODEL_DIR', str(tmp_path))
    app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=90).run()
    app.sidebar.radio[0].set_value('Upload a CSV').run()
    uploader = next(u for u in app.file_uploader if u.label == 'Equipment readings')
    uploader.set_value(('private.csv', (ROOT / 'data/ai4i2020.csv').read_bytes(), 'text/csv')).run()
    next(b for b in app.button if b.label == 'Check and compare models').click().run()
    next(b for b in app.button if b.label == 'Save selected model locally').click().run()
    saved = next(tmp_path.glob('*.joblib'))
    original = saved.read_bytes()
    batch = next(u for u in app.file_uploader if u.label == 'Readings to score')
    batch.set_value(('batch.csv', (ROOT / 'data/new_readings.csv').read_bytes(), 'text/csv')).run()
    next(b for b in app.sidebar.button if b.label == 'Clear session data').click().run()
    assert not app.exception
    assert app.session_state.get('run') is None
    assert app.session_state.get('checks') is None
    app.sidebar.radio[0].set_value('Upload a CSV').run()
    assert next(u for u in app.file_uploader if u.label == 'Equipment readings').value is None
    assert saved.read_bytes() == original
    next(b for b in app.sidebar.button if b.label == 'Reload saved model').click().run()
    assert not app.exception
    assert next(u for u in app.file_uploader if u.label == 'Readings to score').value is None


def test_all_invalid_batch_offers_audit_without_empty_score_download(tmp_path, monkeypatch):
    monkeypatch.setenv('SIGNALREADY_MODEL_DIR', str(tmp_path))
    app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=90).run()
    next(b for b in app.button if b.label == 'Check and compare models').click().run()
    frame = core.read_csv((ROOT / 'data/new_readings.csv').read_bytes()).assign(Type='INVALID')
    next(u for u in app.file_uploader if u.label == 'Readings to score').set_value(('bad.csv', frame.to_csv(index=False).encode(), 'text/csv')).run()
    assert not app.exception
    assert any('No readings were scored' in w.value for w in app.warning)
    labels = [b.proto.label for b in app.get('download_button')]
    assert 'Download batch audit' in labels
    assert 'Download scored readings' not in labels


def test_local_privacy_configuration_is_explicit():
    config = tomllib.loads((ROOT / '.streamlit/config.toml').read_text())
    assert config['server']['address'] == '127.0.0.1'
    assert config['server']['enableCORS'] is True
    assert config['server']['enableXsrfProtection'] is True
    assert config['server']['enableStaticServing'] is False
    assert config['browser']['gatherUsageStats'] is False
    assert config['client']['showErrorDetails'] == 'none'
