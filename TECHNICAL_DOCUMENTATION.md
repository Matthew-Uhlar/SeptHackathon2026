# SignalReady technical documentation

Submission item 5 for ABB Accelerator 2026 Theme 1 (Agentic Predictive Maintenance Studio). It covers solution architecture / technologies used / implementation approach / setup instructions.

## What the solution does

SignalReady is a local guided modeling studio for equipment failure data. An engineer loads a CSV in the AI4I 2020 format. The app profiles and checks the data. It trains two standard models on a seeded split and picks one with a fixed rule on a separate selection group. Then it reports failures found and missed alongside false alarms on a final group that played no part in the choice. It explains the model and saves it locally. The saved model classifies new readings.

A person starts every step. The app automates the machine learning work between those steps but does not act on equipment or make maintenance decisions.

## Architecture

```text
            Browser (Streamlit UI on 127.0.0.1)
                         |
                      app.py
     sidebar: data source / saved runs / reload / clear
     tabs: 1 Data readiness / 2 Model comparison /
           3 Try a prediction / 4 What drove the model
                         |
   +---------------------+-----------------------------+
   |                     |                             |
 core.py            feature modules               local files
 read_csv           (see Module map)              data/ai4i2020.csv
 check_data                                       data/bad_sample.csv
 data_issue_examples                              models/*.joblib
 class_balance                                    (trusted saves only)
 train / metrics
 predict
 save_run / load_run
 explain / text_report
```

Everything runs in one Python process on one computer. There is no database / network service / live equipment connection. The proposal deliberately keeps that boundary.

### Data flow

1. **Parse.** `read_csv` rejects files over 10 MB / non-UTF-8 text / blank or duplicate headers / rows whose width differs from the header.
2. **Check.** `check_data` blocks training for missing columns / 50 to 50000 rows violated / empty required cells / non-finite or negative readings / types other than L M H / labels other than 0 or 1 / identical readings with conflicting labels / fewer than 10 unique examples of either outcome. It warns about repeated examples and excluded extra columns. `data_issue_examples` locates up to 20 problem cells by row and column without echoing values.
3. **Train.** `train` normalizes numbers and removes repeated examples. Then it makes a stratified seeded split: 60% training / 20% selection / 20% final check. Each model is a scikit-learn `Pipeline` of a `ColumnTransformer` (StandardScaler on five readings plus OneHotEncoder with the fixed L/M/H categories) and a class-balanced estimator. Preprocessing therefore fits on training rows only.
4. **Select.** The model with the higher F1 on the selection group wins. The final group is scored only after selection. The threshold stays at 0.5 and nothing is refit.
5. **Report.** Metrics for both models plus an always-no-failure baseline. JSON and plain-text reports carry the dataset fingerprint / seed / split sizes / software versions / limitations.
6. **Save and reload.** `save_run` writes a joblib artifact with a unique name through a temporary file. `load_run` validates structure / metric consistency / scikit-learn version before the run enters the UI.
7. **Predict.** `predict` validates a reading and rejects a product type absent from training. It lists readings outside the training range.

### Module map

| File | Responsibility |
|---|---|
| app.py | Streamlit UI and session state. |
| core.py | Parsing / checks / training / metrics / persistence / explanations / reports. |
| fetch_data.py | Downloads the original UCI sample without modifying it. |
| data/bad_sample.csv | Intentionally flawed fixture for the demo. |
| test_*.py | Automated tests (pytest plus Streamlit AppTest). |

## Technologies used

| Technology | Use | License |
|---|---|---|
| Python 3.11 or 3.12 | Language | PSF |
| Streamlit 1.64 | Local web UI | Apache 2.0 |
| scikit-learn 1.9 | Pipelines / logistic regression / random forest / metrics | BSD 3-Clause |
| pandas 3.0 | CSV loading and checks | BSD 3-Clause |
| NumPy | Numeric checks | BSD 3-Clause |
| joblib 1.6 | Local model persistence | BSD 3-Clause |
| Altair | Explanation chart (bundled with Streamlit) | BSD 3-Clause |
| pytest 9.1 | Tests | MIT |

Dataset: AI4I 2020 Predictive Maintenance Dataset. UCI Machine Learning Repository. https://doi.org/10.24432/C5HS5C. CC BY 4.0. The readings are synthetic.

The theme suggests FastAPI / MLflow / LangGraph / Docker / SHAP / LightGBM / PostgreSQL. The solo proposal limited the build to one local app with standard scikit-learn models so that every result stays auditable within a 40-hour budget. The design keeps those as future scope (see below) rather than partial integrations.

## Implementation approach

- **Trust before accuracy.** The problem statement is that a model score can hide important mistakes. So every screen leads with missed failures and false alarms and compares against a baseline that never predicts failure.
- **No leakage by construction.** Only six approved inputs reach the model. IDs and failure-mode columns are excluded. Duplicates are removed before splitting. Preprocessing fits inside the training pipeline.
- **Held-out honesty.** Selection and final evaluation use separate groups. The final group never influences the choice.
- **Auditability.** Each run records a data fingerprint / seed / split indices / UTC training time / software versions / format version. Reloads validate all of it.
- **Plain language.** Messages tell the user what to fix. Explanations state what they do not show.
- **Test-driven fixes.** Each defect found in review received a regression test. Tests isolate saved models in a temporary folder.

## Setup instructions

Windows with the included launcher:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python fetch_data.py   # only if data/ai4i2020.csv is missing
```

Then double-click **Start SignalReady.bat** or run:

```powershell
.venv\Scripts\python -m streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

macOS or Linux:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1
```

Run the tests with `python -m pytest -q`. Set `SIGNALREADY_MODEL_DIR` to choose where saved runs are stored.

## Limits

- Generated data. No claim of factory performance.
- Random row splits do not validate future periods or unseen machines.
- No time-to-failure forecast / warning lead time / calibrated probability.
- One fixed CSV format. One local user.
- Joblib artifacts must come from this app. Never load an untrusted model file.

## Future scope

- Time-aware or machine-aware evaluation once real equipment data with timestamps and asset IDs is available.
- A FastAPI scoring endpoint in a Docker image for plant integration.
- MLflow experiment tracking to replace local joblib metadata.
- SHAP explanations and gradient-boosted models (LightGBM or XGBoost) evaluated with the same held-out discipline.
- Probability calibration before any score is presented as a likelihood.
