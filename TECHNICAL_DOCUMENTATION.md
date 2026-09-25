# SignalReady technical documentation

Submission item 5 for ABB Accelerator 2026 Theme 1 (Agentic Predictive Maintenance Studio). It covers solution architecture / technologies used / implementation approach / setup instructions. Every statement below was checked against core.py and app.py on September 25 2026.

## What the solution does

SignalReady is a local guided modeling studio for equipment failure data. An engineer loads a CSV in the AI4I 2020 format. The app checks the data and blocks training until blocking problems are fixed. It trains two standard models on a seeded split and picks one with a fixed rule on a separate selection group. Then it reports failures found and missed alongside false alarms on a final group that played no part in the choice. It explains which inputs the fitted model relied on and saves the model locally. A saved model classifies new readings.

A person starts every step. The app automates the machine learning work between those steps but does not act on equipment or make maintenance decisions. It is not an autonomous agent and has no chat interface.

## Architecture

```text
            Browser (Streamlit UI on 127.0.0.1)
                         |
                      app.py
     sidebar: data source / saved runs / reload / clear
     tabs: 1 Data readiness / 2 Model comparison /
           3 Try a prediction / 4 What drove the model
                         |
            +------------+---------------------+
            |                                  |
          core.py                         local files
          read_csv                        data/ai4i2020.csv
          check_data                      data/bad_sample.csv
          data_issue_examples             models/*.joblib
          class_balance                   (trusted local saves only)
          train / metrics
          predict
          save_run / load_run / run_label
          explain / explanation_note
          public_report / text_report / run_metadata
```

<!-- COORDINATOR: update after integration. Add profiling.py / narrative.py / completion_checks.py / inference.py to the diagram and the module map only once app.py imports them. -->

Everything runs in one Python process on one computer. There is no database / network service / live equipment connection. The Streamlit server binds to 127.0.0.1 and usage statistics are off (.streamlit/config.toml). The proposal deliberately keeps that boundary.

### Data flow

1. **Parse.** `read_csv` rejects files over 10,000,000 bytes / text that is not UTF-8 / blank or duplicate headers / rows whose field count differs from the header. The Streamlit upload limit is also set to 10 MB.
2. **Check.** `check_data` blocks training for missing required columns / fewer than 50 or more than 50000 rows / empty required cells / non-finite or negative readings / product types other than L M H / labels other than 0 or 1 / identical readings with conflicting labels / fewer than 10 unique examples of either outcome. It warns about repeated examples and lists extra columns that are excluded. `data_issue_examples` locates up to 20 invalid cells by data row and column without repeating their values. It covers missing / non-numeric / negative / wrong-type / wrong-label cells. Duplicates and conflicting labels are reported by `check_data` as counts rather than row locations. `class_balance` counts failure and no-failure examples after repeats are removed.
3. **Train.** `train` converts readings to numbers and removes repeated examples. Then it makes a stratified split with seed 42: 60% training / 20% selection / 20% final check. Each model is a scikit-learn `Pipeline` of a `ColumnTransformer` (StandardScaler on five readings plus OneHotEncoder with the fixed L/M/H categories) and a class-balanced estimator:
   - `LogisticRegression(max_iter=1500, class_weight='balanced')`
   - `RandomForestClassifier(n_estimators=120, max_depth=12, min_samples_leaf=2, class_weight='balanced')`

   Preprocessing therefore fits on training rows only.
4. **Select.** The model with the higher F1 on the selection group wins. On an exact tie the first listed model (logistic regression) wins. The final group is scored only after selection. The threshold stays at the default 0.5 and nothing is refit.
5. **Report.** Final-check metrics for both models plus an always-no-failure baseline: failures found / failures missed / false alarms / correct no-failure readings / detection rate / share of warnings that were correct / F1. `public_report` (JSON) and `text_report` (plain text) carry the dataset fingerprint / seed / split sizes / software versions / limitations. The fingerprint is a SHA-256 hash of the cleaned and deduplicated training table.
6. **Save and reload.** `save_run` writes a joblib artifact with a unique file name through a temporary file then renames it so earlier saves are kept. `load_run` checks the format version / recorded scikit-learn version / training time / fingerprint format / input columns / reading ranges. It also checks that every confusion matrix sums to its group size and that each rate agrees with its counts. A failed reload keeps the previously active model.
7. **Predict.** `predict` validates a reading and rejects a product type absent from the training examples. It lists readings outside the training range. The result is a class (failure pattern or no failure pattern). No score or probability is shown.

### Module map

