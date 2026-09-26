"""Traceable downloads without changing model scoring or exposing rejected values."""
import pandas as pd

from core import run_metadata
from inference import SCORE_COLUMN, safe_text


def batch_export_tables(run, results, problems, input_hash):
    """Return scored readings plus a ledger accounting for every submitted row."""
    identity = {
        'Selected model': run['winner'],
        'Training dataset fingerprint': run['fingerprint'],
        'Training time (UTC)': run_metadata(run).get('trained_at_utc') or 'Unknown (legacy run)',
        'Scored file fingerprint': input_hash,
    }
    scored = results.copy()
    records = [
        {'Data row': int(row['Data row']), 'Status': 'Scored', 'Problem': '',
         'Model flag': row['Model flag'], SCORE_COLUMN: row[SCORE_COLUMN]}
        for row in results.to_dict('records')
    ]
    records.extend({'Data row': p['Data row'], 'Status': 'Skipped', 'Problem': p['Problem'],
                    'Model flag': '', SCORE_COLUMN: None} for p in problems)
    audit = pd.DataFrame(records, columns=['Data row', 'Status', 'Problem', 'Model flag', SCORE_COLUMN])
    audit = audit.sort_values('Data row').reset_index(drop=True)
    for column, value in identity.items():
        scored[column] = safe_text(value)
        audit[column] = safe_text(value)
    return scored, audit
