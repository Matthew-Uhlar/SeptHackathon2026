"""Record a captioned walkthrough of SignalReady as an MP4.

This is a helper for producing the demo video. It is not part of the app.
It starts the app on a spare port with an empty temporary model folder and
drives the real UI with Playwright while captions follow DEMO_SCRIPT.md.
The numbers in the captions come from the same seeded training run that the
app performs so they match the screen.

Extra requirements (not needed to run the app):
    pip install playwright imageio-ffmpeg

Usage:
    python demo/record_demo.py [--out demo/SignalReady_demo.mp4] [--chromium PATH]
"""
import argparse
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import read_csv, train, class_balance  # noqa: E402

WIDTH, HEIGHT = 1280, 720
READ_RATE = 3.0  # words per second; tuned so the walkthrough stays near five minutes
TABS = ['1  Data readiness', '2  Model comparison', '3  Try a prediction', '4  What drove the model']

OVERLAY_JS = """
(args) => {
  const [kind, text] = args;
  let card = document.getElementById('demo-card');
  let cap = document.getElementById('demo-caption');
  if (!cap) {
    cap = document.createElement('div');
    cap.id = 'demo-caption';
    cap.style.cssText = 'position:fixed;left:50%;bottom:22px;transform:translateX(-50%);max-width:1040px;'
      + 'background:rgba(16,40,46,0.92);color:#fff;font:500 21px/1.4 system-ui,sans-serif;'
      + 'padding:12px 22px;border-radius:10px;z-index:2147483646;text-align:center;box-shadow:0 4px 18px rgba(0,0,0,.25)';
    document.body.appendChild(cap);
  }
  if (!card) {
    card = document.createElement('div');
    card.id = 'demo-card';
    card.style.cssText = 'position:fixed;inset:0;background:#10282e;color:#fff;display:none;flex-direction:column;'
      + 'justify-content:center;align-items:center;text-align:center;z-index:2147483647;font-family:system-ui,sans-serif;padding:60px';
    document.body.appendChild(card);
  }
  if (kind === 'caption') { cap.textContent = text; cap.style.display = text ? 'block' : 'none'; card.style.display = 'none'; }
  if (kind === 'card') { card.innerHTML = text; card.style.display = 'flex'; cap.style.display = 'none'; }
  if (kind === 'clear') { card.style.display = 'none'; cap.style.display = 'none'; }
}
"""

HIDE_CHROME_CSS = ('[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stAppDeployButton"],[data-testid="stMainMenu"],'
                   '[data-testid="stDecoration"],[data-testid="stStatusWidget"]{visibility:hidden !important}')


# A rerun is finished when the running icon is gone and no element is marked stale (faded).
RUNNING_JS = """() => !!document.querySelector('[data-testid="stStatusWidgetRunningIcon"], [data-testid="stStatusWidgetRunningManIcon"], [data-testid="stSpinner"], [data-stale="true"]')"""


def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def facts():
    df = read_csv((ROOT / 'data/ai4i2020.csv').read_bytes())
    run = train(df)
    balance = class_balance(df)
    winner = run['winner']
    other = next(n for n in run['test'] if n not in (winner, 'Always no failure'))
    base = run['test']['Always no failure']
    from inference import model_score, score_batch, batch_summary
    stressed = {'Type': 'L', 'Air temperature [K]': 300., 'Process temperature [K]': 310., 'Rotational speed [rpm]': 1500.,
                'Torque [Nm]': 65., 'Tool wear [min]': 210.}
    batch, problems = score_batch(run, read_csv((ROOT / 'data/new_readings.csv').read_bytes()))
    return {
        'stressed_score': model_score(run, stressed)['score'], 'batch': batch_summary(batch), 'skipped': len(problems),
        'winner': winner, 'other': other,
        'w': run['test'][winner], 'o': run['test'][other],
        'base_correct': base['Correct no-failure readings'],
        'total': run['counts']['final check'],
        'failures': balance['Failure'], 'share': balance['Failure'] / (balance['Failure'] + balance['No failure']),
    }


