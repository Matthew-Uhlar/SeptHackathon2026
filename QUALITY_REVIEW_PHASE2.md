# SignalReady quality review (phase 2: integrated app)

Prepared September 25 2026 by the quality and accuracy team. This is an independent skeptical review of the integrated application against the idea-phase proposal and the official Theme 1 criteria in PROPOSAL_CRITERIA.md. It also checks the machine learning and every claim the app makes.

- Code reviewed at commit 6d7058b (app.py / core.py / profiling.py / narrative.py / completion_checks.py / inference.py / make_results_summary.py). Commit 0b5d9c3 changed only PROPOSAL_CRITERIA.md and CODEX_HANDOFF_CURRENT.md.
- Documents reviewed in the working tree. During this review the deliverables team had uncommitted edits in README.md / PROJECT_SUMMARY.md / TECHNICAL_DOCUMENTATION.md / COMPLIANCE_REVIEW.md / SUBMISSION_CHECKLIST.md / DEMO_GUIDE.md / DEMO_SCRIPT.md. Document findings below refer to that working-tree state and may already be superseded.
- Verification used Linux Python 3.11 with the pinned requirements in a throwaway venv. Scripts ran from a scratch folder. Nothing was written into ./models. No Streamlit server was started.
- This review changed no file other than this one.

## Summary verdict

**Sound and honest. Ready to submit after a small set of fixes.** No leakage or honesty violation was found in the model workflow. Every model rule in CLAUDE_HANDOFF_CURRENT.md holds in code and was confirmed numerically on the included sample. The numbers in RESULTS_SUMMARY.md / the narrative / the demo script reproduce exactly. No user-facing string calls the score a probability / confidence / likelihood. No user-facing string has a comma immediately before "and".

There are no P1 findings. The most important P2 items are:

1. The results narrative tells users that **uploaded** data is "generated equipment data" (narrative.py:139). That is a factual misstatement for any upload.
2. The answer-giveaway rule **misses a text "failure type" column** when the label has a little noise. This is the most common real-world form of this giveaway (profiling.py:119).
3. **Every rerun costs about 2.5 to 3 seconds on the sample** (about 13 seconds at 50,000 rows) because `data_issue_examples` scans every cell in Python even when the file is clean. Tab switches and every button trigger a rerun (app.py:125). A one-line gate removes it without changing behavior.
4. The committed demo video (demo/SignalReady_demo.mp4, commit 982cd8b) predates the integration commit. Several documents now point to it as the demo. It must be re-recorded or confirmed before submission.

Test suite: 192 passed on Linux in an isolated copy (see "Test run" below).

## Findings

Severity: P1 = must fix before submission (breaks a rule or misleads) / P2 = should fix (visible inaccuracy or notable gap) / P3 = polish.

