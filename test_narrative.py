import copy
import re
from pathlib import Path

import pytest

import core
from narrative import results_summary
from make_results_summary import build_summary

ROOT = Path(__file__).parent


@pytest.fixture(scope='module')
def run():
    df = core.read_csv((ROOT / 'data/ai4i2020.csv').read_bytes())
    return core.train(df, source_label='UCI AI4I generated sample')


def stats(tp, fn, fp, tn):
    return {'Failures found': tp, 'Failures missed': fn, 'False alarms': fp, 'Correct no-failure readings': tn,
            'Failure detection rate': tp / (tp + fn) if tp + fn else 0.0,
            'Warnings that were correct': tp / (tp + fp) if tp + fp else 0.0,
            'F1': 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0}


def synthetic(winner_counts, other_counts, val_f1=(0.6, 0.4), baseline=True):
    total = sum(winner_counts)
    failures = winner_counts[0] + winner_counts[1]
    test = {'Random forest': stats(*winner_counts), 'Logistic regression': stats(*other_counts)}
    if baseline:
        test['Always no failure'] = stats(0, failures, 0, total - failures)
    validation = {'Random forest': dict(stats(1, 1, 1, 1), F1=val_f1[0]),
                  'Logistic regression': dict(stats(1, 1, 1, 1), F1=val_f1[1])}
    return {'winner': 'Random forest', 'validation': validation, 'test': test,
            'counts': {'training': 3 * total, 'selection': total, 'final check': total}}


def assert_style(sentences):
    assert sentences and all(isinstance(s, str) and s.strip() for s in sentences)
    text = ' '.join(sentences)
    assert ', and' not in text
    for banned in ['probability', 'caused by', 'will fail', 'time to failure', 'guarantee']:
        assert banned not in text.lower()


def test_numbers_match_final_check(run):
    sentences = results_summary(run)
    assert_style(sentences)
    text = ' '.join(sentences)
    winner = run['winner']
    s = run['test'][winner]
    tp, fn, fp = s['Failures found'], s['Failures missed'], s['False alarms']
    failures, total = tp + fn, run['counts']['final check']
    assert f'{winner} found {tp} of the {failures} actual failures and missed {fn}.' in text
    assert f'It raised {tp + fp} warnings and {fp} were false alarms.' in text
    assert f'held {total} readings' in text
    tenths = int(tp * 10 / (tp + fp) + 0.5)
    assert f'About {tenths} of every 10 warnings' in text
    base = run['test']['Always no failure']
    accuracy = base['Correct no-failure readings'] / total
    assert f'{accuracy:.1%}' in text and 'find none of the' in text
    assert 'selection group' in sentences[0] and 'final check played no part' in sentences[0]
    assert 'generated equipment data' in sentences[-1] and 'do not forecast' in sentences[-1]


def test_tradeoff_mentions_other_model(run):
    text = ' '.join(results_summary(run))
    other = next(n for n in run['test'] if n not in (run['winner'], 'Always no failure'))
    w, o = run['test'][run['winner']], run['test'][other]
    assert other in text
    assert str(o['Failures found']) in text and str(o['False alarms']) in text
    if (o['Failures found'] - w['Failures found']) * (o['False alarms'] - w['False alarms']) > 0:
        assert 'Neither model is better on both counts.' in text


def test_deterministic_and_loaded_run_matches(run, tmp_path):
    loaded = core.load_run(core.save_run(run, tmp_path))
    assert results_summary(run) == results_summary(copy.deepcopy(run)) == results_summary(loaded)


def test_zero_warnings():
    sentences = results_summary(synthetic((0, 40, 0, 160), (10, 30, 5, 155)))
    assert_style(sentences)
    text = ' '.join(sentences)
    assert 'raised no warnings' in text and 'found 0 of the 40 actual failures and missed 40' in text


def test_zero_failures_and_no_baseline_row():
    sentences = results_summary(synthetic((0, 0, 3, 197), (0, 0, 7, 193), baseline=False))
    assert_style(sentences)
    text = ' '.join(sentences)
    assert 'None of them were actual failures' in text and 'could not be measured' in text
    assert '100.0%' in text
    assert 'Caution' not in text
    assert 'Random forest raised 3 warnings. All of them were false alarms.' in text


def test_small_failure_count_caution_and_few_warnings():
    sentences = results_summary(synthetic((5, 3, 2, 190), (6, 2, 9, 183)))
    assert_style(sentences)
    text = ' '.join(sentences)
    assert 'only 8 actual failures' in text
    assert '5 of its 7 warnings were correct.' in text


def test_no_caution_at_thirty_failures():
    text = ' '.join(results_summary(synthetic((20, 10, 10, 160), (25, 5, 30, 140))))
    assert 'Caution' not in text


