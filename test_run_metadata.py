from datetime import datetime
from pathlib import Path
import joblib
import pandas as pd
import pytest
import core

@pytest.fixture(scope='module')
def run():
    return core.train(pd.read_csv(Path(__file__).parent / 'data/ai4i2020.csv'))

def test_audit_metadata_and_exports(run):
    metadata = run['metadata']
    assert metadata['format_version'] == core.RUN_FORMAT_VERSION
    assert datetime.fromisoformat(metadata['trained_at_utc']).utcoffset().total_seconds() == 0
    assert metadata['dependencies']['scikit-learn'] == core.sklearn.__version__
    assert core.public_report(run)['metadata'] == metadata
    assert metadata['trained_at_utc'] in core.text_report(run)
    assert 'Unspecified CSV' in core.text_report(run)

def test_legacy_is_explicit_without_fabricated_date(run, tmp_path):
    legacy = {k:v for k,v in run.items() if k not in ['metadata', 'source_label']}
    restored = core.load_run(core.save_run(legacy, tmp_path))
    assert restored['metadata']['status'] == 'legacy / unknown'
    assert restored['metadata']['trained_at_utc'] is None
    assert restored['source_label'] == 'Unknown legacy source'
    assert 'Unknown for legacy run' in core.text_report(restored)

@pytest.mark.parametrize('replacement,match', [
    ({'format_version': 999}, 'unsupported format'),
    ({'format_version': 1, 'dependencies': {'scikit-learn':'0.0'}}, 'different scikit-learn'),
])
def test_incompatible_metadata_rejected(run, tmp_path, replacement, match):
    broken = dict(run, metadata=replacement)
    with pytest.raises(ValueError, match=match):
        core.load_run(core.save_run(broken, tmp_path))

def test_repeated_saves_preserve_first_file(run, tmp_path):
    first = core.save_run(run, tmp_path)
    content = first.read_bytes()
    second = core.save_run(run, tmp_path)
    assert first != second
    assert core.run_label(first) != core.run_label(second)
    assert first.read_bytes() == content
    assert core.load_run(second)['metadata'] == run['metadata']
    assert not list(tmp_path.glob('*.tmp'))

def test_failed_save_removes_partial_file(run, tmp_path, monkeypatch):
    def fail_dump(obj, path):
        Path(path).write_bytes(b'partial')
        raise OSError('Disk full')
    monkeypatch.setattr(core.joblib, 'dump', fail_dump)
    with pytest.raises(OSError, match='Disk full'):
        core.save_run(run, tmp_path)
    assert list(tmp_path.iterdir()) == []

def test_sklearn_deserialization_warning_is_rejected(tmp_path, monkeypatch):
    import warnings
    def incompatible(path):
        warnings.warn(core.InconsistentVersionWarning(estimator_name='RandomForestClassifier', current_sklearn_version='1', original_sklearn_version='0'))
    monkeypatch.setattr(core.joblib, 'load', incompatible)
    with pytest.raises(ValueError, match='different scikit-learn'):
        core.load_run(tmp_path / 'trusted.joblib')

def test_partial_legacy_metadata_normalizes(run, tmp_path):
    restored = core.load_run(core.save_run(dict(run, metadata={'format_version': 0}), tmp_path))
    assert restored['metadata'] == {'format_version': 0, 'status': 'legacy / unknown', 'trained_at_utc': None, 'dependencies': {}}

@pytest.mark.parametrize('metadata', [None, [], {}, {'format_version': 0, 'dependencies': None}, {'format_version':0, 'trained_at_utc':123}, {'format_version':0, 'dependencies': {'python':None}}])
def test_malformed_metadata_rejected(run, tmp_path, metadata):
    with pytest.raises(ValueError):
        core.load_run(core.save_run(dict(run, metadata=metadata), tmp_path))

@pytest.mark.parametrize('label', [None, 123, [], '', '  '])
def test_invalid_source_label_rejected(run, tmp_path, label):
    with pytest.raises(ValueError, match='source label'):
        core.load_run(core.save_run(dict(run, source_label=label), tmp_path))

@pytest.mark.parametrize('group,key,value', [('test','F1',1.2), ('validation','F1',-1), ('test','Failures found',1.5), ('test','False alarms',True), ('validation','Failures missed',99999), ('test','Failure detection rate',0.12345)])
def test_corrupted_metrics_rejected(run, tmp_path, group, key, value):
    import copy
    broken = dict(run)
    broken[group] = copy.deepcopy(run[group])
    broken[group][run['winner']][key] = value
    with pytest.raises(ValueError):
        core.load_run(core.save_run(broken, tmp_path))