| ID | Sev | File:line | Finding | Evidence | Recommended fix |
|---|---|---|---|---|---|
| Q1 | P2 | narrative.py:139 to 141 | The closing sentence always says "These results come from generated equipment data split into random rows." It is shown for uploaded files too. The app labels those "Uploaded CSV (origin not verified)" (app.py:154). The sentence then states something the app cannot know. | Trained on a 1,500-row upload labeled `Uploaded CSV (origin not verified)`. `results_summary` still ended with "These results come from generated equipment data". | Branch on `run.get('source_label')`: keep the current sentence for `UCI AI4I generated sample`. Otherwise say "These results come from the supplied data split into random rows. Its origin has not been verified." Add a test in test_narrative.py. |
| Q2 | P2 | profiling.py:118 to 120 (`_text_evidence`) | The text rule requires every repeated value to appear with only one outcome. One noisy value blocks the whole column. A "Failure type" column like the Kaggle version of AI4I (No Failure / Heat / Power / Overstrain / Tool Wear / Random) is not flagged because 9 "No Failure" rows are labeled failures and 18 "Random" rows are labeled no failure. | Built that column from TWF / HDF / PWF / OSF / RNF on the sample. `answer_giveaway_columns` returned no entry for it. The crosstab shows Heat 115/0 / Power 91/0 / Overstrain 78/0 / Tool Wear 46/0 failures only. | Mirror the numeric nonzero rule for text: flag when one or more repeated values (support of at least 5) have a failure share of at least 95% and together cover no more than half of the labeled rows. Keep the current rule as a second path. Word the evidence as counts only so no text value is echoed. Add a test with a noisy failure-type column. |
| Q3 | P2 | app.py:125 / core.py:122 to 155 | `data_issue_examples` loops over every cell with `.iloc` when the file has no problems. The whole data tab reruns on every tab switch (`on_change='rerun'`, app.py:106) and on every button. | Timed on the sample: read_csv 0.05 s / check_data 0.02 s / giveaway 0.10 s / profile 0.03 s / **data_issue_examples 2.56 s (2.86 s on an idle machine)**. A 50,000-row file took 14.6 s for the whole data tab. | In app.py:125 call it only when there are blocking errors: `examples = data_issue_examples(df, limit=ISSUE_EXAMPLE_LIMIT) if report['errors'] else []`. Every problem it can report also produces a `check_data` error so the output is unchanged. |
| Q4 | P2 | demo/SignalReady_demo.mp4 / PROJECT_SUMMARY.md / SUBMISSION_CHECKLIST.md / COMPLIANCE_REVIEW.md | The committed video was added in 982cd8b before the features were wired into app.py (6d7058b). Working-tree docs now call it the demo. demo/record_demo.py has uncommitted edits so a re-record appears to be in progress. | `git log -- demo/SignalReady_demo.mp4` shows only 982cd8b. | Re-record from the frozen app. Watch it end to end. Commit the new file before pointing the portal at it. |
| Q5 | P3 | completion_checks.py:73 to 83 | "Both models use the same final examples" only checks that each model's counts add up to the final group size with the same number of actual failures. That is necessary but not sufficient. The losing model is not saved so its predictions cannot be rechecked. | Code review. Any two confusion tables with equal totals and equal positives pass. | Keep the name from the proposal. Reword the detail: "Every row in the final table covers the same 2000 readings with the same 68 actual failures. This is consistent with one shared final group. The repeat run check retrains both models on it." |
| Q6 | P3 | completion_checks.py:161 to 171 | "Known bad inputs receive clear warnings" only asserts that the flawed sample has at least one blocking error. Both reported errors come from the same missing cell. The repeated-example warning is never checked so a broken duplicate detector would still pass. The check also does not involve the active run. | `check_data(bad_sample)` gives 2 errors (empty cell / "Air temperature [K] must contain finite numbers") plus the warning with `duplicates == 1`. | Also require `report['duplicates'] > 0` and a warning. Mention in the detail that it uses the built-in flawed file. |
| Q7 | P3 | completion_checks.py:86 to 102 | No check covers the slide 7 promise "Keep data preparation within the training portion". It is true in code but the live checks do not show it. | Verified separately: scaler `n_samples_seen_` = 6000 = training count. Scaler `mean_` equals training-row means and differs from all-row means. | Fold it into "Final check kept separate" so there are still six checks: pass only when `scaler.n_samples_seen_ == counts['training']`. When the file matches, also compare `mean_` with the training rows. |
| Q8 | P3 | profiling.py:159 to 162 | The giveaway sentence says the pattern "suggests this column records the answer rather than a reading taken beforehand". Plausible legitimate columns also trigger it: a strong sensor (Vibration with AUC 1.00) / a pre-alarm flag with 98% precision / a row counter in a file sorted by label. The column is excluded either way so the only effect is the message. | All three synthetic columns were flagged at strength of at least 0.97. | Soften: "Such strong agreement suggests this column may record the answer or be filled in after the outcome. If it is a genuine reading taken beforehand it could be a future input. This is a pattern in the file rather than proof of a cause." |
| Q9 | P3 | inference.py:144 / 162 / app.py:268 | The batch table and the downloaded CSV use the column name "Model score". The uncalibrated note is a caption that does not travel with the file. Passed-through Product ID text is written unchanged. A value starting with `=` / `+` / `-` / `@` becomes a spreadsheet formula when opened. | Batch output kept a `=cmd|x` Product ID unchanged. | Rename the column to "Model score (uncalibrated)" (update test_inference.py:203 / 215). Prefix a `'` to passed-through ID text that starts with `=` / `+` / `-` / `@` before download. |
| Q10 | P3 | TECHNICAL_DOCUMENTATION.md:54 | "The fingerprint is a SHA-256 hash of the cleaned and deduplicated training table." It hashes the whole cleaned table after duplicates are removed. That includes all three groups and the excluded columns (core.py:201). | Code review. RESULTS_SUMMARY.md already says "SHA-256 of the cleaned rows". | "...a SHA-256 hash of the whole cleaned file after repeated examples are removed. It covers every group and the excluded columns." |
| Q11 | P3 | app.py:187 | "These checks confirm the promises this workflow makes for the active run." Q5 / Q6 show that one check is a consistency check and one does not use the active run. | Code review. | "These checks retest the proposal's completion promises. Most use the active run. The bad-input check uses the built-in flawed sample. The repeat check retrains on the selected file when it matches the run." |
| Q12 | P3 | app.py:144 | "Only rows marked Input or Target are used for training." The table rows are columns of the data file. A reader can confuse them with data rows. | UI text. | "Only columns marked Input or Target are used for training." |
| Q13 | P3 | app.py:245 / app.py:248 / inference.py:24 | The what-if table also swaps the product type but the text only mentions training averages. COMPLIANCE_REVIEW.md lists the same point. | `what_if` adds a `type H` / `type M` row. | Use the replacements already suggested in COMPLIANCE_REVIEW.md. |
| Q14 | P3 | core.py:94 to 101 | One missing numeric cell produces two blocking messages (empty cell / "must contain finite numbers in every row"). The flawed sample shows "2 blocking issues" for a single problem. | `check_data(bad_sample)['errors']`. | Skip the finite-number message for a column whose only non-finite values are missing. Check test_edge_cases.py for exact error-count assertions before changing. |
| Q15 | P3 | test_regressions.py:86 | The test copies app.py to a temporary folder and expects `models/` beside it. It fails when `SIGNALREADY_MODEL_DIR` is set in the shell because the app then reads that folder instead. | Failed with the variable set. Passed alone without it. | Add `monkeypatch.delenv('SIGNALREADY_MODEL_DIR', raising=False)` at the start of the test. |
| Q16 | P3 | core.py:397 to 399 / inference.py:297 to 312 | Batch validation and `core.predict` agree on every row class tested: missing / invalid type / leading space in type / negative / infinite / text in a number / unseen type. The only difference is text in a number. `core.predict` then raises Python's raw "could not convert string to float" message. The UI form cannot send text so users never see it. | 8-row comparison script. | Optional: wrap the `float()` calls in core.predict with a clear message. Keep the two rule sets in sync (the handoff already warns). |
| Q17 | P3 | app.py (several) | Streamlit prints a deprecation warning for `use_container_width` on each dataframe. The pinned 1.64.0 still works. | Test log. | No action before the deadline. Replace with `width='stretch'` only when upgrading Streamlit. |

