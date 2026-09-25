# SignalReady demo video script

Word-for-word narration for submission item 3 (demo video). Target length about 4 minutes 35 seconds. Hard limit 5 minutes. It follows DEMO_GUIDE.md.

The timings assume a calm pace of about 150 words per minute. They have not been measured with a human reader yet. Do one timed read-through before recording and trim the lines marked *(trim if long)* first.

## Before you record

- Start the app with Start SignalReady.bat (or the README command). Use a browser window at least 1280 pixels wide so the comparison table fits.
- Use an empty model folder so the sidebar starts clean: close the app and move or rename the models folder first. Do not delete earlier saved runs you want to keep.
- Select **Included sample** once to confirm the data loads. Then select **Try a flawed sample** so the recording starts there.
- Close other tabs and notifications. No personal files or names should appear on screen.
- Numbers in square brackets such as [found] must be read from the screen during the recording. Reference values from a Linux check on September 25 2026 are given in the notes. They can change with library versions so never read them from this page.
- Steps marked **INTEGRATION-DEPENDENT** describe features that were still being integrated when this script was written. Record them only if you can see them in the app. Skip them otherwise. The script works without them.

## Section 1. The problem (0:00 to 0:25)

**Shot:** App header with the title SignalReady and the blue notice about generated data. Sidebar visible.

**Narration:**

> Hi, I'm Matt Uhlar. This is SignalReady, my prototype for Theme 1 of the ABB Accelerator: the Agentic Predictive Maintenance Studio.
>
> Here's the problem it tackles. A failure model can score well and still be useless. Failures are rare so a model that never predicts one can look about 97 percent accurate. SignalReady is a guided studio that makes those hidden mistakes visible before anyone trusts a model.

## Section 2. Bad data gets caught first (0:25 to 1:05)

**Shot:** Sidebar Data source is **Try a flawed sample**. Tab **1 Data readiness** is open. Show the metrics row / the red errors / the yellow warnings. Then the **Where to correct the file** table. Hover over the grey **Check and compare models** button.

**Narration:**

> Every run starts with a data check. This built-in sample has two planted problems.
>
> The red messages block training: a required reading is empty. The yellow warning says one example is repeated. It will be removed so the same reading can't land in both training and testing.
>
> This table points to the exact place to fix: data row 10, air temperature, missing value. It shows the location but not the value so private readings are not repeated on screen.
>
> Notice the Check and compare button is disabled. The app will not train on data it knows is broken.

**Notes:** Reference values: 2 blocking issues / 1 repeated example / row 10 Air temperature [K].

**INTEGRATION-DEPENDENT insert A (about 15 seconds). Column profile and answer-giveaway detection.** Only if a column profile appears on Data readiness:

> The studio also profiles each column. Here it flags the failure-type columns as answer giveaways. They are only known after a failure so they are kept out of training.

## Section 3. Clean data and the rare-failure trap (1:05 to 1:40)

**Shot:** Switch Data source to **Included sample**. Show the Readings metric / the outcome balance line / the Excluded columns caption / the green ready message. Click **Check and compare models**. The app switches to Model comparison.

**Narration:**

> Now the real sample: ten thousand generated equipment readings from the public UCI AI4I dataset.
>
> Only [failures] of them are failures. That's about [share] percent. That's why this app never leads with accuracy.
>
> The ID columns and the failure-type columns are excluded automatically. Only six approved inputs can enter training: product type plus five sensor readings.
>
> One click trains two models. Sixty percent of the examples train them. A separate twenty percent picks the winner. The last twenty percent is a final check that plays no part in the choice.

**Notes:** Reference values: 339 failure examples (3.4%) and 9,661 no-failure examples. Training takes a few seconds.

## Section 4. What the models missed (1:40 to 2:40)

**Shot:** Tab **2 Model comparison**. Show the Selected model heading / the three metrics / the full table. Point at the **Always no failure** row. Open the **How this run was checked** expander for two seconds. Click **Download results report (readable)**.

**Narration:**

> The selected model is [winner]. It was chosen by F1 on the selection group before the final check was ever scored.
>
> On the final check it found [found] failures. It missed [missed]. It raised [false alarms] false alarms.
>
> Now look at the bottom row. A model that always says no failure gets [correct normal] of [total] readings right. It catches zero failures. That's the trap this table is built to expose.
>
> The comparison also keeps the losing model in view. Logistic regression catches a different mix: more failures found but far more false alarms. *(trim if long)*
>
> Every run records its data fingerprint / random seed / split sizes / software versions. The same details go into this downloadable report so anyone can check the result later.

**Notes:** Reference values: winner Random forest / 52 found / 16 missed / 40 false alarms. Always no failure: 1,932 correct of 2,000 / 0 found. Logistic regression: 56 found / 12 missed / 326 false alarms. If the logistic regression line no longer matches the screen, drop it.

