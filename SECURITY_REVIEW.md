# SignalReady security and privacy review

September 26 2026. Scope: one trusted user running the local Windows app. This is an engineering review with regression checks and dependency scanning rather than a penetration test or a guarantee of complete security.

## Controls

| Area | Protection | Verification |
|---|---|---|
| Network exposure | Server and launcher bind to 127.0.0.1 | Configuration test and local launch |
| Browser requests | CORS and XSRF protections explicitly enabled | Configuration test |
| Accidental file exposure | Static-file serving explicitly disabled | Configuration test |
| Diagnostics | Browser error details hidden; application errors use bounded messages | Configuration test and error regression suite |
| Telemetry | Streamlit usage statistics disabled | Configuration test |
| Uploads | CSV only in the UI; UTF-8 and header/row checks; 10 MB byte limit; 64-column cap; training and batch row limits | Input and security regression tests |
| Upload retention | Uploads processed in memory; Clear session data resets upload widgets and active results | Test with training and batch uploads followed by clearing and reloading |
| Export privacy | Audit includes every row's status without repeating rejected values; model/data identity accompanies exports | Export regression tests |
| Spreadsheet formulas | Formula-like ID strings including leading line breaks or whitespace receive an apostrophe | Parametrized regression tests |
| Saved models | No uploaded pickle/model endpoint; only trusted local joblib files; structural and version checks; unique atomic saves | Persistence and corruption tests |
| Dependencies | Pinned app dependencies; installed environment scanned using pip-audit 2.10.1 | DEPENDENCY_AUDIT.json |

## Dependency scan

The first scan identified advisories for pip 25.0.1. The project virtual environment's installer was updated to pip 26.2.1. The repeat scan covered 48 installed packages with zero skipped packages and reported no known vulnerabilities. The original application dependencies were not changed. Only package names and versions were sent to the advisory service. No uploaded readings or model files were sent.

The scanner was installed in a separate audit environment rather than added to runtime requirements. This finding is dated evidence. Future vulnerabilities can be disclosed after this scan. Follow README setup instructions to update pip when creating a new environment and periodically repeat dependency auditing.

## Data handling and limits

Uploaded training and batch CSV files are not automatically written to disk by application code. Explicit Save writes a fitted model with metadata and ranges to the local models folder. Models can reveal information about training data even without the raw CSV. Explicit downloads contain the displayed results and approved readings. Treat model files and downloads as sensitive when their source data is sensitive.

Clear session data resets the current browser session's uploads and results. It does not delete saved models or downloaded files. It does not promise forensic erasure from RAM / operating-system swap / browser caches or backups. Close the server when finished and use the operating system's protected account and disk encryption when handling confidential data.

Joblib uses pickle. Validation happens after deserialization and cannot make an untrusted file safe. A model folder is a trusted code boundary: never copy in downloaded model files or expose a writeable shared model folder to untrusted users. The saved-run comparison also reads that folder.

There is no application login / multi-user isolation / app-level encryption / TLS endpoint. These are not supplied by localhost binding. Another process or user already controlling the computer is outside this app's protection. Do not expose this prototype through a public tunnel or change its listener to 0.0.0.0. A hosted or shared version needs a separate authentication / authorization / encrypted transport / storage and retention design before use.

## Remaining release checks

Watch and re-record the demo for the new controls. Fresh-machine Windows installation remains a separate verification. Review the configured user account and storage permissions for the machine that will hold confidential data. No real industrial data or third-party service was used during these tests.
