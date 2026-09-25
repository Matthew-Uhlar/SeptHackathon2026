# SignalReady test report (testing team)

Prepared September 25 2026. The testing team exercised the integrated app like a demanding user and a QA engineer. It then added `test_acceptance.py`. No other repository file was changed. Nothing was committed and nothing was written into ./models.

## Environment

- Linux container with 4 CPUs. Python 3.11.15 in a throwaway venv with the pinned requirements: streamlit 1.64.0 / scikit-learn 1.9.1 / pandas 3.0.6 / numpy 2.4.6 / joblib 1.6.0 / pytest 9.1.1. Playwright with headless Chromium build 1194.
- Commits: exploratory browser testing started at **6d7058b**. The fix team committed 0b5d9c3 to 2059626 during testing, including the `data_issue_examples` gate (quality finding Q3). All findings below were rechecked at **2059626**. The final suite ran at 2059626 plus the new test file.
- App under test: `streamlit run app.py --server.port 8540 --server.headless true` with `SIGNALREADY_MODEL_DIR` pointed at a scratch folder. Streamlit tables are canvas elements so their contents were read with AppTest (`streamlit.testing.v1`, default_timeout=60).
- Screenshots and the Playwright scripts live in the session scratch folder under `testing/shots` (6d7058b) and `testing/shots2` (2059626). They are not part of the repository.

## What was tested

1. The full demo path in a real browser: flawed sample → included sample → train → Model comparison (summary / completion checks / downloads / How this run was checked) → What drove the model → save → page refresh → reload → Try a prediction (defaults / torque 65 with tool wear 210 / speed 1300 with torque 65 / air temperature 310) → batch scoring of data/new_readings.csv → Compare saved runs. A 390-pixel-wide viewport was also checked.
2. Exploratory edge cases through AppTest and the browser: 18 malformed or partial training uploads / an extra column identical to the target (plain / inverted / text / lower-case name) / 10 batch files (missing column / all rows invalid / header only / 5,000 and 5,001 rows / text numbers / quoted numbers / non-UTF-8 / empty) / switching the data source after training and after reload / clearing the active model / completion checks on a reloaded run while a different file or no file is selected / tab state after every action / repeated saves / corrupt `.joblib` files and a folder named `.joblib` / a saved file deleted while the app is open.
3. Downloads: the JSON report / the readable report / the scored-readings CSV compared with the screen.
4. Accessibility and wording: labels / error messages / any sentence that reads as a probability / cause / forecast claim.
5. Performance: first load / training / every tab switch / completion checks / save / reload / prediction / batch scoring.

## Results

| Area | Result | Evidence |
|---|---|---|
| Slide 10: known bad inputs receive clear warnings | Pass | Flawed sample: 2 blocking errors / row 10 Air temperature [K] located / train button disabled. 11 bad uploads each give a specific error and no run (`test_slide10_known_bad_inputs_receive_clear_warnings`). |
| Slide 10: answer columns never enter training | Pass | IDs and TWF / HDF / PWF / OSF / RNF excluded. An extra column equal to the target (also inverted / as text / lower-case name) is flagged as a giveaway and kept out of the fitted model (`test_slide10_answer_columns_never_enter_training`). |
| Slide 10: both models use the same final examples | Pass | Every final-table row sums to 2,000 with 68 failures. Stored final indices are disjoint and reproduce the winner's metrics exactly. |
| Slide 10: reloading preserves predictions | Pass | Refresh then reload gives identical predictions and scores on all 2,000 final rows. Prediction form scores match the original model. All six live checks Passed after reload. |
| Demo path in the browser | Pass with one visual bug (B1) | No console errors. Reference values in DEMO_SCRIPT.md reproduce: 52 found / 16 missed / 40 false alarms / Torque then Rotational speed / 1300 rpm with 65 Nm flagged / air 310 out of range / batch 29 scored / 4 flagged / 3 outside / 2 skipped. |
| Completion checks in the UI | Pass | Six rows Passed on the matching file. Repeat check reads Not checked on a reloaded run while the flawed sample or no file is selected. Detail text is truncated on screen (UX 3). |
| Downloads | Pass | JSON equals `public_report(run)`. Every model row in the readable report matches the on-screen table. Scored CSV equals `score_batch` output and its counts match the metrics. |
| Tab state | Pass | Train → Model comparison. Downloads / save / prediction / batch upload keep the open tab. Refresh returns to Data readiness (expected). Reload stays on Data readiness (UX 5). |
| Training upload edge cases | Pass except B3 | Non-UTF-8 / UTF-16 / binary / ragged rows / repeated or blank headers / missing columns / text numbers / negative / bad type / bad label / too few rows all rejected with a specific message. UTF-8 BOM with CRLF (Excel "CSV UTF-8") is accepted. |
| Batch scoring edge cases | Pass | Missing column and >5,000 rows give clear errors. Invalid rows are skipped with reasons. Exactly 5,000 rows are scored. An empty or all-invalid file shows zeros without a warning (UX 9). |
| Saved runs | Pass except B5 / B6 / B7 | Repeated saves keep every file and select the newest. Corrupt files are listed as "Could not be loaded" and do not break the app. |
| Wording | Pass | Automated scan of every rendered heading / text / caption / alert found no probability / chance / confidence / cause / forecast claim outside a negated sentence. |
| Accessibility basics | Pass with notes | Every input has a visible label with units. Alerts carry text rather than colour alone. The chart has a table alternative. Key disclaimers are small grey captions (UX 13). |
| Full test suite | Pass | **245 passed / 1 skipped / 5 xfailed in 127 s** (251 collected). No ./models folder was created. |

