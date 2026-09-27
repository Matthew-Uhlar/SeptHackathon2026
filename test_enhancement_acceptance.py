"""Independent acceptance checks for bounded competitive enhancements."""
from copy import deepcopy
import pytest
from decision_support import maintenance_scenario

@pytest.fixture
def scenario_run():
    return {'winner': 'Model A', 'fingerprint': 'a'*64,
            'counts': {'selection': 10},
            'validation': {
                'Model A': {'Failures found': 2, 'Failures missed': 1, 'False alarms': 2, 'Correct no-failure readings': 5},
                'Model B': {'Failures found': 1, 'Failures missed': 2, 'False alarms': 0, 'Correct no-failure readings': 7}},
            'test': {'must never enter scenario': object()}}

def test_cost_scenario_ignores_final_results_and_does_not_change_selection(scenario_run):
    original_validation = deepcopy(scenario_run['validation'])
    first = maintenance_scenario(scenario_run, 0, 10)
    scenario_run['test'] = None
    second = maintenance_scenario(scenario_run, 0, 10)
    assert first == second
    assert scenario_run['winner'] == 'Model A'
    assert scenario_run['validation'] == original_validation
    rows = {r['Model']: r for r in first['comparison']}
    assert rows['Model A']['Hypothetical error cost'] == 20
    assert rows['Model B']['Hypothetical error cost'] == 0
    assert rows['Always no failure']['Missed failures'] == 3
    assert rows['Model A']['Warnings to review'] == 4
    assert first['evaluation_group'] == 'selection'
    assert first['identity']['decision_threshold'] == .5

@pytest.mark.parametrize('invalid', [True, False, -1, float('nan'), float('inf'), 1000001, '100', None])
def test_cost_scenario_rejects_invalid_costs(scenario_run, invalid):
    with pytest.raises(ValueError):
        maintenance_scenario(scenario_run, invalid, 1)
    with pytest.raises(ValueError):
        maintenance_scenario(scenario_run, 1, invalid)

def test_cost_scenario_handles_zero_cost_tie(scenario_run):
    result = maintenance_scenario(scenario_run, 0, 0)
    assert all(r['Hypothetical error cost'] == 0 for r in result['comparison'])
    assert result['identity']['selected_model'] == 'Model A'

def test_cost_scenario_rejects_different_outcomes_despite_equal_row_totals(scenario_run):
    scenario_run['validation']['Model B']['Failures missed'] = 1
    scenario_run['validation']['Model B']['Correct no-failure readings'] = 8
    with pytest.raises(ValueError, match='same selection-group outcomes'):
        maintenance_scenario(scenario_run)

@pytest.fixture(scope='module')
def enhancement_ui(tmp_path_factory):
    from pathlib import Path
    import streamlit.testing.v1.app_test as module
    from streamlit.runtime.memory_media_file_storage import MemoryMediaFileStorage
    from streamlit.testing.v1 import AppTest
    downloads = {}
    class Capture(MemoryMediaFileStorage):
        def load_and_get_id(self, path_or_data, mimetype, kind, filename=None):
            key = super().load_and_get_id(path_or_data, mimetype, kind, filename)
            downloads[key] = path_or_data
            return key
    patch = pytest.MonkeyPatch()
    patch.setenv('SIGNALREADY_MODEL_DIR', str(tmp_path_factory.mktemp('enhancement-models')))
    patch.setattr(module, 'MemoryMediaFileStorage', Capture)
    app = AppTest.from_file(str(Path(__file__).parent / 'app.py'), default_timeout=90).run()
    next(b for b in app.button if b.label == 'Check and compare models').click().run(timeout=90)
    assert not app.exception
    yield app, downloads
    patch.undo()

def _download(app, downloads, label):
    button = next(b for b in app.get('download_button') if b.proto.label == label)
    value = downloads[button.proto.url.rsplit('/', 1)[-1].split('.')[0]]
    return value.decode('utf-8') if isinstance(value, bytes) else value