| File | Responsibility |
|---|---|
| app.py | Streamlit UI and session state. |
| core.py | Parsing / checks / training / metrics / persistence / explanations / reports. |
| fetch_data.py | Downloads the original UCI sample without modifying it. Only needed if data/ai4i2020.csv is missing. |
| data/ai4i2020.csv | Unmodified UCI AI4I 2020 file (10,000 rows). |
| data/bad_sample.csv | Small intentionally flawed fixture for the demo. Its values were written for this project in the AI4I column layout. |
| .streamlit/config.toml | Local-only server address / 10 MB upload limit / usage statistics off / theme. |
| Start SignalReady.bat | Windows launcher for an existing .venv. |
| test_*.py | Automated tests (pytest plus Streamlit AppTest). |

## Technologies used

Versions are the pins in requirements.txt. Unpinned libraries show the version installed by those pins on September 25 2026. Licenses were read from each installed package's metadata. THIRD_PARTY_NOTICES.md lists every installed dependency.

| Technology | Version | Use | License |
|---|---|---|---|
| Python | 3.11 or later (tested 3.12.14 on Windows and 3.11.15 on Linux) | Language | PSF-2.0 |
| Streamlit | 1.64.0 | Local web UI | Apache-2.0 |
| scikit-learn | 1.9.1 | Pipelines / logistic regression / random forest / metrics | BSD-3-Clause |
| pandas | 3.0.6 | CSV loading and checks | BSD-3-Clause |
| NumPy | 2.4.6 (installed with the pins) | Numeric checks | BSD-3-Clause (bundled parts under 0BSD / MIT / Zlib / CC0-1.0) |
| joblib | 1.6.0 | Local model persistence | BSD-3-Clause |
| Altair | 6.3.0 (installed with Streamlit) | Explanation chart | BSD-3-Clause |
| SciPy | 1.17.1 (installed with scikit-learn) | Used inside scikit-learn | BSD-3-Clause |
| pytest | 9.1.1 | Tests | MIT |

Python 3.11 is the minimum because scikit-learn 1.9.1 / pandas 3.0.6 / NumPy 2.4.6 require it.

Dataset: Matzka S. (2020). AI4I 2020 Predictive Maintenance Dataset. UCI Machine Learning Repository. https://doi.org/10.24432/C5HS5C. CC BY 4.0. The readings are synthetic.

The theme suggests FastAPI / MLflow / LangGraph / Docker / SHAP / LightGBM / PostgreSQL. The solo proposal limited the build to one local app with standard scikit-learn models so that every result stays auditable within a 40-hour budget. Those technologies are listed as future scope below rather than as partial integrations.

## Implementation approach

- **Trust before accuracy.** The problem statement is that a model score can hide important mistakes. The results screen leads with failures found and missed alongside false alarms and compares them with a baseline that never predicts failure.
- **No leakage by construction.** Only six approved inputs reach the model. IDs and failure-type columns are excluded. Duplicates are removed before splitting so the same example cannot land in two groups. Preprocessing fits inside the training pipeline.
- **Held-out honesty.** Selection and final evaluation use separate groups. The final group never influences the choice.
- **Auditability.** Each new run records a data fingerprint / seed / split row indices / UTC training time / software versions / format version. Reloads check the parts listed in step 6 above. Older runs show their audit details as unknown instead of inventing them.
- **Plain language.** Messages tell the user what to fix. Explanations state what they do not show.
- **Test-driven fixes.** Each defect found in review received a regression test. Save and reload tests use a temporary model folder so real saved runs are never touched.

## Setup instructions

Requirements: Python 3.11 or later (3.12 recommended on Windows). No internet connection is needed after installation because the sample data is in the repository.

Windows:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Then double-click **Start SignalReady.bat** or run:

```powershell
.venv\Scripts\python -m streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

macOS or Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1
```

The app opens at http://127.0.0.1:8501. Only if data/ai4i2020.csv is missing, run `python fetch_data.py` once with the environment's Python to download it.

Run the tests with `python -m pytest -q` using the environment's Python. Set the `SIGNALREADY_MODEL_DIR` environment variable to choose where saved runs are stored (default: the models folder, which git ignores).

## Limits

- Generated data. No claim of factory performance.
- Random row splits do not validate future periods or unseen machines.
- No time-to-failure forecast / warning lead time / calibrated probability.
- One fixed CSV format. One local user.
- Joblib artifacts must come from this app. Never load an untrusted model file. The app does not accept uploaded model files.

## Future scope

- Time-aware or machine-aware evaluation once real equipment data with timestamps and asset IDs is available.
- A FastAPI scoring endpoint in a Docker image for plant integration.
- MLflow experiment tracking to replace local joblib metadata.
- SHAP explanations and gradient-boosted models (LightGBM or XGBoost) evaluated with the same held-out discipline.
- Engineered inputs that match known failure mechanisms such as mechanical power or the gap between process and air temperature.
- Probability calibration before any score is presented as a likelihood.