## Bugs

Severity reflects impact on the submission demo and judging. Each open bug has a strict xfail test in test_acceptance.py so the suite stays green while documenting it.

| ID | Severity | Steps to reproduce | Expected | Actual | Suggested fix |
|---|---|---|---|---|---|
| B1 | **High** | Fresh page (empty model folder is fine) / Included sample / Check and compare models / then immediately Save selected model locally without any other click. | One tab bar and one results block. | A second tab bar appears above the "Active model" caption (in some runs a stale copy of the results block with an empty table box also appeared above it). It stays through later tab clicks until the page is refreshed. Screenshots `12_dup_top.png` / `11_after_save_tabs.png` / `11_reload_after_delete.png`. Visiting another tab before saving avoids it, which is why DEMO_SCRIPT section order does not hit it. | The Save handler calls `st.rerun()` inside the tab while the number of elements above `st.tabs` changes between runs (the training notice goes away and the Saved notice arrives). Streamlit does not clear stale elements from an interrupted run. Preferred: move Save (and ideally Train) into `on_click` callbacks like `run_checks` so no mid-script `st.rerun()` is needed. Alternative: keep the elements above the tabs fixed with one `st.container()` created before the tabs for notices / reload errors / the active-model caption, or show notices with `st.toast`. Verify with `SIGNALREADY_BROWSER_TESTS=1 pytest -k browser`. |
| B2 | Medium | Upload a 50,000-row file with one empty cell (the documented maximum). Click any tab. | A tab switch in well under a second. | `data_issue_examples` loops cell by cell with `.iloc`: 12.4 s on every rerun. The clean-file case was fixed in 19ac460 (2.6 s → skipped). | Vectorize it: build one boolean problem mask per column with pandas / take the first 20 positions in row-major order with `np.argwhere`. Or cache it with `st.cache_data` keyed by the upload fingerprint. |
| B3 | Low | Upload the sample with Machine failure written as True/False (pandas `to_csv` of a bool column). | Either accepted or one clear message such as "Use 0 or 1 rather than TRUE / FALSE". | Blocking error "At least 10 unique examples of each outcome are required" while the line below says "17 failure examples ... and 583 no-failure examples". `value_counts().get(0)` does not match a boolean index. | In `check_data` convert the normalized target to float before counting (or reject booleans explicitly with the message above). |
| B4 | Low | Select Try a flawed sample. | "1 repeated example will be removed..." | "1 repeated examples will be removed..." on the demo's first data screen. | Pluralize in `check_data`. |
| B5 | Low | Put a run saved with another scikit-learn version in the model folder. Reload it. | The specific reason from `load_run`, which already says "This saved model used a different scikit-learn version. Train a new run with the current app." | A generic "could not be loaded" message. | In the Reload handler show `str(exc)` for `ValueError` and keep the generic text for other exceptions. |
| B6 | Low | With no active model reload a corrupt file. | Message without a claim about a previous model. | "Any previously active model remains selected." It then stays on every screen until a run is trained or reloaded. | Only add that sentence when a run is active. Clear the error when the data source changes. |
| B7 | Low | Save two runs. While the app is open delete the selected file from the model folder. Click any tab then Reload saved model. | A note that the selected run is gone. | The picker silently falls back to another file and "Saved run restored" loads a different run. (Under AppTest the stale selection makes `run_label` raise FileNotFoundError.) | Before the selectbox: if `saved_run_choice` is not in `saved` pop it and show a caption. Let `run_label` tolerate a missing file. |
| B8 | Low | Reload a run / select Included sample / Run completion checks (six Passed) / switch to Try a flawed sample. | The table either clears or states which file it was checked against. | The table keeps showing "Repeat run gives the same results: Passed" while the text above says the repeat check uses the selected file. | Store the input fingerprint with the results and hide or relabel them when it changes. No xfail test because the current behaviour is arguably a record of the earlier check. |

