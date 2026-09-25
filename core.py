"""Data checks and reproducible model training for the bounded AI4I demo."""
import hashlib
import io
import json
from datetime import datetime, timezone
import platform
import tempfile
import uuid
import warnings
import sklearn
from sklearn.exceptions import InconsistentVersionWarning
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC = ['Air temperature [K]', 'Process temperature [K]', 'Rotational speed [rpm]', 'Torque [Nm]', 'Tool wear [min]']
FEATURES = ['Type'] + NUMERIC
TARGET = 'Machine failure'
SEED = 42
RUN_FORMAT_VERSION = 1

def run_metadata(run):
    """Return recorded audit details without inventing facts for legacy files."""
    metadata = run.get('metadata', {'format_version': 0})
    if not isinstance(metadata, dict):
        raise ValueError('This saved run contains invalid audit details. Train a new run.')
    metadata = dict(metadata)
    version = metadata.get('format_version')
    if type(version) is not int or version not in (0, RUN_FORMAT_VERSION):
        raise ValueError('This saved run uses an unsupported format. Train a new run with the current app.')
    if version == 0:
        metadata.setdefault('trained_at_utc', None)
        metadata.setdefault('dependencies', {})
        metadata['status'] = 'legacy / unknown'
    else:
        metadata['status'] = 'recorded'
    dependencies = metadata.get('dependencies')
    if not isinstance(dependencies, dict) or any(not isinstance(k, str) or not isinstance(v, str) or not v.strip() for k, v in dependencies.items()):
        raise ValueError('This saved run contains invalid software versions. Train a new run.')
    timestamp = metadata.get('trained_at_utc')
    if timestamp is not None:
        if not isinstance(timestamp, str):
            raise ValueError('This saved run contains an invalid training date. Train a new run.')
        parsed = datetime.fromisoformat(timestamp)
        if parsed.utcoffset() is None:
            raise ValueError('This saved run is missing its training time zone. Train a new run.')
    return metadata


def _new_metadata():
    return {"format_version": RUN_FORMAT_VERSION, "status": "recorded",
            "trained_at_utc": datetime.now(timezone.utc).isoformat(),
            "dependencies": {"python": platform.python_version(), "scikit-learn": sklearn.__version__,
                             "numpy": np.__version__, "pandas": pd.__version__, "joblib": joblib.__version__}}


def read_csv(raw):
    if len(raw) > 10_000_000:
        raise ValueError('Please use a CSV smaller than 10 MB.')
    try:
        import csv
        reader = csv.reader(io.StringIO(raw.decode('utf-8-sig')), strict=True)
        header = next(reader)
        if len(header) != len(set(header)):
            raise ValueError('Column names repeat. Give each column a unique name.')
        if not header or any(not col.strip() for col in header):
            raise ValueError('Every column needs a name in the first row.')
        for line, row in enumerate(reader, start=2):
            if not row:
                continue
            if len(row) != len(header):
                raise ValueError(f'This file could not be read. Row {line} has {len(row)} fields but the header has {len(header)}. Check commas and quoted values.')
        return pd.read_csv(io.BytesIO(raw))
    except (UnicodeError, csv.Error, pd.errors.ParserError, pd.errors.EmptyDataError, StopIteration) as exc:
        raise ValueError('This file could not be read. Use a UTF-8 CSV with a header row.') from exc

