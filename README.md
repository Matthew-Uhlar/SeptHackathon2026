# SignalReady

A local maintenance modeling prototype for the ABB Accelerator idea proposal.

## Challenge alignment

SignalReady implements a guided modeling studio for Theme 1. A person starts each step and reviews the results. Model selection follows a fixed rule. The current prototype does not implement an autonomous agent or an AI chat copilot. Its contribution is a small auditable workflow for data readiness and model comparison. Broader agent behavior remains future work.

## Start on this computer

Double-click **Start SignalReady.bat**. Keep the terminal open while using the app.

## Set up elsewhere

Use Python 3.12. Run these commands inside this folder:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python fetch_data.py
.venv\Scripts\python -m streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

## Demo

1. Select the included sample, or select Try a flawed sample to see a small built-in file with a missing reading and a repeated example.
2. Review the data-readiness report. IDs and failure-type labels are excluded. The flawed sample shows how blocking errors and warnings appear before training is allowed. A correction table lists up to 20 problem cells by data row and column without repeating their values. The outcome balance line counts failure and no-failure examples after repeats are removed.
3. Choose Check and compare models.
4. Open Model comparison to inspect missed failures and false alarms. A PROTOTYPE label near the results is a reminder that this uses generated data rather than a live equipment connection.
5. Download the results report as JSON or as a plain-text readable report with the same fingerprint, model choice, split sizes, metrics and a limitations paragraph.
6. Open What drove the model to inspect fitted model attributes learned from training examples. This shows model behavior and is not a physical cause of failure.
7. Save the selected model locally. Restart the app and reload it from the sidebar.
8. Open Try a prediction to enter readings with the displayed units. The same PROTOTYPE label appears next to the result.

## Modeling decisions

The only inputs are product type and five equipment measurements. The target is Machine failure. Identical input and target examples are removed before splitting. Conflicting labels for identical inputs block training. Missing readings block training so the user must correct them explicitly.

The fixed random split reserves 60% for training plus 20% for model selection and 20% for a final check. Each group preserves the class balance. Preprocessing fits only on training rows. Two fixed models use class balancing. F1 on the selection group chooses the winner before the app evaluates final examples. The models use the default 0.5 threshold. They are not refit after selection. No final-test tuning is performed.

This is a generated-data classification demo. Random row splits do not validate future-time forecasting or generalization to unseen equipment. The app makes no claim about warning lead time or calibrated failure probabilities. It is not connected to industrial equipment. A PROTOTYPE label appears next to a prediction result and next to a saved or loaded run as a reminder.

The What drove the model tab uses fitted training attributes without evaluating selection or final-check examples. Logistic regression shows absolute coefficient sizes. Numeric inputs are standardized but product-type indicators use 0 or 1 so they have different scales. Random forest shows impurity-based importance which can favor inputs with more possible values. The scores are model-specific and should not be compared across model families. Neither method establishes cause or explains an individual prediction.

CSV rows must match the header width. Numeric values are normalized before duplicate and conflicting-label checks. The encoder declares the fixed L/M/H schema without learning categories from held-out rows. Prediction rejects a product type absent from training examples rather than guessing its behavior.

The data/bad_sample.csv file is a small built-in fixture with the same required columns as the real sample. It intentionally contains a missing required reading and a repeated example so the data-readiness checks can be demonstrated without editing the UCI file.

Saved models use joblib and must only come from this local app. Do not place untrusted model files in the models folder. The app does not accept uploaded model files. Uploaded CSV data is held in memory. Saving a run stores a model plus evaluation metadata and a data fingerprint locally.

Reloading checks the saved run's structure before using it. This detects incomplete artifacts but does not make an untrusted joblib file safe. Loaded results and explanations retain their original dataset identity when the selected input file changes.

New saved runs record their training time in UTC plus a format version and software versions. The data source distinguishes included generated examples from unverified uploads. Older runs display unknown audit details. Unsupported formats or incompatible scikit-learn versions require a new training run. Each save creates a separate file so earlier runs are preserved.

If a reload fails the app keeps the previous active model and displays its identity with a persistent error message. Clear active model removes it from the current session without deleting saved files. Readable reports include all final-check metrics plus selection scores and the explanation limitations.

## Data credit

AI4I 2020 Predictive Maintenance Dataset (2020). UCI Machine Learning Repository. https://doi.org/10.24432/C5HS5C

License: CC BY 4.0 https://creativecommons.org/licenses/by/4.0/

The included sample preserves the original downloaded file. Its equipment readings are synthetic. Cleaning occurs only in the training workflow.

## Tests

```powershell
.venv\Scripts\python -m pytest -q
```

UI save/reload tests set `SIGNALREADY_MODEL_DIR` to a temporary folder. They must never touch the user's actual saved runs. That environment variable is a local test/deployment setting and is not exposed as a file upload option.
