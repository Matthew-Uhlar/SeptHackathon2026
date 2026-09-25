# SignalReady handoff to Codex

Updated September 25 2026 by Claude (cloud session). This supersedes the status sections of CLAUDE_HANDOFF_CURRENT.md. Product rules / model rules / cautions in that file remain in force. This is a live checkpoint that is rewritten at each stable milestone because a usage limit can end the session without warning.

## Where the work lives

- Repository: matthew-uhlar/septhackathon2026. Working branch: `claude/jolly-fermi-9zawua`. Pull it before continuing. No pull request has been opened.
- Codex's previously uncommitted work was committed by Matt as 317c9fa "Pushing Local work to Git". Run `git log --oneline 317c9fa..` to see Claude commits.

## Verified checkpoint

- Linux Python 3.11.15 with the pinned requirements.txt versions in a throwaway venv.
- Before any Claude edit: 105 passed.
- After Claude's changes: **110 passed** in 142 seconds (105 + 2 class balance tests + 2 guidance UI tests + 1 second-save test).
- Live browser check (headless Chromium through Playwright against `streamlit run` on port 8517 with SIGNALREADY_MODEL_DIR pointed at a temporary folder):
  - Flawed sample shows "Where to correct the file" with Data row 10 / Air temperature [K] / Missing value. That matches line 11 of data/bad_sample.csv.
  - Outcome balance for the flawed sample reads 13 failure examples (23.6%) and 42 no-failure examples.
  - Saving into an empty model folder shows the Saved local runs picker and Reload button with no extra interaction. **The first-save sidebar refresh item is verified.**
  - The user stays on Model comparison after saving (see fix 3 below).
- The Windows .venv was not available to Claude. Re-run `.venv\Scripts\python -m pytest -q` natively before treating these changes as Windows-verified.

## Done by Claude

1. `core.class_balance(df)` counts No failure / Failure / Unusable labels among unique normalized examples (same deduplication as training). Returns None when required columns are missing. Tests in test_data_guidance.py.
2. Data readiness tab shows a "Where to correct the file" expander (up to `ISSUE_EXAMPLE_LIMIT = 20` rows from `data_issue_examples`: Data row / Column / Problem, never the cell value) plus an outcome balance line. Tests in test_data_guidance_ui.py.
3. Found in the browser: after Save the rerun inserted elements above the tabs and Streamlit reset the view to tab 1. `st.tabs` now uses `key='active_tab', on_change='rerun'` so the open tab survives reruns. Switching tabs now triggers a rerun which is cheap because training only runs on its button. AppTest cannot click tabs so this is covered by the browser check only.
4. test_session_recovery.py gained a second-save regression: the newest save becomes the picker selection and the first save is kept.
5. README and DEMO_GUIDE mention the correction table and outcome balance.

## Still open

- Windows-native test run of Claude's changes.
- Fresh-machine Windows install and a human-timed demo recording remain unverified.
- Participant identity / publication / recording / portal upload remain owner tasks. Recheck event requirements before asserting deadlines.
- Optional agentic or rule-based recommendation direction still needs Matt's answer. Do not implement without it.
- Done: after training the app switches to Model comparison through a `switch_tab` request applied before the tabs render. The one-time success message uses `st.session_state.notice`. Test in test_session_recovery.py.

## Team round (in progress)