def check_data(df):
    errors, warnings = [], []
    missing = [c for c in FEATURES + [TARGET] if c not in df]
    ignored = [c for c in df if c not in FEATURES + [TARGET]]
    if missing:
        return {'errors': ['Missing required columns: ' + ', '.join(missing)], 'warnings': [], 'ignored': ignored, 'duplicates': 0}
    if not 50 <= len(df) <= 50000:
        errors.append('Use between 50 and 50000 rows for this local prototype.')
    if df[FEATURES + [TARGET]].isna().any().any():
        errors.append('Some required readings or failure labels are empty. Correct them before training.')
    for col in NUMERIC + [TARGET]:
        values = pd.to_numeric(df[col], errors='coerce')
        if not np.isfinite(values).all():
            errors.append(f'{col} must contain finite numbers in every row.')
        elif col in NUMERIC and (values < 0).any():
            errors.append(f'{col} contains negative readings. Check the units and values.')
    if not df['Type'].isin(['L', 'M', 'H']).all():
        errors.append('Type must be L or M or H.')
    if not pd.to_numeric(df[TARGET], errors='coerce').isin([0, 1]).all():
        errors.append('Machine failure must be 0 for no failure or 1 for failure.')
    normalized = df[FEATURES + [TARGET]].copy()
    normalized[NUMERIC + [TARGET]] = normalized[NUMERIC + [TARGET]].apply(pd.to_numeric, errors='coerce')
    duplicates = int(normalized.duplicated(subset=FEATURES + [TARGET]).sum())
    if duplicates:
        noun = 'example' if duplicates == 1 else 'examples'
        warnings.append(f'{duplicates} repeated {noun} will be removed before splitting the data. IDs do not make repeated readings unique.')
    unique = normalized.drop_duplicates(subset=FEATURES + [TARGET])
    if unique.duplicated(subset=FEATURES, keep=False).any():
        errors.append('Identical readings have conflicting failure labels. Resolve these before training.')
    # astype(float) makes True/False labels count as 1/0 like the other checks treat them.
    counts = pd.to_numeric(unique[TARGET], errors='coerce').astype(float).value_counts()
    if min(counts.get(0, 0), counts.get(1, 0)) < 10:
        errors.append('At least 10 unique examples of each outcome are required for the three data groups.')
    if ignored:
        warnings.append('Extra columns are excluded from training. Only the six approved equipment inputs are allowed.')
    return {'errors': errors, 'warnings': warnings, 'ignored': ignored, 'duplicates': duplicates}


def data_issue_examples(df, limit=20):
    """Locate invalid values without copying readings into diagnostics.

    Data row means the one-based parsed row position rather than a physical CSV
    line number. Missing columns are explained by check_data instead.
    """
    if type(limit) is not int or limit < 0:
        raise ValueError('The example limit must be a nonnegative integer.')
    if limit == 0 or any(column not in df for column in FEATURES + [TARGET]):
        return []
    columns = FEATURES + [TARGET]
    messages = [None, 'Missing value. Fill in this required reading or label.', 'Choose L or M or H.', 'Use a finite number.',
                'Use 0 for no failure or 1 for failure.', 'Use a nonnegative reading. Check the units.']
    # One problem code per cell, vectorized so large files stay fast. The first matching rule wins.
    codes = np.zeros((len(df), len(columns)), dtype=np.int8)
    for j, column in enumerate(columns):
        missing = df[column].isna().to_numpy()
        if column == 'Type':
            code = np.where(missing, 1, np.where(df[column].isin(['L', 'M', 'H']).to_numpy(), 0, 2))
        else:
            values = pd.to_numeric(df[column], errors='coerce').astype(float).to_numpy()
            finite = np.isfinite(values)
            out_of_rule = ~np.isin(values, [0, 1]) if column == TARGET else values < 0
            code = np.where(missing, 1, np.where(~finite, 3, np.where(out_of_rule, 4 if column == TARGET else 5, 0)))
        codes[:, j] = code
    rows, cols = np.nonzero(codes)  # row-major order: parsed position then schema order
    return [{'Data row': int(r) + 1, 'Column': columns[c], 'Problem': messages[codes[r, c]]}
            for r, c in zip(rows[:limit], cols[:limit])]

def class_balance(df):
    """Count outcomes among unique normalized examples, matching what training keeps.

    Returns None when required columns are missing. Labels other than 0 or 1
    are counted separately so they are not silently treated as either outcome.
    """
    if any(column not in df for column in FEATURES + [TARGET]):
        return None
    normalized = df[FEATURES + [TARGET]].copy()
    normalized[NUMERIC + [TARGET]] = normalized[NUMERIC + [TARGET]].apply(pd.to_numeric, errors='coerce')
    labels = normalized.drop_duplicates(subset=FEATURES + [TARGET])[TARGET]
    no_failure, failure = int((labels == 0).sum()), int((labels == 1).sum())
    return {'No failure': no_failure, 'Failure': failure, 'Unusable labels': int(len(labels) - no_failure - failure)}

def metrics(y, predictions):
    tn, fp, fn, tp = confusion_matrix(y, predictions, labels=[0, 1]).ravel()
    return {'Failures found': int(tp), 'Failures missed': int(fn), 'False alarms': int(fp),
            'Correct no-failure readings': int(tn), 'Failure detection rate': float(recall_score(y, predictions, zero_division=0)),
            'Warnings that were correct': float(precision_score(y, predictions, zero_division=0)),
            'F1': float(f1_score(y, predictions, zero_division=0))}

