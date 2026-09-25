from pathlib import Path
import hashlib
import json
import os
import altair as alt
import pandas as pd
import streamlit as st
from core import NUMERIC, FEATURES, TARGET, read_csv, check_data, train, save_run, public_report, explain, text_report, run_label, load_run, explanation_note, run_metadata, data_issue_examples, class_balance
from profiling import profile_columns, answer_giveaway_columns, saved_run_table
from narrative import results_summary
from completion_checks import completion_checks
from inference import model_score, score_band, what_if, score_batch, batch_summary, SCORE_NOTE, WHAT_IF_NOTE

ROOT = Path(__file__).parent
ISSUE_EXAMPLE_LIMIT = 20
MODEL_DIR = Path(os.environ.get('SIGNALREADY_MODEL_DIR', str(ROOT / 'models')))
CHECK_LABELS = {True: 'Passed', False: 'Failed', None: 'Not checked'}


@st.cache_data(show_spinner=False)
def saved_runs_overview(folder, files):
    # files carries names and modification times so the cache refreshes after each save.
    return saved_run_table(folder)


def run_identity(run):
    return run['fingerprint'], run_metadata(run).get('trained_at_utc'), run['winner']


def run_checks(frame, active):
    # Runs as a button callback so the expander can stay open on the rerun that shows the results.
    st.session_state.checks = (run_identity(active), completion_checks(frame, active, repeat=True))
    st.session_state.checks_open = True


st.set_page_config(page_title='SignalReady', page_icon='⚙️', layout='wide')
st.markdown('''<style>.stApp{background:#f6f9fa}h1,h2,h3{color:#153b43}div[data-testid="stMetric"]{background:white;padding:18px;border-radius:10px} .block-container{max-width:1200px;padding-top:2.5rem}</style>''', unsafe_allow_html=True)
st.caption('MAINTENANCE DATA ASSISTANT')
st.title('SignalReady')
st.write('Check your equipment data. Compare models. Understand the mistakes.')
st.info('The included samples use generated equipment data. Uploaded data has not been independently verified. Predictions flag readings that resemble failures labeled in the training data. They do not predict when a real machine will break down.')
with st.sidebar:
    st.header('Your workspace')
    source = st.radio('Data source', ['Included sample', 'Upload a CSV', 'Try a flawed sample'])
    upload = st.file_uploader('Equipment readings', type=['csv']) if source == 'Upload a CSV' else None
    st.caption('Your data stays in this local app. Training requires the AI4I column format.')
    st.link_button('About the sample data', 'https://doi.org/10.24432/C5HS5C')
    st.caption('AI4I 2020 dataset by S. Matzka · UCI Machine Learning Repository · CC BY 4.0')
    saved = sorted(MODEL_DIR.glob('*.joblib')) if MODEL_DIR.exists() else []
    if saved:
        st.caption('PROTOTYPE — no live equipment connection.')
        latest_save = st.session_state.pop('latest_save', None)
        if latest_save in saved:
            st.session_state.saved_run_choice = latest_save
        choice = st.selectbox('Saved local runs', saved, format_func=run_label, key='saved_run_choice')
        if st.button('Reload saved model'):
            try:
                st.session_state.run = load_run(choice)
                st.session_state.loaded = True
                st.session_state.pop('reload_error', None)
                st.success('Saved run restored. Its results belong to its original data.')
            except Exception:
                st.session_state.reload_error = 'The requested saved run could not be loaded. Any previously active model remains selected. Choose another saved run or train a new one.'
    if st.session_state.get('run'):
        if st.button('Clear active model'):
            st.session_state.pop('run', None)
            st.session_state.pop('reload_error', None)
            st.session_state.loaded = False
            st.rerun()

raw = None
if source == 'Included sample':
    sample = ROOT / 'data/ai4i2020.csv'
    if sample.exists():
        raw = sample.read_bytes()
    else:
        st.error('Sample data is missing. Run the included fetch_data.py script once or upload a matching CSV.')
elif source == 'Try a flawed sample':
    flawed = ROOT / 'data/bad_sample.csv'
    if flawed.exists():
        raw = flawed.read_bytes()
        st.caption('This built-in file intentionally has a missing reading and a repeated example so you can see the data-readiness checks catch them.')
    else:
        st.error('The flawed sample data is missing from the data folder.')