Matt asked for three development teams plus a quality team and a testing team with Claude overseeing. PROPOSAL_CRITERIA.md holds the idea-phase deck content. Matt supplied a PDF of the HackerEarth page. Its rules / judging weights / submission items / Theme 1 list are now in PROPOSAL_CRITERIA.md. Deadline: Sep 27 4:59 PM Central (the page's timeline graphic says Sep 28). Three development agents were launched in the background with strict new-file ownership. If this handoff still says in progress, check whether their files exist and whether their tests pass before integrating:

- Team A: profiling.py + test_profiling.py: profile_columns / answer_giveaway_columns / saved_run_table (experiment tracking).
- Team B: narrative.py / completion_checks.py / make_results_summary.py -> RESULTS_SUMMARY.md plus tests.
- Team C: inference.py + test_inference.py: model_score with an uncalibrated-score note / what_if per-prediction sensitivity / score_batch for CSV scoring.
- Team 4 (deliverables and compliance): may edit README / DEMO_GUIDE / PROJECT_SUMMARY / TECHNICAL_DOCUMENTATION and create SUBMISSION_CHECKLIST / THIRD_PARTY_NOTICES / DEMO_SCRIPT / COMPLIANCE_REVIEW. No code edits.
- Coordinator integrates the modules into app.py. PROJECT_SUMMARY.md and TECHNICAL_DOCUMENTATION.md (submission items 1 and 5) are drafted. Update their module map after integration.
- Quality team reviews against PROPOSAL_CRITERIA.md and the official rules. Testing team adds test_acceptance.py and TEST_REPORT.md.

Stay within the guided-studio framing. The deck says the user stays in control and rules out a separate chatbot.

## Dev team results (committed 982cd8b, NOT yet wired into app.py)

- profiling.py: profile_columns(df) / answer_giveaway_columns(df) (flags TWF HDF PWF OSF at strength 1.0; UDI / Product ID / RNF not flagged) / saved_run_table(folder).
- narrative.py: results_summary(run) -> list[str]. completion_checks.py: completion_checks(df, run, repeat=True) -> six checks with Passed True/False/None (about 1.7 s with repeat). make_results_summary.py writes RESULTS_SUMMARY.md.
- inference.py: model_score / score_band(score, flag) / SCORE_NOTE / what_if / WHAT_IF_NOTE / score_batch(run, df) / batch_summary. Batch validation duplicates core.predict rules in `_row_problems`; update both if core changes.
- All AppTest instances use default_timeout=60 (3-second default failed under load). Full suite 188 passed on Linux.
- Also done: Apache 2.0 LICENSE + NOTICE. master fast-forwarded to the branch at Matt's request (keep master in sync at verified milestones). demo/record_demo.py produces a captioned MP4. demo/SignalReady_demo.mp4 is an interim recording of the pre-integration UI; re-record after integration.
- Next: integrate into app.py (Data readiness: giveaway warnings + profile expander; Model comparison: narrative + completion checks button + saved-run table; Try a prediction: score / band / what-if + batch CSV scoring). Then update docs at `<!-- COORDINATOR` markers / re-record video / quality + testing teams.

## Team 4 results (committed 7984413 and 64e5d4f)

- Deliverables: PROJECT_SUMMARY / TECHNICAL_DOCUMENTATION / README / DEMO_GUIDE updated. New DEMO_SCRIPT / SUBMISSION_CHECKLIST / THIRD_PARTY_NOTICES / COMPLIANCE_REVIEW.
- Docs contain `<!-- COORDINATOR: update after integration -->` markers where Team A/B/C features must be added once wired into app.py. Search for that string after integration.
- Coordinator applied UI wording fixes: prediction disclaimer / dataset creator credit (S. Matzka, from agent knowledge because the UCI site is blocked) / explanation header. Kept "MAINTENANCE DATA ASSISTANT" because the idea deck uses that subtitle.
- Owner actions: repo is private and work is on a non-default branch / record video / confirm eligibility and solo entry / decide AI-assistance note and license / portal upload before Sep 27 4:59 PM Central.

## Reproducing Claude's checks on Linux

```bash
python3 -m venv venv && venv/bin/pip install -r requirements.txt playwright
venv/bin/python -m pytest -q
SIGNALREADY_MODEL_DIR=/some/temp/dir venv/bin/python -m streamlit run app.py --server.port 8517 --server.headless true
```

In this cloud container Chromium lives at /opt/pw-browsers/chromium-1194/chrome-linux/chrome. Do not run `playwright install` there.
