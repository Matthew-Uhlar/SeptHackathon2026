# SignalReady compliance review

## September 26 2026 checkpoint

Matt authorized bounded improvements after the earlier feature freeze. Current Windows evidence is 266 passed / 1 skipped plus all six completion checks passing. The optional real browser test was skipped. Local privacy controls and data export checks are documented in SECURITY_REVIEW.md. The installed dependency scan reports no known vulnerabilities in 48 packages. Earlier commit-specific counts and freeze statements below are historical. The demo must be refreshed to match the new controls. No hosted security or autonomous maintenance capabilities are claimed.


Prepared September 25 2026 by the deliverables and compliance team. It checks the repository against the official rules / Theme 1 / the idea-phase proposal as captured in PROPOSAL_CRITERIA.md. First written against commit 132878c. Updated after the feature modules were wired in (6d7058b) and again after the bug-fix round (85255c2). Evidence now cites files and functions at commit 85255c2 and line numbers refer to app.py at that commit. This is a document review and not legal advice.

Items marked **Owner** need Matt. Items marked **Coordinator** need the person integrating app.py.

## Top risks (highest first)

| Rank | Risk | Why it matters | Action | Who |
|---|---|---|---|---|
| 1 | Source code not reachable by judges | The GitHub repository was still private at the last check on September 25 2026. Submission item 4 asks for a link to the complete source code. `master` is the default branch and was behind the working branch at the last check (0ca9588 compared with 85255c2). | Fast-forward `master` to the final commit. Make the repository public or grant access as the portal requires. Test the link while logged out. | Owner |
| 2 | Demo video not final | Item 3 is required. Incomplete submissions are not considered. A captioned recording without voice exists at demo/SignalReady_demo.mp4. The coordinator was re-recording it for the app at 85255c2. | Watch the final file end to end. Submit it or add a voiceover from DEMO_SCRIPT.md. | Owner |
| 3 | Eligibility / solo participation | Only currently enrolled students at accredited US institutions may enter. Individual participation is "governed by ABB's final eligibility criteria". | Confirm enrollment and that a solo entry is accepted before the deadline. | Owner |
| 4 | Theme-fit perception of "Agentic" | The app is a guided studio with a fixed selection rule. A judge scoring problem-solution fit (20%) may look for autonomous behavior. | Present it openly as a deliberate human-in-the-loop design (see "Presenting the agentic question honestly"). Do not call it an agent. | Owner / Coordinator |
| 5 | Late integration churn | Three modules were wired in on September 25 (commit 6d7058b) two days before the deadline. A quality review and a testing round followed. The testing team's bugs B1 to B8 and five UX items were fixed in 85255c2. The suite then had 253 tests: the 252 default tests passed on Linux and the opt-in browser test also passed. Features are now frozen and the docs match 85255c2. Any further change still risks the demo. | Keep the freeze. Rerun the full suite after any later change. Run the final verification list in SUBMISSION_CHECKLIST.md on Windows. | Coordinator |
| 6 | "Original work during the hackathon period" is only partly evidenced by git | Every commit through 85255c2 is dated September 25 2026. The first commit is a "Baseline snapshot before continued development" that already holds a working app and tests. Git cannot show when that baseline was written. | Be ready to state when the baseline code was written (it must be after the event began). Keep any earlier local files or notes. | Owner |
| 7 | AI-assistance disclosure | The captured rules are silent on AI coding tools. The public history lists "Claude" as the author of several commits. Internal review and handoff notes in the repository discuss AI agents. | Decide whether to add a short disclosure. Suggested wording below. Check the full terms on the portal for any AI rule. | Owner |
| 8 | Dataset credit in the app omits the creator | Resolved in commit 64e5d4f. The sidebar now names S. Matzka. | None. | Done |
| 9 | Code license | Resolved. Apache 2.0 added as LICENSE with a NOTICE that excludes the CC BY 4.0 dataset. | Owner checks the portal's IP terms for any conflict. | Done |
| 10 | Deadline mismatch | Header says Sep 27 4:59 PM Central. The timeline graphic says Sep 28. | Plan for Sep 27. | Owner |

## Official rules

