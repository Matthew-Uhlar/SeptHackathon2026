# SignalReady demonstration

Target length: under five minutes. This is a presentation outline rather than a measured human delivery time. DEMO_SCRIPT.md turns this outline into a word-for-word narration with a shot list and timings.

A captioned walkthrough without voice is at demo/SignalReady_demo.mp4. demo/record_demo.py re-records it from the live app (it needs Playwright and imageio-ffmpeg which are not app requirements).

## Before recording

Start the app using Start SignalReady.bat. Confirm that the sample data loads. Keep the browser wide enough to show the comparison table. Use the included sample for the recording so no private data appears. Start with an empty model folder so the sidebar is clean. Keep data/new_readings.csv ready for the batch upload.

## 0 to 55 seconds

Explain the problem: a high model score can conceal missed failures or a column that gives away the answer. Choose Try a flawed sample. Show the missing-reading error and repeated-example warning. Open Where to correct the file to show the data row and column that need fixing. Point out that training is blocked until required values are corrected.

## 55 to 105 seconds

Choose Included sample. Show the Possible answer giveaway warnings for the failure-type columns and briefly open Column profile. Explain that only six approved inputs can enter training. Point out the outcome balance line showing how rare failures are. Click Check and compare models. The app opens Model comparison when it finishes. Explain that training uses 60 percent of the rows while model selection and final evaluation each use a separate 20 percent.

## 105 to 160 seconds

On Model comparison explain the actual displayed counts of failures found and failures missed alongside false alarms. Compare them with Always no failure. The selection group chooses the winner before the app evaluates the final group. Point to What these results mean. Open Completion checks and run them. All six should pass for a fresh run on the included sample.

Do not quote results from an old report. Encoder changes and library versions can change measured results. Use the values displayed by the run being demonstrated. RESULTS_SUMMARY.md shows the values from the latest regeneration.

## 160 to 175 seconds

Open What drove the model. Describe the fitted model's input importance. These scores describe how the model was fitted and do not establish a mechanical cause. They do not explain a single prediction.

## 175 to 260 seconds

Save the model. Refresh the page and reload the saved run from the sidebar. Open Try a prediction. Enter a low rotational speed with a high torque (for example 1300 rpm and 65 Nm) to show a flagged reading. Show the Model score (uncalibrated) and its note that the score is not the chance of failure. Show the what-if table. Enter an air temperature outside the training range to show the warning. Then upload data/new_readings.csv under Score a file of readings. Show the counts / the skipped rows with their reasons / the download button.

## 260 to 290 seconds

Close by stating that this is a local guided modeling studio using generated equipment data. The engineer stays in the loop on purpose. It does not forecast a real breakdown time or operate machinery. Its value is making data problems and model mistakes visible to the engineer.

## Submission items still requiring the owner

- Decide whether to submit the captioned recording as it is or record a voiced version from DEMO_SCRIPT.md.
- Confirm current portal requirements and deadline (treat Sep 27 2026 4:59 PM Central as the deadline).
- Provide participant details and a repository URL. Judges need access if the GitHub repository is still private.
- Upload the final files to the event portal.

SUBMISSION_CHECKLIST.md tracks each item with its status.

The live completion checks and the plain-language summary do not make the app an autonomous agent. The demo should use the guided-studio description.
