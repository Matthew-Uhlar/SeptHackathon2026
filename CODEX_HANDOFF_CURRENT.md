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
- Possible polish (not started): after training the success message asks the user to open Model comparison. With the keyed tabs the app could switch there automatically by setting `st.session_state.active_tab` before the tabs render. Leave it unless Matt wants it.

## Planned next round (not started)

Matt asked for three development teams plus a quality team and a testing team with Claude overseeing. PROPOSAL_CRITERIA.md holds the idea-phase deck content. Claude is waiting for a PDF copy of the HackerEarth challenge page because the cloud environment blocks that site. Planned features map to the deck:

- Team A: answer-giveaway column check for excluded columns (slide 2). New leakage.py with tests.
- Team B: prepared plain-language results summary (slides 6 and 11). New narrative.py with tests plus a script that writes RESULTS_SUMMARY.md.
- Team C: in-app completion checks and repeat-run verification (slides 8 and 10). New completion_checks.py with tests.
- Coordinator integrates the modules into app.py and writes PROJECT_SUMMARY.md.
- Quality team reviews against PROPOSAL_CRITERIA.md and the official rules. Testing team adds test_acceptance.py and TEST_REPORT.md.

Stay within the guided-studio framing. The deck says the user stays in control and rules out a separate chatbot.

## Reproducing Claude's checks on Linux

```bash
python3 -m venv venv && venv/bin/pip install -r requirements.txt playwright
venv/bin/python -m pytest -q
SIGNALREADY_MODEL_DIR=/some/temp/dir venv/bin/python -m streamlit run app.py --server.port 8517 --server.headless true
```

In this cloud container Chromium lives at /opt/pw-browsers/chromium-1194/chrome-linux/chrome. Do not run `playwright install` there.
