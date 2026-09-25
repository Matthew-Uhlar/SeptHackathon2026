# SignalReady compliance review

Prepared September 25 2026 by the deliverables and compliance team. It checks the repository against the official rules / Theme 1 / the idea-phase proposal as captured in PROPOSAL_CRITERIA.md. Evidence cites files and functions as of commit 132878c. Line numbers refer to app.py at that commit. This is a document review and not legal advice.

Items marked **Owner** need Matt. Items marked **Coordinator** need the person integrating app.py.

## Top risks (highest first)

| Rank | Risk | Why it matters | Action | Who |
|---|---|---|---|---|
| 1 | Source code not reachable by judges | The GitHub repository was private on September 25 2026. The work is on branch `claude/jolly-fermi-9zawua` while `master` is the default branch. Submission item 4 asks for a link to the complete source code. | Merge to `master` or name the branch. Make the repository public or grant access as the portal requires. Test the link while logged out. | Owner |
| 2 | Demo video not recorded | Item 3 is required. Incomplete submissions are not considered. | Record from DEMO_SCRIPT.md after integration is frozen. | Owner |
| 3 | Eligibility / solo participation | Only currently enrolled students at accredited US institutions may enter. Individual participation is "governed by ABB's final eligibility criteria". | Confirm enrollment and that a solo entry is accepted before the deadline. | Owner |
| 4 | Theme-fit perception of "Agentic" | The app is a guided studio with a fixed selection rule. A judge scoring problem-solution fit (20%) may look for autonomous behavior. | Present it openly as a deliberate human-in-the-loop design (see "Presenting the agentic question honestly"). Do not call it an agent. | Owner / Coordinator |
| 5 | Late integration churn | Three new modules are being wired in two days before the deadline. Docs could describe features the app does not show. Untested wiring could break the demo. | Freeze features at a set time. Rerun the full suite. Update the marked doc sections only after wiring. Run the final verification list in SUBMISSION_CHECKLIST.md. | Coordinator |
| 6 | "Original work during the hackathon period" is only partly evidenced by git | Every commit through 132878c is dated September 25 2026. The first commit is a "Baseline snapshot before continued development" that already holds a working app and tests. Git cannot show when that baseline was written. | Be ready to state when the baseline code was written (it must be after the event began). Keep any earlier local files or notes. | Owner |
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
| Original work developed during the hackathon period | Likely met with an evidence gap | Idea phase Aug 11 to Sep 18. Prototype phase Sep 18 to Sep 27. All 16 commits through 132878c fall on Sep 25 2026 (3509ab4 at 03:38 UTC through 132878c at 21:51 UTC). No commit predates Aug 11. The GitHub repository was created Sep 25 2026 at 21:19 UTC. No copied third-party code was found: app.py and core.py import only published libraries. data/bad_sample.csv was written for this project (none of its 56 readings match a UCI row). | Owner confirms the baseline snapshot was written during the event. See risk 6. |
| Open-source used with proper attribution | Met | THIRD_PARTY_NOTICES.md lists every installed dependency with version and license. README.md links it. | Recheck if requirements.txt changes. |
| Compliance with open-source licenses | Met | All libraries are installed by the user from PyPI and are not modified or redistributed in this repository. Licenses are permissive (Apache-2.0 / BSD / MIT / PSF / MIT-CMU) plus MPL-2.0 for certifi and runtime-exception GPL / LGPL files bundled inside the NumPy and SciPy binaries. None places conditions on SignalReady's own code. | None. |
| Dataset license (CC BY 4.0) | Met in docs. Partly in app | Attribution elements required by CC BY 4.0: creator (Stephan Matzka) / title / DOI link / license name and link / whether changes were made (none to the stored file). All are in THIRD_PARTY_NOTICES.md. README.md and PROJECT_SUMMARY.md carry the citation. The app sidebar (app.py:24 to 25) links the DOI and names the license but not the creator. | Coordinator: sidebar fix below. |
| No plagiarism / IP infringement / unethical conduct | Met as far as reviewed | "ABB" appears only in documents as the event name ("ABB Accelerator 2026") which is descriptive use. The app UI does not use the ABB name / logo / colors (app.py theme uses its own teal #087f78). No third-party logos or images are in the repository. The UCI dataset is credited. | Keep ABB branding out of the video and deck except for naming the event. |
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
| Automated dataset profiling and quality assessment | core.py:read_csv (format checks) / core.py:check_data (blocking errors and warnings) / core.py:data_issue_examples (cell locations) / core.py:class_balance (outcome balance). Shown in app.py data tab. | No per-column statistics. Answer-giveaway columns are excluded by the fixed input list (core.py:FEATURES) rather than detected. | Being integrated: profiling.py column profile and answer-giveaway detection. Until wired in, describe it as "quality assessment" not "profiling". <!-- COORDINATOR: update after integration --> |
| Intelligent task and model selection | core.py:train picks the higher selection-group F1 between two models before the final check. | Task type is fixed (binary classification). Only two model families. The rule is fixed rather than adaptive. | Call it "transparent rule-based selection". Show both selection F1 scores on Model comparison (they are already in core.py:text_report). |
| Data preprocessing and feature engineering | core.py:train: numeric conversion / deduplication / ColumnTransformer with StandardScaler and fixed L/M/H OneHotEncoder fitted on training rows only. | No engineered features. | State this plainly. List engineered features as future scope (done in TECHNICAL_DOCUMENTATION.md). |
| Model training and evaluation | core.py:train (seeded stratified 60/20/20) / core.py:metrics / always-no-failure baseline. Tests: test_core.py:test_no_leakage_or_overlap / test_baseline_and_counts. | Random row split only. | None for the prototype. Time-aware evaluation stays future scope. |
| Explainable AI using feature importance and confidence scores | core.py:explain / core.py:explanation_note. Global chart in app.py explain tab with limits stated. | No per-prediction explanation. No confidence score. | Being integrated: inference.py uncalibrated score with an honest note and what-if sensitivity. Never call the score a probability or a confidence. <!-- COORDINATOR: update after integration --> |
| Experiment tracking and model comparison | Two-model table with baseline (app.py results tab). core.py:save_run / run_metadata / run_label / load_run keep fingerprint / seed / time / versions per run. | No side-by-side table of saved runs. | Being integrated: profiling.py saved-run comparison table. <!-- COORDINATOR: update after integration --> |
| One-click deployment of trained models | "Save selected model locally" button (app.py results tab) with core.py:save_run. Reload in the sidebar with core.py:load_run validation. | No serving endpoint. The proposal ruled out a cloud service. | Call it "one-click local save and reload". Do not call it production deployment. FastAPI and Docker stay future scope. |
| Interactive prediction and inference dashboard | app.py prediction tab with core.py:predict (type check / range warning). | Single reading only. No score. | Being integrated: inference.py batch CSV scoring. <!-- COORDINATOR: update after integration --> |

### Judging criteria

| Criterion (weight) | Current evidence | Gap | Low-risk action |
|---|---|---|---|
| Innovation and creativity (20%) | The studio is built around exposing mistakes: correction table / always-no-failure baseline / missed failures shown first / explanation limits on screen. | Uses standard models. No novel algorithm. | Lead the video and summary with the "a score can hide mistakes" angle. |
| Technical excellence (25%) | Leakage-safe pipeline / separate selection and final groups / audit metadata / validated reloads / atomic unique saves / 111 automated tests passing on Linux (September 25 2026). | Few of the suggested technologies (no MLflow / FastAPI / Docker / SHAP / boosting). | Explain the scope choice once (TECHNICAL_DOCUMENTATION.md does). Mention the test count only after the final run. |
| Problem-solution fit (20%) | Covers data quality / training / evaluation / comparison / explanation / packaging / inference in one flow. | Not agentic. Several theme items are partial. | Honest framing below. Integrate the planned modules only if they are tested in time. |
| Scalability and feasibility (15%) | Runs on one ordinary computer with free open-source tools. Clear upgrade path in TECHNICAL_DOCUMENTATION.md future scope. | One fixed CSV format. 50000-row limit. Local single user. | Present the limits as deliberate prototype bounds with a named next step for each. |
| User experience (10%) | Numbered tabs / disabled train button on bad data / plain-language messages / range warnings / tab kept after save. | No guided "next step" hints beyond captions. | None required. |
| Presentation and demo (10%) | DEMO_SCRIPT.md timed script with shot list and closing impact statement. | Not yet recorded or timed by a person. | Record with one timed rehearsal first. |

### Presenting the agentic question honestly

SignalReady does not plan / choose tools / act on its own. It never runs a step the engineer did not start. The proposal chose this on purpose: "The user stays in control of each step" and no separate chatbot. Suggested framing for the summary / video / deck:

> SignalReady takes the automation half of an agentic studio and deliberately leaves the decisions with the engineer. Once asked, it runs the full modeling pipeline on its own: data checks / leakage-safe split / training / selection / evaluation / explanation / packaging. The engineer approves each hand-off because a maintenance model that no one has checked should not act on its own. A future version could add an agent that proposes the next step. The audit trail and held-out checks built here are what would keep such an agent honest.

Avoid: "agent" / "autonomous" / "AI copilot" / "intelligent assistant" as descriptions of the current app.

## Proposal versus build

| Slide | Promise | Status | Evidence or note |
|---|---|---|---|
| 2 Problem | Show data warnings | Delivered | core.py:check_data / data_issue_examples. Data readiness tab. |
| 2 Problem | Handle answer-giveaway columns | Delivered by construction. Detection partial | Fixed six-input list (core.py:FEATURES). Extra columns listed as excluded. Detection of giveaway columns being integrated (profiling.py). |
| 2 Problem | Explain missed failures alongside false alarms | Delivered | Model comparison metrics and table. core.py:metrics. |
| 3 Workflow | Load the sample or a matching file | Delivered | Sidebar data source. core.py:read_csv. |
| 3 Workflow | Warnings about missing or repeated readings | Delivered | core.py:check_data. test_core.py:test_duplicates_ignore_ids. |
| 3 Workflow | Compare two models on reserved examples | Delivered | core.py:train. |
| 3 Workflow | Save a model and use it for a new prediction | Delivered | core.py:save_run / load_run / predict. |
| 3 Workflow | User stays in control of each step | Delivered | Every step is a button press. |
| 4 Scope | File loading with clear data warnings | Delivered | As above. |
| 4 Scope | Two standard machine learning models | Delivered | Logistic regression and random forest. |
| 4 Scope | Results explained in everyday language | Partially delivered | Plain metric names ("Failures missed" / "False alarms") and captions. A generated plain-language summary is being integrated (narrative.py). |
| 4 Scope | Prediction form with model saving | Delivered | Prediction tab plus save and reload. |
| 4 Scope | One local app / one file format / no live machine / no cloud or chatbot | Delivered | .streamlit/config.toml binds 127.0.0.1. No network calls in app.py or core.py. The sidebar only links to the dataset page. |
| 5 Data and limits | Public UCI AI4I data under CC BY 4.0 | Delivered | data/ai4i2020.csv unmodified. Credit in docs and sidebar. |
| 5 Data and limits | No claim of breakdown timing or warning time | Delivered | app.py:18 banner / core.py:text_report limitations / README.md. |
| 6 Technology | Python / Streamlit / pandas / scikit-learn | Delivered | requirements.txt. |
| 6 Technology | Prepared text explains the checked results | Partially delivered | Fixed captions and core.py:text_report. Generated summary being integrated. |
| 7 Model checks | Remove record IDs and failure-type columns | Delivered | core.py:FEATURES. test_core.py:test_no_leakage_or_overlap. |
| 7 Model checks | Reserve 20% for the final check | Delivered | core.py:train. |
| 7 Model checks | Data preparation within the training portion | Delivered | Pipeline fitted on training rows only. |
| 7 Model checks | Compare with always-no-failure | Delivered | "Always no failure" row. |
| 7 Model checks | Report detected / missed / false alarms. No score promised | Delivered | core.py:metrics. No accuracy headline. |
| 8 Build plan | Error tests and repeat runs | Delivered | 111 tests. test_regressions.py:test_repeatable_training_and_persistence. |
| 8 Build plan | Setup guide and demo | Setup guide delivered. Demo partly | README.md / TECHNICAL_DOCUMENTATION.md. Video not recorded yet. |
| 9 Risks | Stop new features after September 23 | Not followed | Correction table and outcome balance were added September 25 and three modules are being added. Mitigation: freeze now and rerun all tests. |
| 9 Risks | Drop the optional importance chart first | Not needed | The chart was built with its limits stated. |
| 9 Risks | Show missed failures and false alarms / keep final check separate | Delivered | As above. |
| 9 Risks | State that generated data only supports a demonstration | Delivered | Banner / reports / docs. |
| 9 Risks | One file format with clear errors | Delivered | core.py:read_csv / check_data plus tests in test_edge_cases.py. |
| 10 Demo | File with a known problem / clean run / explain mistakes / reload for a prediction | Delivered in the app. Video pending | data/bad_sample.csv. DEMO_SCRIPT.md. |
| 10 Completion check | Known bad inputs receive clear warnings | Delivered | test_edge_cases.py / test_data_guidance_ui.py. A live on-screen check is being integrated (completion_checks.py). |
| 10 Completion check | Answer columns never enter training | Delivered | test_core.py:test_no_leakage_or_overlap / test_explain_covers_approved_features. |
| 10 Completion check | Both models use the same final examples | Delivered by construction | core.py:train scores both models on the same X_test. No dedicated test was found. The live check being integrated would cover it. |
| 10 Completion check | Reloading preserves predictions | Delivered | test_core.py:test_saved_model_reproduces. |
| 11 Submission | Working local app | Delivered | |
| 11 Submission | Source code with dataset credit | Delivered. Access pending | Repository private (risk 1). |
| 11 Submission | Setup guide and project summary | Delivered | README.md / PROJECT_SUMMARY.md. |
| 11 Submission | Short demo video and results summary | Pending | Video: owner. Per-run readable report exists now. RESULTS_SUMMARY.md generator being integrated. |
| 11 Submission | Cost and downtime savings need later testing | Delivered | Stated in PROJECT_SUMMARY.md impact section. |

## Owner-only items

1. Eligibility: currently enrolled at an accredited US college or university.
2. Registration on the official microsite under Theme 1 with one project.
3. Individual participation accepted under ABB's final eligibility criteria.
4. Deadline: plan for Sep 27 2026 4:59 PM Central despite the Sep 28 graphic.
5. Repository access for judges (risk 1).
6. Demo video recording and upload.
7. AI-assistance disclosure decision.
8. Code license decision.
9. Statement on when the baseline snapshot was written if asked (risk 6).
10. Whether to include the idea-phase deck. If included, check it against the proposal-versus-build table so it does not promise the "Not followed" or "Partially delivered" items as finished.

## Wording that overclaims

### App UI strings (Coordinator: this team cannot edit .py files)

No UI string claims real equipment validation / breakdown timing / calibrated probabilities / autonomous agent behavior. app.py:18 / app.py:161 / app.py:194 and the core.py:text_report limitations paragraph already state the limits well. These smaller items remain:

| Location | Current text | Issue | Suggested replacement |
|---|---|---|---|
| app.py:15 | `MAINTENANCE DATA ASSISTANT` | "Assistant" can read as an AI assistant or copilot. | `GUIDED MAINTENANCE MODELING STUDIO` |
| app.py:18 | `Predictions identify failure patterns in readings.` | Slightly strong: the model flags resemblance to labeled failures. | `Predictions flag readings that resemble failures labeled in the training data.` |
| app.py:25 | `AI4I 2020 dataset · UCI Machine Learning Repository · CC BY 4.0` | CC BY 4.0 attribution should name the creator. | `AI4I 2020 dataset by S. Matzka · UCI Machine Learning Repository · CC BY 4.0` |
| app.py:201 | `What drove the model's decisions?` | "Decisions" can suggest a per-prediction explanation. The chart is global. | `Which inputs did the model rely on most?` (the tab label can stay) |

No test asserts on these four strings. For any integrated module: an uncalibrated score must not be labelled "probability" / "confidence" / "likelihood" / "risk %". What-if output must not be described as a cause or a repair.

### Documents

| Location | Issue | Status |
|---|---|---|
| PROJECT_SUMMARY.md (earlier draft) | "full audit trail" / "easier and safer" / "exact rows and columns" for conflicting labels which the correction table does not locate | Fixed in this pass. |
| TECHNICAL_DOCUMENTATION.md (earlier draft) | "The app profiles" the data (profiling is not wired in) / "Reloads validate all of it" (split indices and seed are not validated) / Altair "bundled with Streamlit" (it is a separate package that Streamlit installs) / NumPy license listed as BSD-3-Clause only / architecture box for feature modules that did not exist | Fixed in this pass. |
| README.md (earlier draft) | Setup said fetch_data.py was a required step although the data is committed / credit lacked the creator / "Open Model comparison" after training (the app switches automatically since commit 09ba38c) | Fixed in this pass. |
| QUALITY_REVIEW.md / handoff files | Internal notes. No overclaims found. They describe the agentic gap candidly. | Owner decision on where they live (see AI-assistance note). |
| PROPOSAL_CRITERIA.md | Accurate. Its Theme 1 table marks planned items as planned. | None. |