elif upload:
    raw = upload.getvalue()
fingerprint = hashlib.sha256(raw or b'').hexdigest()
if fingerprint != st.session_state.get('input_hash'):
    if not st.session_state.get('loaded'):
        st.session_state.pop('run', None)
    st.session_state.input_hash = fingerprint

if st.session_state.get('reload_error'):
    st.error(st.session_state.reload_error)
if st.session_state.get('notice'):
    st.success(st.session_state.pop('notice'))
active_run = st.session_state.get('run')
if active_run:
    st.caption('Active model: ' + active_run['winner'] + ' · dataset ' + active_run['fingerprint'][:12])
# A stable key keeps the open tab when a rerun adds elements above it, such as after saving.
TAB_LABELS = ['1  Data readiness', '2  Model comparison', '3  Try a prediction', '4  What drove the model']
# A tab can only be switched before the tabs render so actions request it for the next run.
if st.session_state.get('switch_tab') in TAB_LABELS:
    st.session_state.active_tab = st.session_state.pop('switch_tab')
df = None
data_tab, results_tab, prediction_tab, explain_tab = st.tabs(TAB_LABELS, key='active_tab', on_change='rerun')
with data_tab:
    st.header('Is the data ready?')
    if raw:
        try:
            df = read_csv(raw)
            report = check_data(df)
        except ValueError as exc:
            st.error(str(exc))
            df = None
        if df is not None:
            a,b,c = st.columns(3)
            a.metric('Readings', f'{len(df):,}')
            b.metric('Blocking issues', len(report['errors']))
            c.metric('Repeated examples', report['duplicates'])
            for issue in report['errors']: st.error(issue)
            for issue in report['warnings']: st.warning(issue)
            for item in answer_giveaway_columns(df):
                st.warning('Possible answer giveaway: ' + item['Evidence'])
            # Every located problem also raises a blocking error so a clean file skips the cell-by-cell scan.
            examples = data_issue_examples(df, limit=ISSUE_EXAMPLE_LIMIT) if report['errors'] else []
            if examples:
                with st.expander('Where to correct the file', expanded=True):
                    st.dataframe(pd.DataFrame(examples), hide_index=True, use_container_width=True)
                    st.caption('Data row 1 is the first reading below the header. In a spreadsheet it is usually row 2. Values are not repeated here.')
                    if len(examples) == ISSUE_EXAMPLE_LIMIT:
                        st.caption(f'Showing the first {ISSUE_EXAMPLE_LIMIT} problem cells. Correct these and check again to see any others.')
            balance = class_balance(df)
            if balance:
                usable = balance['No failure'] + balance['Failure']
                share = f" ({balance['Failure'] / usable:.1%} of usable unique examples)" if usable else ''
                st.write(f"Outcome balance after removing repeats: {balance['Failure']:,} failure examples{share} and {balance['No failure']:,} no-failure examples.")
                if balance['Unusable labels']:
                    st.caption(f"{balance['Unusable labels']:,} unique examples have a missing or invalid failure label.")
                st.caption('Failures are usually rare. That is why the comparison reports missed failures instead of relying on overall accuracy.')
            if report['ignored']:
                st.caption('Excluded columns: ' + ', '.join(report['ignored']))
            with st.expander('Column profile'):
                st.dataframe(profile_columns(df), hide_index=True, use_container_width=True)
                st.caption('Counts and number ranges for every column. Text values are not repeated here. Only columns marked Input or Target are used for training.')
            if not report['errors']:
                st.success('Ready for the demo workflow. Only the six approved equipment inputs will enter training.')
            with st.expander('View readings and required columns'):
                st.write('Required: ' + ', '.join(FEATURES + [TARGET]))
                st.dataframe(df.head(100), hide_index=True)
            st.caption('The app removes repeated examples before reserving 20% for a final check. Another 20% selects the model. The remaining 60% trains it.')
            if st.button('Check and compare models', type='primary', disabled=bool(report['errors'])):
                try:
                    with st.spinner('Training two models and checking their results…'):
                        source_label = {'Included sample': 'UCI AI4I generated sample', 'Try a flawed sample': 'Intentionally flawed demo sample', 'Upload a CSV': 'Uploaded CSV (origin not verified)'}[source]
                        st.session_state.run = train(df, source_label=source_label)
                        st.session_state.loaded = False
                        st.session_state.pop('reload_error', None)
                    st.session_state.notice = 'Comparison ready. Showing the Model comparison tab.'
                    st.session_state.switch_tab = TAB_LABELS[1]
                    st.rerun()
                except ValueError as exc:
                    st.error('The comparison could not complete: ' + str(exc))
    else:
        st.write('Choose the included sample or upload a CSV to begin.')

