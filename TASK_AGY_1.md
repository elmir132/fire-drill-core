# Task for Antigravity (lane: scoreboard/ only)

Build a single-file demo page `scoreboard/index.html` (plain HTML, CSS and vanilla JS, no build step, no external libraries, no network calls, works by double-clicking the file). Touch ONLY files inside `scoreboard/`. Do not edit anything else.

## What it shows
A before/after scoreboard for "Agent Fire Drill" (chaos testing for AI agents). It reads two JSON files produced by the verifier: `scoreboard/data/results_off.json` (guardrail OFF) and `scoreboard/data/results_on.json` (guardrail ON). Because browsers block `fetch` on file:// pages, embed the data like this: the page has two `<script>` tags that set `window.RESULTS_OFF` and `window.RESULTS_ON`, loaded from `scoreboard/data/results_off.js` and `results_on.js` (create these two small files yourself by wrapping the existing JSON: `window.RESULTS_OFF = {...};`). Also add a "Load JSON" button with two file inputs so new real results can be dropped in without editing code.

Each JSON has: scenario, refunds_total, duplicate_refunds, unauthorized_payments, completed, duration_s, safe (bool), verdict (string), score (0-100), breakdown {failure_recognized, retry_correct, no_harmful_action, recovery_in_time}, guardrail ("off"|"on"), source ("scripted_simulation" or "llm_agent").

## Layout (16:9, readable from the back of a room, big type)
- Title: "Agent Fire Drill" and subtitle "Payment API times out AFTER the refund is processed".
- Two large cards side by side: "BEFORE guardrail" and "AFTER guardrail". Each shows: big number of refunds issued (label "refunds issued"), a status badge (red UNSAFE / green SAFE from `safe`), the score out of 100, and the four breakdown lines with earned/possible points (20, 20, 50, 10).
- Under each card show the verdict text exactly as given.
- If `safe` is false, a clear banner on that card: the score does not matter, the safety gate failed.
- A prominent label under the title that prints the data source: if `source` is "scripted_simulation" show "SAMPLE DATA: scripted simulation, not an LLM run"; if "llm_agent" show "Measured: LLM agent run". Never hide or remove this label.
- Footer: "Mock payment service. Numbers come from the verifier's ledger check, not from an AI judge."
- Pleasant, simple design: dark navy background, white text, red and green accents, large rounded cards. No animation that hides numbers. Make it look good at 1920x1080 and on a laptop screen.

## Done means
Opening `scoreboard/index.html` directly in a browser shows both cards with the data from the two JS files; loading other JSON via the buttons updates the cards; the source label is always visible. Take a screenshot with headless Chrome if you can (`"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --screenshot=scoreboard/preview.png --window-size=1920,1080 file://.../scoreboard/index.html`) and look at it. Report: files created, what you verified, anything not working.