**INTEGRATION-DEPENDENT insert B (about 15 seconds). Plain-language summary and completion checks.** Only if they appear on Model comparison:

> Below the table the studio writes a plain-language summary of the run. These live checks confirm the proposal's promises for this run: answer columns never entered training and both models used the same final examples.

## Section 5. What drove the model (2:40 to 3:10)

**Shot:** Tab **4 What drove the model**. Show the bar chart and the caption under it.

**Narration:**

> This tab shows which inputs the fitted model leaned on. For this run it's mostly [top input] and [second input].
>
> The caption says what this is not. It's not a physical cause of failure and it doesn't explain one prediction. I kept those limits on screen on purpose so an engineer doesn't over-read the chart.

**Notes:** Reference values: Torque [Nm] then Rotational speed [rpm] then Tool wear [min].

## Section 6. Save / reload / predict (3:10 to 4:05)

**Shot:** Back to **2 Model comparison**. Click **Save selected model locally**. Show the green Saved message and the new **Saved local runs** picker in the sidebar. Refresh the browser page. Click **Reload saved model** in the sidebar. Open **3 Try a prediction**. Click **Check these readings** with the defaults. Then set Rotational speed to 1300 and Torque to 65 and check again. Then set Air temperature to 310 and check again.

**Narration:**

> One click saves the selected model on this computer with its audit details. I'll refresh the page to simulate a restart and reload it from the sidebar.
>
> Now a new set of readings. With these defaults the model does not flag a failure pattern.
>
> If I lower the speed and raise the torque the model flags a failure pattern.
>
> And if I enter an air temperature outside anything it saw in training the app warns that the model may be unreliable here. It tells you when it's guessing.

**Notes:** Reference results: defaults give no flag. Speed 1300 with torque 65 gives a flag. Air temperature 310 gives the outside-the-training-range warning. Check these combinations before recording because a different library version can change them.

**INTEGRATION-DEPENDENT insert C (about 20 seconds). Model score / what-if / batch scoring.** Only if they appear on Try a prediction:

> The model also gives a score. It's labelled as uncalibrated because it is not a failure probability. The what-if view shows how the result responds when one reading changes. And a whole CSV of readings can be scored at once and downloaded.

## Section 7. Close and impact (4:05 to 4:35)

**Shot:** Return to **2 Model comparison** with the table visible. End on the app header.

**Narration:**

> A word on the agentic part. I kept the engineer in the loop on purpose.
>
> To be clear about scope: this runs on one computer with generated data. It doesn't connect to machines. It doesn't forecast when a breakdown will happen or give calibrated probabilities. The engineer makes every decision. The studio does the modeling work between those decisions and shows its mistakes honestly.
>
> The next step is a trial on real plant data with time-aware testing then a scoring service for plant systems. The impact I'm aiming for is simple: engineers should see what a model misses before they trust it. Thanks for watching.

## Running time

| Section | Start | End |
|---|---|---|
| 1 Problem | 0:00 | 0:25 |
| 2 Bad data | 0:25 | 1:05 |
| 3 Clean data | 1:05 | 1:40 |
| 4 Model comparison | 1:40 | 2:40 |
| 5 What drove the model | 2:40 | 3:10 |
| 6 Save / reload / predict | 3:10 | 4:05 |
| 7 Close | 4:05 | 4:35 |

The core narration is about 655 words which is roughly 4 minutes 20 seconds of speaking. Clicks / training / the page refresh add pauses so the first timed read-through decides what to trim.

Inserts A / B / C add about 50 seconds if all three are recorded. In that case drop the lines marked *(trim if long)* and shorten Section 5 to its first sentence to stay under 5 minutes.

## How the video covers the judging criteria

This table is for planning. Do not read it aloud.

| Criterion | Where the video shows it |
|---|---|
| Innovation and creativity (20%) | Section 1 framing and Section 4 baseline row: the studio is built around exposing mistakes rather than a single score |
| Technical excellence (25%) | Section 3 split discipline / Section 4 audit details / Section 6 reload with validation |
| Problem-solution fit (20%) | Sections 2 to 6 walk the Theme 1 flow: data quality / training / comparison / explanation / packaging / inference |
| Scalability and feasibility (15%) | Section 7: runs on one ordinary computer with standard open-source tools. Clear next steps to plant data and a scoring service |
| User experience (10%) | Numbered tabs / disabled button on bad data / correction table / plain-language warnings |
| Presentation and demo (10%) | Timed sections / one story from bad data to a prediction / closing impact statement |

## Recording tips

- Record at 1080p. Zoom the browser to 110 or 125 percent so table text is readable.
- Move the mouse slowly and pause for one second on each number you read out.
- If a take goes wrong, keep recording and restart the sentence. Cut it later.
- Export as MP4. Check the portal's size limit before uploading. If the portal wants a link, upload to a service that allows unlisted sharing and test the link in a private browser window.