def train(df, source_label="Unspecified CSV"):
    report = check_data(df)
    if report['errors']:
        raise ValueError(' '.join(report['errors']))
    clean = df.copy()
    clean[NUMERIC] = clean[NUMERIC].apply(pd.to_numeric)
    clean[TARGET] = pd.to_numeric(clean[TARGET]).astype(int)
    clean = clean.drop_duplicates(subset=FEATURES + [TARGET]).reset_index(drop=True)
    X, y = clean[FEATURES], clean[TARGET]
    X_dev, X_test, y_dev, y_test = train_test_split(X, y, test_size=.2, stratify=y, random_state=SEED)
    X_train, X_val, y_train, y_val = train_test_split(X_dev, y_dev, test_size=.25, stratify=y_dev, random_state=SEED)
    models, validation = {}, {}
    for name, estimator in [('Logistic regression', LogisticRegression(max_iter=1500, class_weight='balanced', random_state=SEED)),
                            ('Random forest', RandomForestClassifier(n_estimators=120, max_depth=12, min_samples_leaf=2, class_weight='balanced', n_jobs=2, random_state=SEED))]:
        preprocessing = ColumnTransformer([('numbers', StandardScaler(), NUMERIC), ('type', OneHotEncoder(categories=[['L', 'M', 'H']], handle_unknown='error'), ['Type'])])
        model = Pipeline([('prepare', preprocessing), ('model', estimator)])
        model.fit(X_train, y_train)
        models[name] = model
        validation[name] = metrics(y_val, model.predict(X_val))
    winner = max(validation, key=lambda name: validation[name]['F1'])
    # Selection is locked using validation examples before any test predictions.
    final = {name: metrics(y_test, model.predict(X_test)) for name, model in models.items()}
    final['Always no failure'] = metrics(y_test, np.zeros(len(y_test), dtype=int))
    digest = hashlib.sha256(clean.to_csv(index=False).encode()).hexdigest()
    return {'metadata': _new_metadata(), 'source_label': source_label, 'model': models[winner], 'winner': winner, 'validation': validation, 'test': final,
            'counts': {'training': len(X_train), 'selection': len(X_val), 'final check': len(X_test)},
            'split_indices': {'training': X_train.index.tolist(), 'selection': X_val.index.tolist(), 'final': X_test.index.tolist()},
            'fingerprint': digest, 'features': FEATURES, 'seed': SEED,
            'observed_types': sorted(X_train['Type'].unique().tolist()),
            'ranges': {c: [float(X_train[c].min()), float(X_train[c].max())] for c in NUMERIC}}

