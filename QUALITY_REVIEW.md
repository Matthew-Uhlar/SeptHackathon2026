# SignalReady Quality Review (Team B)

**Scope note:** `app.py` and `core.py` are being actively edited by Team A while this review runs. All findings below are against a **frozen pre-enhancement snapshot** of those two files (captured before Team A started its four planned additions). Re-run this checklist against the merged files before final submission — none of the verdicts below account for Team A's explanation view, demo fixture, human-readable report, or "prototype only" labeling, since those did not exist in the reviewed code. `README.md`, `CLAUDE_HANDOFF.md`, and `test_core.py` were read live (not being edited by anyone) and are current as of this review.

---

## 1. Alignment with Theme 1 "Agentic Predictive Maintenance Studio"

**Verdict: Concern**

The "studio" half plausibly fits: a bounded, engineer-facing workspace that loads data, checks it, compares two models, and lets a user try predictions is a reasonable 40-hour interpretation of a "predictive maintenance studio."

The "agentic" half does not show up anywhere in the reviewed code. The entire flow in `app.py` is linear and human-driven at every step:
- `data_tab`: user picks a source → clicks "Check and compare models" (a button, not an autonomous trigger)
- `results_tab`: user reads output, optionally clicks "Save selected model locally"
- `prediction_tab`: user fills a form and clicks "Check these readings"

There is no planning loop, no autonomous multi-step tool use, no LLM-driven reasoning, and no code anywhere (`app.py` or `core.py`) that makes a decision on the user's behalf beyond the single fixed rule `winner = max(validation, key=...F1...)` in `core.py`, which is deterministic model selection, not agentic behavior. Nothing in the app initiates work without a click.

**Fix (concrete):** Two honest paths, pick one given remaining hours:
- Reframe the pitch/README language to explicitly own this as a "tool-assisted studio, not an autonomous agent" and state why (trust, auditability of a maintenance decision) — cheap, preempts judge pushback.
- Or add one small, genuinely agentic touch within scope, e.g., an automatic post-comparison recommendation ("given these results, consider X") driven by a short rule set over `run['test']` — but only if it doesn't threaten the 40-hour budget (see Item 3).

Do not silently leave this unaddressed; a judge evaluating against "Agentic Predictive Maintenance Studio" will notice the workflow is deterministic and button-driven.

---

## 2. Claims appropriate for synthetic data

**Verdict: Pass** (one minor UI-signal concern, not a text-content violation)

