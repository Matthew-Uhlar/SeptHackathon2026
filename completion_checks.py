"""Live versions of the proposal's completion checks (slide 10) and repeat runs (slide 8).

Each check returns {'Check': short name, 'Passed': True / False / None, 'Detail': plain sentence}.
Passed=None means the check could not be applied to this run. Nothing here tunes or refits
the stored model. The repeat check trains a separate throwaway run only to compare results.
Temporary saves go to a TemporaryDirectory and never into ./models.
"""
import hashlib
import itertools
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

import core
from core import FEATURES, NUMERIC, TARGET, SEED

ROOT = Path(__file__).parent
BAD_SAMPLE = ROOT / 'data' / 'bad_sample.csv'
COUNT_KEYS = ['Failures found', 'Failures missed', 'False alarms', 'Correct no-failure readings']
ANSWER_COLUMNS = ['UDI', 'Product ID', TARGET, 'TWF', 'HDF', 'PWF', 'OSF', 'RNF']


def clean_frame(df):
    """Rebuild the deduplicated frame exactly as core.train does before splitting."""
    clean = df.copy()
    clean[NUMERIC] = clean[NUMERIC].apply(pd.to_numeric)
    clean[TARGET] = pd.to_numeric(clean[TARGET]).astype(int)
    return clean.drop_duplicates(subset=FEATURES + [TARGET]).reset_index(drop=True)


def data_fingerprint(df):
    """SHA-256 of the cleaned frame computed the same way as core.train. None if the data cannot be cleaned."""
    try:
        clean = clean_frame(df)
    except (KeyError, ValueError, TypeError):
        return None
    return hashlib.sha256(clean.to_csv(index=False).encode()).hexdigest()


def _final_indices(clean):
    """Recompute core.train's final-check row positions for runs without stored indices."""
    X, y = clean[FEATURES], clean[TARGET]
    _, X_test, _, _ = train_test_split(X, y, test_size=.2, stratify=y, random_state=SEED)
    return X_test.index.tolist()


def _result(name, passed, detail):
    return {'Check': name, 'Passed': passed, 'Detail': detail}


def _guarded(name, function):
    try:
        return function(name)
    except Exception as exc:  # A broken or tampered run should produce a failed check rather than a crash.
        return _result(name, False, f'The check could not complete ({type(exc).__name__}). Train a new run.')


def check_answer_columns(run, name='Answer columns never enter training'):
    recorded = list(run.get('features') or [])
    fitted = list(getattr(run['model'], 'feature_names_in_', []))
    leaked = sorted(set(recorded + fitted) & set(ANSWER_COLUMNS))
    if recorded == FEATURES and fitted == FEATURES:
        return _result(name, True, 'The recorded inputs and the fitted model both use only the six approved equipment inputs. '
                                   'Record IDs / failure-type columns / the failure label are not model inputs.')
    if leaked:
        return _result(name, False, 'Answer or ID columns appear among the model inputs: ' + ', '.join(leaked) + '.')
    return _result(name, False, 'The recorded or fitted model inputs differ from the six approved equipment inputs.')


def check_same_final_examples(run, name='Both models use the same final examples'):
    size = run['counts']['final check']
    totals = {model: sum(int(stats[k]) for k in COUNT_KEYS) for model, stats in run['test'].items()}
    failures = {model: int(stats['Failures found']) + int(stats['Failures missed']) for model, stats in run['test'].items()}
    wrong = [model for model, total in totals.items() if total != size]
    if wrong:
        return _result(name, False, f'Results for {"; ".join(wrong)} do not add up to the {size} final-check readings.')
    if len(set(failures.values())) != 1:
        return _result(name, False, 'The models report different numbers of actual failures so they were not checked on the same readings.')
    return _result(name, True, f'Every row in the final table adds up to the same {size} readings '
                               f'with the same {next(iter(failures.values()))} actual failures.')


def check_final_separate(run, name='Final check kept separate'):
    indices = run.get('split_indices')
    if not indices:
        return _result(name, None, 'Not checked: this run does not record which rows went into each group.')
    groups = {'training': indices['training'], 'selection': indices['selection'], 'final check': indices['final']}
    sets = {group: set(rows) for group, rows in groups.items()}
    repeated = [group for group, rows in groups.items() if len(rows) != len(sets[group])]
    overlaps = [f'{a} / {b}' for a, b in itertools.combinations(sets, 2) if sets[a] & sets[b]]
    mismatched = [group for group in groups if len(groups[group]) != run['counts'][group]]
    if overlaps:
        return _result(name, False, 'Some rows appear in more than one group: ' + '; '.join(overlaps) + '.')
    if repeated:
        return _result(name, False, 'Some rows are listed twice inside one group: ' + '; '.join(repeated) + '.')
    if mismatched:
        return _result(name, False, 'Recorded group sizes do not match the stored rows for: ' + '; '.join(mismatched) + '.')
    return _result(name, True, f'Training / selection / final-check rows do not overlap. Their sizes match the recorded '
                               f'{run["counts"]["training"]} / {run["counts"]["selection"]} / {run["counts"]["final check"]} rows.')