Also confirmed from the quality review: one missing cell produces two blocking messages so the flawed sample shows "Blocking issues 2" (QUALITY_REVIEW_PHASE2 Q14).

## UX input ranked by impact on the demo and judging

1. **Fix B1 before recording.** A duplicated tab bar right after Save is the most visible defect a judge could hit on the README path.
2. **Hide Streamlit's Deploy button.** It shows in the toolbar on every screen. Clicking it offers Streamlit Community Cloud deployment. That contradicts the "no cloud service" scope and invites confusion with the "one-click deployment" theme item. Add `[client]` / `toolbarMode = "viewer"` to .streamlit/config.toml.
3. **Make the completion-check evidence readable.** The Detail column is cut off after about 60 characters in the canvas table (`03_completion_checks.png`). These sentences are the slide 10 proof. Render them with `st.table` or as one markdown line per check with Passed / Not checked first.
4. **Calm the Data readiness screen for the clean sample.** Four long yellow "Possible answer giveaway" boxes plus a yellow "Extra columns are excluded" box make good data look broken and push the green Ready message and the train button below the fold (`02_included_ready.png`). Use one info box: "4 excluded columns look like answer giveaways and are kept out of training: HDF / OSF / PWF / TWF" with the evidence in an expander.
5. **Open Model comparison after Reload saved model** (as training does) and show the restore message in the main area. Today only a sidebar message and a small caption change.
6. **Warn before discarding an unsaved run.** Switching the data source (even a brief flip to Upload a CSV) silently drops a trained run that was not saved.
7. **Readable saved-run labels.** The sidebar picker truncates "Run 1dcd9c32 / 6fea1b | saved 20…" so two saves look identical. Lead with model and time, for example "Random forest · 25 Sep 22:57 · 6fea1b". The label uses local file time while the comparison table uses UTC. Say which.
8. **Keep the score from reading as a percentage.** "Model score (uncalibrated) 0.707" is the largest number on the prediction screen. Lead with the flag and band sentence and show the score smaller, or label it "not a probability" in the metric itself.
9. **Batch results.** Warn and expand the skipped-rows list when no rows are scored. Hide the download for an empty result. Put the run identity (model / dataset fingerprint / trained time) into the scored CSV or its file name. Include skipped rows with their reason so the file accounts for every input row. Whole numbers are written as 1553.0.
10. **Error messages that say what to do next.** Missing columns: add "Rename the headers to match exactly or use the AI4I layout". Detect a semicolon-separated file and say so. An empty upload shows "Choose the included sample or upload a CSV to begin" rather than "The file is empty". A whitespace-only last line is rejected as "Row N has 1 fields".
11. **Self-contained reports.** Add the plain-language summary and the completion-check results to the readable report. Add the fingerprint to the download file names.
12. **Small wording.** "Ready for the demo workflow" also appears for uploaded files ("Ready to compare models"). The column profile shows the word None for text columns. The tab name "What drove the model" hints at causation where the header already says "rely on".
13. **Accessibility.** Important limits (PROTOTYPE / not a physical cause / uncalibrated) sit in small grey captions. Consider normal-size text for at least the prediction disclaimer.

## Performance

Browser times are click-to-idle with Playwright and include a fixed wait of about 0.7 s in the harness. AppTest times are server-side script runs.

| Step | Browser at 6d7058b | Browser at 2059626 | AppTest at 2059626 |
|---|---|---|---|
| First page load (included sample) | 4.4 s | 1.9 s | 2.1 s |
| Switch to flawed / included sample | 1.1 / 3.2 s | 1.1 / 1.2 s | 0.13 s rerun on flawed |
| Train both models (click to results) | 8.4 s | 2.4 s | 1.3 s (core.train 0.86 s) |
| Tab switch (12 samples) | 3.5 to 4.6 s | 1.0 to 1.2 s | 0.33 to 0.38 s rerun |
| Run completion checks | 8.0 s | 2.7 s | 1.7 s (checks alone 1.5 s) |
| Save | 6.4 s | 1.5 s | 0.8 s |
| Page refresh / reload saved run | 3.9 / 3.8 s | 1.3 / 1.2 s | |
| Check these readings | 4.3 s | 1.2 s | what_if 0.16 s |
| Batch scoring 31 rows | 4.3 s | 1.2 s | score_batch 31 rows 0.08 s / 5,000 rows 0.17 s |
| data_issue_examples | 2.6 s on the clean 10,000-row sample (now skipped) | | 12.4 s at 50,000 rows with one bad cell (B2) |

The fix in 19ac460 removed most of the lag. Every interaction on the sample now feels immediate apart from training and completion checks, which show a spinner or finish in about two seconds.

## test_acceptance.py

46 tests. They run in about 50 s on their own.

