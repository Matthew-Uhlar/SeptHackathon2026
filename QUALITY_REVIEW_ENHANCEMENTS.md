# SignalReady enhancement quality review

September 27 2026. Independent review of the staging build against PROPOSAL_CRITERIA.md and SECURITY_REVIEW.md. Deadline-day scope remains a local app with fixed models and no separate chatbot or cloud service.

## Initial assessment

The selected additions are well aligned with the proposal's central problem: making misleading model scores easier to recognize. They add decision context and evidence portability without changing the training algorithm. Technical correctness and demo clarity matter more than adding unsupported claims of agentic autonomy.

| Addition | Judging relevance | Required accuracy boundary |
|---|---|---|
| Hypothetical maintenance error costs | Problem-solution fit and practical usefulness | Use selection examples and illustrative cost units. Never call the result savings or total maintenance cost. Preserve the selected model and threshold. |
| Incoming batch familiarity summary | Technical excellence and usable quality screening | Show scored-row denominator and skipped rows. Range checks are descriptive screening rather than statistical drift detection or proof of trustworthy predictions. |
| Model review card | Feasibility and presentation clarity | Record actual evidence and known limits. Human next steps remain pending actions rather than automatic completion assertions. |

## Cost implementation reviewed

Reviewed decision_support.py and the Explore maintenance trade-offs expander in app.py. Both use selection results. Counts are checked for consistency and an always-no-failure baseline is calculated from the selection outcomes. The result records model identity plus assumed costs and the fixed threshold. The limitations correctly exclude other operating costs and distinguish flagged readings from distinct machines or staff hours. No actionable defect identified in this implementation.

## Acceptance requirements for the remaining implementation

- Empty scored results must produce unavailable familiarity evidence rather than a reassuring zero percentage.
- Percentages must use valid scored rows as the denominator. Skipped readings must remain explicit.
- A batch within each numeric range can still contain unfamiliar combinations or unusual concentrations. Say so rather than label it safe or validated.
- Any training mean comparison must read the fitted training scaler. Do not compute a reference using selection or final-check rows.
- Batch exports must keep model/data provenance and avoid repeating rejected values.
- The review card must not certify completion checks unless their actual results are supplied. A run object alone does not prove repeatability or save/reload test completion.
- Keep owner responsibilities and later factory validation distinct from demonstrated synthetic-data results.

At this initial review familiarity.py and review_card.py were not yet present. Their implementation review will follow in this same report.

## Implementation review

Reviewed familiarity.py plus review_card.py and their app integration once available. The numeric screening uses only scored rows and excludes skipped rows. Inclusive range boundaries are implemented correctly. Empty results return an unavailable status with no percentage table. The mean is explicitly a batch mean rather than an inferred training reference. The note correctly states that in-range data can still yield wrong predictions and that this is not a statistical drift test.

The model review card delegates evidence to text_report and adds concrete human next steps. It explicitly says completion checks must still be run and retained separately. It does not claim deployment approval. Its privacy wording matches its aggregate content.

### P2 — Range screening download did not initially identify the scored batch (resolved)

At first implementation review the familiarity report included dataset_fingerprint and selected_model but not the incoming file fingerprint or training timestamp. The app named the download using only the training fingerprint. Scoring two different uploaded files against one run therefore produced range-screening files with the same identity and filename despite different evidence.

Repair applied: the report includes training timestamp and the app adds the incoming file SHA-256 to the range-screening export and its filename. No submitted values are repeated. This preserves the existing export auditability standard.

No other actionable defect found in the three added features during this read-only implementation review. Runtime checks are owned by the testing team.