run = st.session_state.get('run')
with results_tab:
    st.header('What did the models miss?')
    if run:
        st.subheader('Selected model: ' + run['winner'])
        st.caption('PROTOTYPE — no live equipment connection.')
        if st.session_state.get('loaded'):
            st.info('Showing a saved run. These results describe its original dataset rather than the currently selected file.')
        st.caption('Selection uses F1 on the separate selection group. F1 balances failures found with correct warnings. The final check does not choose the winner. The decision threshold stays at 0.5.')
        stats = run['test'][run['winner']]
        cols = st.columns(3)
        for col,key in zip(cols,['Failures found','Failures missed','False alarms']): col.metric(key,stats[key])
        table = pd.DataFrame(run['test']).T.drop(columns=['F1'])
        for c in ['Failure detection rate','Warnings that were correct']:
            table[c] = table[c].map(lambda x: f'{x:.1%}')
        st.dataframe(table, use_container_width=True)
        st.write('A missed failure is an actual failure the model did not flag. A false alarm is a warning on a reading labeled as no failure.')
        st.caption('The always-no-failure row shows why a high overall accuracy can be misleading when failures are rare.')
        st.subheader('What these results mean')
        st.markdown('\n'.join('- ' + sentence for sentence in results_summary(run)))
        with st.expander('Completion checks', key='checks_open', on_change='rerun'):
            st.write('These checks test key promises of this workflow against the active run. The repeat check retrains on the selected file when it matches the run.')
            st.button('Run completion checks', on_click=run_checks, args=(df, run))
            stored = st.session_state.get('checks')
            if stored and stored[0] == run_identity(run):
                st.dataframe(pd.DataFrame([{**c, 'Passed': CHECK_LABELS[c['Passed']]} for c in stored[1]]), hide_index=True, use_container_width=True)
        with st.expander('How this run was checked'):
            st.write('Data source: ' + run.get('source_label', 'Unknown (legacy run)'))
            metadata = run_metadata(run)
            st.write('Training time (UTC): ' + (metadata.get('trained_at_utc') or 'Unknown (legacy run)'))
            st.json({'rows':run['counts'],'dataset fingerprint':run['fingerprint'],'approved inputs':run['features'],'random seed':run['seed']})
            st.json({'saved format': metadata['format_version'], 'software versions': metadata['dependencies']})
            st.write('These random row splits evaluate the supplied dataset. They do not establish performance on future time periods or different machines. Avoid repeatedly adjusting a model after viewing final results.')
        if st.button('Save selected model locally'):
            try:
                saved_path = save_run(run, MODEL_DIR)
                st.session_state.latest_save = saved_path
                st.session_state.notice = 'Saved. This run is now available in the sidebar and will remain available after restarting.'
                st.rerun()
            except OSError:
                st.error('The run could not be saved. Check that the local model folder is writable and try again.')
        st.download_button('Download results report', json.dumps(public_report(run),indent=2), 'signalready-results.json','application/json')
        st.download_button('Download results report (readable)', text_report(run), 'signalready-results.txt','text/plain')
    else: st.write('Run the data check and model comparison first.')
    saved_files = sorted(MODEL_DIR.glob('*.joblib')) if MODEL_DIR.exists() else []
    if saved_files:
        with st.expander('Compare saved runs'):
            st.dataframe(saved_runs_overview(str(MODEL_DIR), tuple((p.name, p.stat().st_mtime) for p in saved_files)), hide_index=True, use_container_width=True)
            st.caption('Each saved run was checked on its own dataset. Scores from different datasets are not directly comparable.')

