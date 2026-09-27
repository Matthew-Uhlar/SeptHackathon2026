# SignalReady technical documentation

## September 26 2026 update

Windows verification passed 266 tests with one optional browser test skipped. The older commit references below describe the prior baseline. exports.py now builds scored exports and an audit that records the outcome of every submitted batch row with model and dataset identity. app.py retains unsaved runs across source changes with clear notices and provides Clear session data to reset uploads and results. Saved files remain intact. CSV inputs have a 64-column cap and formula-like exported identifiers are escaped. See SECURITY_REVIEW.md for explicit local server protections and deployment limits. Model training and selection behavior are unchanged.

## September 27 2026 enhancement update

The app adds a selection-group hypothetical error-cost explorer / incoming batch numeric range screening / a downloadable model review card. The explorer uses illustrative user assumptions and does not tune the model or claim savings. Range screening uses valid scored rows and records skipped rows plus training and incoming-file fingerprints. It is a descriptive familiarity check rather than statistical drift detection. The review card lists evidence and human review actions without claiming deployment approval. The complete staged suite for this update passed 302 tests with one optional browser test skipped.


Submission item 5 for ABB Accelerator 2026 Theme 1 (Agentic Predictive Maintenance Studio). It covers solution architecture / technologies used / implementation approach / setup instructions. Every statement below was checked against app.py / core.py / profiling.py / narrative.py / completion_checks.py / inference.py at commit 85255c2 on September 25 2026.

## What the solution does