class Demo:
    def __init__(self, page):
        self.page = page

    def overlay(self, kind, text=''):
        self.page.evaluate(OVERLAY_JS, [kind, text])

    def say(self, text, hold=0.0):
        self.overlay('caption', text)
        time.sleep(max(3.0, len(text.split()) / READ_RATE) + hold)

    def card(self, html, seconds):
        self.overlay('card', html)
        time.sleep(seconds)

    def settle(self, seconds=1.2):
        # Streamlit reruns asynchronously. Wait for the running indicator to clear.
        deadline = time.time() + 60
        while time.time() < deadline:
            running = self.page.evaluate(RUNNING_JS)
            if not running:
                break
            time.sleep(0.3)
        time.sleep(seconds)

    def highlight(self, locator, seconds=1.0):
        locator.scroll_into_view_if_needed()
        locator.evaluate("(el) => { el.dataset.prevOutline = el.style.outline; el.style.outline = '3px solid #e8a33d'; el.style.outlineOffset = '3px'; }")
        time.sleep(seconds)
        locator.evaluate("(el) => { el.style.outline = el.dataset.prevOutline || ''; }")

    def click(self, locator, pause=0.8):
        self.highlight(locator, pause)
        locator.click()
        self.settle()

    def tab(self, label):
        self.click(self.page.get_by_role('tab', name=label), 0.6)

    def scroll_to(self, locator):
        locator.scroll_into_view_if_needed()
        time.sleep(0.6)

    def prepare_page(self):
        self.page.add_style_tag(content=HIDE_CHROME_CSS)
        self.overlay('clear')


