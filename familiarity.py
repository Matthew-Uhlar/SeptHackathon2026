"""Descriptive range screening of valid scored rows. Not statistical drift detection."""
import numpy as np
import pandas as pd
from core import NUMERIC

FAMILIARITY_NOTE = (
    'This compares valid scored readings with the numeric ranges seen during training. '
    'Skipped rows are excluded from every percentage. Unknown product types are skipped by the input checks. '
    'An in-range batch can still differ from training or produce wrong predictions. '
    'This is a range screening check rather than a statistical drift test or proof of safety. '
    'Review sensor units and data collection changes before relying on unfamiliar readings.')


def batch_familiarity(run, results, skipped_count=0):
    if type(skipped_count) is not int or skipped_count < 0:
        raise ValueError('Skipped row count must be a nonnegative whole number.')
    report = {'rows_scored': len(results), 'rows_skipped': skipped_count,
              'status': 'No valid readings to assess', 'inputs': [],
              'dataset_fingerprint': run['fingerprint'], 'selected_model': run['winner'],
              'training_time_utc': run.get('metadata', {}).get('trained_at_utc'),
              'limitations': FAMILIARITY_NOTE}
    if results.empty:
        return report
    rows = []
    try:
        for column in NUMERIC:
            low, high = run['ranges'][column]
            if not np.isfinite([low, high]).all() or low > high:
                raise ValueError('Training ranges are unavailable. Train a new run.')
            values = pd.to_numeric(results[column], errors='raise').to_numpy(dtype=float)
            if not np.isfinite(values).all() or (values < 0).any():
                raise ValueError('Only valid scored readings can be assessed.')
            outside = int(((values < low) | (values > high)).sum())
            # Divide before summing to avoid overflow for finite large readings.
            rows.append({'Input': column, 'Training minimum': float(low),
                         'Training maximum': float(high), 'Batch mean': float((values / len(values)).sum()),
                         'Outside training range': outside,
                         'Outside training range (%)': 100 * outside / len(values)})
    except (KeyError, TypeError) as exc:
        raise ValueError('Scored readings or training ranges are incomplete.') from exc
    report['inputs'] = rows
    report['status'] = ('Review unfamiliar readings' if any(r['Outside training range'] for r in rows)
                        else 'No numeric range exceedances found')
    return report
