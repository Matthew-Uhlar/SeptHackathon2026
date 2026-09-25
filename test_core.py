from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import pytest
from core import FEATURES, NUMERIC, TARGET, check_data, read_csv, train, predict, save_run

@pytest.fixture(scope='module')
def sample():
    return pd.read_csv(Path(__file__).parent/'data/ai4i2020.csv')

@pytest.fixture(scope='module')
def run(sample):
    return train(sample)

def test_original_ready(sample):
    assert not check_data(sample)['errors']

def test_missing_column(sample):
    assert check_data(sample.drop(columns=[NUMERIC[0]]))['errors']

@pytest.mark.parametrize('value',[np.nan,np.inf,'broken',-1])
def test_invalid_readings(sample,value):
    bad=sample.copy().astype({NUMERIC[0]:object})
    bad.loc[0,NUMERIC[0]]=value
    assert check_data(bad)['errors']

def test_invalid_target(sample):
    bad=sample.copy();bad.loc[0,TARGET]=2
    assert check_data(bad)['errors']

def test_duplicates_ignore_ids(sample):
    extra=sample.iloc[[0]].copy();extra['UDI']=999999
    assert check_data(pd.concat([sample,extra],ignore_index=True))['duplicates']==1

def test_conflicting_labels_block(sample):
    extra=sample.iloc[[0]].copy();extra[TARGET]=1-extra[TARGET]
    assert any('conflicting' in e for e in check_data(pd.concat([sample,extra],ignore_index=True))['errors'])

def test_duplicate_headers_rejected():
    with pytest.raises(ValueError,match='repeat'):
        read_csv(b'A,A\n1,2')

def test_no_leakage_or_overlap(run):
    assert list(run['model'].feature_names_in_)==FEATURES
    groups=[set(x) for x in run['split_indices'].values()]
    assert all(not a.intersection(b) for i,a in enumerate(groups) for b in groups[i+1:])
    assert sum(map(len,groups))==sum(run['counts'].values())

def test_baseline_and_counts(run):
    assert run['test']['Always no failure']['Failures found']==0
    for row in run['test'].values():
        assert sum(row[k] for k in ['Failures found','Failures missed','False alarms','Correct no-failure readings'])==run['counts']['final check']

def test_saved_model_reproduces(run,sample,tmp_path):
    restored=joblib.load(save_run(run,tmp_path))
    np.testing.assert_array_equal(run['model'].predict(sample[FEATURES].head(100)),restored['model'].predict(sample[FEATURES].head(100)))

def test_out_of_range_reported(run,sample):
    row=sample.iloc[0][FEATURES].to_dict();row[NUMERIC[0]]=10000
    assert NUMERIC[0] in predict(run,row)[1]

def test_app_workflow():
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_file(str(Path(__file__).parent/'app.py')).run(timeout=30)
    assert not app.exception
    next(b for b in app.button if b.label=='Check and compare models').click().run(timeout=60)
    assert not app.exception
    assert 'run' in app.session_state
    next(b for b in app.button if b.label=='Check these readings').click().run()
    assert not app.exception