| Rule | Status | Evidence | Action |
|---|---|---|---|
| Register through the official microsite | Owner check | Not verifiable from the repository. | Confirm the registration shows Theme 1 and SignalReady. |
| Choose one theme | Met | Every document names Theme 1 only (PROPOSAL_CRITERIA.md / README.md / PROJECT_SUMMARY.md). | None. |
| Submit one project | Owner check | One repository and one app. | Submit only once (updates before the deadline are allowed). |
| Original work developed during the hackathon period | Likely met with an evidence gap | Idea phase Aug 11 to Sep 18. Prototype phase Sep 18 to Sep 27. All commits through 85255c2 fall on Sep 25 2026 (3509ab4 at 03:38 UTC through 85255c2 later that evening). No commit predates Aug 11. The GitHub repository was created Sep 25 2026 at 21:19 UTC. No copied third-party code was found: app.py and core.py import only published libraries. data/bad_sample.csv and data/new_readings.csv were written for this project (none of their 56 and 31 readings match a UCI row). | Owner confirms the baseline snapshot was written during the event. See risk 6. |
| Open-source used with proper attribution | Met | THIRD_PARTY_NOTICES.md lists every installed dependency with version and license plus the optional demo-recording tools. README.md links it. LICENSE (Apache 2.0) and NOTICE cover the project's own code. | Recheck if requirements.txt changes. |
| Compliance with open-source licenses | Met | All libraries are installed by the user from PyPI and are not modified or redistributed in this repository. Licenses are permissive (Apache-2.0 / BSD / MIT / PSF / MIT-CMU) plus MPL-2.0 for certifi and runtime-exception GPL / LGPL files bundled inside the NumPy and SciPy binaries. None places conditions on SignalReady's own code. | None. |
| Dataset license (CC BY 4.0) | Met in docs. Partly in app | Attribution elements required by CC BY 4.0: creator (Stephan Matzka) / title / DOI link / license name and link / whether changes were made (none to the stored file). All are in THIRD_PARTY_NOTICES.md. README.md and PROJECT_SUMMARY.md carry the citation. The app sidebar (app.py:24 to 25) links the DOI and names the license but not the creator. | Coordinator: sidebar fix below. |
| No plagiarism / IP infringement / unethical conduct | Met as far as reviewed | "ABB" appears only in documents as the event name ("ABB Accelerator 2026") which is descriptive use. The app UI does not use the ABB name / logo / colors (app.py theme uses its own teal #087f78). No third-party logos or images are in the repository. The captioned demo video names "ABB ACCELERATOR 2026 · THEME 1" in plain text on its title card (demo/record_demo.py) which is also descriptive. The UCI dataset is credited in the app / docs / NOTICE / the video's closing card. | Keep ABB logos out of the video and deck. Naming the event is fine. |
| Eligibility: currently enrolled US college or university student | Owner check | Not verifiable from the repository. | Confirm. |
| Team size 1 to 5 / individual participation per ABB's final criteria | Owner check | Solo build. | Confirm solo entries are accepted. |

### Code license (decided: Apache 2.0)

Matt asked the coordinator to research and choose a license. Apache 2.0 was selected: it is permissive like every dependency / matches Streamlit's license / adds an explicit patent grant and patent-retaliation clause that corporate legal teams look for when judging real-world adoption. The owner keeps the copyright. LICENSE holds the unmodified standard text (MD5 3b83ef96387f14655fc854ddc3c6bd57). NOTICE states the copyright and that data/ai4i2020.csv stays under CC BY 4.0. The owner should still check the portal's full IP terms. The options considered were:

| Option | Effect | Fit |
|---|---|---|
| MIT | Anyone may reuse with the copyright notice. Shortest text. Compatible with every dependency. | Good default for a public hackathon repository. |
| Apache-2.0 | Like MIT plus an explicit patent grant and a NOTICE convention. Same license as Streamlit. | Good if patent clarity matters. |
| No license | All rights reserved. Judges can still read the code if they have access. Others cannot legally reuse it. | Suits keeping commercial options open for the Accelerator. |

Whatever is chosen, add one line saying that data/ai4i2020.csv remains under CC BY 4.0 and is not covered by the code license.

### Suggested AI-assistance note (Owner decision)

If Matt chooses to disclose, this fits at the top of README.md where a comment marks the spot:

> SignalReady was designed / directed / reviewed / tested by Matt Uhlar. AI coding assistants (Claude and Codex) helped write code / tests / documentation under his direction. The commit history shows which commits they authored.

The repository also holds internal process notes (CLAUDE_HANDOFF*.md / CODEX_HANDOFF*.md / QUALITY_REVIEW*.md / SESSION_STATUS.md). They are candid about the agentic gap and the tools used. Matt may keep them as evidence of the process or move them into a dev-notes folder so judges land on the submission documents first. They contain no secrets or personal data beyond the author name.

## Theme 1 alignment

### "The solution could include" items

| Theme item | Current evidence | Gap | Low-risk action |
|---|---|---|---|
| Automated dataset profiling and quality assessment | core.py:read_csv (format checks) / core.py:check_data (blocking errors and warnings) / core.py:data_issue_examples (cell locations) / core.py:class_balance (outcome balance) / profiling.py:profile_columns (Column profile expander) / profiling.py:answer_giveaway_columns (one information line naming the flagged columns plus the Why these columns look like answer giveaways expander, app.py:162 to 168). On the included sample it flags TWF / HDF / PWF / OSF and not UDI / Product ID / RNF. | Giveaway detection only examines excluded columns. The six approved inputs are fixed rather than chosen from the data. | Present detection as explaining the exclusion. Do not claim it would catch a leak hidden inside an approved input. |
| Intelligent task and model selection | core.py:train picks the higher selection-group F1 between two models before the final check. narrative.py:results_summary states both selection F1 scores in plain language on Model comparison. | Task type is fixed (binary classification). Only two model families. The rule is fixed rather than adaptive. | Call it "transparent rule-based selection". |
| Data preprocessing and feature engineering | core.py:train: numeric conversion / deduplication / ColumnTransformer with StandardScaler and fixed L/M/H OneHotEncoder fitted on training rows only. | No engineered features. | State this plainly. Engineered features are listed as future scope in TECHNICAL_DOCUMENTATION.md. |
| Model training and evaluation | core.py:train (seeded stratified 60/20/20) / core.py:metrics / always-no-failure baseline / completion_checks.py:completion_checks (six live checks behind the Run completion checks button shown as a readable st.table at app.py:223 to 231. "Final check kept separate" also confirms the fitted scaler saw only the training rows). Tests: test_core.py:test_no_leakage_or_overlap / test_baseline_and_counts / test_completion_checks.py. | Random row split only. | None for the prototype. Time-aware evaluation stays future scope. |
| Explainable AI using feature importance and confidence scores | core.py:explain / core.py:explanation_note (global chart) / inference.py:model_score shown as "Model score (uncalibrated)" with SCORE_NOTE (app.py:274 to 276) / inference.py:what_if table with WHAT_IF_NOTE (app.py:277 to 284). | The score is uncalibrated so it is not a confidence in the statistical sense. What-if is one-at-a-time sensitivity rather than SHAP. | Keep the "uncalibrated" label and the note. Never call the score a probability / confidence / likelihood / risk %. SHAP and calibration stay future scope. |
| Experiment tracking and model comparison | Two-model table with baseline (app.py results tab). core.py:save_run / run_metadata / run_label / load_run keep fingerprint / seed / time / versions per run. profiling.py:saved_run_table powers the Compare saved runs expander (app.py:245 to 249). | Local files only. No tracking server. | MLflow stays future scope. |
| One-click deployment of trained models | "Save selected model locally" button (app.py results tab) with core.py:save_run. Reload in the sidebar with core.py:load_run validation. | No serving endpoint. The proposal ruled out a cloud service. | Call it "one-click local save and reload". Do not call it production deployment. FastAPI and Docker stay future scope. |
| Interactive prediction and inference dashboard | app.py prediction tab with inference.py:model_score (type check / range warning / score / band) and inference.py:score_batch with batch_summary for CSV scoring of up to 5000 rows plus a download whose score column is "Model score (uncalibrated)" (app.py:287 to 303). data/new_readings.csv demonstrates it: 29 scored / 4 flagged / 3 outside range / 2 skipped. | Local upload only. No streaming or scheduled scoring. | None for the prototype. |

### Judging criteria

| Criterion (weight) | Current evidence | Gap | Low-risk action |
|---|---|---|---|
| Innovation and creativity (20%) | The studio is built around exposing mistakes: correction table / answer-giveaway detection / always-no-failure baseline / missed failures shown first / live completion checks that retest the proposal's promises / honest uncalibrated score. | Uses standard models. No novel algorithm. | Lead the video and summary with the "a score can hide mistakes" angle. |
| Technical excellence (25%) | Leakage-safe pipeline / separate selection and final groups / audit metadata / validated reloads / atomic unique saves / feature modules kept free of UI code / 253 automated tests at commit 85255c2 (252 default tests passed on Linux plus an opt-in browser test) / a testing round whose eight bugs were fixed with regression tests. | Few of the suggested technologies (no MLflow / FastAPI / Docker / SHAP / boosting). | Explain the scope choice once (TECHNICAL_DOCUMENTATION.md does). Mention the test count only after the final run. |
| Problem-solution fit (20%) | Every Theme 1 item has at least a partial implementation: profiling and quality / training and evaluation / comparison and run tracking / explanation with a score and what-if / local packaging / single and batch inference. | Not agentic. Selection and deployment are the thinnest items. | Honest framing below. |
| Scalability and feasibility (15%) | Runs on one ordinary computer with free open-source tools. Batch scoring handles files of up to 5000 readings. Clear upgrade path in TECHNICAL_DOCUMENTATION.md future scope. | One fixed CSV format. 50000-row limit. Local single user. | Present the limits as deliberate prototype bounds with a named next step for each. |
| User experience (10%) | Numbered tabs / disabled train button on bad data / plain-language messages and results summary / one calm information line for answer giveaways / readable completion-check table / range warnings / skipped batch rows explained / tab kept after save / Model comparison opens after training and after reload / no Deploy button. | Testing-team UX items 6 to 10 are open (TEST_REPORT.md), for example no warning before an unsaved run is discarded. | None required before the deadline. |
| Presentation and demo (10%) | Captioned recording demo/SignalReady_demo.mp4 / DEMO_SCRIPT.md timed script with shot list and closing impact statement / RESULTS_SUMMARY.md. | The recording has no voice. The narrated script is not yet timed by a person. | Consider a voiceover from DEMO_SCRIPT.md after one timed rehearsal. |

### Presenting the agentic question honestly

SignalReady does not plan / choose tools / act on its own. It never runs a step the engineer did not start. The proposal chose this on purpose: "The user stays in control of each step" and no separate chatbot. Suggested framing for the summary / video / deck:

> SignalReady takes the automation half of an agentic studio and deliberately leaves the decisions with the engineer. Once asked, it runs the full modeling pipeline on its own: data checks and profiling / leakage-safe split / training / selection / evaluation / its own completion checks / explanation / packaging / scoring. The engineer approves each hand-off because a maintenance model that no one has checked should not act on its own. A future version could add an agent that proposes the next step. The audit trail and held-out checks built here are what would keep such an agent honest.

Avoid: "agent" / "autonomous" / "AI copilot" / "intelligent assistant" as descriptions of the current app.

## Proposal versus build

| Slide | Promise | Status | Evidence or note |
|---|---|---|---|
| 2 Problem | Show data warnings | Delivered | core.py:check_data / data_issue_examples. Data readiness tab. |
| 2 Problem | Handle answer-giveaway columns | Delivered | Fixed six-input list (core.py:FEATURES) plus profiling.py:answer_giveaway_columns which names HDF / OSF / PWF / TWF on the sample. |
| 2 Problem | Explain missed failures alongside false alarms | Delivered | Model comparison metrics and table. core.py:metrics. |
| 3 Workflow | Load the sample or a matching file | Delivered | Sidebar data source. core.py:read_csv. |
| 3 Workflow | Warnings about missing or repeated readings | Delivered | core.py:check_data. test_core.py:test_duplicates_ignore_ids. |
| 3 Workflow | Compare two models on reserved examples | Delivered | core.py:train. |
| 3 Workflow | Save a model and use it for a new prediction | Delivered | core.py:save_run / load_run / predict. |
| 3 Workflow | User stays in control of each step | Delivered | Every step is a button press. |
| 4 Scope | File loading with clear data warnings | Delivered | As above. |
| 4 Scope | Two standard machine learning models | Delivered | Logistic regression and random forest. |
| 4 Scope | Results explained in everyday language | Delivered | Plain metric names ("Failures missed" / "False alarms") / captions / narrative.py:results_summary under What these results mean. |
| 4 Scope | Prediction form with model saving | Delivered | Prediction tab plus save and reload. |
| 4 Scope | One local app / one file format / no live machine / no cloud or chatbot | Delivered | .streamlit/config.toml binds 127.0.0.1. No network calls in app.py or core.py. The sidebar only links to the dataset page. |
| 5 Data and limits | Public UCI AI4I data under CC BY 4.0 | Delivered | data/ai4i2020.csv unmodified. Credit in docs and sidebar. |
| 5 Data and limits | No claim of breakdown timing or warning time | Delivered | app.py:91 banner / core.py:text_report limitations / README.md. |
| 6 Technology | Python / Streamlit / pandas / scikit-learn | Delivered | requirements.txt. |
| 6 Technology | Prepared text explains the checked results | Delivered | narrative.py fills fixed sentence templates from the recorded counts. core.py:text_report. RESULTS_SUMMARY.md. |
| 7 Model checks | Remove record IDs and failure-type columns | Delivered | core.py:FEATURES. test_core.py:test_no_leakage_or_overlap. |
| 7 Model checks | Reserve 20% for the final check | Delivered | core.py:train. |
| 7 Model checks | Data preparation within the training portion | Delivered | Pipeline fitted on training rows only. |
| 7 Model checks | Compare with always-no-failure | Delivered | "Always no failure" row. |
| 7 Model checks | Report detected / missed / false alarms. No score promised | Delivered | core.py:metrics. No accuracy headline. |
| 8 Build plan | Error tests and repeat runs | Delivered | 253 tests at commit 85255c2. test_regressions.py:test_repeatable_training_and_persistence. completion_checks.py:check_repeat retrains live. |
| 8 Build plan | Setup guide and demo | Delivered | README.md / TECHNICAL_DOCUMENTATION.md / demo/SignalReady_demo.mp4 (captioned, no voice). |
| 9 Risks | Stop new features after September 23 | Not followed | The correction table / outcome balance / three feature modules were added September 25. Mitigation: a quality review and a testing round followed. Bugs B1 to B8 were fixed in 85255c2 with regression tests. Features are now frozen. |
| 9 Risks | Drop the optional importance chart first | Not needed | The chart was built with its limits stated. |
| 9 Risks | Show missed failures and false alarms / keep final check separate | Delivered | As above. |
| 9 Risks | State that generated data only supports a demonstration | Delivered | Banner / reports / docs. |
| 9 Risks | One file format with clear errors | Delivered | core.py:read_csv / check_data plus tests in test_edge_cases.py. |
| 10 Demo | File with a known problem / clean run / explain mistakes / reload for a prediction | Delivered | data/bad_sample.csv / DEMO_SCRIPT.md / demo/SignalReady_demo.mp4. |
| 10 Completion check | Known bad inputs receive clear warnings | Delivered | test_edge_cases.py / test_data_guidance_ui.py. Also retested live by completion_checks.py:check_bad_inputs which requires both a blocking error and the repeated-example warning. |
| 10 Completion check | Answer columns never enter training | Delivered | test_core.py:test_no_leakage_or_overlap / test_explain_covers_approved_features. Retested live by completion_checks.py:check_answer_columns. |
| 10 Completion check | Both models use the same final examples | Delivered | core.py:train scores both models on the same X_test. Retested live by completion_checks.py:check_same_final_examples which confirms the counts are consistent with one shared final group of the stored size. |
| 10 Completion check | Reloading preserves predictions | Delivered | test_core.py:test_saved_model_reproduces. Retested live by completion_checks.py:check_reload. |
| 11 Submission | Working local app | Delivered | |
| 11 Submission | Source code with dataset credit | Delivered. Access pending | Repository private (risk 1). |
| 11 Submission | Setup guide and project summary | Delivered | README.md / PROJECT_SUMMARY.md. |
| 11 Submission | Short demo video and results summary | Delivered. Owner review pending | Captioned video demo/SignalReady_demo.mp4 (voiceover optional). RESULTS_SUMMARY.md generated by make_results_summary.py. |
| 11 Submission | Cost and downtime savings need later testing | Delivered | Stated in PROJECT_SUMMARY.md impact section. |

## Owner-only items

1. Eligibility: currently enrolled at an accredited US college or university.
2. Registration on the official microsite under Theme 1 with one project.
3. Individual participation accepted under ABB's final eligibility criteria.
4. Deadline: plan for Sep 27 2026 4:59 PM Central despite the Sep 28 graphic.
5. Repository access for judges and a final fast-forward of `master` (risk 1).
6. Demo video review (captioned recording or voiced version) and upload.
7. AI-assistance disclosure decision.
8. Check the portal's IP terms against the Apache 2.0 license.
9. Statement on when the baseline snapshot was written if asked (risk 6).
10. Whether to include the idea-phase deck. If included, check it against the proposal-versus-build table so it does not promise the "Not followed" or "Partially delivered" items as finished.

## Wording that overclaims

### App UI strings (Coordinator: this team cannot edit .py files)

Rechecked at commit 85255c2 including the strings from profiling.py / narrative.py / completion_checks.py / inference.py. No UI string claims real equipment validation / breakdown timing / calibrated probabilities / autonomous agent behavior. The score is labelled "Model score (uncalibrated)" on screen and in the batch download with SCORE_NOTE saying it is not the chance of failure. The giveaway evidence says a column "may record the answer or be filled in after the outcome" and ends with "a pattern in the file rather than proof of a cause". The narrative's last sentence denies breakdown forecasting and says an uploaded file's origin has not been verified. Earlier suggestions applied: banner / sidebar credit / explanation heading (64e5d4f) and the two what-if captions (app.py:280 and app.py:283). These items remain:

| Location | Current text | Issue | Suggested replacement |
|---|---|---|---|
| app.py:88 | `MAINTENANCE DATA ASSISTANT` | Not yet changed. "Assistant" can read as an AI assistant or copilot. | `GUIDED MAINTENANCE MODELING STUDIO` |
| inference.py:23 WHAT_IF_NOTE (shown at app.py:284) | `Each row shows how the model score responds when one reading is replaced by its training average while the other readings stay the same.` | The table also has product-type rows that swap to another type rather than an average. The app.py captions now say so but this note does not. Minor. | `Each row shows how the model score responds when one reading is replaced by its training average or the product type by another type seen in training while the other inputs stay the same.` |

No other wording changes are needed. Keep the rule for any later edit: never label the score "probability" / "confidence" / "likelihood" / "risk %" and never describe what-if output as a cause or a repair.

### Documents

| Location | Issue | Status |
|---|---|---|
| PROJECT_SUMMARY.md (earlier draft) | "full audit trail" / "easier and safer" / "exact rows and columns" for conflicting labels which the correction table does not locate | Fixed in this pass. |
| TECHNICAL_DOCUMENTATION.md (earlier draft) | "The app profiles" the data (profiling is not wired in) / "Reloads validate all of it" (split indices and seed are not validated) / Altair "bundled with Streamlit" (it is a separate package that Streamlit installs) / NumPy license listed as BSD-3-Clause only / architecture box for feature modules that did not exist | Fixed in this pass. |
| README.md (earlier draft) | Setup said fetch_data.py was a required step although the data is committed / credit lacked the creator / "Open Model comparison" after training (the app switches automatically since commit 09ba38c) | Fixed in this pass. |
| QUALITY_REVIEW.md / handoff files | Internal notes. No overclaims found. They describe the agentic gap candidly. | Owner decision on where they live (see AI-assistance note). |
| PROJECT_SUMMARY.md / TECHNICAL_DOCUMENTATION.md / README.md / DEMO_GUIDE.md / DEMO_SCRIPT.md / SUBMISSION_CHECKLIST.md (after integration and after the bug-fix round) | Features were described only after checking app.py and each module at commits 6d7058b and 85255c2. Values quoted for the sample (giveaway columns / batch counts / completion checks / scores) were reproduced on Linux at 85255c2. | Done. |
| PROPOSAL_CRITERIA.md | Owned by the coordinator. Its Theme 1 table was updated after integration (commit 0b5d9c3). | None from this team. |
