# Latest audit-metadata verification — resolved

The latest saved-run audit and recovery changes were independently reviewed after integration. The reported partial-metadata crash is resolved: run_metadata fills legacy dependencies and timestamp defaults while validating metadata types. load_run now rejects empty or non-string source labels before returning a run. The UI therefore does not receive the two malformed values identified in the preceding review.

Saved result counts must be nonnegative integers and match the evaluated row count. Detection rate plus precision and F1 must agree with the confusion counts within a tight numerical tolerance. These checks cover both selection and final result groups. Recorded scikit-learn version mismatches are rejected and genuinely legacy audit details remain labeled unknown. New saves use unique paths and a temporary file in the same folder so saving again preserves earlier runs.

Source labels now distinguish generated included data from uploaded data whose origin is unverified. Reload failure retains the previous valid active run and presents a persistent error. Clearing the active model removes the run and recovery error. No new actionable defect was found in this scoped follow-up.

This was code verification only. The independent testing agent is running the suite so no duplicate full-suite run was performed. Earlier sections are retained as review history rather than open findings.

---
# Follow-up verification — resolved findings

The sections below this update preserve the initial review for traceability. They no longer describe open defects.

I re-read the updated core.py plus app.py and test_edge_cases.py along with test_saved_validation.py and test_regressions.py. The coordinator reports 64 passing Windows tests before the final chart formatting change. This follow-up is code verification rather than a second full-suite run.

| Initial finding | Current status and evidence |
|---|---|
| P1 tests overwrite production models | Resolved. An autouse fixture sets SIGNALREADY_MODEL_DIR to a fresh tmp_path for each edge-case test and redirects the cleanup variable there. The app uses MODEL_DIR for both save and listing. The other persistence tests use temporary paths or copied app directories. |
| P2 incomplete saved run crashes after reload | Resolved for the reported path. load_run checks required metadata plus model feature names and explanation support before returning. Session state assignment only occurs after successful validation. The temporary-app regression checks that an incomplete dictionary produces a friendly error without a UI exception. |
| P2 misleading explanation source and scales | Resolved. UI and docstring correctly say fitted training attributes. Method-specific notes distinguish forest split importance from coefficient magnitude and describe category scaling and missing coefficient direction. README explicitly says scores are not comparable across model families. |
| P2 tests reload arbitrary user file | Resolved by isolated per-test storage. Each affected test now sees only its own saved run. A multiple-run selection test remains optional coverage rather than an open defect. |
| P3 missing saved-model explanation disclosure | Resolved. Explanation tab now identifies saved-model provenance when loaded is true. |

The horizontal chart uses readable input labels while leaving scores unchanged. The updated CSV width checks plus normalization before duplicate checks preserve the evaluation design. Explicit L/M/H encoder categories come from the declared schema rather than held-out data. Prediction refuses an unobserved training product type. The final check remains outside model selection.

No additional P1 or P2 issue was identified within these scoped repairs. Structure checks are not a guarantee against every arbitrary malformed pickle and do not make untrusted joblib safe. The existing trusted-local restriction remains appropriate. Final runtime verification after the chart edit remains with the coordinating/testing agents.

---
# SignalReady quality review — September 25 2026

Review scope: current CODEX_HANDOFF.md plus app.py and core.py with the saved-run tests and README. This is a read-only code review apart from this report. The coordinating agent confirmed 46 tests passing in the pinned Windows environment. I did not repeat the suite because two tests still write into the user's model folder.

## Verdict

The bounded classification workflow remains aligned with the solo proposal. Its explanation view needs wording corrections. Saved-run validation and test isolation need repair before treating the application as fully verified.

## Actionable findings

### P1 — UI tests can overwrite a real saved model

Evidence: test_edge_cases.py:31 sets MODELS_DIR to the production app folder. Lines 276 and 321 click the real Save selected model locally button. core.save_run uses the dataset fingerprint as the filename and replaces an existing file at that path. Both tests train the included sample so they target the same filename as a normal user sample run.

The cleanup guard only preserves preexisting filenames. It does not preserve their bytes or timestamp after replacement. A stand-in saved run with a different filename surviving the suite does not cover this collision. The tests can also remove a newly saved user run created concurrently because cleanup treats every new filename as test-owned.

Fix: run UI tests against a temporary copied app/data directory or inject a temporary storage directory. Never glob or write production models during a test. Verify that an existing sentinel file at the exact sample fingerprint path remains byte-for-byte unchanged. This is a test-quality repair within current scope.

