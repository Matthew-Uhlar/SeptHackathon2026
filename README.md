# SignalReady

A local maintenance modeling prototype for the ABB Accelerator idea proposal.

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

1. Select the included sample.
2. Review the data-readiness report. IDs and failure-type labels are excluded.
3. Choose Check and compare models.
4. Open Model comparison to inspect missed failures and false alarms.
5. Save the selected model locally. Restart the app and reload it from the sidebar.
6. Open Try a prediction to enter readings with the displayed units.

## Modeling decisions

The only inputs are product type and five equipment measurements. The target is Machine failure. Identical input and target examples are removed before splitting. Conflicting labels for identical inputs block training. Missing readings block training so the user must correct them explicitly.

The fixed random split reserves 60% for training plus 20% for model selection and 20% for a final check. Each group preserves the class balance. Preprocessing fits only on training rows. Two fixed models use class balancing. F1 on the selection group chooses the winner before the app evaluates final examples. The models use the default 0.5 threshold. They are not refit after selection. No final-test tuning is performed.

This is a generated-data classification demo. Random row splits do not validate future-time forecasting or generalization to unseen equipment. The app makes no claim about warning lead time or calibrated failure probabilities. It is not connected to industrial equipment.

Saved models use joblib and must only come from this local app. Do not place untrusted model files in the models folder. The app does not accept uploaded model files. Uploaded CSV data is held in memory. Saving a run stores a model plus evaluation metadata and a data fingerprint locally.

## Data credit

AI4I 2020 Predictive Maintenance Dataset (2020). UCI Machine Learning Repository. https://doi.org/10.24432/C5HS5C

License: CC BY 4.0 https://creativecommons.org/licenses/by/4.0/

The included sample preserves the original downloaded file. Its equipment readings are synthetic. Cleaning occurs only in the training workflow.

## Tests

```powershell
.venv\Scripts\python -m pytest -q
```
