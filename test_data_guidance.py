import numpy as np
import pandas as pd
import pytest
from core import FEATURES, NUMERIC, TARGET, data_issue_examples


def frame():
    return pd.DataFrame([['L', 300., 310., 1500., 40., 100., 0]] * 3, columns=FEATURES + [TARGET], index=[22,22,80])


def test_clean_data_and_missing_columns_need_no_cell_examples():
    assert data_issue_examples(frame()) == []
    assert data_issue_examples(frame().drop(columns=[TARGET])) == []


@pytest.mark.parametrize('column,value,phrase', [('Type','secret-invalid-type','Choose'), (TARGET,2,'0 for no failure'), (NUMERIC[0],-1,'nonnegative'), (NUMERIC[1],np.inf,'finite'), (NUMERIC[2],'secret-invalid-number','finite'), (TARGET,np.nan,'Missing')])
def test_invalid_value_location_without_private_value(column,value,phrase):
    data = frame().astype(object)
    data.iloc[1, data.columns.get_loc(column)] = value
    issues = data_issue_examples(data)
    assert len(issues) == 1
    assert issues[0]['Data row'] == 2
    assert issues[0]['Column'] == column
    assert phrase in issues[0]['Problem']
    assert 'secret' not in str(issues)


def test_cap_and_order_use_parsed_position_then_schema():
    data = frame().astype(object)
    data.loc[:,:] = None
    first = data_issue_examples(data,limit=2)
    assert [x['Column'] for x in first] == FEATURES[:2]
    assert all(x['Data row'] == 1 for x in first)
    assert len(data_issue_examples(data)) == 20
    assert data_issue_examples(data,limit=0) == []
    assert data_issue_examples(data,limit=2) == first


def test_numeric_text_is_valid():
    data = frame().astype(str)
    assert data_issue_examples(data) == []


@pytest.mark.parametrize('limit', [-1,True,1.5])
def test_invalid_limit_rejected(limit):
    with pytest.raises(ValueError):
        data_issue_examples(frame(),limit)


def test_class_balance_counts_unique_examples_like_training():
    from core import class_balance
    data = frame()
    data.loc[5] = ['M', 301., 311., 1600., 50., 120., 1]
    data.loc[6] = ['H', 302., 312., 1700., 55., 130., 'x']
    assert class_balance(data) == {'No failure': 1, 'Failure': 1, 'Unusable labels': 1}
    assert class_balance(data.astype(str)) == {'No failure': 1, 'Failure': 1, 'Unusable labels': 1}
    assert class_balance(data.drop(columns=['Type'])) is None


def test_sample_balance_matches_training_minimum_rule():
    from pathlib import Path
    from core import class_balance, read_csv
    sample = read_csv((Path(__file__).parent / 'data/ai4i2020.csv').read_bytes())
    balance = class_balance(sample)
    assert balance['Unusable labels'] == 0
    assert balance['Failure'] >= 10 and balance['No failure'] >= 10
    assert balance['Failure'] < balance['No failure']