SignalReady is a local guided modeling studio for equipment failure data. An engineer loads a CSV in the AI4I 2020 format. The app profiles and checks the data. It blocks training until blocking problems are fixed and warns about columns that give away the answer. It trains two standard models on a seeded split and picks one with a fixed rule on a separate selection group. Then it reports failures found and missed alongside false alarms on a final group that played no part in the choice. It explains the result in plain sentences and can retest six completion checks from the proposal. It shows which inputs the fitted model relied on and saves the model locally. A saved model classifies a single reading with an uncalibrated score and a what-if view or scores a whole CSV of readings at once.

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
   +------------+-------------+--------------+-------------+
   |            |             |              |             |
 core.py    profiling.py  narrative.py  completion_    inference.py
 read_csv   profile_      results_      checks.py      model_score
 check_data   columns       summary     completion_    score_band
 data_issue_ answer_                      checks       what_if
   examples   giveaway_                                score_batch
 class_       columns                                  batch_summary
   balance  saved_run_
 train /      table
   metrics
 predict              local files
 save_run /           data/ai4i2020.csv / data/bad_sample.csv /
   load_run           data/new_readings.csv
 explain /            models/*.joblib (trusted local saves only)
   reports
```

The four feature modules are plain Python with no Streamlit code so they are tested directly. They all build on core.py and never change what enters training. make_results_summary.py reuses core.py / narrative.py / completion_checks.py to write RESULTS_SUMMARY.md from the included sample.

Train / save / reload / clear run as button callbacks so each click redraws the page once in its new state. An earlier mid-script rerun could leave a duplicate tab bar in the browser (testing-team bug B1 in TEST_REPORT.md).

Everything runs in one Python process on one computer. There is no database / network service / live equipment connection. The Streamlit server binds to 127.0.0.1 / usage statistics are off / the toolbar is in viewer mode so Streamlit's Deploy button is hidden (.streamlit/config.toml). The proposal deliberately keeps that boundary.

### Data flow

1. **Parse.** `read_csv` rejects files over 10,000,000 bytes / text that is not UTF-8 / blank or duplicate headers / rows whose field count differs from the header. The Streamlit upload limit is also set to 10 MB.
2. **Check.** `check_data` blocks training for missing required columns / fewer than 50 or more than 50000 rows / empty required cells / non-finite or negative readings / product types other than L M H / labels other than 0 or 1 / identical readings with conflicting labels / fewer than 10 unique examples of either outcome. It warns about repeated examples and lists extra columns that are excluded. When there is a blocking error `data_issue_examples` locates up to 20 invalid cells by data row and column without repeating their values. It is vectorized with NumPy so a 50,000-row file is scanned in well under 3 seconds. It covers missing / non-numeric / negative / wrong-type / wrong-label cells. Duplicates and conflicting labels are reported by `check_data` as counts rather than row locations. `class_balance` counts failure and no-failure examples after repeats are removed.
3. **Profile.** `profiling.profile_columns` lists every column with its role (Input / Target / Excluded) / missing count / unique count / numeric min, median and max. Text values are never copied into the profile. `profiling.answer_giveaway_columns` tests each excluded column against the failure label with a fixed rule. A numeric column is flagged when on its own it separates the labels with a folded ROC AUC of at least 0.9 or when at least 95% of the rows where it is nonzero are failures. A text column is flagged when its repeated values each occur with only one outcome. A second tolerant text rule also flags repeated values that are failures in at least 95% of their rows when together they fill at least 5 and no more than half of the labeled rows. Unique IDs never qualify. On the included sample it flags HDF / OSF / PWF / TWF and not UDI / Product ID / RNF. The app shows one information line naming the flagged columns plus an expander with the evidence for each. The evidence says the column may record the answer or be filled in after the outcome and that this is a pattern in the file rather than proof. Flagged columns are already excluded from training so the note explains the exclusion rather than changing it.
4. **Train.** `train` converts readings to numbers and removes repeated examples. Then it makes a stratified split with seed 42: 60% training / 20% selection / 20% final check. Each model is a scikit-learn `Pipeline` of a `ColumnTransformer` (StandardScaler on five readings plus OneHotEncoder with the fixed L/M/H categories) and a class-balanced estimator:
   - `LogisticRegression(max_iter=1500, class_weight='balanced')`
   - `RandomForestClassifier(n_estimators=120, max_depth=12, min_samples_leaf=2, class_weight='balanced')`

   Preprocessing therefore fits on training rows only.
5. **Select.** The model with the higher F1 on the selection group wins. On an exact tie the first listed model (logistic regression) wins. The final group is scored only after selection. The threshold stays at the default 0.5 and nothing is refit.
6. **Report.** Final-check metrics for both models plus an always-no-failure baseline: failures found / failures missed / false alarms / correct no-failure readings / detection rate / share of warnings that were correct / F1. `public_report` (JSON) and `text_report` (plain text) carry the dataset fingerprint / seed / split sizes / software versions / limitations. The fingerprint is a SHA-256 hash of the whole uploaded table after number normalization and removal of repeated examples. It covers every column and all three groups because it is computed before the split. `narrative.results_summary` turns the recorded counts into plain sentences from fixed templates. No language model is involved.
   `completion_checks.completion_checks` runs six checks from the proposal on the active run when the user presses Run completion checks: the recorded and fitted inputs are exactly the six approved inputs / every model's final counts cover the same number of readings and actual failures which is consistent with one shared final group of the stored size / the three row groups do not overlap and the fitted scaler saw only the training rows / a fresh training run on the same file gives identical results / a save and reload into a temporary folder gives identical predictions / data/bad_sample.csv produces both a blocking error and the repeated-example warning. A check reports Not checked when it cannot apply, such as a repeat run when the selected file differs from the run's data. The app shows the results as a static table with Result and Detail columns so the evidence wraps. It marks them out of date when the selected file or the active run changes.
7. **Save and reload.** `save_run` writes a joblib artifact with a unique file name through a temporary file then renames it so earlier saves are kept. `load_run` checks the format version / recorded scikit-learn version / training time / fingerprint format / input columns / reading ranges. It also checks that every confusion matrix sums to its group size and that each rate agrees with its counts. A failed reload states the reason and keeps any previously active model. A successful reload opens Model comparison. If the selected saved file disappears from the folder the sidebar says so instead of silently switching to another run. `profiling.saved_run_table` lists every saved run with its source / training time / selection and final-check F1 / counts. Files that cannot be loaded are listed as such instead of stopping the table.
8. **Predict.** `predict` validates a reading and rejects a product type absent from the training examples. It lists readings outside the training range. The result is a class (failure pattern or no failure pattern).
   `inference.model_score` adds the model's `predict_proba` output for the failure class as an uncalibrated score from 0 to 1. The app labels it "Model score (uncalibrated)" and states that it is not the chance of failure. Class balancing pushes these scores upward. `inference.what_if` replaces one reading at a time with its training average (taken from the fitted scaler) or the product type with another type seen in training and reports the score change and whether the flag would change. `inference.score_batch` applies the same validation to every row of an uploaded CSV of up to 5000 rows. Invalid rows are skipped and listed by data row without repeating their values. The rest get a flag / score / outside-range note and download as a CSV. The score column is named "Model score (uncalibrated)". ID text that starts like a spreadsheet formula gets a leading apostrophe so it cannot run when the file is opened.

### Module map

| File | Responsibility |
|---|---|
| app.py | Streamlit UI and session state. |
| core.py | Parsing / checks / training / metrics / persistence / explanations / reports. |
| profiling.py | Column profile / answer-giveaway detection / saved-run comparison table. |
| narrative.py | Plain-language results summary from fixed templates. |
| completion_checks.py | Six live completion checks for a trained or reloaded run. |
| inference.py | Uncalibrated model score / score band / what-if sensitivity / batch CSV scoring. |
| make_results_summary.py | Regenerates RESULTS_SUMMARY.md from the included sample. |
| fetch_data.py | Downloads the original UCI sample without modifying it. Only needed if data/ai4i2020.csv is missing. |
| data/ai4i2020.csv | Unmodified UCI AI4I 2020 file (10,000 rows). CC BY 4.0. |
| data/bad_sample.csv | Small intentionally flawed fixture for the demo. Written for this project in the AI4I column layout. |
| data/new_readings.csv | 31 readings written for this project to demonstrate batch scoring. Two rows are deliberately invalid. |
| demo/record_demo.py | Optional helper that records a captioned walkthrough MP4 with Playwright and imageio-ffmpeg. Not part of the app or its requirements. |
| .streamlit/config.toml | Local-only server address / 10 MB upload limit / usage statistics off / viewer toolbar (no Deploy button) / theme. |
| Start SignalReady.bat | Windows launcher for an existing .venv. |
| test_*.py | Automated tests (pytest plus Streamlit AppTest). |

## Technologies used

Versions are the pins in requirements.txt. Unpinned libraries show the version installed by those pins on September 25 2026. Licenses were read from each installed package's metadata. THIRD_PARTY_NOTICES.md lists every installed dependency.

| Technology | Version | Use | License |
|---|---|---|---|
| Python | 3.11 or later (tested 3.12.14 on Windows and 3.11.15 on Linux) | Language | PSF-2.0 |
| Streamlit | 1.64.0 | Local web UI | Apache-2.0 |
| scikit-learn | 1.9.1 | Pipelines / logistic regression / random forest / metrics / ROC AUC for giveaway detection | BSD-3-Clause |
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
- **Auditability.** Each new run records a data fingerprint / seed / split row indices / UTC training time / software versions / format version. Reloads check the parts listed in step 7 above. Older runs show their audit details as unknown instead of inventing them.
- **Plain language.** Messages tell the user what to fix. Explanations state what they do not show.
- **Honest scores.** The model score is always labelled uncalibrated with a note that it is not a failure probability. What-if results are described as model behavior rather than cause.
- **Test-driven fixes.** Each defect found in review received a regression test. Save and reload tests use a temporary model folder so real saved runs are never touched. A testing round found eight bugs (TEST_REPORT.md). All were fixed in 85255c2 with a test covering each. At that commit the suite had 253 tests: the 252 that run by default passed on Linux and the opt-in browser test (`SIGNALREADY_BROWSER_TESTS=1`) also passed.

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

Run the tests with `python -m pytest -q` using the environment's Python. The suite takes a few minutes because many tests train both models. Regenerate RESULTS_SUMMARY.md with `python make_results_summary.py`. Set the `SIGNALREADY_MODEL_DIR` environment variable to choose where saved runs are stored (default: the models folder, which git ignores).

## Limits

- Generated data. No claim of factory performance.
- Random row splits do not validate future periods or unseen machines.
- No time-to-failure forecast / warning lead time / calibrated probability. The model score is uncalibrated.
- What-if sensitivity changes one reading at a time. Inputs interact so the changes do not add up to the full score.
- Answer-giveaway detection is a fixed statistical rule on excluded columns. It is a pattern in the file rather than proof.
- One fixed CSV format. One local user.
- Joblib artifacts must come from this app. Never load an untrusted model file. The app does not accept uploaded model files.

## Future scope

- Time-aware or machine-aware evaluation once real equipment data with timestamps and asset IDs is available.
- A FastAPI scoring endpoint in a Docker image for plant integration.
- MLflow experiment tracking to replace local joblib metadata.
- SHAP explanations and gradient-boosted models (LightGBM or XGBoost) evaluated with the same held-out discipline.
- Engineered inputs that match known failure mechanisms such as mechanical power or the gap between process and air temperature.
- Probability calibration before any score is presented as a likelihood.
