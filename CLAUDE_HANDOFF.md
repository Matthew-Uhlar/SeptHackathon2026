# SignalReady Development Handoff

Prepared: September 24, 2026

## Purpose

Continue development of SignalReady for the ABB Accelerator 2026. SignalReady is a local machine learning app for checking equipment data and comparing two failure classification models. The app is an idea phase prototype. It uses generated sample data and does not make claims about real equipment safety or the timing of a future breakdown.

## Product goal

Help an engineer with basic Python experience follow a small and understandable workflow:

1. Load the included equipment data or upload a CSV with the same columns.
2. Check the data for blocking problems.
3. Train and compare two standard machine learning models.
4. Review failures found, failures missed, and false alarms.
5. Save the selected model locally.
6. Enter a new set of readings and receive a classification with an out of range warning when appropriate.

The solo scope is intentional. Keep the prototype local and bounded before adding integrations or extra model types.

## Current project layout

- `SignalReady/app.py` — Streamlit user interface and session flow.
- `SignalReady/core.py` — CSV parsing, data checks, model training, metrics, prediction, and local save logic.
- `SignalReady/data/ai4i2020.csv` — downloaded UCI AI4I 2020 sample dataset.
- `SignalReady/fetch_data.py` — downloads the public sample dataset.
- `SignalReady/test_core.py` — 15 automated tests covering core validation and the Streamlit workflow.
- `SignalReady/requirements.txt` — pinned Python dependencies.
- `SignalReady/README.md` — setup, modeling decisions, data credit, and limitations.
- `SignalReady/Start SignalReady.bat` — Windows launcher.
- `SignalReady/.streamlit/config.toml` — local theme and upload limit.
- `SignalReady/models/` — created at runtime for locally saved `.joblib` runs and intentionally ignored by Git.

The working app was previously opened at `http://127.0.0.1:8501/`.

## Setup on Windows

From the `SignalReady` folder:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python fetch_data.py
.venv\Scripts\python -m streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

For this workspace the existing environment is `SignalReady/.venv`. The app can also be started by double-clicking `Start SignalReady.bat`.

Run tests with:

```powershell
.venv\Scripts\python -m pytest -q
```

Verified before this handoff: `15 passed`.

## Current modeling design

Required inputs are `Type` plus these five numeric readings:

- `Air temperature [K]`
- `Process temperature [K]`
- `Rotational speed [rpm]`
- `Torque [Nm]`
- `Tool wear [min]`

Target: `Machine failure` where `0` means no failure and `1` means failure.

The app excludes identifiers and failure mode columns. It rejects missing values, invalid types, negative readings, conflicting labels, too few examples, duplicate headers, and files outside the 50 to 50000 row range. Exact duplicate input and target rows are removed before splitting.

The current split is a fixed seeded random split:

- 60% training
- 20% model selection
- 20% final check

Preprocessing fits only on training rows. The two models are class-balanced logistic regression and a random forest. F1 on the selection group chooses the winner. The final group is evaluated after selection. The default prediction threshold remains 0.5. The baseline row always predicts no failure.

The app reports:

- failures found
- failures missed
- false alarms
- correct no-failure readings
- failure detection rate
- warnings that were correct
- F1

Saved runs include the trained model, metrics, row counts, split indices, approved feature names, training ranges, a data fingerprint, and the random seed. The app only loads locally created model files from its own `models` directory. It does not accept uploaded model files.

## Important product limits

Do not describe this prototype as a real predictive maintenance system. It is a generated-data classification demonstration.

- The dataset is synthetic and does not prove factory performance.
- Random row splits do not validate future-time forecasting or unseen equipment.
- The app does not estimate warning lead time.
- The app does not provide calibrated failure probabilities.
- The app does not connect to live machines.
- The app does not authorize maintenance work or identify a repair.
- The app supports one fixed CSV format.

Dataset credit: AI4I 2020 Predictive Maintenance Dataset, UCI Machine Learning Repository, DOI `https://doi.org/10.24432/C5HS5C`, CC BY 4.0.

## Recommended next development

Prioritize changes that improve trust and demo clarity:

1. Add a model explanation view based on the training or selection data. Keep the wording clear that feature importance shows model behavior and does not prove physical cause.
2. Add a small built-in “bad file” demo fixture with missing values or a duplicate row so the data-readiness screen can be demonstrated without editing the UCI file.
3. Add a download-ready human-readable results report that includes dataset fingerprint, model choice, split sizes, metrics, and limitations.
4. Add a visible “prototype only” label to the prediction result and saved-run view.
5. Consider a time-aware evaluation mode only after the data assumptions support it. Do not add it just to make the app sound more industrial.

## Quality review still needed

An independent quality review was requested against the original ABB brief and the solo proposal but could not run because the delegated environment hit its usage limit. Recheck:

- alignment with Theme 1 Agentic Predictive Maintenance Studio
- whether all claims remain appropriate for synthetic data
- whether the 40-hour solo scope is preserved
- whether upload errors and saved-run state are understandable
- whether the final check remains untouched by model selection
- whether the app clearly separates classification from real failure forecasting

## Testing review still needed

An independent UI and edge-case testing team was also requested but could not run because of the same usage limit. Test at minimum:

- malformed CSV and non-UTF-8 CSV
- duplicate headers
- missing required columns
- empty numeric values and nonnumeric values
- invalid product type and target labels
- conflicting labels for identical features
- too few rows or too few examples in one class
- changing the selected input after a saved run is loaded
- save and reload of a model
- prediction values outside the training range
- Streamlit tab state after training and after reload
- download of the JSON results report

## Handoff rules for future contributors

- Preserve the bounded local scope until the core demo is stable.
- Do not tune a model using final-check results.
- Do not claim the synthetic dataset represents ABB equipment.
- Keep user-facing text plain and avoid commas immediately before the word “and.”
- Add a regression test for every bug fix.
- Update `README.md` when model choices, data assumptions, or setup steps change.
- Run the full test suite after each meaningful change.
- Keep saved model loading limited to locally produced artifacts. Joblib files can execute code when loaded so never widen this to arbitrary uploads.

## Definition of done for the next handoff

The next contributor should leave the app with the existing 15 tests passing plus tests for every new feature. The app should run from the launcher on a clean Windows machine with the setup instructions. The demo should show data warnings, a fair model comparison, a saved model reload, a prediction, and a clear limitation statement within five minutes.
