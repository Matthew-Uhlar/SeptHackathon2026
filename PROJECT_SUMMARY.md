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

1. **Data readiness.** Loads a CSV in the AI4I 2020 column format. Training is blocked when required values are missing or invalid or when identical readings carry conflicting labels. A correction table lists up to 20 problem cells by data row and column. An outcome balance line shows how rare failures are. ID columns and failure-type columns are excluded from training by a fixed list of six approved inputs.
2. **Model comparison.** Trains logistic regression and a random forest on a seeded 60/20/20 split. The selection group picks the winner by F1. The final group then reports failures found and failures missed alongside false alarms. A baseline that always predicts no failure sits in the same table to show why accuracy alone misleads.
3. **Explanation.** Shows which inputs the fitted model relied on. The screen states what these scores do not show: they are not a physical cause and they do not explain a single prediction.
4. **Save and predict.** Saves the selected model locally with its data fingerprint / seed / split sizes / training time / software versions. A saved run can be reloaded after a restart. The prediction form classifies a new set of readings and warns when a reading falls outside the training range.

<!-- COORDINATOR: update after integration. If profiling.py / narrative.py / completion_checks.py / inference.py are wired into app.py, add one line each here (column profile and answer-giveaway detection / plain-language results summary and live completion checks / uncalibrated model score with what-if sensitivity and batch CSV scoring). Until then they are not part of the submitted app. -->

## Impact

The intended benefit is an easier way for engineers to understand a basic maintenance modeling workflow and to see data problems and model mistakes before anyone relies on a model. Every result carries enough audit detail to be checked again later.

The evidence is limited on purpose. The included dataset is synthetic. Random row splits do not show how the model would perform on future periods or on different machines. The prototype does not forecast when a machine will break down and does not give calibrated failure probabilities. Cost and downtime savings would require a later trial on real equipment data.

Where this could go next: time-aware evaluation on real plant data with timestamps and asset IDs / a scoring service for plant integration / managed experiment tracking / richer explanations. TECHNICAL_DOCUMENTATION.md lists these as future scope.

## Submission contents

| Item | Where |
|---|---|
| 1. Project summary | This file |
| 2. Working prototype | app.py and core.py. Setup in README.md or TECHNICAL_DOCUMENTATION.md |
| 3. Demo video | Recorded by the participant from DEMO_SCRIPT.md (outline in DEMO_GUIDE.md) |
| 4. Source code | This repository |
| 5. Technical documentation | TECHNICAL_DOCUMENTATION.md |
| 6. Presentation deck (optional) | Idea-phase deck supplied separately by the participant |
| Attribution | THIRD_PARTY_NOTICES.md |
| Rules check | COMPLIANCE_REVIEW.md |

Dataset credit: Matzka S. (2020). AI4I 2020 Predictive Maintenance Dataset. UCI Machine Learning Repository. https://doi.org/10.24432/C5HS5C. Licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). The included copy is unmodified.
