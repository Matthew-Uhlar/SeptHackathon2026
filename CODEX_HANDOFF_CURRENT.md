# SignalReady handoff to Codex

Updated September 25 2026 by Claude (cloud session). This supersedes the status sections of CLAUDE_HANDOFF_CURRENT.md. Product rules / model rules / cautions in that file remain in force. This is a live checkpoint that is rewritten at each stable milestone because a usage limit can end the session without warning.

## Where the work lives

- Repository: matthew-uhlar/septhackathon2026. Working branch: `claude/jolly-fermi-9zawua`. Pull it before continuing.
- Codex's previously uncommitted work was committed by Matt as 317c9fa "Pushing Local work to Git". Claude work starts after that commit. Run `git log --oneline 317c9fa..` to see Claude commits.

## Verified checkpoint

- Linux Python 3.11.15 with the pinned requirements.txt versions in a throwaway venv: **105 passed** at 317c9fa before any Claude edit. This includes test_data_guidance.py (the data_issue_examples helper).
- Windows .venv was not available to Claude. Re-run the suite natively on Windows before treating Claude changes as Windows-verified.

## In progress (Claude)

1. First-save sidebar refresh. Codex's version sets `latest_save` then calls `st.rerun()`. Claude is adding an AppTest regression that saves into an empty model folder and asserts the picker appears without another interaction.
2. UI integration of `data_issue_examples` (row/column correction guidance table in Data readiness) plus class balance display. Core helper and its tests already exist.

Anything listed here without a later "Done" entry below is unfinished. Check `git status` and `git diff` first.

## Done by Claude

- `core.class_balance(df)` counts No failure / Failure / Unusable labels among unique normalized examples (same deduplication as training). Returns None when required columns are missing. Tests in test_data_guidance.py.
- Data readiness tab now shows a "Where to correct the file" expander (up to 20 `data_issue_examples` rows: Data row / Column / Problem, never the cell value) plus an outcome balance line. Tests in test_data_guidance_ui.py.
- test_session_recovery.py gained a second-save regression: the newest save becomes the picker selection and the first save is kept.

## Still open after Claude's items

- Fresh-machine Windows install and a human-timed demo recording remain unverified.
- Participant identity / publication / recording / portal upload remain owner tasks.
- Optional agentic or rule-based recommendation direction still needs Matt's answer. Do not implement without it.
