"""Dataset profiling / answer-giveaway checks / saved-run comparison.

These helpers are independent of Streamlit so they can be tested directly.
They describe the supplied data and saved local runs. They never change what
enters training: only core.FEATURES are used as model inputs.
"""
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

import core

# Answer-giveaway rule thresholds. Kept as module constants so the UI and the
# documentation can quote the same numbers.
GIVEAWAY_AUC = 0.9            # single-column separation score (ROC AUC folded to 0.5..1)
GIVEAWAY_NONZERO_RATE = 0.95  # share of failure labels among rows where the column is nonzero
MIN_SUPPORT = 5               # minimum rows behind a nonzero or text-value pattern
MIN_CLASS_ROWS = 5            # minimum rows of each outcome before a separation score is computed
NUMERIC_SHARE = 0.95          # share of filled values that must be numbers to treat a column as numeric
TEXT_COVERAGE = 0.95          # share of filled rows that repeated text values must cover

PROFILE_COLUMNS = ['Column', 'Role', 'Missing', 'Unique values', 'Min', 'Median', 'Max']
RUN_TABLE_COLUMNS = ['Run', 'Data source', 'Trained (UTC)', 'Selected model', 'Selection F1', 'Final-check F1',
                     'Failures found', 'Failures missed', 'False alarms', 'Dataset']


def _role(name):
    if name in core.FEATURES:
        return 'Input'
    if name == core.TARGET:
        return 'Target'
    return 'Excluded'


def _as_numbers(series):
    """Finite numeric values of a series. Text and infinite values become NaN."""
    try:
        values = pd.to_numeric(series, errors='coerce')
    except (TypeError, ValueError):
        values = pd.Series(np.nan, index=series.index)
    values = values.astype(float)
    return values.where(np.isfinite(values))


def _is_numeric(series, numbers):
    """A column is numeric when most filled values convert to finite numbers."""
    filled = int(series.notna().sum())
    return filled > 0 and numbers.notna().sum() >= NUMERIC_SHARE * filled


def _unique_count(series):
    try:
        return int(series.nunique(dropna=True))
    except TypeError:
        return int(series.astype(str).where(series.notna()).nunique(dropna=True))


def profile_columns(df):
    """One summary row per column. Only counts and numeric summaries are reported.

    Min / Median / Max come from the values that convert to finite numbers and are
    None for text columns. Raw text values are never copied into the profile.
    """
    rows = []
    for position, name in enumerate(df.columns):
        series = df.iloc[:, position]
        numbers = _as_numbers(series)
        numeric = _is_numeric(series, numbers)
        valid = numbers.dropna()
        rows.append({'Column': str(name), 'Role': _role(name), 'Missing': int(series.isna().sum()),
                     'Unique values': _unique_count(series),
                     'Min': float(valid.min()) if numeric and len(valid) else None,
                     'Median': float(valid.median()) if numeric and len(valid) else None,
                     'Max': float(valid.max()) if numeric and len(valid) else None})
    profile = pd.DataFrame(rows, columns=PROFILE_COLUMNS)
    for column in ['Min', 'Median', 'Max']:  # keep None for text columns instead of NaN
        profile[column] = pd.Series([row[column] for row in rows], index=profile.index, dtype=object)
    return profile.astype({'Missing': int, 'Unique values': int})


def _share(value):
    return f'{value:.0%}'


def _numeric_evidence(values, y):
    """Return (strength, sentence) for a numeric excluded column or None."""
    findings = []
    if min(int((y == 0).sum()), int((y == 1).sum())) >= MIN_CLASS_ROWS:
        auc = float(roc_auc_score(y, values))
        auc = max(auc, 1 - auc)
        if auc >= GIVEAWAY_AUC:
            findings.append((auc, f'On its own it separates failure labels from no-failure labels with a score of {auc:.2f} '
                                  f'where 0.5 means no separation and 1.0 means perfect separation.'))
    nonzero = values != 0
    support = int(nonzero.sum())
    if MIN_SUPPORT <= support <= 0.5 * len(values):
        rate = float(y[nonzero].mean())
        if rate >= GIVEAWAY_NONZERO_RATE:
            findings.append((rate, f'In the {support:,} labeled rows where it is not zero, {_share(rate)} are labeled as failures.'))
    if not findings:
        return None
    return max(strength for strength, _ in findings), ' '.join(sentence for _, sentence in findings)