## Leakage and evaluation integrity (item 1)

| Rule from CLAUDE_HANDOFF_CURRENT.md | Result | Evidence |
|---|---|---|
| Deduplicate normalized examples before the seeded 60/20/20 split | Holds | core.py:182 to 188. `split_indices` are positions in the deduplicated frame. 6000 / 2000 / 2000 on the sample with no overlap. |
| Preprocessing fits on training rows only | Holds | Pipeline fit on `X_train` (core.py:194). Checked: scaler `n_samples_seen_` = 6000 and `mean_` equals training-row means (differs from all-row means). |
| Selection F1 picks the winner before final evaluation | Holds | core.py:197 then 199. Winner Random forest at 0.570 against 0.243. |
| Threshold 0.5 / no refit / no tuning on final results | Holds | `predict` only. On the 2,000 final rows `predict` equals `score > 0.5` for the winner. No score was exactly 0.5. |
| Uncalibrated outputs never presented as probabilities | Holds | Grep of app.py and the four modules finds "probab" / "chance" only in the negative ("not the chance"). Metric label "Model score (uncalibrated)". |
| Global explanations do not claim cause | Holds | core.py:309 to 310 / app.py:276 / narrative and giveaway text say "pattern" / "model behavior". |
| What-if training averages use training rows only | Holds | inference.py:253 to 255 reads the fitted scaler `mean_`. Numerically equal to the training rows. |
| Ranges and observed types from training rows only | Holds | core.py:206 to 207. Recomputed from the training indices. |
| Profiling / giveaway / class balance influence training | They do not | They read the whole file for display only. Training uses `core.FEATURES` only. |