def test_scenario_ui_download_changes_assumptions_without_retraining(enhancement_ui):
    import json
    app, downloads = enhancement_ui
    original = app.session_state['run']
    identity = (original['fingerprint'], original['winner'], deepcopy(original['metadata']), deepcopy(original['test']))
    next(n for n in app.number_input if n.label == 'Assumed units per missed failure').set_value(0.).run()
    next(n for n in app.number_input if n.label == 'Assumed units per false alarm').set_value(123.).run()
    assert not app.exception
    report = json.loads(_download(app, downloads, 'Download trade-off scenario'))
    assert report['evaluation_group'] == 'selection'
    assert report['assumptions'] == {'units_per_missed_failure': 0., 'units_per_false_alarm': 123.}
    assert all(row['Hypothetical error cost'] == row['False alarms'] * 123 for row in report['comparison'])
    current = app.session_state['run']
    assert (current['fingerprint'], current['winner'], current['metadata'], current['test']) == identity

def test_range_screening_boundaries_denominator_and_irrelevant_columns():
    import pandas as pd
    from core import NUMERIC
    from familiarity import batch_familiarity
    run = {'ranges': {c: [10., 20.] for c in NUMERIC}, 'fingerprint': 'a'*64, 'winner': 'Model A'}
    frame = pd.DataFrame({c: [10., 20., 30.] for c in NUMERIC})
    frame['Machine failure'] = ['not used'] * 3
    before = frame.copy(deep=True)
    result = batch_familiarity(run, frame, 7)
    assert result['rows_scored'] == 3 and result['rows_skipped'] == 7
    for row in result['inputs']:
        assert row['Batch mean'] == 20.
        assert row['Outside training range'] == 1
        assert row['Outside training range (%)'] == pytest.approx(100/3)
    pd.testing.assert_frame_equal(frame, before)
    assert 'statistical drift' in result['limitations'] and 'proof of safety' in result['limitations']

def test_range_screening_empty_batch_is_unavailable():
    import pandas as pd
    from familiarity import batch_familiarity
    result = batch_familiarity({'fingerprint': 'b'*64, 'winner': 'Model B'}, pd.DataFrame(), 6)
    assert result['status'] == 'No valid readings to assess'
    assert result['inputs'] == [] and result['rows_skipped'] == 6

@pytest.mark.parametrize('bad', [float('nan'), float('inf'), -1., 'broken'])
def test_range_screening_rejects_unscored_invalid_values(bad):
    import pandas as pd
    from core import NUMERIC
    from familiarity import batch_familiarity
    run = {'ranges': {c: [0., 20.] for c in NUMERIC}, 'fingerprint': 'a'*64, 'winner': 'Model A'}
    frame = pd.DataFrame({c: [bad] for c in NUMERIC})
    with pytest.raises(ValueError):
        batch_familiarity(run, frame)

def test_review_card_download_has_identity_and_pending_review(enhancement_ui):
    from review_card import model_review_card
    app, downloads = enhancement_ui
    run = app.session_state['run']
    card = _download(app, downloads, 'Download model review card')
    assert card == model_review_card(run)
    for value in [run['fingerprint'], run['winner'], run['metadata']['trained_at_utc'], run['source_label']]:
        assert value in card
    assert 'human review required' in card
    assert 'does not certify that those checks passed' in card
    assert 'not deployment approval' in card
    assert ', and' not in card

def test_batch_familiarity_ui_export_matches_scored_rows(enhancement_ui):
    import json
    import pandas as pd
    from pathlib import Path
    from inference import score_batch
    from familiarity import batch_familiarity
    app, downloads = enhancement_ui
    raw = (Path(__file__).parent / 'data/new_readings.csv').read_bytes()
    uploader = next(u for u in app.tabs[2].file_uploader if u.label == 'Readings to score')
    uploader.set_value(('new_readings.csv', raw, 'text/csv')).run(timeout=90)
    assert not app.exception
    scored, problems = score_batch(app.session_state['run'], pd.read_csv(Path(__file__).parent / 'data/new_readings.csv'))
    expected = batch_familiarity(app.session_state['run'], scored, len(problems))
    exported = json.loads(_download(app, downloads, 'Download range screening'))
    assert exported['scored_file_sha256'] == __import__('hashlib').sha256(raw).hexdigest()
    exported.pop('scored_file_sha256')
    assert exported == expected
    assert exported['rows_scored'] == 29 and exported['rows_skipped'] == 2
    panel = next(e for e in app.tabs[2].expander if e.label == 'How familiar are these readings?')
    assert len(panel.dataframe[0].value) == 5
