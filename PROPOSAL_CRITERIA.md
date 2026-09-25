# SignalReady proposal criteria

Extracted from Matt's idea-phase deck (signalready_submission.pptx) on September 25 2026. This is the reference that feature work and quality reviews check against. The challenge page https://www.hackerearth.com/community/challenges/hackathon/abb-accelerator-2026/ was not reachable from the cloud session so rules were not re-verified there. The deck notes say the timeline was checked on September 12 2026.

## Event framing

- ABB Accelerator 2026 / Artificial Intelligence and Machine Learning.
- Theme 1: Agentic Predictive Maintenance Studio. Idea phase proposal.
- Solo build. One participant owns the build and testing as well as the documentation.
- Portal prototype cutoff listed as September 27 2026. Proposal target completion September 26.

## Problem (slide 2)

A model score can hide important mistakes.

- Missing readings can weaken the model.
- Some columns can accidentally give away the answer.
- A model can miss failures even when its overall score looks high.
- SignalReady will show data warnings and explain missed failures alongside false alarms.

## Workflow (slide 3)

1. Load the sample file or a file with matching columns.
2. Review warnings about missing or repeated readings.
3. Compare two models on reserved examples.
4. Save a model and use it for a new prediction.

The user stays in control of each step.

## Scope (slide 4)

Core features: file loading with clear data warnings / two standard machine learning models / results explained in everyday language / a prediction form with model saving.

Scope boundary: one local app on one computer / one fixed file format / no live machine connection / no cloud service or separate chatbot.

## Data and limits (slide 5)

Public UCI AI4I 2020 dataset with generated equipment readings and failure labels (https://doi.org/10.24432/C5HS5C, CC BY 4.0). The demo flags readings associated with failure. Forecasting the timing of a real breakdown requires later work with suitable equipment data. The prototype does not establish advance warning time.

## Technology (slide 6)

Python / Streamlit / pandas / scikit-learn. Logistic regression provides a simple comparison. Random forest can learn more complex patterns. Prepared text explains the checked results.

## Model checks (slide 7)

- Remove record IDs and failure-type answer columns from inputs.
- Reserve 20% of the examples for the final check.
- Keep data preparation within the training portion.
- Compare both models with an approach that always predicts no failure.
- Report detected failures and missed failures alongside false alarms. No prediction score is promised before testing.

## Build plan (slide 8)

40 hours for one person with basic Python experience. Includes "Error tests and repeat runs" on September 23 and "Setup guide and demo" on September 24.

## Risks (slide 9)

- Limited time: stop new features after September 23. Drop the optional measurement-importance chart first.
- Misleading results: show missed failures and false alarms. Keep the final check separate from training.
- Limited evidence: generated data supports a demonstration. Factory performance needs a later trial.
- Unexpected inputs: support one file format and explain errors clearly.

## Demo and completion checks (slide 10)

Demo: show a file with a known problem / run a clean sample through both models / explain missed failures and false alarms / reload the saved model for a prediction.

Completion checks:

- Known bad inputs receive clear warnings.
- Answer columns never enter training.
- Both models use the same final examples.
- Reloading preserves predictions.

## Planned submission (slide 11)

Working local app / source code with dataset credit / setup guide and project summary / short demo video and results summary. The intended benefit is an easier way to understand a basic maintenance modeling workflow. Cost and downtime savings require later testing.
