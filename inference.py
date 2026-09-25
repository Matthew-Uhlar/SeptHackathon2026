"""Per-reading scores with sensitivity checks and batch scoring for a trained run.

Everything here reuses the fitted pipeline in a run created by core.train.
Scores are the model's uncalibrated internal output. They are never presented
as failure probabilities or as a forecast of when equipment will fail.
"""
import numpy as np
import pandas as pd

import core

THRESHOLD = 0.5
NEAR_MARGIN = 0.1
ID_COLUMNS = ['UDI', 'Product ID']
FLAG_LABELS = {1: 'Failure pattern', 0: 'No failure pattern'}

SCORE_NOTE = ('The model score is an uncalibrated internal score from 0 to 1. Scores above the 0.5 decision threshold '
              'are flagged. Balanced class weighting during training pushes scores upward. The score is not the chance '
              'that this equipment will fail.')

WHAT_IF_NOTE = ('Each row shows how the model score responds when one reading is replaced by its training average '
                'while the other readings stay the same. This describes model behavior. It is not a physical cause '
                'or a repair recommendation. Inputs interact so these changes do not add up to the full score.')


def _frame(row):
    """Build the one-row input frame exactly as core.predict does."""
    return pd.DataFrame([row], columns=core.FEATURES)


def _known_types(run):
    known = run.get('observed_types')
    if known is None:
        known = run['model'].named_steps['prepare'].named_transformers_['type'].categories_[0]
    return [str(t) for t in known]


def model_score(run, row):
    """Validate with core.predict then return its flag with the uncalibrated score.

    Returns {'flag': 0 or 1, 'score': float between 0 and 1, 'outside': list of input names}.
    Raises ValueError with core.predict's message for invalid readings.
    """
    flag, outside = core.predict(run, row)
    score = float(run['model'].predict_proba(_frame(row))[0, 1])
    return {'flag': int(flag), 'score': score, 'outside': list(outside)}


def score_band(score, flag):
    """Coarse wording for a score that never contradicts the model flag.

    Random forest uses argmax so a score of exactly 0.5 is not flagged. The band
    therefore follows the flag first and only uses the score for distance.
    """
    score = float(score)
    if flag and score >= THRESHOLD + NEAR_MARGIN:
        return 'Well above the 0.5 threshold'
    if not flag and score <= THRESHOLD - NEAR_MARGIN:
        return 'Well below the 0.5 threshold'
    return 'Near the 0.5 threshold'


def _training_means(run):
    scaler = run['model'].named_steps['prepare'].named_transformers_['numbers']
    return dict(zip(core.NUMERIC, (float(v) for v in scaler.mean_)))


def _format_number(value):
    return f'{float(value):g}'


def what_if(run, row):
    """Model-agnostic sensitivity for one reading.

    Replaces one input at a time with its training average (read from the fitted
    scaler so only training rows are involved) or with another product type seen
    in training. Rows are sorted by the absolute score change.
    """
    base = model_score(run, row)
    means = _training_means(run)
    variants, labels = [], []
    for column in core.NUMERIC:
        changed = dict(row)
        changed[column] = means[column]
        variants.append(changed)
        labels.append((column, _format_number(row[column]), f'training average {means[column]:.1f}'))
    for other in _known_types(run):
        if other == row['Type']:
            continue
        changed = dict(row)
        changed['Type'] = other
        variants.append(changed)
        labels.append(('Type', str(row['Type']), f'type {other}'))
    frame = pd.DataFrame(variants, columns=core.FEATURES)
    frame[core.NUMERIC] = frame[core.NUMERIC].astype(float)
    scores = run['model'].predict_proba(frame)[:, 1]
    flags = run['model'].predict(frame)
    rows = []
    for (column, current, compared), score, flag in zip(labels, scores, flags):
        rows.append({'Input': column, 'Current value': current, 'Compared with': compared,
                     'Score change': float(base['score'] - score),
                     'Flag would change': bool(int(flag) != base['flag'])})
    rows.sort(key=lambda item: abs(item['Score change']), reverse=True)
    return rows


def _row_problems(df, known_types):
    """Apply core.predict's rules to every row at once. Returns a Series of messages or None."""
    problems = pd.Series([None] * len(df), index=df.index, dtype=object)
    numbers = df[core.NUMERIC].apply(pd.to_numeric, errors='coerce').astype(float)
    types = df['Type']
    missing = df[core.FEATURES].isna().any(axis=1)
    valid_type = types.apply(lambda t: isinstance(t, str) and t in ('L', 'M', 'H'))
    bad_numbers = ~(np.isfinite(numbers) & (numbers >= 0)).all(axis=1)
    unseen = valid_type & ~types.isin(known_types)
    # Order mirrors core.predict so a row gets the same reason it would get there.
    for mask, message in [(unseen, 'This product type was absent from the training examples.'),
                          (bad_numbers, 'Every reading must be a finite nonnegative number.'),
                          (~valid_type, 'Product type must be L or M or H.'),
                          (missing, 'A required reading or product type is empty.')]:
        problems[mask] = message
    return problems, numbers


def score_batch(run, df, limit=5000):
    """Score a table of readings without failing the whole batch.

    Returns (results, problems). results has one row per valid reading. problems
    lists skipped rows as {'Data row': one-based position, 'Problem': sentence}
    without repeating the submitted values. A target column is ignored.
    """
    if type(limit) is not int or limit <= 0:
        raise ValueError('The row limit must be a positive whole number.')
    missing_columns = [c for c in core.FEATURES if c not in df]
    if missing_columns:
        raise ValueError('Missing required columns: ' + ', '.join(missing_columns))
    if len(df) > limit:
        raise ValueError(f'Please score at most {limit} rows at a time. This file has {len(df)} rows.')
    df = df.reset_index(drop=True)
    problems_by_row, numbers = _row_problems(df, _known_types(run))
    valid = problems_by_row.isna()
    problems = [{'Data row': int(i) + 1, 'Problem': problems_by_row[i]} for i in df.index[~valid]]
    ids = [c for c in ID_COLUMNS if c in df]
    columns = ['Data row'] + ids + core.FEATURES + ['Model flag', 'Model score', 'Outside training range']
    if not valid.any():
        return pd.DataFrame(columns=columns), problems
    inputs = pd.concat([df.loc[valid, ['Type']], numbers.loc[valid]], axis=1)[core.FEATURES]
    flags = run['model'].predict(inputs)
    scores = run['model'].predict_proba(inputs)[:, 1]
    outside_parts = []
    for column in core.NUMERIC:
        low, high = run['ranges'][column]
        values = inputs[column]
        outside_parts.append(np.where((values < low) | (values > high), column, ''))
    outside = [', '.join(name for name in names if name) for names in zip(*outside_parts)]
    results = pd.DataFrame({'Data row': (inputs.index + 1).astype(int)})
    for column in ids:
        results[column] = df.loc[valid, column].to_numpy()
    for column in core.FEATURES:
        results[column] = inputs[column].to_numpy()
    results['Model flag'] = [FLAG_LABELS[int(f)] for f in flags]
    results['Model score'] = np.round(scores.astype(float), 3)
    results['Outside training range'] = outside
    return results[columns].reset_index(drop=True), problems


def batch_summary(results):
    """Counts for a score_batch result table."""
    return {'Rows scored': int(len(results)),
            'Flagged': int((results['Model flag'] == FLAG_LABELS[1]).sum()) if len(results) else 0,
            'Outside training range': int((results['Outside training range'] != '').sum()) if len(results) else 0}
