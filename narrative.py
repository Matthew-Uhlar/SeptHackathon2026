"""Plain-language sentences that explain a checked SignalReady run.

Every sentence is filled from fixed templates using only the recorded run
results (run['test'] / run['validation'] / run['counts'] / run['winner']).
No language model is involved and nothing here refits or tunes a model.
"""

BASELINE = 'Always no failure'
COUNT_KEYS = ['Failures found', 'Failures missed', 'False alarms', 'Correct no-failure readings']
# Source labels set by the app for the included generated files. Anything else (uploads / legacy / unknown)
# is described as supplied data whose origin has not been verified.
GENERATED_SOURCES = ('UCI AI4I generated sample', 'Intentionally flawed demo sample')


def _n(count, singular, plural=None):
    """Return '1 failure' or '3 failures'."""
    word = singular if count == 1 else (plural or singular + 's')
    return f'{count} {word}'


def _join(items):
    """Join phrases with 'and' only between the last two and never a comma before it."""
    items = list(items)
    if len(items) <= 1:
        return ''.join(items)
    return '; '.join(items[:-1]) + ' and ' + items[-1]


def _counts(stats):
    tp, fn, fp, tn = (int(stats[k]) for k in COUNT_KEYS)
    return tp, fn, fp, tn


def _selection_sentences(run, winner):
    validation = run.get('validation') or {}
    if winner not in validation:
        return [f'{winner} was chosen on the separate selection group. The final check played no part in that choice.']
    best = validation[winner]['F1']
    others = [name for name in validation if name != winner]
    if not others:
        return [f'{winner} was chosen on the separate selection group with an F1 score of {best:.3f}. '
                'The final check played no part in that choice.']
    tied = [name for name in others if validation[name]['F1'] == best]
    if tied:
        return [f'{winner} and {_join(tied)} tied on the selection group with an F1 score of {best:.3f}. '
                f'{winner} was kept because it is listed first. The final check played no part in that choice.']
    compared = _join(f'{name} at {validation[name]["F1"]:.3f}' for name in others)
    return [f'{winner} was selected because it had the highest F1 score on the separate selection group '
            f'({best:.3f} compared with {compared}). The final check played no part in that choice.']


def _warning_sentence(winner, tp, fp, subject='It'):
    warnings = tp + fp
    if warnings == 0:
        return f'{winner} raised no warnings in the final check. That means no false alarms but also no failures found.'
    if tp == 0:
        return f'{subject} raised {_n(warnings, "warning")}. {"It was a false alarm" if warnings == 1 else "All of them were false alarms"}.'
    start = f'{subject} raised {_n(warnings, "warning")} and {_n(fp, "was a false alarm", "were false alarms") if fp else "none were false alarms"}.'
    if fp == 0:
        return start + ' Every warning was correct.'
    if warnings < 10:
        return start + f' {tp} of its {_n(warnings, "warning")} {"was" if tp == 1 else "were"} correct.'
    tenths = int(tp * 10 / warnings + 0.5)
    if tenths == 0:
        return start + ' Fewer than 1 of every 10 warnings was correct.'
    if tenths == 10:
        return start + ' Nearly every warning was correct.'
    return start + f' About {tenths} of every 10 warnings {"was" if tenths == 1 else "were"} correct.'


def _baseline_sentence(total, failures):
    if total == 0:
        return None
    accuracy = (total - failures) / total
    if failures == 0:
        return (f'A rule that always predicts no failure would be right on {accuracy:.1%} of final-check readings '
                'because this group has no failures to miss.')
    return (f'A rule that always predicts no failure would be right on {accuracy:.1%} of final-check readings '
            f'but it would find none of the {_n(failures, "actual failure")}. '
            'That is why this page reports missed failures instead of overall accuracy.')


