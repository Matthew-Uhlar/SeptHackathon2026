"""Data checks and reproducible model training for the bounded AI4I demo."""
import hashlib
import io
import json
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

def read_csv(raw):
    if len(raw) > 10_000_000:
        raise ValueError('Please use a CSV smaller than 10 MB.')
    try:
        import csv
        header = next(csv.reader(io.StringIO(raw.decode('utf-8-sig'))))
        if len(header) != len(set(header)):
            raise ValueError('Column names repeat. Give each column a unique name.')
        return pd.read_csv(io.BytesIO(raw))
    except (UnicodeError, pd.errors.ParserError, pd.errors.EmptyDataError, StopIteration) as exc:
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
    duplicates = int(df.duplicated(subset=FEATURES + [TARGET]).sum())
    if duplicates:
        warnings.append(f'{duplicates} repeated examples will be removed before splitting the data. IDs do not make repeated readings unique.')
    unique = df.drop_duplicates(subset=FEATURES + [TARGET])
    if unique.duplicated(subset=FEATURES, keep=False).any():
        errors.append('Identical readings have conflicting failure labels. Resolve these before training.')
    counts = pd.to_numeric(unique[TARGET], errors='coerce').value_counts()
    if min(counts.get(0, 0), counts.get(1, 0)) < 10:
        errors.append('At least 10 unique examples of each outcome are required for the three data groups.')
    if ignored:
        warnings.append('Extra columns are excluded from training. Only the six approved equipment inputs are allowed.')
    return {'errors': errors, 'warnings': warnings, 'ignored': ignored, 'duplicates': duplicates}

def metrics(y, predictions):
    tn, fp, fn, tp = confusion_matrix(y, predictions, labels=[0, 1]).ravel()
    return {'Failures found': int(tp), 'Failures missed': int(fn), 'False alarms': int(fp),
            'Correct no-failure readings': int(tn), 'Failure detection rate': float(recall_score(y, predictions, zero_division=0)),
            'Warnings that were correct': float(precision_score(y, predictions, zero_division=0)),
            'F1': float(f1_score(y, predictions, zero_division=0))}

def train(df):
    report = check_data(df)
    if report['errors']:
        raise ValueError(' '.join(report['errors']))
    clean = df.drop_duplicates(subset=FEATURES + [TARGET]).copy()
    clean[NUMERIC] = clean[NUMERIC].apply(pd.to_numeric)
    clean[TARGET] = pd.to_numeric(clean[TARGET]).astype(int)
    X, y = clean[FEATURES], clean[TARGET]
    X_dev, X_test, y_dev, y_test = train_test_split(X, y, test_size=.2, stratify=y, random_state=SEED)
    X_train, X_val, y_train, y_val = train_test_split(X_dev, y_dev, test_size=.25, stratify=y_dev, random_state=SEED)
    models, validation = {}, {}
    for name, estimator in [('Logistic regression', LogisticRegression(max_iter=1500, class_weight='balanced', random_state=SEED)),
                            ('Random forest', RandomForestClassifier(n_estimators=120, max_depth=12, min_samples_leaf=2, class_weight='balanced', n_jobs=2, random_state=SEED))]:
        preprocessing = ColumnTransformer([('numbers', StandardScaler(), NUMERIC), ('type', OneHotEncoder(handle_unknown='error'), ['Type'])])
        model = Pipeline([('prepare', preprocessing), ('model', estimator)])
        model.fit(X_train, y_train)
        models[name] = model
        validation[name] = metrics(y_val, model.predict(X_val))
    winner = max(validation, key=lambda name: validation[name]['F1'])
    # Selection is locked using validation examples before any test predictions.
    final = {name: metrics(y_test, model.predict(X_test)) for name, model in models.items()}
    final['Always no failure'] = metrics(y_test, np.zeros(len(y_test), dtype=int))
    digest = hashlib.sha256(clean.to_csv(index=False).encode()).hexdigest()
    return {'model': models[winner], 'winner': winner, 'validation': validation, 'test': final,
            'counts': {'training': len(X_train), 'selection': len(X_val), 'final check': len(X_test)},
            'split_indices': {'training': X_train.index.tolist(), 'selection': X_val.index.tolist(), 'final': X_test.index.tolist()},
            'fingerprint': digest, 'features': FEATURES, 'seed': SEED,
            'ranges': {c: [float(X_train[c].min()), float(X_train[c].max())] for c in NUMERIC}}

def save_run(run, folder):
    """Write trusted locally created models only. Never load uploaded pickle files."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    filename = run['fingerprint'][:16] + '.joblib'
    target = folder / filename
    temp = target.with_suffix('.tmp')
    joblib.dump(run, temp)
    temp.replace(target)
    return target

def public_report(run):
    return {k: v for k, v in run.items() if k not in ['model', 'split_indices']}

def predict(run, row):
    values = pd.DataFrame([row], columns=FEATURES)
    if values.isna().any().any() or row['Type'] not in ['L', 'M', 'H']:
        raise ValueError('Complete every reading and choose a valid product type.')
    for c in NUMERIC:
        if not np.isfinite(float(row[c])) or float(row[c]) < 0:
            raise ValueError('Use finite nonnegative readings.')
    outside = [c for c in NUMERIC if not run['ranges'][c][0] <= float(row[c]) <= run['ranges'][c][1]]
    return int(run['model'].predict(values)[0]), outside