Completion checks (does each test what its name says?):

| Check | Tests what it claims? | Can it pass vacuously? |
|---|---|---|
| Answer columns never enter training | Yes. Recorded and fitted input names must equal the six approved inputs. | Only in the sense that any `core.train` run passes. Tampering fails it (test_completion_checks.py). |
| Both models use the same final examples | Partly (Q5). Totals and positives only. | Yes for any two tables with equal totals and positives. |
| Final check kept separate | Yes for row groups. Does not show preprocessing (Q7). | Returns Not checked for legacy runs without indices rather than passing. |
| Repeat run gives the same results | Yes. Retrains and compares winner / both groups' metrics / counts / indices / final predictions. | No. Not checked when the file differs. |
| Reloading preserves predictions | Yes. Temporary save then `load_run`. With the matching file it reproduces the recorded final metrics. Otherwise 729 grid readings. | No. |
| Known bad inputs receive clear warnings | Partly (Q6). Uses the fixed fixture. "Clear" is not tested. | Yes if duplicate detection broke. |

The repeat-run fingerprint helper (`completion_checks.clean_frame` / `data_fingerprint`) repeats core.py:182 to 185 and 201 step for step. It matched the stored fingerprint on the sample. The only difference: it skips `check_data`. That cannot create a false match because a file that fails the checks never produced a run.

## Answer-giveaway detection (item 2)

- On the sample it flags TWF / HDF / PWF / OSF at strength 1.0 through the nonzero rule. UDI / Product ID / RNF are not flagged. RNF is correctly left alone: its nonzero rows are mostly labeled no failure.
- Rules are deterministic with sensible support minimums. Edge inputs did not crash: boolean columns / 10^18 values / mixed text and numbers / all-empty columns.
- False negative: Q2.
- False positives with misleading wording: Q8. Harmless in effect because the column is excluded either way.
- Mostly-zero 0/1 flag: flagged only when at least 95% of its nonzero rows are failures. A flag at 77% precision was correctly not flagged.
- No causal claim: the text ends with "a pattern in the file rather than proof of a cause".

## Narrative (item 3)

Every number in the sample narrative was recomputed. Winner F1 0.570 against 0.243 / 2000 final readings / 68 failures / found 52 missed 16 / 92 warnings with 40 false alarms / 52 of 92 = 0.565 rounds to "about 6 of every 10" / baseline 1932 of 2000 = **96.6% (correct)** / Logistic regression found 4 more (56 against 52) with 286 more false alarms (326 against 40). The comparison is fair: it states the trade-off and does not switch models after the final check. Tie / zero-warning / zero-failure / dominance / legacy / small-count cases each have a template and a test. The only error found is Q1.

## Inference (item 4)

- `score_band` follows the flag first. On all 2,000 final rows no band contradicted the flag. Random forest ties at 0.5 are not flagged and are labeled "Near the 0.5 threshold".
- SCORE_NOTE is accurate: uncalibrated / 0 to 1 / threshold 0.5 / balanced weighting raises scores / not the chance of failure.
- What-if sign is correct: base minus variant, so positive means the current value raises the score. The caption says the same.
- Batch validation matches core.predict in rule and priority (Q16). The range test is inclusive in both. UDI and Product ID pass through. Other ID-like columns are dropped silently.
- Demo reference values reproduce: 1300 rpm with 65 Nm gives flag 1 / score 0.626 / "Well above". The top what-if row is Torque (+0.543, flag would change). Air temperature 310 is outside the range. The default readings give score 0.000 with every change below 0.001. data/new_readings.csv gives 29 scored / 4 flagged / 3 outside / 2 skipped (rows 30 and 31).

## Proposal versus build (item 5)

