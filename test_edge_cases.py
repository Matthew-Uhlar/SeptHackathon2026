"""Edge-case and UI-state tests for SignalReady, filling the gaps left by
test_core.py against the checklist in CLAUDE_HANDOFF.md's
"Testing review still needed" section.

These tests deliberately target the documented, stable contracts of
core.py (read_csv/check_data/train/predict/save_run/public_report) and
app.py's session-state rules rather than incidental implementation
details, since app.py/core.py are being actively edited elsewhere.
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest

from core import (
    FEATURES,
    NUMERIC,
    TARGET,
    check_data,
    predict,
    public_report,
    read_csv,
    save_run,
    train,
)

APP_PATH = Path(__file__).parent / 'app.py'
MODELS_DIR = APP_PATH.parent / 'models'


@pytest.fixture(scope='module')
def sample():
    return pd.read_csv(Path(__file__).parent / 'data/ai4i2020.csv')


@pytest.fixture(scope='module')
def run(sample):
    return train(sample)


# ---------------------------------------------------------------------------
# Malformed / non-UTF-8 CSV (gap: existing tests only cover duplicate headers)
# ---------------------------------------------------------------------------

def test_empty_file_rejected():
    with pytest.raises(ValueError, match='could not be read'):
        read_csv(b'')


def test_non_utf8_bytes_rejected():
    # Raw Latin-1 bytes with a high-bit byte sequence that is not valid
    # UTF-8 (or utf-8-sig), so decoding must fail before parsing.
    raw = 'Type,Air temperature [K]\n\xe9\xe8,1\n'.encode('latin-1')
    with pytest.raises(ValueError, match='could not be read'):
        read_csv(raw)


def test_malformed_csv_mismatched_columns_rejected():
    # Header declares 3 columns; data rows have 2 and 4 fields.
    raw = b'A,B,C\n1,2\n3,4,5,6\n'
    with pytest.raises(ValueError, match='could not be read'):
        read_csv(raw)


# ---------------------------------------------------------------------------
# Missing required columns (gap: multiple missing at once + full message)
# ---------------------------------------------------------------------------

def test_multiple_missing_columns_all_named(sample):
    bad = sample.drop(columns=[NUMERIC[0], NUMERIC[1], 'Type'])
    errors = check_data(bad)['errors']
    assert len(errors) == 1
    for col in [NUMERIC[0], NUMERIC[1], 'Type']:
        assert col in errors[0], f'{col} should be listed in the missing-columns message'


def test_completely_wrong_schema_reports_all_required_columns():
    wrong = pd.DataFrame({'foo': [1, 2], 'bar': [3, 4]})
    errors = check_data(wrong)['errors']
    assert len(errors) == 1
    for col in FEATURES + [TARGET]:
        assert col in errors[0]


# ---------------------------------------------------------------------------
# Empty / nonnumeric values (gap: empty string, whitespace/thousands sep,
# and missing values specifically in Type or the target column)
# ---------------------------------------------------------------------------

def test_empty_string_numeric_value_blocked(sample):
    bad = sample.copy().astype({NUMERIC[0]: object})
    bad.loc[0, NUMERIC[0]] = ''
    assert check_data(bad)['errors']


def test_thousands_separator_value_blocked(sample):
    # '1,000' is not parseable as a plain number by pd.to_numeric and must
    # be treated as a blocking error, not silently coerced.
    bad = sample.copy().astype({NUMERIC[0]: object})
    bad.loc[0, NUMERIC[0]] = '1,000'
    assert check_data(bad)['errors']


def test_missing_type_value_blocked(sample):
    bad = sample.copy().astype({'Type': object})
    bad.loc[0, 'Type'] = np.nan
    errors = check_data(bad)['errors']
    assert any('empty' in e for e in errors)
    assert any('Type must be' in e for e in errors)


def test_missing_target_value_blocked(sample):
    bad = sample.copy()
    bad.loc[0, TARGET] = np.nan
    errors = check_data(bad)['errors']
    assert any('empty' in e for e in errors)


# ---------------------------------------------------------------------------
# Invalid product Type values (gap: existing test only covers invalid target)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('value', ['X', 'l', '', '5', 'LM'])
def test_invalid_type_values_blocked(sample, value):
    bad = sample.copy().astype({'Type': object})
    bad.loc[0, 'Type'] = value
    assert any('Type must be' in e for e in check_data(bad)['errors'])


# ---------------------------------------------------------------------------
# Too few rows / too many rows / too few examples of one class (gap)
# ---------------------------------------------------------------------------

def test_too_few_rows_blocked(sample):
    tiny = sample.head(30)
    errors = check_data(tiny)['errors']
    assert any('between 50 and 50000 rows' in e for e in errors)


def test_too_many_rows_blocked(sample):
    # Build a frame just over the 50000-row ceiling by tiling the sample.
    # Exact-duplicate rows are fine here: duplicates only produce a warning,
    # the row-count check is what we're exercising.
    big = pd.concat([sample] * 100, ignore_index=True).head(50001)
    assert len(big) == 50001
    errors = check_data(big)['errors']
    assert any('between 50 and 50000 rows' in e for e in errors)


def test_too_few_examples_of_minority_class_blocked(sample):
    class0 = sample[sample[TARGET] == 0].head(60)
    class1 = sample[sample[TARGET] == 1].head(5)
    thin = pd.concat([class0, class1], ignore_index=True)
    errors = check_data(thin)['errors']
    assert any('At least 10 unique examples' in e for e in errors)


# ---------------------------------------------------------------------------
# Prediction values outside the training range (gap: below-min + multi-col)
# ---------------------------------------------------------------------------

def test_prediction_below_range_reported(run, sample):
    row = sample.iloc[0][FEATURES].to_dict()
    row[NUMERIC[0]] = run['ranges'][NUMERIC[0]][0] - 100
    outside = predict(run, row)[1]
    assert NUMERIC[0] in outside


def test_prediction_multiple_columns_out_of_range_all_flagged(run, sample):
    row = sample.iloc[0][FEATURES].to_dict()
    row[NUMERIC[0]] = run['ranges'][NUMERIC[0]][0] - 100
    row[NUMERIC[1]] = run['ranges'][NUMERIC[1]][1] + 1000
    outside = predict(run, row)[1]
    assert NUMERIC[0] in outside
    assert NUMERIC[1] in outside
    assert len(outside) == 2


# ---------------------------------------------------------------------------
# Save/reload gap: public_report works on a restored (joblib-loaded) run
# ---------------------------------------------------------------------------

def test_public_report_on_restored_run(run, tmp_path):
    restored = joblib.load(save_run(run, tmp_path))
    report = public_report(restored)
    assert 'model' not in report
    assert 'split_indices' not in report
    assert report['fingerprint'] == run['fingerprint']
    assert report['winner'] == run['winner']


# ---------------------------------------------------------------------------
# AppTest-based checks: tab state, input-after-reload, and JSON download
# ---------------------------------------------------------------------------

# The mock Runtime that AppTest installs during .run() is torn down
# (Runtime._instance = None) before .run() returns, so a download button's
# bytes must be captured through its MemoryMediaFileStorage while that
# instance is still the one in use. We patch its constructor once, at
# import time, to record every storage instance AppTest creates; the most
# recent entry always belongs to the AppTest we just ran.
import streamlit.testing.v1.app_test as _app_test_module  # noqa: E402

_captured_storages = []
_orig_storage_init = _app_test_module.MemoryMediaFileStorage.__init__


def _capturing_storage_init(self, media_endpoint):
    _orig_storage_init(self, media_endpoint)
    _captured_storages.append(self)


_app_test_module.MemoryMediaFileStorage.__init__ = _capturing_storage_init


def _get_download_button_bytes(app, label):
    """Fetch the bytes behind a rendered download_button, using the most
    recently created mock media storage (see the patch above)."""
    button = next(b for b in app.download_button if b.label == label)
    storage = _captured_storages[-1]
    filename = button.proto.url.rsplit('/', 1)[-1]
    return storage.get_file(filename).content


def _trained_app():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
    assert not app.exception
    next(b for b in app.button if b.label == 'Check and compare models').click().run(timeout=60)
    assert not app.exception
    assert 'run' in app.session_state
    return app


def test_model_comparison_tab_shows_winner_and_metrics_after_training():
    app = _trained_app()
    run_obj = app.session_state['run']
    comparison_tab = app.tabs[1]
    assert comparison_tab.subheader[0].value == 'Selected model: ' + run_obj['winner']
    expected = run_obj['test'][run_obj['winner']]
    metric_values = {m.label: m.value for m in comparison_tab.metric}
    for key in ['Failures found', 'Failures missed', 'False alarms']:
        assert metric_values[key] == str(expected[key])


def test_download_json_report_matches_public_report():
    app = _trained_app()
    run_obj = app.session_state['run']
    raw = _get_download_button_bytes(app, 'Download results report')
    payload = json.loads(raw)
    expected = public_report(run_obj)
    assert payload['fingerprint'] == expected['fingerprint']
    assert payload['winner'] == expected['winner']
    assert set(payload.keys()) == set(expected.keys())
    assert 'model' not in payload
    assert 'split_indices' not in payload


def test_reload_saved_model_restores_tab_content_without_retraining():
    app = _trained_app()
    trained_run = app.session_state['run']
    next(b for b in app.button if b.label == 'Save selected model locally').click().run(timeout=30)
    assert not app.exception
    saved_files = sorted(MODELS_DIR.glob('*.joblib'))
    assert saved_files, 'expected "Save selected model locally" to write a .joblib file'
    try:
        from streamlit.testing.v1 import AppTest

        reloaded_app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
        reload_button = next(b for b in reloaded_app.sidebar.button if b.label == 'Reload saved model')
        reload_button.click().run(timeout=30)
        assert not reloaded_app.exception
        assert reloaded_app.session_state.get('loaded') is True
        assert reloaded_app.session_state['run']['fingerprint'] == trained_run['fingerprint']
        # The comparison tab should show the reloaded run's content without
        # any retraining having happened.
        comparison_tab = reloaded_app.tabs[1]
        assert comparison_tab.subheader[0].value == 'Selected model: ' + trained_run['winner']
        assert any('saved run' in info.value for info in comparison_tab.info)
    finally:
        for f in MODELS_DIR.glob('*.joblib'):
            f.unlink(missing_ok=True)


def test_changing_data_source_after_reload_keeps_loaded_run():
    """Documents the current, intentional session-state behavior in app.py:

    ``if not st.session_state.get('loaded'): st.session_state.pop('run', None)``

    only clears ``run`` on a new input fingerprint when the current run was
    NOT loaded from a saved file. So once a saved run is reloaded
    (``loaded=True``), switching the data source (a new fingerprint) does
    NOT clear or retrain ``run`` -- the app keeps showing the previously
    loaded run's results/prediction/explanation tabs, tagged with the
    "Showing a saved run" notice, until the user explicitly retrains via
    "Check and compare models". This test exercises that interaction and
    pins down the current (non-crashing) behavior; it is not asserting this
    is bug-free UX, only that it matches the documented guard and that the
    app does not crash or silently mix data from two different sources.
    """
    app = _trained_app()
    trained_run = app.session_state['run']
    next(b for b in app.button if b.label == 'Save selected model locally').click().run(timeout=30)
    assert not app.exception
    try:
        from streamlit.testing.v1 import AppTest

        reloaded_app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
        reload_button = next(b for b in reloaded_app.sidebar.button if b.label == 'Reload saved model')
        reload_button.click().run(timeout=30)
        assert not reloaded_app.exception
        assert reloaded_app.session_state.get('loaded') is True
        hash_after_reload = reloaded_app.session_state.get('input_hash')

        # Switch the data source -- this changes the input fingerprint.
        reloaded_app.sidebar.radio[0].set_value('Try a flawed sample').run(timeout=30)
        assert not reloaded_app.exception, 'switching data source after a reload must not crash the app'

        assert reloaded_app.session_state.get('input_hash') != hash_after_reload, (
            'the input fingerprint should update to reflect the newly selected data source'
        )
        assert reloaded_app.session_state.get('loaded') is True, (
            'loaded should remain True: it is only cleared by training a new run, not by '
            'switching the data source'
        )
        assert 'run' in reloaded_app.session_state, (
            'because loaded=True, the pop("run") guard in app.py should NOT fire, so the '
            'previously reloaded run must survive the data-source change unchanged'
        )
        assert reloaded_app.session_state['run']['fingerprint'] == trained_run['fingerprint'], (
            'the displayed run should still be the reloaded one (tied to the original dataset), '
            'not a run for the newly selected data source, since no retraining happened'
        )
        # The UI should still be honest that this is a saved run, not one
        # trained on the currently selected data source.
        comparison_tab = reloaded_app.tabs[1]
        assert any('saved run' in info.value for info in comparison_tab.info)
    finally:
        for f in MODELS_DIR.glob('*.joblib'):
            f.unlink(missing_ok=True)