def save_run(run, folder):
    """Write trusted locally created models only. Never load uploaded pickle files."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    # A unique destination preserves previous saves. rename is atomic and refuses
    # replacement on Windows. The temporary file lives on the same filesystem.
    target = folder / (run['fingerprint'][:16] + '-' + uuid.uuid4().hex + '.joblib')
    with tempfile.NamedTemporaryFile(dir=folder, suffix='.tmp', delete=False) as handle:
        temp = Path(handle.name)
    try:
        joblib.dump(run, temp)
        temp.rename(target)
    finally:
        temp.unlink(missing_ok=True)
    return target


def run_label(path):
    """Readable name for a saved run in the sidebar picker."""
    path = Path(path)
    suffix = f' / {path.stem[-6:]}' if '-' in path.stem else ''
    try:
        saved = f'saved {datetime.fromtimestamp(path.stat().st_mtime):%Y-%m-%d %H:%M:%S}'
    except OSError:
        saved = 'file missing'
    return f'Run {path.stem[:8]}{suffix} | {saved}'

def public_report(run):
    report = {k: v for k, v in run.items() if k not in ['model', 'split_indices']}
    report['metadata'] = run_metadata(run)
    report.setdefault('source_label', 'Unknown legacy source')
    return report

def load_run(path):
    """Validate a trusted local artifact before it enters UI state.

    Validation detects incomplete files but does not make untrusted pickle safe.
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', InconsistentVersionWarning)
            run = joblib.load(path)
    except InconsistentVersionWarning as exc:
        raise ValueError('This saved model used a different scikit-learn version. Train a new run with the current app.') from exc
    try:
        if not isinstance(run, dict):
            raise ValueError('Invalid saved run.')
        metadata = run_metadata(run)
        version = metadata['format_version']
        if type(version) is not int or version not in (0, RUN_FORMAT_VERSION):
            raise ValueError('This saved run uses an unsupported format. Train a new run with the current app.')
        recorded_sklearn = metadata.get('dependencies', {}).get('scikit-learn')
        if recorded_sklearn is not None and recorded_sklearn != sklearn.__version__:
            raise ValueError('This saved model used a different scikit-learn version. Train a new run with the current app.')
        if version == RUN_FORMAT_VERSION:
            if not recorded_sklearn or not metadata.get('trained_at_utc'):
                raise ValueError('This saved run is missing audit details. Train a new run.')
            datetime.fromisoformat(metadata['trained_at_utc'])
        run['metadata'] = metadata
        run.setdefault('source_label', 'Unknown legacy source')
        if not isinstance(run['source_label'], str) or not run['source_label'].strip():
            raise ValueError('This saved run contains an invalid data source label. Train a new run.')
        if run['features'] != FEATURES:
            raise ValueError('Invalid saved run.')
        if not isinstance(run['fingerprint'], str) or len(run['fingerprint']) != 64:
            raise ValueError('Invalid saved run fingerprint.')
        int(run['fingerprint'], 16)
        if run['winner'] not in run['validation'] or run['winner'] not in run['test']:
            raise ValueError('Saved run is missing model results.')
        for key in ['training', 'selection', 'final check']:
            if type(run['counts'][key]) is not int or run['counts'][key] <= 0:
                raise ValueError('Saved run contains invalid row counts.')
        count_keys = ['Failures found', 'Failures missed', 'False alarms', 'Correct no-failure readings']
        for group, count_name in [('validation', 'selection'), ('test', 'final check')]:
            for stats in run[group].values():
                if any(type(stats[k]) is not int or stats[k] < 0 for k in count_keys):
                    raise ValueError('Saved run contains invalid result counts.')
                if sum(stats[k] for k in count_keys) != run['counts'][count_name]:
                    raise ValueError('Saved result counts do not match the checked rows.')
                tp, fn, fp, tn = (stats[k] for k in count_keys)
                expected_rates = {'Failure detection rate': tp / (tp + fn) if tp + fn else 0,
                                  'Warnings that were correct': tp / (tp + fp) if tp + fp else 0,
                                  'F1': 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0}
                for key, expected in expected_rates.items():
                    value = stats[key]
                    if isinstance(value, bool) or not np.isfinite(value) or not 0 <= value <= 1 or not np.isclose(value, expected, rtol=1e-7, atol=1e-10):
                        raise ValueError('Saved run contains inconsistent result rates.')
        model = run['model']
        if list(model.feature_names_in_) != FEATURES:
            raise ValueError('Saved model has different input columns.')
        for c in NUMERIC:
            low, high = run['ranges'][c]
            if not np.isfinite([low, high]).all() or low > high:
                raise ValueError('Saved run contains invalid reading ranges.')
        run['seed']
        explain(run)
    except (KeyError, TypeError, AttributeError, OverflowError) as exc:
        raise ValueError('This saved run is incomplete or incompatible. Train a new run.') from exc
    return run

def explanation_note(run):
    estimator = run['model'].named_steps['model']
    if hasattr(estimator, 'feature_importances_'):
        return 'Bars show how much each input helped the trees separate training examples. These built-in importance scores can favor inputs with more possible values. They do not measure cause or the explanation for one prediction.'
    return 'Bars show the size of each fitted coefficient without its positive or negative direction. Numeric inputs use standardized units. Product-type indicators use 0 or 1 so their scale differs. These scores do not measure cause or explain one prediction.'

def explain(run):
    """Feature importance for the selected model, computed only from training data
    that was already inside the fitted pipeline (never the final-check group).

    This describes fitted model attributes learned from training data. It does not
    show a physical cause of failure and it is not a repair recommendation.
    """
    model = run['model']
    preprocessing = model.named_steps['prepare']
    names = preprocessing.get_feature_names_out()
    estimator = model.named_steps['model']
    if hasattr(estimator, 'feature_importances_'):
        values = estimator.feature_importances_
    elif hasattr(estimator, 'coef_'):
        values = np.abs(estimator.coef_[0])
    else:
        raise ValueError('This model type does not support an explanation view.')
    order = np.argsort(values)[::-1]
    return [{'feature': str(names[i]), 'importance': float(values[i])} for i in order]