| Slide | Promise | Status | Evidence |
|---|---|---|---|
| 2 | Show data warnings | Delivered | core.py:check_data / data_issue_examples / app.py:117 to 141 |
| 2 | Columns that give away the answer | Delivered | core.py:FEATURES excludes them. profiling.py:answer_giveaway_columns warns (app.py:123). Gap Q2. |
| 2 | Explain missed failures alongside false alarms | Delivered | core.py:metrics / narrative.py:results_summary |
| 3 | Load sample or matching file | Delivered | app.py:44 to 86 / core.py:read_csv |
| 3 | Warnings on missing or repeated readings | Delivered | core.py:check_data |
| 3 | Compare two models on reserved examples | Delivered | core.py:train |
| 3 | Save a model and use it for a new prediction | Delivered | core.py:save_run / load_run / inference.py:model_score |
| 3 | User stays in control of each step | Delivered | Every step is a button. Nothing runs by itself. |
| 4 | File loading with clear warnings / two models / everyday-language results / prediction form with saving | Delivered | As above plus narrative.py |
| 4 | One local app / one format / no live machine / no cloud or chatbot | Delivered | .streamlit binds 127.0.0.1. No network calls. Batch scoring uses the same format. |
| 5 | Public UCI data credited / no timing claim | Delivered | Sidebar credit app.py:47 to 48. Banner app.py:41. |
| 6 | Python / Streamlit / pandas / scikit-learn / prepared text | Delivered | requirements.txt / narrative.py fixed templates |
| 7 | Remove IDs and failure-type columns | Delivered | core.py:FEATURES / check_answer_columns |
| 7 | Reserve 20% for the final check | Delivered | core.py:187 |
| 7 | Data preparation within training | Delivered. Not shown live | Verified numerically. Q7 would show it. |
| 7 | Compare with always no failure | Delivered | core.py:200 / narrative baseline sentence |
| 7 | Report found / missed / false alarms. No score promised | Delivered | The per-reading uncalibrated score is not a performance promise so it does not conflict. |
| 8 | Error tests and repeat runs | Delivered | Test suite / completion_checks.py:check_repeat |
| 8 | Setup guide and demo | Setup delivered. Demo pending | README / TECHNICAL_DOCUMENTATION. Video predates integration (Q4). |
| 9 | Stop new features after Sep 23 | Not followed | Features added Sep 25. Mitigation: freeze now. |
| 9 | Drop the importance chart first | Not needed | Chart kept with limits stated. |
| 9 | Misleading results / limited evidence / unexpected inputs | Delivered | Baseline row / banner / read_csv errors / batch skip reasons |
| 10 | Demo: known-problem file / clean run / explain mistakes / reload for prediction | Delivered in app | data/bad_sample.csv / sidebar reload. Video pending. |
| 10 | Four completion checks | Delivered live plus two extras | completion_checks.py. Q5 and Q6 are partial strength. |
| 11 | App / source with credit / setup guide and summary / video and results summary | Delivered except video | RESULTS_SUMMARY.md reproduces exactly. Repository visibility is an owner task. |

## Theme 1 and judging criteria (item 6)

| Theme 1 item | Evidence | Gap |
|---|---|---|
| Dataset profiling and quality assessment | read_csv / check_data / data_issue_examples / class_balance / profile_columns / answer_giveaway_columns | Q2. No per-column distribution chart. |
| Intelligent task and model selection | Fixed F1 rule on the selection group. Narrative explains it. | Two fixed models. Rule-based rather than adaptive. |
| Preprocessing and feature engineering | Training-only scaler and fixed L/M/H encoder | No engineered features (future scope). |
| Model training and evaluation | Seeded stratified split / baseline / six live checks | Random rows only. |
| Explainable AI with importance and confidence | Global importance / what-if / uncalibrated score | Not calibrated so not a statistical confidence. Stated honestly. |
| Experiment tracking and comparison | Audit metadata / saved-run table / repeat check | Local files only. |
| One-click deployment | One-click local save and validated reload | No serving endpoint (ruled out by the proposal). |
| Prediction and inference dashboard | Single form with score and what-if / batch CSV with download | None for scope. |

| Criterion (weight) | Strength | Gap | Best quick win |
|---|---|---|---|
| Innovation (20%) | Mistake-first framing / giveaway detection / live proposal checks | Standard models | QW4 (catch the noisy failure-type column) |
| Technical excellence (25%) | Leakage-safe pipeline verified numerically / validated reloads / large test suite | No MLflow / SHAP / FastAPI | QW6 (show training-only preparation live) / QW7 |
| Problem-solution fit (20%) | Every Theme 1 item at least partly covered | Not agentic by design | Keep the honest guided-studio framing |
| Scalability and feasibility (15%) | Batch scoring up to 5000 rows / clear upgrade path | 13 s reruns at 50,000 rows | QW2 |
| User experience (10%) | Plain language / guided tabs / skip reasons | 2.5 to 3 s lag on every click | QW2 |
| Presentation and demo (10%) | Timed script / reproduced reference values | Video predates integration | QW1 |