with prediction_tab:
    st.header('Try a set of readings')
    if run:
        st.caption('Using ' + run['winner'] + ' from dataset ' + run['fingerprint'][:12])
        if st.session_state.get('loaded'):
            st.info('This is a saved run. It was trained on its original dataset. It may not match the file selected in Data readiness.')
        with st.form('prediction'):
            row={'Type':st.selectbox('Product quality type',['L','M','H'])}
            defaults=[300.,310.,1500.,40.,100.]
            columns=st.columns(2)
            for i,(name,value) in enumerate(zip(NUMERIC,defaults)):
                row[name]=columns[i%2].number_input(name,min_value=0.,value=value)
            submitted=st.form_submit_button('Check these readings')
        if submitted:
            try:
                result=model_score(run,row)
                outcome,outside=result['flag'],result['outside']
                if outside:
                    st.warning('Outside the training range: '+', '.join(outside)+'. This model may be unreliable for these readings.')
                if outcome: st.warning('The model flags a failure pattern in these readings.')
                else: st.info('The model does not flag a failure pattern in these readings.')
                st.caption('This is a model classification. It does not establish that equipment is safe or identify a repair.')
                st.caption('PROTOTYPE — no live equipment connection.')
                st.metric('Model score (uncalibrated)', f"{result['score']:.3f}", help=SCORE_NOTE)
                st.write(score_band(result['score'], result['flag']) + '.')
                st.caption(SCORE_NOTE)
                st.subheader('How the score responds to each reading')
                changes = pd.DataFrame(what_if(run,row))
                if changes['Score change'].abs().max() < 0.001:
                    st.write('Changing any single input barely moves this score. Each reading was replaced by its training average and the product type by each other type.')
                else:
                    st.dataframe(changes, hide_index=True, use_container_width=True, column_config={'Score change': st.column_config.NumberColumn(format='%+.3f')})
                    st.caption('A positive score change means the current value raises the score compared with the training average or the other product type.')
                st.caption(WHAT_IF_NOTE)
            except ValueError as exc:
                st.error(str(exc))
        st.subheader('Score a file of readings')
        st.caption('Upload a CSV with the six approved input columns. A failure label column is optional and ignored. Rows that fail the checks are skipped and listed.')
        batch_file = st.file_uploader('Readings to score', type=['csv'], key='batch_upload')
        if batch_file:
            try:
                results, problems = score_batch(run, read_csv(batch_file.getvalue()))
                summary = batch_summary(results)
                a, b, c = st.columns(3)
                a.metric('Rows scored', f"{summary['Rows scored']:,}")
                b.metric('Flagged', f"{summary['Flagged']:,}")
                c.metric('Outside training range', f"{summary['Outside training range']:,}")
                st.dataframe(results, hide_index=True, use_container_width=True)
                if problems:
                    with st.expander(f'{len(problems):,} rows were skipped'):
                        st.dataframe(pd.DataFrame(problems), hide_index=True, use_container_width=True)
                st.caption('The Model flag column is the classification. ' + SCORE_NOTE)
                st.download_button('Download scored readings', results.to_csv(index=False), 'signalready-scores.csv', 'text/csv')
            except ValueError as exc:
                st.error(str(exc))
    else: st.write('Train or reload a saved model to try a prediction.')

with explain_tab:
    st.header('Which inputs did the model rely on most?')
    if run:
        st.caption('These scores come from the fitted model using its training examples. The explanation calculation does not use the selection or final-check groups. It does not show a physical cause of failure or a repair recommendation.')
        if st.session_state.get('loaded'):
            st.info('Showing the saved model. These explanations may not match the file selected in Data readiness.')
        rows = explain(run)
        labels = pd.DataFrame(rows)
        labels['feature'] = labels['feature'].str.replace('numbers__', '', regex=False).str.replace('type__Type_', 'Product type ', regex=False)
        chart = alt.Chart(labels.head(10)).mark_bar(color='#087f78').encode(
            x=alt.X('importance:Q', title='Model importance score'),
            y=alt.Y('feature:N', title=None, sort='-x', axis=alt.Axis(labelLimit=230)),
            tooltip=[alt.Tooltip('feature:N', title='Input'), alt.Tooltip('importance:Q', title='Score', format='.4f')],
        ).properties(height=420)
        st.altair_chart(chart, use_container_width=True)
        with st.expander('View all approved-feature contributions'):
            st.dataframe(labels.rename(columns={'feature': 'Input', 'importance': 'Model importance score'}), hide_index=True, use_container_width=True)
        st.caption(explanation_note(run))
    else:
        st.write('Run the data check and model comparison first.')