def text_report(run):
    """Plain-text results report covering the fingerprint, model choice, split sizes,
    the full metrics table and a short limitations paragraph. Kept independent of
    Streamlit so it can be tested directly."""
    winner = run['winner']
    selection_f1 = run['validation'][winner]['F1']
    lines = []
    lines.append('SignalReady results report')
    lines.append('===========================')
    lines.append('')
    metadata = run_metadata(run)
    lines.append(f'Run format: {metadata["format_version"]} ({metadata.get("status", "unknown")})')
    lines.append(f'Training completed (UTC): {metadata.get("trained_at_utc") or "Unknown for legacy run"}')
    lines.append('Software versions: ' + (json.dumps(metadata.get('dependencies', {}), sort_keys=True) if metadata.get('dependencies') else 'Unknown for legacy run'))
    lines.append(f'Data source: {run.get("source_label", "Unknown legacy source")}')
    lines.append(f'Dataset fingerprint: {run["fingerprint"]}')
    lines.append(f'Selected model: {winner}')
    lines.append(f'Selection reason: highest F1 on the separate selection group ({selection_f1:.3f}).')
    lines.append('The final check group played no part in choosing the winner.')
    lines.append('Decision threshold: 0.5. Models are not refit after selection.')
    lines.append(f'Random seed: {run["seed"]}')
    lines.append('Approved inputs: ' + '; '.join(run['features']))
    lines.append('')
    lines.append('Row counts:')
    lines.append(f'  Training: {run["counts"]["training"]}')
    lines.append(f'  Selection: {run["counts"]["selection"]}')
    lines.append(f'  Final check: {run["counts"]["final check"]}')
    lines.append('')
    lines.append('Final check metrics:')
    header = f'{"Model":<22}{"Found":>8}{"Missed":>8}{"False alarms":>14}{"Correct normal":>16}{"Detection rate":>16}{"Precision":>11}{"F1":>8}'
    lines.append(header)
    lines.append('-' * len(header))
    for name, stats in run['test'].items():
        lines.append(
            f'{name:<22}{stats["Failures found"]:>8}{stats["Failures missed"]:>8}'
            f'{stats["False alarms"]:>14}{stats["Correct no-failure readings"]:>16}{stats["Failure detection rate"]:>16.1%}'
            f'{stats["Warnings that were correct"]:>11.1%}{stats["F1"]:>8.3f}'
        )
    lines.append('Found = correctly flagged failures. Missed = failures without a warning.')
    lines.append('False alarms = warnings on no-failure readings. Correct normal = no-failure readings without a warning.')
    lines.append('Detection rate = share of failures found. Precision = share of warnings that were correct.')
    lines.append('F1 balances detection rate with precision. A zero score is used when the relevant calculation has no positive cases.')
    lines.append('')
    lines.append('Selection-group F1 scores (used to choose the model):')
    for name, stats in run['validation'].items():
        lines.append(f'  {name}: {stats["F1"]:.3f}')
    lines.append('')
    lines.append('Explanation guide: ' + explanation_note(run))
    lines.append('')
    lines.append('Limitations:')
    lines.append(
        'This is a classification demonstration rather than a live '
        'predictive maintenance system. Included samples are synthetic. Uploaded data origins '
        'are not verified. These results do not prove factory performance. Random row splits evaluate this dataset and do not '
        'validate future-time forecasting or unseen equipment. The app does not '
        'estimate warning lead time or provide calibrated failure probabilities and '
        'it does not connect to live machines. Results describe model behavior on '
        'held-out rows rather than a guarantee about real equipment.'
    )
    return '\n'.join(lines)

def predict(run, row):
    values = pd.DataFrame([row], columns=FEATURES)
    if values.isna().any().any() or row['Type'] not in ['L', 'M', 'H']:
        raise ValueError('Complete every reading and choose a valid product type.')
    for c in NUMERIC:
        if not np.isfinite(float(row[c])) or float(row[c]) < 0:
            raise ValueError('Use finite nonnegative readings.')
    known_types = run.get('observed_types', run['model'].named_steps['prepare'].named_transformers_['type'].categories_[0])
    if row['Type'] not in known_types:
        raise ValueError('This product type was absent from the training examples. Choose a represented type or train with more representative data.')
    outside = [c for c in NUMERIC if not run['ranges'][c][0] <= float(row[c]) <= run['ranges'][c][1]]
    return int(run['model'].predict(values)[0]), outside