### P2 — Reload accepts incompatible saved contents and then crashes

Evidence: app.py:29 assigns joblib.load(choice) directly to session state. The catch only covers deserialization and assignment. A valid joblib containing a nonempty incomplete dictionary can load successfully. The subsequent results section accesses run['winner'] outside the catch. Other missing fields or an incompatible pipeline can fail in the explanation or prediction tab. These are compatibility failures as well as possible damaged-artifact failures. A truncated unreadable joblib is already caught.

Fix: load to a temporary variable and validate the expected fields and supported fitted pipeline before replacing the active run. Display the existing friendly failure message and retain a prior valid run when validation fails. Add regression coverage for an incomplete dictionary and an unsupported fitted estimator. This does not make untrusted joblib files safe to load. Keep the existing local trusted-artifact restriction.

### P2 — Explanation labels claim evidence that is not computed

Evidence: core.py:125-142 reads model attributes only. Random forest uses feature_importances_ and logistic regression uses absolute coefficients. It never reads selection observations. Yet app.py:144 plus core.py:129 and two README paragraphs say the explanation describes training and selection data.

The shared caption at app.py:150 also oversimplifies the two methods. Random forest values summarize training split improvements. Logistic values are coefficient magnitudes: the numeric inputs are standardized but one-hot product categories remain 0/1. Their bars are not held-out performance contributions and the two methods do not share an importance scale. The coefficient signs have been discarded so the view cannot identify whether a measurement raises or lowers the model score.

Fix: label the source as the fitted model trained on the training group. Use method-specific plain language. Explain that larger absolute logistic coefficients indicate a larger score change for a defined input change and that bars across the different methods should not be compared. For forest explain that the bars summarize training split usefulness and may favor some kinds of inputs. Keep the existing statement that these are not physical causes or repair instructions. No new explainer dependency is necessary.

### P2 — Reload tests depend on whatever saved run sorts first

Evidence: test_edge_cases.py:284-285 and 327-328 click Reload saved model without selecting their newly saved run. app.py sorts all model filenames and selects the first by default. If an unrelated saved run sorts first these tests fail despite correct product behavior or exercise the wrong run.

Fix: isolate the folder as above and explicitly select the target saved run. Include two temporary saved runs in one regression test to ensure the selected run is restored.

### P3 — Explanation tab lacks saved-run provenance

Results and prediction tabs correctly disclose that a saved run belongs to its original dataset. The explanation tab does not show that disclosure or the run fingerprint. A user can reload a run then switch to the flawed sample and see importance bars without an explanation that they belong to the older run.

Fix: repeat the saved-run notice or show a compact selected-model and dataset identifier in that tab.

## Requirement and accuracy checks

| Solo proposal commitment | Current evidence | Assessment |
|---|---|---|
| One dataset and fixed upload format | Six approved features plus Machine failure target | Met |
| Missing readings and duplicate checks | check_data blocks missing values and flags duplicates | Met |
| Exclude identifiers and failure-type answers | Explicit FEATURES allowlist used in training | Met |
| Two standard models | Logistic regression plus random forest | Met |
| Same reserved examples for model comparison | Both final metric dictionaries use the same X_test and y_test | Met |
| Preparation learned on training data only | Pipeline fitted on X_train only | Met |
| Final check does not select model | Winner determined from validation F1 before final predictions | Met |
| Baseline and maintenance-relevant errors | Always-no-failure row plus missed failures and false alarms | Met |
| Short global model explanation | Attribute-based explanation exists | Function present; wording fix needed |
| Local model saving and reloading | save_run plus sidebar reload | Happy path supported; incompatible artifact handling incomplete |
| Honest generated-data limitations | Main banner and prediction/report caveats | Met for included sample |
| Solo scope | No added cloud service or new model family | Preserved |

The explanation addition introduces no final-check leakage. The selected estimator is still fitted only on training rows. The classification output remains clearly distinct from forecasting when a machine will fail. No calibrated probability or actual factory-performance claim is present.

The original theme's agentic ambition remains a positioning gap rather than a newly introduced defect in the agreed solo prototype. The prior review's suggestion of a rule-based recommendation does not by itself establish autonomous agent behavior. The user decision is pending and this review does not require that addition. Do not let final-check results drive automatic model tuning.

## Verification limits

This review traces the current code rather than asserting a new full runtime test result. The Windows test result was supplied by the coordinating agent. Clean-machine launcher validation and a timed demo remain separate checks. Original submission deliverables such as a demo recording are not established by the application test suite.