def record(out, chromium):
    from playwright.sync_api import sync_playwright

    f = facts()
    w, o = f['w'], f['o']
    port = free_port()
    models = tempfile.mkdtemp(prefix='signalready-demo-models-')
    video_dir = tempfile.mkdtemp(prefix='signalready-demo-video-')
    env = dict(os.environ, SIGNALREADY_MODEL_DIR=models)
    server = subprocess.Popen([sys.executable, '-m', 'streamlit', 'run', str(ROOT / 'app.py'), '--server.address', '127.0.0.1',
                               '--server.port', str(port), '--server.headless', 'true', '--browser.gatherUsageStats', 'false'],
                              cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f'http://127.0.0.1:{port}/'
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium) if chromium else p.chromium.launch()
            # Warm the server before recording so the video does not start on a loading screen.
            warm = browser.new_page()
            for _ in range(60):
                try:
                    warm.goto(url, timeout=5000)
                    warm.get_by_text('Is the data ready?').wait_for(timeout=20000)
                    break
                except Exception:
                    time.sleep(1)
            warm.close()

            context = browser.new_context(viewport={'width': WIDTH, 'height': HEIGHT}, record_video_dir=video_dir,
                                          record_video_size={'width': WIDTH, 'height': HEIGHT})
            page = context.new_page()
            d = Demo(page)
            page.goto(url)
            page.get_by_text('Is the data ready?').wait_for(timeout=60000)
            d.prepare_page()
            radio = page.get_by_test_id('stRadioGroup')

            # Title
            d.card('<div style="font-size:18px;letter-spacing:.2em;opacity:.75">ABB ACCELERATOR 2026 · THEME 1</div>'
                   '<div style="font-size:64px;font-weight:700;margin:18px 0">SignalReady</div>'
                   '<div style="font-size:26px;opacity:.9">A guided studio that shows what a failure model misses before anyone trusts it</div>'
                   '<div style="font-size:18px;opacity:.7;margin-top:36px">Solo prototype by Matt Uhlar · captioned walkthrough</div>', 4)

            # 1. Problem
            d.say('A failure model can score well and still be useless.')
            d.say(f'Failures are rare. A model that never predicts one looks about {1 - f["share"]:.0%} accurate on this data.')
            d.say('SignalReady makes those hidden mistakes visible. The engineer starts every step and reviews every result.')

            # 2. Bad data
            d.click(radio.get_by_text('Try a flawed sample'))
            d.say('Every run starts with a data check. This built-in sample has two planted problems.')
            d.scroll_to(page.get_by_text('Some required readings or failure labels are empty'))
            d.say('Red messages block training: a required reading is empty. The yellow warning says one example is repeated and will be removed.')
            guide = page.locator('[data-testid="stExpander"]', has_text='Where to correct the file')
            d.highlight(guide, 0.4)
            d.say('This table points to the exact place to fix: data row 10 / air temperature / missing value. It never repeats the value itself.', 0.5)
            button = page.get_by_role('button', name='Check and compare models')
            d.highlight(button, 0.4)
            d.say('The Check and compare button stays disabled. The app will not train on data it knows is broken.')

            # 3. Clean data
            d.click(radio.get_by_text('Included sample'))
            d.say(f'Now the real sample: 10,000 generated equipment readings from the public UCI AI4I 2020 dataset.')
            d.scroll_to(page.get_by_text('Outcome balance'))
            d.say(f'Only {f["failures"]} are failures ({f["share"]:.1%}). That is why this app never leads with accuracy.')
            d.scroll_to(page.get_by_text('Possible answer giveaway').first)
            d.say('The studio also spots columns that give away the answer. These failure-type columns are only known after a failure.', 0.5)
            d.say('They are already excluded. Only six approved inputs can enter training: product type plus five sensor readings.')
            d.say('One click trains two models. 60% of examples train them. 20% picks the winner. The last 20% is a final check that plays no part in the choice.')
            d.scroll_to(page.get_by_role('button', name='Check and compare models'))
            d.click(page.get_by_role('button', name='Check and compare models'))
            page.get_by_text('Selected model:').wait_for(timeout=120000)
            d.settle(1.5)

            # 4. Model comparison
            d.say(f'The selected model is {f["winner"].lower()}. F1 on the selection group chose it before the final check was scored.')
            d.say(f'On {f["total"]:,} final-check readings it found {w["Failures found"]} failures / missed {w["Failures missed"]} / raised {w["False alarms"]} false alarms.', 0.5)
            table = page.locator('[data-testid="stDataFrame"]').filter(visible=True).first
            d.scroll_to(table)
            d.highlight(table, 0.3)
            d.say(f'The always-no-failure row gets {f["base_correct"]:,} of {f["total"]:,} readings right yet catches zero failures. That is the trap this table exposes.', 0.5)
            d.say(f'The other model stays in view. {f["other"]} found {o["Failures found"]} failures but raised {o["False alarms"]} false alarms.')
            d.scroll_to(page.get_by_text('What these results mean'))
            d.say('Prepared plain-language sentences explain the checked results so no one has to decode the table alone.', 1.0)
            d.click(page.get_by_text('Completion checks', exact=True))
            d.click(page.get_by_role('button', name='Run completion checks'))
            page.locator('[data-testid="stExpander"]', has_text='Run completion checks').locator('[data-testid="stDataFrame"]').wait_for(timeout=60000)
            d.settle(1.0)
            d.scroll_to(page.locator('[data-testid="stExpander"]', has_text='Run completion checks').locator('[data-testid="stDataFrame"]'))
            d.say('Live completion checks prove the proposal promises for this run: no answer columns / same final examples / a repeat run matches / reloading preserves predictions.', 1.0)
            d.highlight(page.get_by_role('button', name='Download results report (readable)'), 0.3)
            d.say('Every run records its fingerprint / seed / split sizes / software versions. Reports carry the same details.')

            # 5. Explanation
            d.tab(TABS[3])
            d.scroll_to(page.get_by_text('Bars show', exact=False).filter(visible=True).first)
            d.say('This tab shows which inputs the fitted model leaned on most. The caption says it is not a physical cause of failure.', 0.5)

            # 6. Save / reload / predict
            d.tab(TABS[1])
            d.click(page.get_by_role('button', name='Save selected model locally'))
            page.get_by_text('Saved. This run is now available').wait_for(timeout=30000)
            d.highlight(page.get_by_text('Saved local runs'), 0.3)
            d.say('One click saves the model locally with its audit details. Refreshing the page simulates a restart.')
            page.reload()
            page.get_by_text('Is the data ready?').wait_for(timeout=60000)
            d.prepare_page()
            d.click(page.get_by_role('button', name='Reload saved model'))
            d.say('The saved run is validated and restored from the sidebar without retraining.')
            d.tab(TABS[2])
            submit = page.get_by_role('button', name='Check these readings')
            d.click(submit)
            d.say('With typical readings the model does not flag a failure pattern.')
            page.get_by_label('Torque [Nm]').fill('65')
            page.get_by_label('Tool wear [min]').fill('210')
            d.say('Now high torque on a worn tool.')
            d.click(submit)
            d.scroll_to(page.get_by_text('Model score (uncalibrated)'))
            d.say(f'The model flags a failure pattern. Its score is {f["stressed_score"]:.2f}. It is labeled uncalibrated because it is not the chance of failure.', 0.5)
            d.scroll_to(page.get_by_text('How the score responds to each reading'))
            d.say('The what-if table shows which readings pushed this result: torque first then tool wear. It describes the model rather than a physical cause.', 1.0)
            page.get_by_label('Air temperature [K]').fill('310')
            d.say('Now an air temperature outside anything seen in training.')
            d.click(submit)
            d.scroll_to(page.get_by_text('Outside the training range'))
            d.say('The app warns that the model may be unreliable here. It tells you when it is guessing.', 0.5)
            d.scroll_to(page.get_by_text('Score a file of readings'))
            page.locator('[data-testid="stFileUploaderDropzoneInput"]').last.set_input_files(str(ROOT / 'data/new_readings.csv'))
            page.get_by_text('Rows scored').wait_for(timeout=60000)
            d.settle(1.0)
            d.scroll_to(page.get_by_text('Rows scored'))
            b = f['batch']
            d.say(f'A whole file of new readings can be scored at once: {b["Rows scored"]} scored / {b["Flagged"]} flagged / {b["Outside training range"]} outside the training range.', 0.5)
            d.say(f'{f["skipped"]} invalid rows are skipped with a plain reason. The results download as a CSV.', 0.5)

            # 7. Close
            d.tab(TABS[1])
            d.say('Scope: one computer / generated data / no machine connection / no breakdown-time forecast. The engineer makes every decision.')
            d.say('Next step: a trial on real plant data with time-aware testing then a scoring service for plant systems.')
            d.card('<div style="font-size:52px;font-weight:700">SignalReady</div>'
                   '<div style="font-size:26px;margin:22px 0;opacity:.9">See what a model misses before you trust it.</div>'
                   '<div style="font-size:18px;opacity:.75">Python · scikit-learn · pandas · Streamlit · Apache 2.0</div>'
                   '<div style="font-size:16px;opacity:.65;margin-top:26px">Data: AI4I 2020 Predictive Maintenance Dataset by S. Matzka · UCI Machine Learning Repository · CC BY 4.0</div>', 5)

            video = page.video
            context.close()
            browser.close()
            webm = video.path()
    finally:
        server.terminate()
        server.wait(timeout=20)
        shutil.rmtree(models, ignore_errors=True)

    import imageio_ffmpeg
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-loglevel', 'error', '-i', str(webm),
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '26', '-pix_fmt', 'yuv420p', '-r', '25',
                    '-movflags', '+faststart', str(out)], check=True)
    shutil.rmtree(video_dir, ignore_errors=True)
    print(f'Wrote {out}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--out', default=str(ROOT / 'demo/SignalReady_demo.mp4'))
    parser.add_argument('--chromium', default=None, help='Path to a Chromium executable if Playwright browsers are not installed')
    args = parser.parse_args()
    record(args.out, args.chromium)