Audited every `st.write` / `st.info` / `st.caption` / `st.success` / `st.warning` / `st.error` literal in the `app.py` snapshot (39 strings, dynamic ones excluded from wording review since they're just data). All are consistently hedged and match the "Important product limits" in both `README.md` and `CLAUDE_HANDOFF.md`:

- Top banner: `st.info('Prototype using generated equipment data. Predictions identify failure patterns in readings. They do not predict when a real machine will break down.')` — directly pre-empts the "no time forecasting" limit.
- `results_tab`: `st.write('These random row splits evaluate this generated dataset. They do not establish performance on future time periods or different machines. Avoid repeatedly adjusting a model after viewing final results.')` — matches the README's "Random row splits do not validate future-time forecasting or generalization to unseen equipment."
- `prediction_tab`: `st.caption('This is a model classification. It does not establish that equipment is safe or identify a repair.')` — matches "does not authorize maintenance work or identify a repair."
- Saved-run banner: `st.info('Showing a saved run. These results describe its original dataset rather than the currently selected file.')` — appropriately scoped, no cross-dataset overclaim.

No instance of "predicts," "forecasts," "safe," "certified," or probability language was found outside these hedged contexts. Nothing in `app.py` claims calibrated probabilities, live-machine connectivity, or lead time — consistent with the limits list.

**Minor concern:** `prediction_tab` uses `st.success('The model does not flag a failure pattern in these readings.')` for a "no failure" classification. `st.success` renders a green checkmark box, which carries a "you're good / safe" visual connotation stronger than the text underneath it disclaims (see Item 6). The words are fine; the icon color is doing unintended work.

**Fix:** Change that one call to `st.info(...)` (keep the caption below unchanged). Trivial, no logic change.

---

## 3. 40-hour solo scope preserved

**Verdict: Concern** (preserved today; real risk in two of Team A's four planned items)

Current code is lean and appropriately scoped: `app.py` is a single flat script (~80 lines) with three tabs and no framework beyond Streamlit; `core.py` is ~100 lines covering CSV parsing, validation, training, and prediction with no custom classes, no async, no external services. This matches "keep the prototype local and bounded" from the handoff.

Assessing the four items actively in progress (per `CLAUDE_HANDOFF.md`'s "Recommended next development" 1–4):

| Planned item | Scope-creep risk | Why |
|---|---|---|
| 1. Model explanation view | **Moderate** | Safe if built on `LogisticRegression.coef_` / `RandomForestClassifier.feature_importances_` (already available on the fitted pipeline, zero new dependencies). Risky if it pulls in SHAP/LIME or a new plotting stack — that's a scope-creep trap for a solo 40-hour build. |
| 2. "Bad file" demo fixture | **Low** | A small static CSV with a missing value / duplicate row plus a button to load it is well-bounded and mirrors existing code paths (`check_data`). |
| 3. Human-readable report download | **Moderate** | Safe if it's a text/Markdown render of the existing `public_report(run)` dict (already used for the JSON download). Risky if it introduces a PDF library (reportlab, weasyprint) or a templating engine — unnecessary new dependency and failure surface for a solo hackathon build. |
| 4. "Prototype only" label | **Low** | Trivial UI text/badge addition. |

Item 5 (time-aware evaluation mode) is explicitly deferred by the handoff itself ("Do not add it just to make the app sound more industrial") and is correctly *not* among Team A's active work — good scope discipline so far.

**Fix (concrete):** For items 1 and 3, explicitly constrain to native sklearn attributes and to reusing `public_report()`/plain text, respectively — no new third-party dependencies. Add this constraint to whatever spec Team A is working from, if not already implicit.

---

## 4. Upload errors and saved-run state understandable

**Verdict: Concern** (error copy is genuinely good; saved-run identification and disclosure have real gaps)

**`check_data()` messages (core.py) — all plain language, Pass:**
Walked every error/warning string: `'Missing required columns: ...'`, `'Use between 50 and 50000 rows for this local prototype.'`, `'Some required readings or failure labels are empty. Correct them before training.'`, `f'{col} must contain finite numbers in every row.'`, `f'{col} contains negative readings. Check the units and values.'`, `'Type must be L or M or H.'`, `'Machine failure must be 0 for no failure or 1 for failure.'`, `f'{duplicates} repeated examples will be removed before splitting the data. IDs do not make repeated readings unique.'`, `'Identical readings have conflicting failure labels. Resolve these before training.'`, `'At least 10 unique examples of each outcome are required for the three data groups.'`, `'Extra columns are excluded from training. Only the six approved equipment inputs are allowed.'`. Every one names the concrete problem and what to do about it. No jargon beyond the domain terms the user already sees in their own CSV headers. Same for `read_csv()`'s three errors (oversized file, repeated headers, unreadable file). This sub-item is a clean Pass.

**Saved-run / session-state interplay (app.py) — traced carefully:**

Variables: `st.session_state.run`, `.loaded`, `.input_hash`. Sidebar reload logic runs *before* the fingerprint-comparison block later in the script (Streamlit executes top to bottom on every rerun), so:
```python
if fingerprint != st.session_state.get('input_hash'):
    if not st.session_state.get('loaded'):
        st.session_state.pop('run', None)
    st.session_state.input_hash = fingerprint
```
- Clicking "Reload saved model" sets `run` and `loaded=True` in the same rerun, *before* this block executes — so a freshly reloaded run is correctly never popped on the same click. No race condition found.
- If a saved run is loaded (`loaded=True`) and the user then uploads a **different** CSV afterward, the fingerprint changes but the run is **not** cleared, because the pop is gated on `not loaded`. This is very likely intentional (a saved model should stay usable for prediction independent of whatever file happens to be selected), and `results_tab` does disclose it: `st.info('Showing a saved run. These results describe its original dataset rather than the currently selected file.')`.
- However, `prediction_tab` does **not** carry the same disclosure — it only shows `st.caption('Using ' + run['winner'] + ' from dataset ' + run['fingerprint'][:12])`, a fingerprint prefix with no plain-language callout that this may not be the file currently shown in the Data tab. A user who skipped the Model comparison tab and went straight to Prediction after uploading a new file could reasonably believe the model reflects their new upload.
- Clicking "Check and compare models" always fully retrains and sets `loaded=False`, correctly overwriting any prior loaded run — no stale-state bug there.
- No crash paths found (raw=None, empty fingerprint, missing sample file, etc. all degrade gracefully to existing messages).

**Concrete gap:** Saved runs are listed in the sidebar by filename stem, which is `run['fingerprint'][:16]` — a bare hex string (e.g. `a3f9c81b2e4d5f60`). With more than one saved run, the picker gives the user no human-readable way to tell them apart (no timestamp, no winner name, no metric).

**Fix (concrete):**
1. Add the same plain-language "this may not match your currently loaded file" caption to `prediction_tab`, not just `results_tab`.
2. Change the `format_func` on the saved-run `st.selectbox` to something like `f"{x.stem[:8]} · saved {datetime.fromtimestamp(x.stat().st_mtime):%Y-%m-%d %H:%M}"`, or store the winner name/F1 in the filename or a small sidecar so the picker is legible without opening the file.

---

## 5. Final check untouched by model selection

**Verdict: Pass — verified rigorously, this is the strongest part of the codebase**

Traced `train()` in `core.py` line by line:
1. `X_dev, X_test = train_test_split(..., test_size=.2, ...)` then `X_train, X_val = train_test_split(X_dev, ..., test_size=.25, ...)` → exactly the documented 60/20/20 split (0.8 × 0.75 = 0.6 train, 0.8 × 0.25 = 0.2 selection).
2. Each pipeline's `ColumnTransformer` (StandardScaler + OneHotEncoder) is fit only inside `model.fit(X_train, y_train)` — preprocessing never sees validation or test rows before prediction, so there is no leakage through preprocessing either, not just through the estimator.
3. `validation[name] = metrics(y_val, model.predict(X_val))` is computed for both models using only `X_val`/`y_val`.
4. `winner = max(validation, key=lambda name: validation[name]['F1'])` — this line is the selection decision, and it is a pure function of the `validation` dict. At this point in the code, `X_test`/`y_test` have not been referenced anywhere. The inline comment even states this explicitly: `# Selection is locked using validation examples before any test predictions.`
5. Only *after* `winner` is fixed does `final = {name: metrics(y_test, model.predict(X_test)) for name, model in models.items()}` run. This calls `.predict()` on already-fitted models (no refit) for *both* models, purely for the comparison table shown in `results_tab` — it does not feed back into `winner`.
6. No code path re-assigns `winner`, re-splits data, or re-fits any model after this line. `models[winner]` (fit once on `X_train`) is what `save_run()` and `predict()` use downstream.

This matches `test_core.py::test_no_leakage_or_overlap`, which independently asserts the three split-index sets are disjoint and sum to the full row count — corroborating evidence already in the test suite. No leakage found; the "no test-set leakage" claim in the README is accurate as implemented.

---

## 6. Classification clearly separated from real failure forecasting

**Verdict: Pass** (same UI-signal caveat as Item 2)

No string in the reviewed `app.py` uses time-to-failure, remaining-useful-life, "safe to operate," or certification language. The two places most at risk of misreading are both explicitly guarded:
- `st.warning('The model flags a failure pattern in these readings.')` — "flags a pattern," not "predicts a failure" or "will fail."
- Immediately below: `st.caption('This is a model classification. It does not establish that equipment is safe or identify a repair.')` — directly disclaims the two likeliest misreadings (safety, repair authorization).

The only residual risk is the same one noted in Item 2: `st.success(...)` on the "no failure flagged" branch visually signals "all clear" more strongly than the accompanying text intends. Recommend the same fix (`st.info` instead of `st.success`) purely for that one call.

---

## Other findings

1. **House-style self-violation (comma before "and") — in `CLAUDE_HANDOFF.md` itself, not in code.** The handoff states the rule "avoid commas immediately before the word 'and'" but its own prose breaks it twice:
   - "Review failures found, failures missed, and false alarms." (Product goal, step 4)
   - "It rejects missing values, invalid types, negative readings, conflicting labels, too few examples, duplicate headers, and files outside the 50 to 50000 row range." (Current modeling design)
   By contrast, I found **no** such Oxford-comma violations in the actual `app.py`/`core.py` user-facing strings in the reviewed snapshot — the code itself follows the rule; only the handoff document doesn't. Worth a quick copy-edit pass on `CLAUDE_HANDOFF.md` since it's the document setting the standard.

2. **Possible BOM/encoding mismatch in `read_csv()` — investigated, not confirmed as a bug.** `read_csv()` decodes with `utf-8-sig` (BOM-safe) only for the duplicate-header check, then calls `pd.read_csv(io.BytesIO(raw))` without specifying an encoding for the actual parse. I tested this concern directly:
   ```python
   raw = b'\xef\xbb\xbfType,Air temperature [K]\nL,300\n'
   pd.read_csv(io.BytesIO(raw)).columns  # -> ['Type', 'Air temperature [K]'], BOM correctly stripped
   ```
   Against the environment's available pandas (2.3.3), the BOM is stripped automatically with no encoding argument, so no bug manifests. **Caveat:** `requirements.txt` pins `pandas==3.0.6`, and this device's Linux Python could not run the project's actual Windows `.venv` to verify against that exact pinned version. Given this is a plausible real-world path (Excel-exported CSVs commonly carry a UTF-8 BOM, and the target user is "an engineer with basic Python experience" who may well export from Excel), I'd still add one cheap regression test — `test_core.py` currently has no BOM case at all — rather than rely on this review's proxy environment.

3. **Test coverage gap:** No existing test in `test_core.py` exercises a BOM-prefixed upload, or the sidebar's stale-loaded-run-then-different-upload path traced in Item 4. Both are cheap to add and directly de-risk points raised above.

4. **Security posture is sound:** `save_run`/model loading is correctly restricted to `ROOT / 'models'` globbing for `.joblib` files created by this app; no path from an uploaded file ever reaches `joblib.load`. This matches the handoff's explicit warning about joblib's code-execution risk and needs no change.