- Demo path (shared session): flawed sample located / giveaways and outcome balance / training opens Model comparison / metrics and narrative match the run / How this run was checked / downloads match the screen / explanation uses approved inputs only / six completion checks Passed.
- Slide 10: 11 parametrized bad uploads / answer columns with a target-copy column / same final examples / reload preserves predictions.
- Reloaded run: default / high-torque (both demo variants) / out-of-range predictions / batch scoring against the download / 6 batch edge cases / completion checks with a different file or no file / Compare saved runs / no probability, cause or forecast claims.
- Session edge cases: switching the data source / clearing the active model / repeated saves / corrupt saved files.
- Strict xfails: B2 / B3 / B4 / B5 / B6. The opt-in browser test for B1 (`SIGNALREADY_BROWSER_TESTS=1`) also fails as expected: "2 tab bars on the page after saving".

Run with `python -m pytest -q test_acceptance.py`. Do not export `SIGNALREADY_MODEL_DIR` for the full suite because test_regressions.py expects it unset (quality finding Q15).

## Resolution

Added September 25 2026 by the deliverables and compliance team after the fix round. The fixes landed in commit **85255c2** ("Fix testing-team bugs B1-B8 and top UX findings"). At that commit the suite has 253 tests. The 252 that run by default passed on Linux (252 passed / 1 skipped in 115 s, rerun independently by this team). The skipped test is the opt-in browser check for B1. The coordinator reports that it also passed with `SIGNALREADY_BROWSER_TESTS=1`. The five former strict xfail tests now pass as ordinary regression tests.

### Bugs

| ID | Status | Fix | Covering test |
|---|---|---|---|
| B1 | Fixed | Train / save / reload / clear run as button callbacks so no mid-script `st.rerun()` is needed. | test_acceptance.py::test_browser_save_right_after_training_shows_one_tab_bar (opt-in: `SIGNALREADY_BROWSER_TESTS=1`) |
| B2 | Fixed | `data_issue_examples` is vectorized with NumPy. It runs only when a blocking error exists. | test_acceptance.py::test_issue_locator_is_fast_on_the_largest_allowed_file (50,000 rows in under 3 s) |
| B3 | Fixed | `check_data` counts the normalized target as float so True/False labels count as 1/0. | test_acceptance.py::test_bool_labels_do_not_produce_contradictory_messages |
| B4 | Fixed | The warning now reads "1 repeated example will be removed". | test_acceptance.py::test_single_repeated_example_warning_is_grammatical |
| B5 | Fixed | A failed reload shows the specific reason from `load_run`. | test_acceptance.py::test_failed_reload_explains_the_reason |
| B6 | Fixed | The "previously active model remains selected" sentence appears only when a run is active. | test_acceptance.py::test_failed_reload_without_active_model_does_not_mention_one |
| B7 | Fixed | If the selected saved file disappears the sidebar says so instead of switching to another run. `run_label` tolerates a missing file. | test_integration_ui.py::test_deleted_saved_run_is_reported_instead_of_silently_switching |
| B8 | Fixed | Completion-check results store the input fingerprint and are marked out of date when the selected file or active run changes. | test_integration_ui.py::test_completion_checks_are_marked_stale_after_the_file_changes |

### UX input

| Item | Status | Change |
|---|---|---|
| 1 Fix B1 before recording | Done | See B1. |
| 2 Hide the Deploy button | Done | .streamlit/config.toml sets `[client]` `toolbarMode = "viewer"`. |
| 3 Readable completion-check evidence | Done | Results render with `st.table` (Check / Result / Detail) so the Detail text wraps. |
| 4 Calm Data readiness for the clean sample | Done | One blue information line names the flagged columns. The evidence moved to the "Why these columns look like answer giveaways" expander. |
| 5 Open Model comparison after reload | Done | A successful reload switches to Model comparison with a restored message in the main area. |
| 6 Warn before discarding an unsaved run | Not done | Open. |
| 7 Readable saved-run labels | Not done | Open. |
| 8 Keep the score from reading as a percentage | Not done | Open. The metric label and note still say "uncalibrated" and "not the chance". |
| 9 Batch results polish | Not done | Open. The download column is now named "Model score (uncalibrated)" and formula-like ID text gets a leading apostrophe but the listed items remain. |
| 10 Error messages that say what to do next | Not done | Open. |
| 11 to 13 | Not done | Open. Lower priority. |

Other changes in the same round: "Final check kept separate" also confirms the fitted data preparation saw only the training rows. "Known bad inputs receive clear warnings" requires both a blocking error and the repeated-example warning. "Both models use the same final examples" now says the counts are consistent with one shared final group. The plain-language summary says an uploaded file's origin has not been verified. Answer-giveaway evidence now says a column "may record the answer or be filled in after the outcome" and a tolerant text rule was added. Features are frozen after this commit.
