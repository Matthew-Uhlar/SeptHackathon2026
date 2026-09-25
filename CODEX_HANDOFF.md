# SignalReady Handoff to Codex

Prepared: September 24, 2026 by Claude (Cowork)
Supersedes the status sections of `CLAUDE_HANDOFF.md`. Read that file too for product goal, modeling design, product limits and contributor rules. Those are all still in force.

## Status at a glance

- Git repo initialized in this folder. Branch `master`. Work is committed in small steps. Run `git log --oneline` to see where things stand.
- Test suite: **43 passed** (15 original + 4 feature tests + 24 edge-case tests). See the caution under "Verification gap" below.
- `QUALITY_REVIEW.md` holds an independent review of the pre-change code. Its quick fixes are tracked in "Open work" below.

## What was done this session

Three parallel teams worked in the same folder with separate file ownership.

**Team A: feature development** (commit `8917ee7`)
- `core.explain(run)` returns feature importance for the selected model. Random forest uses `feature_importances_`. Logistic regression uses the absolute value of its coefficients so both rank the same way. Computed from the fitted model only and never from the final check.
- New tab "4  What drove the model" shows a bar chart plus a table. Wording repeats that this shows model behavior and not physical cause.
- `data/bad_sample.csv` is a 56-row flawed fixture in the AI4I format with one blank reading and one duplicate example. Sidebar option "Try a flawed sample" loads it to demo the data-readiness errors.
- `core.text_report(run)` builds a plain-text report. A second download button "Download results report (readable)" sits next to the JSON one.
- "PROTOTYPE — generated data, not a live equipment connection." caption appears in the sidebar saved-runs area, the results tab and the prediction result.
- README Demo and Modeling decisions sections updated.

**Team B: quality review** (`QUALITY_REVIEW.md`)
- Pass: claims fit synthetic data. Final check is untouched by model selection (verified line by line). Classification is kept separate from forecasting.
- Concern: the "agentic" part of Theme 1 is not present. The workflow is linear and button driven. This needs a decision from Matt (see Open work).
- Concern: `st.success` on a no-failure prediction reads as "all clear." Prediction tab lacks the saved-run disclosure. Saved-run picker shows bare hex names.
- Other: no BOM test. `CLAUDE_HANDOFF.md` breaks its own comma rule twice.

**Team C: edge-case testing** (commit `6f14278`, `test_edge_cases.py`)
- Covers malformed CSV and non-UTF-8 CSV and empty files. Multiple missing columns. Empty and nonnumeric values. Invalid Type labels. Row count and class size limits. Below-range and multi-column out-of-range predictions. `public_report` on a reloaded run. Streamlit tab state after training and reload. JSON download content. Changing the data source after a reload.
- No product bugs found. Behavior to know: after a saved run is reloaded, switching the data source keeps the loaded run. This is intentional and labeled in the results tab.

## Open work (in priority order)

Check `git log` first. Items marked DONE below were finished after this file was first written.

1. Quality-review quick fixes:
   - [ ] Prediction tab: no-failure result uses `st.info` rather than `st.success`.
   - [ ] Prediction tab: show a saved-run disclosure when `loaded` is true.
   - [ ] Saved-run picker: human-readable label with save time.
   - [ ] Regression test for a UTF-8 BOM CSV.
   - [ ] Add `.venv-ci/` to `.gitignore` (leftover folder that could not be deleted from the Linux bridge; delete it on Windows).
2. **Decision needed from Matt:** how to answer the "agentic" part of Theme 1. Option A is to reframe README and pitch as a tool-assisted studio where a person approves each step for trust and auditability. Option B is one small rule-based recommendation step after the comparison. Do not build Option B without Matt's approval. Keep it rule based with no new dependencies if approved.
3. Verify on Windows with the pinned `requirements.txt` (see Verification gap).
4. Verify `Start SignalReady.bat` on a clean Windows machine and time the five-minute demo from `CLAUDE_HANDOFF.md`.
5. Fix the two comma-before-"and" sentences in `CLAUDE_HANDOFF.md`.
6. Still deferred on purpose: time-aware evaluation. Do not add it.

## Verification gap

All test runs this session happened in a Linux shell with Python 3.10. The pinned versions need Python 3.11+ so the tests ran on pandas 2.3.3 and scikit-learn 1.7.2 (streamlit 1.64.0 and joblib 1.6.0 matched). Run the suite once on Windows with the real `.venv` before trusting the 43-pass result:

```powershell
.venv\Scripts\python -m pytest -q
```

## Environment notes

- On Windows run everything natively as in `CLAUDE_HANDOFF.md`. The notes below only matter from a Linux bridge.
- `.pytest_cache` in this folder was unreadable from the Linux bridge and broke pytest collection. Workaround used: rsync the folder to a scratch copy and run pytest there. On Windows you can delete `.pytest_cache` safely.
- Stale `.git/*.lock` files appeared because the bridge could not unlink files. They are cleared now. If `git` reports a lock and no git process is running it is safe to remove it.
- Repo-local git identity is set to Matt's email. Global git config was not touched.

## Rules carried forward

Keep the local bounded scope. Never tune using final-check results. Never claim the data represents ABB equipment. Plain text with no comma directly before "and." A regression test for every bug fix. Update README when model choices or setup change. Run the full suite after each change. Only load joblib files the app created in its own `models` folder.
