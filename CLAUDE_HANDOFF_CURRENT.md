# SignalReady handoff to Claude

> Superseded: CODEX_HANDOFF_CURRENT.md (September 25 2026) records later Claude work. The first-save refresh and data correction guidance items below are finished there with 110 tests passing on Linux.

Updated September 25 2026 by Codex. This supersedes the status sections in CLAUDE_HANDOFF.md and CODEX_HANDOFF.md. This is a live checkpoint.

## Product and constraints

Continue the bounded local SignalReady prototype for ABB Accelerator Theme 1. Use plain language with no comma immediately before the word and. The solo proposal budgets roughly 40 hours for one person with basic Python experience. The app checks a fixed equipment CSV format and compares logistic regression with random forest. It saves the selected model and classifies new readings.

Data is generated UCI AI4I equipment data. Do not claim real equipment validation or time-to-failure forecasting. The app is a guided studio with deterministic selection. It does not implement an autonomous agent. A user question about optional rule-based recommendations is pending. Continue existing-scope fixes without inventing approval for that optional addition.

## Verified checkpoint

- Native Windows Python 3.12.14 in .venv.
- Pinned Streamlit 1.64.0 / scikit-learn 1.9.1 / pandas 3.0.6 / joblib 1.6.0.
- Full suite: 92 passed in 17.81 seconds after audit metadata and session recovery changes. A first-save sidebar refresh fix and bounded data correction guidance are being developed after this checkpoint. Re-run before treating those as verified.
- pip check: no broken requirements.
- Batch launcher started successfully on port 8502 in the existing environment. Temporary verification server was stopped. This does not prove fresh-machine installation.
- Existing app remained at http://127.0.0.1:8501/. Browser checks verified flawed sample blocking and training plus the final horizontal explanation chart with readable labels and correct axes.
- Independent reviewer confirmed all five findings in QUALITY_REVIEW_2026_09_25.md resolved. Independent regression tests: 9 passed.

## Changes completed by Codex

1. Closed Claude's Windows verification gap: the 46-test baseline passed with actual pinned dependencies.
2. CSV parsing rejects short or overwide rows before pandas can silently pad or reindex them. Blank and duplicate headers are rejected.
3. Numeric values normalize before duplicate/conflicting-label checks and training deduplication. Numeric text cannot bypass those checks.
4. Encoder uses the predefined L/M/H schema. Rare valid types in selection or test rows no longer crash training. observed_types records training coverage. Prediction abstains for a type absent from training.
5. load_run validates trusted local artifact structure before assignment to session state. Validation handles incomplete saved dictionaries but does not make untrusted joblib safe.
6. UI catches expected training/prediction errors and save failures with readable messages.
7. Save/reload tests use SIGNALREADY_MODEL_DIR set to a temporary folder. They no longer overwrite real saved runs. The prior cleanup protected filenames but could still overwrite same-fingerprint files.
8. Explanations correctly describe fitted training attributes. Model-specific caveats distinguish impurity-based forest importance from absolute logistic coefficients. Product indicators have a different scale from standardized numeric inputs.
9. Explanation chart has horizontal bars and readable labels plus tooltips. Saved explanations disclose original dataset context.
10. README documents guided-studio scope. DEMO_GUIDE.md supplies a four-minute outline. Launcher explains a missing environment and accepts optional Streamlit arguments.
11. New runs record format 1 plus source label and training timestamp in UTC with Python/scikit-learn/NumPy/pandas/joblib versions. Reports preserve metadata. Legacy metadata stays explicitly unknown. Unsupported formats and mismatched scikit-learn versions are rejected.
12. Saves use unique UUID filenames and a temporary file before rename. Earlier saves are preserved. Picker labels distinguish same-data saves. Failed writes remove partial temporary files.
13. Failed reloads retain the previously active model with a persistent error and dataset identity. Clear active model removes session state without deleting saved artifacts.
14. Saved-run validation rejects invalid audit fields and inconsistent metric values. Each confusion matrix must sum to its group size. Rates must agree with counts. A regression covers a null source label that previously crashed the UI.
15. Readable reports now include all final confusion counts and F1 plus selection F1 scores and model-specific explanation limitations. Uploads are described as unverified rather than assumed synthetic.

## Code map

- app.py: Streamlit UI with four tabs and local session state.
- core.py: parsing / validation / training / prediction / persistence / explanations / reports.
- data/ai4i2020.csv: original UCI synthetic sample. Credit and license in README.
- data/bad_sample.csv: intentionally flawed demonstration fixture.
- test_core.py and test_edge_cases.py: baseline and feature/UI tests.
- test_regressions.py: independent defect reproductions.
- test_saved_validation.py: trusted-local compatibility tests.
- test_run_metadata.py: legacy/audit compatibility and save/metric integrity.
- test_session_recovery.py: failed reload and session clearing.
- README.md: setup and assumptions.
- DEMO_GUIDE.md: demo outline and remaining owner tasks.
- QUALITY_REVIEW_2026_09_25.md: reviewed findings and resolution status.
- SESSION_STATUS.md: short checkpoint.

Git repository is inside SignalReady. Baseline commit: 7ea547c. Current Codex changes are uncommitted at this checkpoint. Inspect git status and git diff before editing. Preserve user work. No remote publication or contest submission has been performed.

## Commands

Run inside SignalReady:

```powershell
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m pip check
.venv\Scripts\python -m streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

Or use Start SignalReady.bat. For a fresh environment follow README. Do not stop another process just to free port 8501. Use an alternate port for an isolated test.

## Model rules

Inputs: Type plus air temperature / process temperature / rotational speed / torque / tool wear. Target: Machine failure. IDs and failure-mode labels never enter training.

Normalized identical examples are deduplicated before seeded 60/20/20 splits. Preprocessing fits only training. Selection F1 chooses the winner before final evaluation. Threshold stays 0.5. Do not tune on final results or refit after selection. Keep the always-no-failure baseline.

Random row splits do not validate future periods or unseen machines. Global explanations do not establish causes or explain single predictions. Do not present uncalibrated outputs as failure probabilities.

## Next work

1. Finish and test the first-save sidebar refresh fix. Live browser verified that the previous implementation saved successfully but required another interaction before showing the saved-run picker.
2. Finish bounded row/column data-correction guidance and class balance display. Development agent owns new core helper/tests while coordinator owns UI integration.
3. Refresh this handoff with final full-suite count and known remaining work. Do not confuse an earlier passing checkpoint with a later untested edit.
4. Fresh-machine Windows installation and a human-timed recording remain unverified. Do not infer these from the local automated tests.
5. Participant identity / repository publication / demo recording / portal upload remain owner tasks. Recheck event requirements before asserting deadlines.
6. Optional agentic/recommendation direction requires the user's answer. A rule set alone would not establish autonomous agent behavior.

## Cautions

.venv-ci is not empty. It contains a Linux environment and was left in place. Do not delete it based on the earlier handoff's description.

Only load trusted app-produced joblib files. Pickle can execute before compatibility validation. No uploaded file should reach load_run.

The edge suite hooks Streamlit's mock media storage to inspect downloads. Review this if upgrading Streamlit. Save tests must remain isolated from user artifacts.

## Usage instruction

The user asked to keep developing until the usage limit and write a Claude handoff. Update this file at stable milestones because a hard limit can prevent a final write. Do not redeem a reset credit without explicit authorization. At the last check usage remained available. Do not claim the limit was reached unless it actually was.