def test_selection_tie():
    text = ' '.join(results_summary(synthetic((30, 10, 10, 150), (30, 10, 10, 150), val_f1=(0.5, 0.5))))
    assert 'tied on the selection group' in text and 'listed first' in text
    assert 'same number of failures (30) with the same number of false alarms (10)' in text


def test_other_model_better_on_final_check_is_reported_honestly():
    text = ' '.join(results_summary(synthetic((30, 10, 20, 140), (35, 5, 10, 150))))
    assert 'did no worse on either count' in text and 'locked on the selection group' in text


def test_winner_dominates():
    text = ' '.join(results_summary(synthetic((35, 5, 10, 150), (30, 10, 20, 140))))
    assert 'found at least as many failures as Logistic regression (35 compared with 30)' in text


def test_fewer_false_alarms_fewer_found():
    text = ' '.join(results_summary(synthetic((35, 5, 30, 130), (30, 10, 10, 150))))
    assert 'raised 20 fewer false alarms (10 compared with 30) but found 5 fewer failures' in text
    assert 'Neither model is better on both counts.' in text


def test_precision_extremes():
    low = ' '.join(results_summary(synthetic((1, 39, 60, 100), (2, 38, 70, 90))))
    assert 'Fewer than 1 of every 10 warnings was correct.' in low
    high = ' '.join(results_summary(synthetic((40, 0, 1, 159), (39, 1, 3, 157))))
    assert 'Nearly every warning was correct.' in high
    perfect = ' '.join(results_summary(synthetic((40, 0, 0, 160), (39, 1, 3, 157))))
    assert 'none were false alarms' in perfect and 'Every warning was correct.' in perfect


def test_legacy_single_model_run():
    legacy = synthetic((30, 10, 10, 150), (1, 1, 1, 1), baseline=False)
    legacy['validation'] = {'Random forest': legacy['validation']['Random forest']}
    del legacy['test']['Logistic regression']
    sentences = results_summary(legacy)
    assert_style(sentences)
    assert 'F1 score of 0.600' in sentences[0]


def test_missing_winner_results():
    broken = synthetic((30, 10, 10, 150), (1, 1, 1, 197))
    del broken['test']['Random forest']
    assert results_summary(broken) == ['Random forest was selected but this run has no final-check results to explain.']


def test_build_summary_markdown(run):
    checks = [{'Check': 'Example', 'Passed': True, 'Detail': 'Fine.'}, {'Check': 'Other', 'Passed': None, 'Detail': 'Skipped.'}]
    text = build_summary(run, checks)
    assert 'python make_results_summary.py' in text and run['fingerprint'] in text
    assert 'scikit-learn ' + core.sklearn.__version__ in text
    for name, s in run['test'].items():
        assert re.search(rf'\| {re.escape(name)} \| {s["Failures found"]} \| {s["Failures missed"]} \| {s["False alarms"]} \|', text)
    assert '| Example | Passed | Fine. |' in text and '| Other | Not checked | Skipped. |' in text
    assert all(f'- {sentence}' in text for sentence in results_summary(run))
    assert ', and' not in text


def test_zero_failures_tradeoff_talks_only_about_false_alarms():
    text = ' '.join(results_summary(synthetic((0, 0, 3, 197), (0, 0, 7, 193))))
    assert 'Random forest raised 3 warnings. All of them were false alarms.' in text
    assert 'Logistic regression raised 7 false alarms compared with 3 for Random forest' in text
    assert '0 compared with 0' not in text


@pytest.mark.parametrize('label', ['UCI AI4I generated sample', 'Intentionally flawed demo sample'])
def test_closing_sentence_for_generated_sources(label):
    run = dict(synthetic((30, 10, 10, 150), (25, 15, 5, 155)), source_label=label)
    sentences = results_summary(run)
    assert_style(sentences)
    assert sentences[-1].startswith('These results come from generated equipment data split into random rows.')
    assert 'not been verified' not in sentences[-1]


@pytest.mark.parametrize('label', ['Uploaded CSV (origin not verified)', 'Unknown legacy source', 'Unspecified CSV', None])
def test_closing_sentence_for_uploads_and_unknown_sources(label):
    run = synthetic((30, 10, 10, 150), (25, 15, 5, 155))
    if label is not None:
        run['source_label'] = label
    sentences = results_summary(run)
    assert_style(sentences)
    last = sentences[-1]
    assert 'generated equipment data' not in ' '.join(sentences)
    assert last.startswith('These results come from the supplied data split into random rows. Its origin has not been verified.')
    assert 'do not forecast when a real machine will break down or prove performance on real equipment' in last
