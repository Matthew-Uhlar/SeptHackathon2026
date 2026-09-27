import json
import pytest
from decision_support import maintenance_scenario

@pytest.fixture
def run():
    return {'winner':'Model A', 'fingerprint':'a'*64, 'counts':{'selection':10}, 'validation':{'Model A':{'Failures found':2,'Failures missed':1,'False alarms':2,'Correct no-failure readings':5}}}

def test_legacy_export_is_json_and_preserves_unknown_time(run):
    report=maintenance_scenario(run)
    assert json.loads(json.dumps(report)) == report
    assert report['identity']['training_time_utc'] is None
    assert report['identity']['data_source'] == 'Unknown legacy source'
    assert report['comparison'][0]['Hypothetical error cost'] == 102

def test_existing_baseline_not_duplicated(run):
    run['validation']['Always no failure']={'Failures found':0,'Failures missed':3,'False alarms':0,'Correct no-failure readings':7}
    assert len(maintenance_scenario(run)['comparison']) == 2

@pytest.mark.parametrize('count',[None,True,10.0,0,-1,'10'])
def test_invalid_group_count(run,count):
    run['counts']['selection']=count
    with pytest.raises(ValueError): maintenance_scenario(run)

@pytest.mark.parametrize('stats',[None,{}, {'Failures found':2}])
def test_incomplete_confusion_counts(run,stats):
    run['validation']['Model A']=stats
    with pytest.raises(ValueError): maintenance_scenario(run)

@pytest.mark.parametrize('value',[True,-1,2.0,float('inf')])
def test_malformed_confusion_values(run,value):
    run['validation']['Model A']['Failures found']=value
    with pytest.raises(ValueError): maintenance_scenario(run)

def test_bad_baseline_rejected(run):
    run['validation']['Always no failure']=dict(run['validation']['Model A'])
    with pytest.raises(ValueError,match='baseline'): maintenance_scenario(run)
