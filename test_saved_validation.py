"""Ensure incompatible trusted-local artifacts fail before reaching the interface."""
import copy
from pathlib import Path
import joblib
import pandas as pd
import pytest
from core import train, save_run, load_run, NUMERIC

@pytest.fixture(scope='module')
def run():
    return train(pd.read_csv(Path(__file__).parent / 'data/ai4i2020.csv'))

def test_valid_local_run_loads(run, tmp_path):
    restored = load_run(save_run(run, tmp_path))
    assert restored['fingerprint'] == run['fingerprint']

@pytest.mark.parametrize('damage', ['fingerprint', 'features', 'model', 'counts', 'ranges', 'test', 'seed'])
def test_missing_required_saved_metadata_is_rejected(run, tmp_path, damage):
    broken = dict(run)
    del broken[damage]
    path = tmp_path / 'incomplete.joblib'
    joblib.dump(broken, path)
    with pytest.raises(ValueError):
        load_run(path)

def test_invalid_ranges_are_rejected(run, tmp_path):
    broken = dict(run, ranges=copy.deepcopy(run['ranges']))
    broken['ranges'][NUMERIC[0]] = [400, 200]
    path = tmp_path / 'invalid.joblib'
    joblib.dump(broken, path)
    with pytest.raises(ValueError):
        load_run(path)
