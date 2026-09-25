from pathlib import Path
import hashlib
import json
import joblib
import pandas as pd
import streamlit as st
from core import NUMERIC, FEATURES, TARGET, read_csv, check_data, train, predict, save_run, public_report

ROOT = Path(__file__).parent
st.set_page_config(page_title='SignalReady', page_icon='⚙️', layout='wide')
st.markdown('''<style>.stApp{background:#f6f9fa}h1,h2,h3{color:#153b43}div[data-testid="stMetric"]{background:white;padding:18px;border-radius:10px} .block-container{max-width:1200px;padding-top:2.5rem}</style>''', unsafe_allow_html=True)
st.caption('MAINTENANCE DATA ASSISTANT')
st.title('SignalReady')
st.write('Check your equipment data. Compare models. Understand the mistakes.')
st.info('Prototype using generated equipment data. Predictions identify failure patterns in readings. They do not predict when a real machine will break down.')
with st.sidebar:
    st.header('Your workspace')
    source = st.radio('Data source', ['Included sample', 'Upload a CSV'])
    upload = st.file_uploader('Equipment readings', type=['csv']) if source == 'Upload a CSV' else None
    st.caption('Your data stays in this local app. Training requires the AI4I column format.')
    st.link_button('About the sample data', 'https://doi.org/10.24432/C5HS5C')
    st.caption('AI4I 2020 dataset · UCI Machine Learning Repository · CC BY 4.0')
    saved = sorted((ROOT / 'models').glob('*.joblib')) if (ROOT / 'models').exists() else []
    if saved:
        choice = st.selectbox('Saved local runs', saved, format_func=lambda x: x.stem)
        if st.button('Reload saved model'):
            try:
                st.session_state.run = joblib.load(choice)
                st.session_state.loaded = True
                st.success('Saved run restored. Its results belong to its original data.')
            except Exception:
                st.error('This saved run could not be loaded. Train a new run with the current app.')

raw = None
if source == 'Included sample':
    sample = ROOT / 'data/ai4i2020.csv'
    if sample.exists():
        raw = sample.read_bytes()
    else:
        st.error('Sample data is missing. Run the included fetch_data.py script once or upload a matching CSV.')
elif upload:
    raw = upload.getvalue()
fingerprint = hashlib.sha256(raw or b'').hexdigest()
if fingerprint != st.session_state.get('input_hash'):
    if not st.session_state.get('loaded'):
        st.session_state.pop('run', None)
    st.session_state.input_hash = fingerprint

data_tab, results_tab, prediction_tab = st.tabs(['1  Data readiness', '2  Model comparison', '3  Try a prediction'])
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
            if report['ignored']:
                st.caption('Excluded columns: ' + ', '.join(report['ignored']))
            if not report['errors']:
                st.success('Ready for the demo workflow. Only the six approved equipment inputs will enter training.')
            with st.expander('View readings and required columns'):
                st.write('Required: ' + ', '.join(FEATURES + [TARGET]))
                st.dataframe(df.head(100), hide_index=True)
            st.caption('The app removes repeated examples before reserving 20% for a final check. Another 20% selects the model. The remaining 60% trains it.')
            if st.button('Check and compare models', type='primary', disabled=bool(report['errors'])):
                with st.spinner('Training two models and checking their results…'):
                    st.session_state.run = train(df)
                    st.session_state.loaded = False
                st.success('Comparison ready. Open the Model comparison tab.')
    else:
        st.write('Choose the included sample or upload a CSV to begin.')

run = st.session_state.get('run')
with results_tab:
    st.header('What did the models miss?')
    if run:
        st.subheader('Selected model: ' + run['winner'])
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
        with st.expander('How this run was checked'):
            st.json({'rows':run['counts'],'dataset fingerprint':run['fingerprint'],'approved inputs':run['features'],'random seed':run['seed']})
            st.write('These random row splits evaluate this generated dataset. They do not establish performance on future time periods or different machines. Avoid repeatedly adjusting a model after viewing final results.')
        if st.button('Save selected model locally'):
            saved_path = save_run(run, ROOT / 'models')
            st.success('Saved. Use the sidebar to reload this run after restarting.')
        st.download_button('Download results report', json.dumps(public_report(run),indent=2), 'signalready-results.json','application/json')
    else: st.write('Run the data check and model comparison first.')

with prediction_tab:
    st.header('Try a set of readings')
    if run:
        st.caption('Using ' + run['winner'] + ' from dataset ' + run['fingerprint'][:12])
        with st.form('prediction'):
            row={'Type':st.selectbox('Product quality type',['L','M','H'])}
            defaults=[300.,310.,1500.,40.,100.]
            columns=st.columns(2)
            for i,(name,value) in enumerate(zip(NUMERIC,defaults)):
                row[name]=columns[i%2].number_input(name,min_value=0.,value=value)
            submitted=st.form_submit_button('Check these readings')
        if submitted:
            outcome,outside=predict(run,row)
            if outside:
                st.warning('Outside the training range: '+', '.join(outside)+'. This model may be unreliable for these readings.')
            if outcome: st.warning('The model flags a failure pattern in these readings.')
            else: st.success('The model does not flag a failure pattern in these readings.')
            st.caption('This is a model classification. It does not establish that equipment is safe or identify a repair.')
    else: st.write('Train or reload a saved model to try a prediction.')
