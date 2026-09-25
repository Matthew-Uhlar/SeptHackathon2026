# SignalReady demo video script

Word-for-word narration for submission item 3 (demo video). Target length about 4 minutes 45 seconds. Hard limit 5 minutes. It follows DEMO_GUIDE.md and matches the app at commit 85255c2.

The timings assume a calm pace of about 150 words per minute. They have not been measured with a human reader yet. Do one timed read-through before recording and cut the lines marked *(trim if long)* first.

A captioned screen recording without voice is kept at demo/SignalReady_demo.mp4 (4 minutes 29 seconds, made by demo/record_demo.py from the current app). This script is for a narrated version or a voiceover on top of that recording.

## Before you record

- Start the app with Start SignalReady.bat (or the README command). Use a browser window at least 1280 pixels wide so the tables fit.
- Use an empty model folder so the sidebar starts clean: close the app and move or rename the models folder first. Do not delete earlier saved runs you want to keep.
- Select **Included sample** once to confirm the data loads. Then select **Try a flawed sample** so the recording starts there.
- Have data/new_readings.csv ready to pick in the file dialog for Section 7.
- Close other tabs and notifications. No personal files or names should appear on screen.
- Numbers in square brackets such as [found] must be read from the screen during the recording. Reference values from a Linux check on September 25 2026 are given in the notes. They can change with library versions so never read them from this page.

## Section 1. The problem (0:00 to 0:25)

**Shot:** App header with the title SignalReady and the blue notice about generated data. Sidebar visible.

**Narration:**

> Hi, I'm Matt Uhlar. This is SignalReady, my prototype for Theme 1 of the ABB Accelerator: the Agentic Predictive Maintenance Studio.
>
> A failure model can score well and still be useless. Failures are rare so a model that never predicts one can look about 97 percent accurate. SignalReady makes those hidden mistakes visible before anyone trusts a model.

## Section 2. Bad data gets caught first (0:25 to 0:55)

**Shot:** Sidebar Data source is **Try a flawed sample**. Tab **1 Data readiness** is open. Show the metrics row / the red errors / the yellow warning "1 repeated example will be removed". Then the **Where to correct the file** table. Hover over the grey **Check and compare models** button.

**Narration:**

> Every run starts with a data check. This built-in sample has two planted problems.
>
> The red messages block training because a required reading is empty. The warning says one example is repeated and will be removed.
>
> This table points to the exact place to fix: data row 10, air temperature. And the Check and compare button stays disabled. The app will not train on data it knows is broken.

**Notes:** Reference values: 2 blocking issues / 1 repeated example / row 10 Air temperature [K].

## Section 3. Clean data and answer giveaways (0:55 to 1:45)

**Shot:** Switch Data source to **Included sample**. Show the blue line "4 excluded columns may give away the answer: HDF, OSF, PWF, TWF. They are already kept out of training." Optionally open **Why these columns look like answer giveaways** for two seconds. Open the **Column profile** expander for three seconds and close it. Show the outcome balance line. Click **Check and compare models**. The app switches to Model comparison.

**Narration:**

> Now the real sample: ten thousand generated readings from the public UCI AI4I dataset.
>
> This blue note is the studio profiling the file. Four failure-type columns agree with the failure label almost perfectly. They may record the answer or be filled in after the outcome. They are already kept out of training. Only six approved inputs can enter: product type plus five sensor readings.
>
> The column profile summarizes every column. Only [failures] examples are failures: about [share] percent.
>
> One click trains two models. Sixty percent of the data trains them. Twenty percent picks the winner. The last twenty percent is a final check that plays no part in the choice.

**Notes:** Reference values: the note names HDF / OSF / PWF / TWF (UDI / Product ID / RNF are not flagged). The expander lists one "Possible answer giveaway:" bullet per column. 339 failure examples (3.4%). Training takes a few seconds.

## Section 4. What the models missed (1:45 to 2:40)

**Shot:** Tab **2 Model comparison**. Show the Selected model heading / the three metrics / the table. Point at the **Always no failure** row. Scroll to **What these results mean**. Open **Completion checks** and click **Run completion checks**. Wait for the table (a repeat training run takes a few seconds). The table shows Check / Result / Detail with the evidence wrapped so it can be read on screen. Pause on it.

**Narration:**

> The selected model is [winner]. It was chosen on the selection group before the final check was ever scored.
>
> On the final check it found [found] failures. It missed [missed]. It raised [false alarms] false alarms.
>
> Now the bottom row. Always saying no failure gets [correct normal] of [total] readings right and catches zero failures. That's the trap this table exposes.
>
> Below it the studio writes out what the numbers mean in plain language, including the trade-off with the other model. *(trim if long)*
>
> These six completion checks come straight from my proposal and the app retests them live. For example: answer columns never enter training and reloading preserves predictions. All six pass.

**Notes:** Reference values: winner Random forest / 52 found / 16 missed / 40 false alarms. Always no failure: 1,932 correct of 2,000 / 0 found. All six checks Passed. RESULTS_SUMMARY.md holds the same values.

## Section 5. What drove the model (2:40 to 2:55)

