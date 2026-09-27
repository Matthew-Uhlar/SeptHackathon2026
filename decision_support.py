"""Hypothetical error costs on the model-selection group only."""
import math

MAX_COST = 1_000_000.0
SCENARIO_NOTE = ('This is a hypothetical error-cost comparison using the selection group. '
                 'Defaults are illustrative cost units rather than measured costs or real savings. '
                 'It excludes inspection costs for correct warnings plus downtime and intervention costs. '
                 'Warning workload counts flagged readings rather than unique machines or staff hours. '
                 'The selected model and its 0.5 decision threshold do not change.')


def maintenance_scenario(run, missed_failure_cost=100.0, false_alarm_cost=1.0):
    costs = []
    for value in (missed_failure_cost, false_alarm_cost):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= MAX_COST:
            raise ValueError('Use a finite cost from 0 to 1000000 units.')
        costs.append(float(value))
    missed_cost, alarm_cost = costs
    if not isinstance(run, dict):
        raise ValueError('Selection-group results are unavailable. Train a new run.')
    validation = run.get('validation')
    counts = run.get('counts')
    count = counts.get('selection') if isinstance(counts, dict) else None
    if not isinstance(validation, dict) or not validation or type(count) is not int or count <= 0:
        raise ValueError('Selection-group results are unavailable. Train a new run.')
    if run.get('winner') not in validation or run.get('winner') == 'Always no failure':
        raise ValueError('The selected model is missing from the selection results. Train a new run.')
    rows = []
    failures = None
    for name, stats in validation.items():
        keys = ('Failures found', 'Failures missed', 'False alarms', 'Correct no-failure readings')
        if not isinstance(name, str) or not isinstance(stats, dict) or any(k not in stats for k in keys):
            raise ValueError('Selection-group counts are incomplete or inconsistent. Train a new run.')
        tp, fn, fp, tn = (stats[k] for k in keys)
        if any(type(n) is not int or n < 0 for n in (tp, fn, fp, tn)) or tp + fn + fp + tn != count:
            raise ValueError('Selection-group counts are incomplete or inconsistent. Train a new run.')
        if failures is not None and failures != tp + fn:
            raise ValueError('Models must use the same selection-group outcomes.')
        failures = tp + fn
        if name == 'Always no failure':
            if tp != 0 or fp != 0:
                raise ValueError('The no-failure baseline contains warnings. Train a new run.')
            continue
        rows.append({'Model': name, 'Missed failures': fn, 'False alarms': fp,
                     'Warnings to review': tp + fp, 'Hypothetical error cost': fn * missed_cost + fp * alarm_cost})
    if failures is None or type(count) is not int or count <= 0:
        raise ValueError('Selection-group results are unavailable. Train a new run.')
    rows.append({'Model': 'Always no failure', 'Missed failures': failures, 'False alarms': 0,
                 'Warnings to review': 0, 'Hypothetical error cost': failures * missed_cost})
    return {'scenario_format': 1, 'evaluation_group': 'selection', 'rows_evaluated': count,
            'identity': {'dataset_fingerprint': run['fingerprint'],
                         'training_time_utc': (run.get('metadata') or {}).get('trained_at_utc'),
                         'data_source': run.get('source_label', 'Unknown legacy source'),
                         'selected_model': run['winner'], 'decision_threshold': 0.5},
            'assumptions': {'units_per_missed_failure': missed_cost, 'units_per_false_alarm': alarm_cost},
            'comparison': rows, 'limitations': SCENARIO_NOTE}
