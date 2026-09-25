# SignalReady project summary

ABB Accelerator 2026 / Theme 1: Agentic Predictive Maintenance Studio / solo prototype by Matt Uhlar.

Submission item 1 (project summary: overview / problem / impact). The other submission items are listed at the end of this file and tracked in SUBMISSION_CHECKLIST.md.

## Overview

SignalReady is a local guided modeling studio for equipment failure data. An engineer loads a CSV of equipment readings. The app checks whether the data is fit for training. It then trains two standard models and picks one with a fixed rule on a separate selection group. It reports what the chosen model got wrong on a final group that played no part in the choice. It shows which inputs the model relied on. The model can be saved locally with its audit details and reloaded to classify new readings.

The engineer starts every step and reviews every result. The app carries out the machine learning work between those decisions. This is a deliberate human-in-the-loop design: the proposal kept the user in control and ruled out a separate chatbot. SignalReady does not act on equipment or make maintenance decisions.

## The problem

A model score can hide important mistakes.

- Failures are rare. A model that never predicts a failure can still be right about 97% of the time on the included sample. Overall accuracy therefore says little about whether failures are caught.
- Missing or invalid readings weaken a model and are easy to overlook in a large file.
- Some columns give away the answer. The sample file includes failure-type columns that are only known after a failure. A model trained on them looks far better than it could be in use.
- An engineer without data science support has no easy way to see these problems before trusting a result.

## The solution

1. **Data readiness.** Loads a CSV in the AI4I 2020 column format. Training is blocked when required values are missing or invalid or when identical readings carry conflicting labels. A correction table lists up to 20 problem cells by data row and column. An outcome balance line shows how rare failures are. A column profile summarizes every column with counts and number ranges. ID columns and failure-type columns are excluded from training by a fixed list of six approved inputs. On top of that exclusion the app tests each excluded column with a fixed rule. When a column agrees with the failure label so strongly that it may record the answer or be filled in after the outcome, one information line names it and an expander explains the evidence. On the included sample it names the four failure-type columns HDF / OSF / PWF / TWF.
2. **Model comparison.** Trains logistic regression and a random forest on a seeded 60/20/20 split. The selection group picks the winner by F1. The final group then reports failures found and failures missed alongside false alarms. A baseline that always predicts no failure sits in the same table to show why accuracy alone misleads. A short plain-language summary explains the result from fixed sentence templates (no language model). A "Run completion checks" button retests six promises from the proposal on the active run and shows each result with its evidence in a readable table: answer columns never enter training / both models use the same final examples / the final check stays separate (including that data preparation was fitted on training rows only) / a repeat run gives the same results / reloading preserves predictions / known bad inputs receive clear warnings. The results are marked out of date when the selected file changes. A table compares every saved run side by side.
3. **Explanation.** Shows which inputs the fitted model relied on. The screen states what these scores do not show: they are not a physical cause and they do not explain a single prediction.
4. **Save and predict.** Saves the selected model locally with its data fingerprint / seed / split sizes / training time / software versions. A saved run can be reloaded after a restart and the app then opens its Model comparison. The prediction form classifies a new set of readings and warns when a reading falls outside the training range. It also shows the model's uncalibrated score with a note that it is not the chance of failure. A what-if table shows how the score moves when each reading is replaced by its training average. A whole CSV of up to 5000 readings can be scored at once. Invalid rows are skipped with a reason and the results download as a CSV whose score column is labelled uncalibrated.

## Impact

The intended benefit is an easier way for engineers to understand a basic maintenance modeling workflow and to see data problems and model mistakes before anyone relies on a model. Every result carries enough audit detail to be checked again later.

On the included sample the selected random forest found 52 of the 68 failures in the 2,000-reading final check with 40 false alarms. A rule that always predicts no failure was right on 96.6% of the same readings yet found none of the failures. RESULTS_SUMMARY.md records these values with all six completion checks passing. It is regenerated by make_results_summary.py and exact numbers can change with library versions.

The evidence is limited on purpose. The included dataset is synthetic. Random row splits do not show how the model would perform on future periods or on different machines. The prototype does not forecast when a machine will break down and does not give calibrated failure probabilities. Cost and downtime savings would require a later trial on real equipment data.

Where this could go next: time-aware evaluation on real plant data with timestamps and asset IDs / a scoring service for plant integration / managed experiment tracking / richer explanations. TECHNICAL_DOCUMENTATION.md lists these as future scope.

## Submission contents

| Item | Where |
|---|---|
| 1. Project summary | This file |
| 2. Working prototype | app.py with core.py / profiling.py / narrative.py / completion_checks.py / inference.py. Setup in README.md or TECHNICAL_DOCUMENTATION.md |
| 3. Demo video | Captioned recording without voice at demo/SignalReady_demo.mp4. Narration script for a voiced version in DEMO_SCRIPT.md |
| 4. Source code | This repository |
| 5. Technical documentation | TECHNICAL_DOCUMENTATION.md |
| 6. Presentation deck (optional) | Idea-phase deck supplied separately by the participant |
| Results summary | RESULTS_SUMMARY.md |
| Attribution and license | THIRD_PARTY_NOTICES.md / LICENSE (Apache 2.0) / NOTICE |
| Rules check | COMPLIANCE_REVIEW.md |

Dataset credit: Matzka S. (2020). AI4I 2020 Predictive Maintenance Dataset. UCI Machine Learning Repository. https://doi.org/10.24432/C5HS5C. Licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). The included copy is unmodified.