def check_repeat(df, run, name='Repeat run gives the same results'):
    if df is None:
        return _result(name, None, 'Not checked: no data file was provided for a repeat run.')
    if data_fingerprint(df) != run['fingerprint']:
        return _result(name, None, "Not checked: the selected file differs from this run's data.")
    again = core.train(df, source_label=run.get('source_label', 'Repeat check'))
    differences = [label for label, key in [('selected model', 'winner'), ('selection results', 'validation'),
                                            ('final-check results', 'test'), ('row counts', 'counts')]
                   if again[key] != run[key]]
    if run.get('split_indices') and again['split_indices'] != run['split_indices']:
        differences.append('row groups')
    if not differences:
        clean = clean_frame(df)
        rows = clean.loc[run['split_indices']['final'] if run.get('split_indices') else _final_indices(clean), FEATURES]
        if not np.array_equal(again['model'].predict(rows), run['model'].predict(rows)):
            differences.append('final-check predictions')
    if differences:
        return _result(name, False, 'A fresh training run on the same data gave different ' + '; '.join(differences) + '.')
    return _result(name, True, f'A fresh training run on the same data picked {run["winner"]} again '
                               'with identical selection results and final-check results.')


def _grid(run):
    """Small deterministic set of readings inside the recorded training ranges."""
    types = run.get('observed_types') or ['L', 'M', 'H']
    levels = [np.linspace(run['ranges'][column][0], run['ranges'][column][1], 3) for column in NUMERIC]
    rows = [[kind, *values] for kind in types for values in itertools.product(*levels)]
    return pd.DataFrame(rows, columns=FEATURES)


def check_reload(df, run, name='Reloading preserves predictions'):
    matched = df is not None and data_fingerprint(df) == run['fingerprint']
    if matched:
        clean = clean_frame(df)
        positions = run['split_indices']['final'] if run.get('split_indices') else _final_indices(clean)
        rows, labels = clean.loc[positions, FEATURES], clean.loc[positions, TARGET]
    else:
        rows, labels = _grid(run), None
    with tempfile.TemporaryDirectory() as folder:
        try:
            loaded = core.load_run(core.save_run(run, folder))
        except ValueError as exc:
            return _result(name, False, 'The saved run could not be reloaded. ' + str(exc))
    before, after = run['model'].predict(rows), loaded['model'].predict(rows)
    if not np.array_equal(before, after):
        return _result(name, False, 'The reloaded model gave different predictions from the model that was saved.')
    if matched:
        if core.metrics(labels, after) != run['test'][run['winner']]:
            return _result(name, False, 'Predictions survived reloading but they do not reproduce the recorded final-check results. '
                                        'The stored model may not be the one that was checked.')
        return _result(name, True, f'After saving to a temporary folder and reloading the model gave identical predictions '
                                   f'on all {len(rows)} final-check readings. They reproduce the recorded final-check results.')
    return _result(name, True, f'After saving to a temporary folder and reloading the model gave identical predictions '
                               f'on {len(rows)} test readings spread across the recorded training ranges.')


def check_bad_inputs(name='Known bad inputs receive clear warnings'):
    if not BAD_SAMPLE.exists():
        return _result(name, None, 'Not checked: the flawed sample file is missing from the data folder.')
    try:
        errors = core.check_data(core.read_csv(BAD_SAMPLE.read_bytes()))['errors']
    except ValueError as exc:
        return _result(name, True, 'The flawed sample was rejected while reading: ' + str(exc))
    if not errors:
        return _result(name, False, 'The flawed sample passed the data checks without a blocking issue.')
    return _result(name, True, f'The flawed sample produced {len(errors)} blocking {"issue" if len(errors) == 1 else "issues"}. '
                               f'First: {errors[0]}')


def completion_checks(df, run, *, repeat=True):
    """Run the proposal completion checks against a trained or reloaded run.

    df is the currently selected data frame or None. repeat=False skips the retraining check.
    """
    results = [
        _guarded('Answer columns never enter training', lambda n: check_answer_columns(run, n)),
        _guarded('Both models use the same final examples', lambda n: check_same_final_examples(run, n)),
        _guarded('Final check kept separate', lambda n: check_final_separate(run, n)),
    ]
    if repeat:
        results.append(_guarded('Repeat run gives the same results', lambda n: check_repeat(df, run, n)))
    else:
        results.append(_result('Repeat run gives the same results', None, 'Not checked: the repeat run was skipped.'))
    results.append(_guarded('Reloading preserves predictions', lambda n: check_reload(df, run, n)))
    results.append(_guarded('Known bad inputs receive clear warnings', lambda n: check_bad_inputs(n)))
    return results
