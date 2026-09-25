# SignalReady project summary

ABB Accelerator 2026 / Theme 1: Agentic Predictive Maintenance Studio / solo prototype.

## The problem

Plants collect equipment readings but turning them into a trustworthy failure model takes machine learning expertise. A model can look accurate while it misses most failures because failures are rare. Missing readings weaken a model. Columns recorded after a failure can quietly give away the answer and make a model look far better than it is. An engineer without data science support has no easy way to see these problems before trusting a result.

## The solution

SignalReady is a local guided studio that automates the machine learning workflow between decisions an engineer makes:

1. **Data readiness.** Loads a CSV in the AI4I format and blocks training on missing / invalid / conflicting data. It points to the exact rows and columns to fix and shows how rare failures are.
2. **Model comparison.** Trains logistic regression and a random forest on a seeded 60/20/20 split. A separate selection group picks the winner. A final group that played no part in the choice reports failures found and missed alongside false alarms. A baseline that never predicts failure shows why accuracy alone misleads.
3. **Explanation.** Shows which inputs the fitted model relied on with clear limits on what that means.
4. **Save and predict.** Saves the model locally with a full audit trail and classifies new readings with a warning when they fall outside the training range.

Every step is started by the user. Every result carries its dataset fingerprint / seed / software versions.

## Impact

The intended benefit is an easier and safer way for engineers to understand a basic maintenance modeling workflow. SignalReady makes data problems and model mistakes visible before anyone relies on a model. Cost and downtime savings would require a later trial on real equipment data. The included dataset is synthetic so the prototype does not claim factory performance or forecast breakdown timing.

## Submission contents

| Item | Where |
|---|---|
| Project summary | This file |
| Working prototype | app.py and core.py. Start with Start SignalReady.bat or README.md |
| Demo video | Recorded by the participant using DEMO_GUIDE.md |
| Source code | This repository |
| Technical documentation | TECHNICAL_DOCUMENTATION.md |
| Presentation deck (optional) | Idea-phase deck supplied separately |

Dataset credit: AI4I 2020 Predictive Maintenance Dataset. UCI Machine Learning Repository. https://doi.org/10.24432/C5HS5C. CC BY 4.0.
