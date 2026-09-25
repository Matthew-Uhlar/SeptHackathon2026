# SignalReady proposal criteria

Extracted from Matt's idea-phase deck (signalready_submission.pptx) on September 25 2026. This is the reference that feature work and quality reviews check against. The official rules below come from a PDF capture of https://www.hackerearth.com/community/challenges/hackathon/abb-accelerator-2026/ taken September 25 2026 at 4:42 PM that Matt supplied.

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

# Official challenge rules (HackerEarth page captured September 25 2026)

## Timeline

- Idea phase: Aug 11 to Sep 18 2026.
- Prototype phase: the page header says Sep 18 to **Sep 27 2026 4:59 PM America/Chicago**. The timeline graphic further down says Sep 28. Treat Sep 27 4:59 PM Central as the deadline.
- Onsite hackathon for top prototype teams: Oct 13 to Oct 14 2026 at ABB Fort Smith Arkansas.
- Submissions can be updated until the deadline. Late or incomplete submissions will not be considered.

## Theme 1: Agentic Predictive Maintenance Studio

"Build an AI-powered AutoML + MLOps Copilot for Industrial Equipment." Help engineers analyze equipment data / identify potential failures before they occur / recommend optimal models / explain predictions / deploy production-ready ML pipelines through an intuitive AI-powered experience.

The solution could include the following. Current SignalReady coverage is noted after each item.

| Theme item | SignalReady status |
|---|---|
| Automated dataset profiling and quality assessment | Data readiness checks / correction table / outcome balance. Column profiling and answer-giveaway detection planned. |
| Intelligent task and model selection | Fixed rule: highest selection-group F1 picks between two models. |
| Data preprocessing and feature engineering | Training-only scaling and fixed type encoding. No engineered features. |
| Model training and evaluation | Seeded 60/20/20 split with an always-no-failure baseline. |
| Explainable AI using feature importance and confidence scores | Global importance chart. Per-prediction explanation and an uncalibrated model score planned. |
| Experiment tracking and model comparison | Two-model comparison plus saved runs with audit metadata. Saved-run comparison table planned. |
| One-click deployment of trained models | One-click local save and reload. No serving endpoint (proposal rules out a cloud service). |
| Interactive prediction and inference dashboard | Single-reading form. Batch scoring of a CSV planned. |

Suggested technologies: AI / ML / AutoML / MLOps / Python / FastAPI / MLflow / LangGraph / Docker / SHAP / LightGBM or XGBoost / PostgreSQL. SignalReady uses Python with scikit-learn / pandas / Streamlit.

## Submission format

1. Project summary: overview of the solution / the problem it solves / its impact.
2. Working prototype or proof of concept.
3. Demo video: a concise walkthrough of the solution / key features / functionality.
4. Source code: link to a GitHub or other repository with the complete source code.
5. Technical documentation: solution architecture / technologies used / implementation approach / setup instructions.
6. Presentation deck (optional): problem statement / solution / technical architecture / business impact / future scope.

## Judging criteria

| Criterion | Weight | Description |
|---|---|---|
| Innovation and creativity | 20% | Originality and potential to solve real-world industrial challenges. |
| Technical excellence | 25% | Implementation quality / architecture / engineering practices / effective use of recommended technologies. |
| Problem-solution fit | 20% | Alignment with the selected theme and its objectives. |
| Scalability and feasibility | 15% | Practicality / scalability / potential for real-world adoption. |
| User experience | 10% | Usability / design / functionality. |
| Presentation and demo | 10% | Clarity / demo quality / communication of impact. |

## Rules

- Register through the official microsite. Choose one theme. Submit one project.
- All submissions must be original work developed during the hackathon period.
- Open-source libraries and publicly available frameworks may be used with proper attribution and in compliance with their licenses.
- Plagiarism / IP infringement / unethical conduct may result in disqualification.
- Eligibility: students currently enrolled in accredited US colleges and universities. Team size 1 to 5. Individual participation is governed by ABB's final eligibility criteria. These are owner checks rather than code checks.