def _text_evidence(values, y):
    """Flag text whose repeated values each match a single outcome. Unique IDs never qualify."""
    text = values.astype(str).str.strip()
    counts = text.value_counts()
    repeated = counts[counts >= MIN_SUPPORT].index
    if len(repeated) < 2:
        return None
    covered = text.isin(repeated)
    if covered.sum() < TEXT_COVERAGE * len(text):
        return None
    purity = y[covered].groupby(text[covered]).agg(['min', 'max'])
    if (purity['min'] != purity['max']).any() or y[covered].nunique() < 2:
        return None
    return 1.0, (f'Each of its {len(repeated)} repeated text values appears only with failure labels or only with '
                 f'no-failure labels. These cover {_share(covered.mean())} of labeled rows.')


def answer_giveaway_columns(df):
    """Excluded columns whose values agree with the failure label strongly enough to give it away.

    Rule (deterministic and applied only to rows where the target is 0 or 1):
    - Numeric column (at least 95% of filled values are finite numbers). Flag when
      its folded single-column ROC AUC is at least 0.9 (needs 5 rows of each outcome)
      or when at least 95% of the rows where it is nonzero are failures (needs at least
      5 nonzero rows that make up no more than half of the labeled rows).
    - Text column. Flag when at least two values each appear in 5 or more rows / those
      values cover at least 95% of filled rows / each value appears with only one outcome
      and both outcomes occur. Unique IDs never qualify.
    Returns [{'Column', 'Evidence', 'Strength'}] sorted by strength (strongest first).
    """
    if core.TARGET not in df.columns or list(df.columns).count(core.TARGET) != 1:
        return []
    target = _as_numbers(df[core.TARGET])
    labeled = target.isin([0, 1])
    if labeled.sum() == 0 or target[labeled].nunique() < 2:
        return []
    allowed = set(core.FEATURES + [core.TARGET])
    flagged = []
    for position, name in enumerate(df.columns):
        if name in allowed:
            continue
        series = df.iloc[:, position][labeled]
        numbers = _as_numbers(series)
        if _is_numeric(series, numbers):
            usable = numbers.notna()
            result = _numeric_evidence(numbers[usable], target[labeled][usable].astype(int)) if usable.any() else None
        else:
            filled = series.notna()
            result = _text_evidence(series[filled], target[labeled][filled].astype(int)) if filled.any() else None
        if result:
            strength, detail = result
            flagged.append({'Column': str(name), 'Strength': round(float(strength), 4),
                            'Evidence': f'{name} is already excluded from training. {detail} Such strong agreement with the '
                                        'failure label suggests this column records the answer rather than a reading taken '
                                        'beforehand. This is a pattern in the file rather than proof of a cause.'})
    return sorted(flagged, key=lambda item: (-item['Strength'], item['Column']))


def _trained_sort_key(value):
    try:
        return datetime.fromisoformat(value).timestamp() if value else None
    except (TypeError, ValueError):
        return None


def saved_run_table(folder):
    """Compare trusted local saved runs (*.joblib in folder). Newest training time first.

    Files that fail validation or cannot be read are listed as 'Could not be loaded'
    instead of stopping the table. Only load app-produced files: pickle is not safe
    for untrusted uploads.
    """
    folder = Path(folder)
    paths = sorted(folder.glob('*.joblib')) if folder.is_dir() else []
    rows = []
    for path in paths:
        try:
            label = core.run_label(path)
        except OSError:
            label = path.name
        try:
            run = core.load_run(path)
        except Exception:  # corrupt pickles raise EOFError / UnpicklingError and similar
            rows.append(({'Run': label, 'Data source': 'Could not be loaded'}, None))
            continue
        winner = run['winner']
        final = run['test'][winner]
        trained = run['metadata'].get('trained_at_utc')
        key = _trained_sort_key(trained)
        shown = datetime.fromisoformat(trained).strftime('%Y-%m-%d %H:%M:%S') if key is not None else 'Unknown (legacy run)'
        rows.append(({'Run': label, 'Data source': run.get('source_label', 'Unknown legacy source'), 'Trained (UTC)': shown,
                      'Selected model': winner, 'Selection F1': round(float(run['validation'][winner]['F1']), 3),
                      'Final-check F1': round(float(final['F1']), 3), 'Failures found': final['Failures found'],
                      'Failures missed': final['Failures missed'], 'False alarms': final['False alarms'],
                      'Dataset': run['fingerprint'][:12]}, key))
    known = sorted((item for item in rows if item[1] is not None), key=lambda item: -item[1])
    unknown = [item for item in rows if item[1] is None]
    return pd.DataFrame([row for row, _ in known + unknown], columns=RUN_TABLE_COLUMNS)