**Shot:** Tab **4 What drove the model**. Show the bar chart and the caption under it.

**Narration:**

> This tab shows which inputs the fitted model relied on most: here [top input] and [second input]. The caption says what it is not: a physical cause or an explanation of one prediction.

**Notes:** Reference values: Torque [Nm] then Rotational speed [rpm].

## Section 6. Save / reload / one prediction (2:55 to 3:55)

**Shot:** Back to **2 Model comparison**. Click **Save selected model locally**. Show the green Saved message and the **Saved local runs** picker in the sidebar. Refresh the browser page. Click **Reload saved model** in the sidebar. The app opens Model comparison with a green restored message. Open **3 Try a prediction**. Set Rotational speed to 1300 and Torque to 65. Click **Check these readings**. Show the flag / the **Model score (uncalibrated)** / the band sentence / the grey note. Scroll to **How the score responds to each reading**. Then set Air temperature to 310 and check again.

**Narration:**

> One click saves the model on this computer with its audit details. I'll refresh the page to simulate a restart and reload it from the sidebar.
>
> Now a new set of readings with low speed and high torque. The model flags a failure pattern.
>
> It also shows a model score. I label it uncalibrated on purpose. It is not the chance that this machine will fail.
>
> The what-if table swaps one reading at a time for its training average. Putting torque back to average would clear the flag on its own. That describes the model, not the physics.
>
> And if I enter an air temperature outside anything it saw in training the app warns that the model may be unreliable here. *(trim if long)*

**Notes:** Reference results: speed 1300 with torque 65 is flagged with a score of about 0.63 ("Well above the 0.5 threshold"). The top what-if row is Torque with "Flag would change" ticked. Air temperature 310 gives the outside-the-training-range warning. With the default readings the score is 0.000 and the app says no single change moves it, which is less interesting to show.

## Section 7. Score a whole file (3:55 to 4:20)

**Shot:** Scroll to **Score a file of readings**. Upload data/new_readings.csv. Show the three metrics / the results table / open the **rows were skipped** expander. Point at **Download scored readings**.

**Narration:**

> Engineers rarely check one reading at a time. Here I score a file of new readings. [scored] rows are scored. [flagged] are flagged. [outside] fall outside the training range. [skipped] invalid rows are skipped with a plain reason instead of breaking the batch. The results download as a CSV.

**Notes:** Reference values: 29 scored / 4 flagged / 3 outside training range / 2 skipped (row 30 invalid product type / row 31 negative reading).

## Section 8. Close and impact (4:20 to 4:50)

**Shot:** Return to **2 Model comparison** with the table visible. End on the app header.

**Narration:**

> On the agentic part: the studio runs the whole modeling pipeline itself but I kept the engineer in the loop on purpose. It uses generated data on one computer. It doesn't connect to machines or forecast when a breakdown will happen.
>
> Next comes a trial on real plant data with time-aware testing then a scoring service for plant systems. The goal is simple: engineers should see what a model misses before they trust it. Thanks for watching.

## Running time

| Section | Start | End |
|---|---|---|
| 1 Problem | 0:00 | 0:25 |
| 2 Bad data | 0:25 | 0:55 |
| 3 Clean data and answer giveaways | 0:55 | 1:45 |
| 4 Model comparison and completion checks | 1:45 | 2:40 |
| 5 What drove the model | 2:40 | 2:55 |
| 6 Save / reload / one prediction | 2:55 | 3:55 |
| 7 Score a whole file | 3:55 | 4:20 |
| 8 Close | 4:20 | 4:50 |

The narration is about 630 words which is roughly 4 minutes 12 seconds of speaking at 150 words per minute. Training / the completion checks / the page refresh / the file upload add about 25 seconds of pauses. That puts the full take near 4:40 to 4:50. If the timed read-through runs past 4:55 cut both *(trim if long)* lines (about 50 words or 20 seconds) and keep the pause while the completion checks run short.

## How the video covers the judging criteria

This table is for planning. Do not read it aloud.

| Criterion | Where the video shows it |
|---|---|
| Innovation and creativity (20%) | Section 1 framing / Section 3 answer-giveaway detection / Section 4 baseline row and live completion checks |
| Technical excellence (25%) | Section 3 split discipline / Section 4 completion checks / Section 6 reload with validation |
| Problem-solution fit (20%) | Sections 2 to 7 walk the Theme 1 flow: profiling and quality / training / comparison / explanation / packaging / inference |
| Scalability and feasibility (15%) | Section 7 batch scoring / Section 8 next steps to plant data and a scoring service |
| User experience (10%) | Numbered tabs / disabled button on bad data / correction table / plain-language summary / skipped rows explained |
| Presentation and demo (10%) | Timed sections / one story from bad data to scored files / closing impact statement |

## Recording tips

- Record at 1080p. Zoom the browser to 110 or 125 percent so table text is readable.
- Move the mouse slowly and pause for one second on each number you read out.
- If a take goes wrong keep recording and restart the sentence. Cut it later.
- Export as MP4. Check the portal's size limit before uploading. If the portal wants a link, upload to a service that allows unlisted sharing and test the link in a private browser window.