def _tradeoff_sentences(run, winner, tp_w, fp_w):
    sentences = []
    others = [name for name in run['test'] if name not in (winner, BASELINE)]
    for other in others:
        tp_o, fn_o, fp_o, _ = _counts(run['test'][other])
        d_tp, d_fp = tp_o - tp_w, fp_o - fp_w
        if tp_o == tp_w == 0 and fn_o == 0:
            sentences.append(f'{other} raised {_n(fp_o, "false alarm")} compared with {fp_w} for {winner} in the final check.')
        elif d_tp == 0 and d_fp == 0:
            sentences.append(f'{other} found the same number of failures ({tp_o}) with the same number of false alarms ({fp_o}) in the final check.')
        elif d_tp >= 0 and d_fp <= 0:
            sentences.append(f'In the final check {other} found {_n(tp_o, "failure")} with {_n(fp_o, "false alarm")}. '
                             f'{winner} found {tp_w} with {fp_w}. So {other} did no worse on either count. '
                             f'{winner} stays selected because the choice was locked on the selection group before the final check. '
                             'Switching now would tune the model on final results.')
        elif d_tp <= 0 and d_fp >= 0:
            sentences.append(f'{winner} found at least as many failures as {other} ({tp_w} compared with {tp_o}) '
                             f'with no more false alarms ({fp_w} compared with {fp_o}) in the final check.')
        elif d_tp > 0:
            sentences.append(f'{other} found {_n(d_tp, "more failure")} ({tp_o} compared with {tp_w}) '
                             f'but raised {_n(d_fp, "more false alarm")} ({fp_o} compared with {fp_w}).')
        else:
            sentences.append(f'{other} raised {_n(-d_fp, "fewer false alarm", "fewer false alarms")} ({fp_o} compared with {fp_w}) '
                             f'but found {_n(-d_tp, "fewer failure", "fewer failures")} ({tp_o} compared with {tp_w}).')
        if (d_tp > 0 and d_fp > 0) or (d_tp < 0 and d_fp < 0):
            sentences.append('Neither model is better on both counts. The right balance depends on the cost of a missed failure compared with a false alarm.')
    return sentences


def results_summary(run):
    """Return deterministic plain-language sentences about a checked run.

    Works for runs from core.train and core.load_run including legacy runs
    without metadata or baseline rows.
    """
    winner = run['winner']
    test = run.get('test') or {}
    if winner not in test:
        return [f'{winner} was selected but this run has no final-check results to explain.']
    tp, fn, fp, tn = _counts(test[winner])
    failures, total = tp + fn, tp + fn + fp + tn
    total = int((run.get('counts') or {}).get('final check', total))

    sentences = _selection_sentences(run, winner)
    if failures == 0:
        sentences.append(f'The final check held {_n(total, "reading")} that the models never saw during training or selection. '
                         'None of them were actual failures so failure detection could not be measured.')
    else:
        sentences.append(f'The final check held {_n(total, "reading")} that the models never saw during training or selection. '
                         f'{failures} of them {"was an actual failure" if failures == 1 else "were actual failures"}.')
        sentences.append(f'{winner} found {tp} of the {_n(failures, "actual failure")} and missed {fn}.')
    sentences.append(_warning_sentence(winner, tp, fp, 'It' if failures else winner))
    baseline = _baseline_sentence(total, failures)
    if baseline:
        sentences.append(baseline)
    sentences.extend(_tradeoff_sentences(run, winner, tp, fp))
    if 0 < failures < 30:
        sentences.append(f'Caution: the final check contains only {_n(failures, "actual failure")}. '
                         'A few different readings could change these rates noticeably so treat them as rough.')
    sentences.append(_source_sentence(run))
    return sentences


def _source_sentence(run):
    if run.get('source_label') in GENERATED_SOURCES:
        origin = 'These results come from generated equipment data split into random rows. '
    else:
        origin = ('These results come from the supplied data split into random rows. '
                  'Its origin has not been verified. ')
    return (origin + 'They describe how the model sorted held-out readings. '
            'They do not forecast when a real machine will break down or prove performance on real equipment.')