## Ranked quick wins (each under one hour)

Each stays inside the proposal scope (local app / user in control / no chatbot) and the honesty rules.

1. **Re-record and commit the demo video from the frozen app (Q4).** Required submission item and 10% of the score. Owner or coordinator.
2. **Gate `data_issue_examples` on blocking errors (Q3).** One line in app.py:125. Removes about 2.5 to 3 s from every click and tab switch on the sample. Output is unchanged. About 10 minutes with a rerun of test_data_guidance_ui.py.
3. **Make the narrative's closing sentence source-aware (Q1).** Fixes the only factual misstatement found in the UI. About 15 minutes with a test.
4. **Add a tolerant text path to the giveaway rule (Q2).** Strengthens the feature judges are most likely to see as original. About 40 minutes with a test.
5. **Wording fixes in one pass (Q8 / Q11 / Q12 / Q13 / Q10).** About 20 minutes. Rerun tests that match text.
6. **Show training-only preparation in the "Final check kept separate" check (Q7).** Keeps six checks. About 30 minutes with a test.
7. **Strengthen the bad-input check (Q6) and reword the same-examples detail (Q5).** About 15 minutes.
8. **Label the batch score column as uncalibrated and neutralize formula-like IDs (Q9).** About 20 minutes including test updates.
9. **Isolate test_regressions.py:86 from the environment variable (Q15).** About 5 minutes.

Recommended cut if time is short: 1 / 2 / 3 / 5. Freeze after that and rerun the full suite on Windows.

## Plain-language rule and user-facing text (items 7 and 8)

- `grep -nE ",[[:space:]]+and\b"` over app.py / core.py / profiling.py / narrative.py / completion_checks.py / inference.py / make_results_summary.py and all submission documents found no match. A multiline search for a string ending in a comma followed by a string starting with "and" also found none. The integration test asserts the same for the narrative.
- Stale integration markers: none remain in the working tree (`COORDINATOR` / "being integrated" / "Needs integration" / "No score" were all resolved by the in-flight edits). They were still present in committed README.md / PROJECT_SUMMARY.md / TECHNICAL_DOCUMENTATION.md / COMPLIANCE_REVIEW.md / SUBMISSION_CHECKLIST.md at 0b5d9c3. **Commit the working-tree doc edits** or the pushed repository will contradict the app (for example TECHNICAL_DOCUMENTATION.md step 7 at 0b5d9c3 says "No score or probability is shown").
- The remaining document inaccuracy is Q10.

## Items verified as correct

- RESULTS_SUMMARY.md: every value reproduces with the pinned versions (fingerprint `1dcd9c32…` / 6000 / 2000 / 2000 / both tables / narrative / six Passed checks).
- PROJECT_SUMMARY.md (working tree): 52 of 68 / 40 false alarms / 96.6% are correct.
- DEMO_SCRIPT.md reference values: 339 failures (3.4%) / Torque then rotational speed in importance (0.312 and 0.307, close) / 1300 rpm and 65 Nm score about 0.63 / new_readings.csv 29 / 4 / 3 / 2.
- The app never trains on anything outside `core.FEATURES`. Giveaway warnings say the column "is already excluded", which is true.
- Out-of-range warnings use training-row minimum and maximum inclusively in both single and batch paths.
- Completion checks run in about 2 seconds on the sample and never write into ./models (TemporaryDirectory).
- `saved_run_table` survives corrupt files and lists them as "Could not be loaded".

## Test run

Full suite in an isolated copy of the code and data at 6d7058b (so no test could touch ./models): **192 passed in 258 seconds**. No models folder was created in the copy. This confirms the 192 count quoted in the working-tree docs. An earlier run with `SIGNALREADY_MODEL_DIR` exported in the shell failed test_regressions.py:86 (Q15). That is a test isolation issue and not an app defect.

## Not verified

- Windows-native test run and the Start SignalReady.bat launcher.
- The live browser UI (no Streamlit server was started). UI behavior was judged from code and AppTest results.
- The content of the demo video and any re-recording in progress.
- The uncommitted document edits by the deliverables team beyond the lines quoted here. They were changing during this review.
- Repository visibility / portal requirements / eligibility (owner items).
