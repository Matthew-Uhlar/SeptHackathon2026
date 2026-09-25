"""Independent regression cases. Persistence and UI use temporary directories only."""
from pathlib import Path
import shutil
import joblib
import numpy as np
import pandas as pd
import pytest
from core import FEATURES, NUMERIC, TARGET, check_data, read_csv, train, predict, save_run

ROOT = Path(__file__).parent

@pytest.fixture
def small():
    df = pd.read_csv(ROOT / 'data/ai4i2020.csv')
    return pd.concat([df[df[TARGET] == 0].head(60), df[df[TARGET] == 1].head(20)], ignore_index=True)[FEATURES + [TARGET]]

def test_overwide_first_row_rejected():
    with pytest.raises(ValueError):
        read_csv(b'A,B\n1,2,3\n4,5,6\n')

def test_short_row_rejected():
    with pytest.raises(ValueError):
        read_csv(b'A,B,C\n1,2,3\n4,5\n')

def test_numeric_text_duplicate_removed(small):
    extra = small.iloc[[0]].astype(object)
    for col in NUMERIC + [TARGET]:
        extra[col] = extra[col].map(str)
    df = pd.concat([small.astype(object), extra], ignore_index=True)
    assert check_data(df)['duplicates'] == 1
    assert sum(train(df)['counts'].values()) == len(small)

def test_numeric_text_conflicting_label_rejected(small):
    extra = small.iloc[[0]].astype(object)
    for col in NUMERIC:
        extra[col] = extra[col].map(str)
    extra[TARGET] = 1 - int(extra[TARGET].iloc[0])
    df = pd.concat([small.astype(object), extra], ignore_index=True)
    assert any('conflicting' in e for e in check_data(df)['errors'])

def test_single_type_training_abstains_for_unseen_product_type(small):
    small['Type'] = 'L'
    run = train(small)
    row = small.iloc[0][FEATURES].to_dict()
    row['Type'] = 'H'
    # Supported schema types still need observed training coverage for predictions.
    with pytest.raises(ValueError, match='absent from the training'):
        predict(run, row)
    assert run['observed_types'] == ['L']

def test_rare_supported_type_does_not_crash_training(small):
    small['Type'] = 'L'
    initial = train(small)
    held_out_index = initial['split_indices']['selection'][0]
    small.loc[held_out_index, 'Type'] = 'H'
    run = train(small)
    assert sum(run['counts'].values()) == len(small)

def test_repeatable_training_and_persistence(small, tmp_path):
    first, second = train(small), train(small)
    assert first['fingerprint'] == second['fingerprint']
    assert first['split_indices'] == second['split_indices']
    assert first['winner'] == second['winner']
    assert first['test'] == second['test']
    saved = save_run(first, tmp_path / 'models')
    restored = joblib.load(saved)
    np.testing.assert_array_equal(first['model'].predict(small[FEATURES]), restored['model'].predict(small[FEATURES]))

def test_unsaved_run_cleared_on_source_change(small, tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest
    # The copied app must fall back to its own models folder.
    monkeypatch.delenv('SIGNALREADY_MODEL_DIR', raising=False)
    shutil.copyfile(ROOT / 'app.py', tmp_path / 'app.py')
    (tmp_path / 'data').mkdir()
    small.to_csv(tmp_path / 'data/ai4i2020.csv', index=False)
    flawed = small.copy()
    flawed.loc[0, NUMERIC[0]] = np.nan
    flawed.to_csv(tmp_path / 'data/bad_sample.csv', index=False)
    app = AppTest.from_file(str(tmp_path / 'app.py'), default_timeout=60).run(timeout=30)
    next(b for b in app.button if b.label == 'Check and compare models').click().run(timeout=60)
    assert not app.exception
    assert 'run' in app.session_state
    app.sidebar.radio[0].set_value('Try a flawed sample').run(timeout=30)
    assert not app.exception
    assert 'run' not in app.session_state
    assert not (tmp_path / 'models').exists()

def test_incompatible_saved_object_is_rejected_without_ui_crash(small, tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest
    # The copied app must fall back to its own models folder.
    monkeypatch.delenv('SIGNALREADY_MODEL_DIR', raising=False)
    shutil.copyfile(ROOT / 'app.py', tmp_path / 'app.py')
    (tmp_path / 'data').mkdir()
    small.to_csv(tmp_path / 'data/ai4i2020.csv', index=False)
    (tmp_path / 'models').mkdir()
    joblib.dump({'winner': 'obsolete run'}, tmp_path / 'models/obsolete.joblib')
    app = AppTest.from_file(str(tmp_path / 'app.py'), default_timeout=60).run(timeout=30)
    next(b for b in app.sidebar.button if b.label == 'Reload saved model').click().run(timeout=30)
    assert not app.exception
    assert app.error

def test_saved_invalid_source_label_cannot_crash_audit_view(small, tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest
    monkeypatch.setenv('SIGNALREADY_MODEL_DIR', str(tmp_path / 'models'))
    run = train(small)
    run['source_label'] = None
    save_run(run, tmp_path / 'models')
    app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=60).run(timeout=30)
    next(b for b in app.sidebar.button if b.label == 'Reload saved model').click().run(timeout=30)
    assert not app.exception
    assert app.error
