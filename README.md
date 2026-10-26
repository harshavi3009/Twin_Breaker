# Twin-Breaker

**Team Obsidian · CASCADE '26 · Problem Statement 2.1, *The First 10 Minutes* · Theme 2, *Crisis Before Crisis***

Twin-Breaker is a calibrated crisis-belief engine for a city duty officer. When two episodes look almost identical in their sensor data (a real cascading flood and a storm that is only noise), the engine can **ASK** one well-chosen question of a responder in the field. The answer changes the belief in a way the passive data cannot, so the two episodes are separated sooner. The belief also stays steady under three stress cases: a rumour wave, a drain-gateway outage, and a camera cut-out.

> **All data in this repository is synthetic and simulated.** The scale is inspired by a published 2005 Mumbai rainfall figure (NIDM). It is not real telemetry, and the event is fictional, set at a real location.

## Live demo

- **Twin test:** https://twin-breaker.vercel.app/twin
- **Control panel:** https://twin-breaker.vercel.app/

The hosted build runs the **scripted demo** only (see [Scripted demo](#scripted-demo)). Live streams are not deployed.

## What the system does

For each minute of an episode the engine:

1. **Ingests** events from drain gateways, rain, traffic, calls, hospitals and citizen reports. It drops duplicates, handles late arrivals, and clusters repeated citizen text.
2. **Updates a belief** over four states: Normal, Storm-noise, Incident, Cascade. Sources are weighted by a learned trust score, and correlated sensors on one gateway are discounted.
3. **Decides** one of four actions: WATCH, PREPARE, ALERT, ESCALATE. It uses expected cost, with hysteresis and a minimum dwell time, and an ALERT or ESCALATE needs a passive channel to corroborate it.
4. **Asks** a question when the value of information is above threshold (at most three asks per episode, at least three minutes apart).
5. **Explains** each change: every reading or reply is scored in bits.

A naive baseline (equal-weight Bayes, no trust, no hysteresis, ALERT at P(C) ≥ 0.7) runs alongside for comparison.

## Repository layout

| Path | Contents |
|---|---|
| `engine/` | Ingest, belief, decision, live loop, config (`engine/config/*.json`) |
| `server/` | FastAPI app, HTTP routes, scripted demo (`server/demo.py`) |
| `web/` | `index.html` (control panel), `twin.html` (twin test), `ward3d.js` (schematic 3D view), vendored Chart.js |
| `generator/` | Synthetic world: episodes, passive sensors, marshal responder, sealed truth |
| `eval/` | Metrics, sweeps, precomputed traces, checks (reads sealed truth; not used by the engine) |
| `scenarios/` | Red-team scenario definitions (rumour wave, gateway outage) |
| `tests/` | pytest suite (48 tests) |
| `plans/` | Locked team build plan and member plans |
| `CREDITS.md` | Libraries, data sources and concepts used |

The engine never reads `generator/sealed/`. Only `eval/` does, and only after a run.

## Quick start

Requirements: Python 3.10 or newer.

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows (on macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
```

Run the tests:

```bash
python -m pytest
```

Start the app:

```bash
python -m uvicorn server.app:app --port 8000
```

Then open http://localhost:8000/twin (twin test) or http://localhost:8000/ (control panel).

### Scripted demo

The twin page opens in **Scripted demo** mode by default. Build its streams once:

```bash
python -m server.demo
```

This writes `data/demo/P1A-s0007.jsonl` and `data/demo/P1B-s0007.jsonl` (both gitignored). The demo then:

- raises both twins above the 20 cm responder threshold by minute 7, with Twin A as the cascade and Twin B as the false alarm;
- asks "Water above ankle at Ambazari underpass?" at minute 7 for both twins;
- returns scripted answers with no delay: Twin A says **yes**, Twin B says **no**;
- uses a raised `reply_weight` of 16, so one officer's answer can outweigh the correlated sensors;
- runs minutes 0 to 10.

**The demo's answers are scripted, not measured.** The divergence at minute 9 is a consequence of those answers. It is not evidence that the engine separates real twins. Both pages show a "SCRIPTED DEMO" label whenever this mode is on.

### Live streams

Live mode runs the engine on generated streams. Generate them first:

```bash
python -m generator.gen --world B --split dev --seeds 1-10 --out data/streams
```

This writes JSONL event streams to `data/streams/` and sealed truth to `generator/sealed/` (both gitignored). The DEV seed 7 twins are `P1A-s0007` and `P1B-s0007`.

In live mode, the twins do **not** currently diverge. Their passive data is nearly identical, and at the default λ = 1 the ASK rule never fires on this data. The twin page reports this honestly.

## HTTP API

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Control panel |
| GET | `/twin` | Twin test |
| GET | `/api/health` | Liveness check |
| GET | `/api/episodes` | Twin episodes available |
| GET | `/api/episodes/{id}?lam=1.0&mode=demo\|live` | Per-minute belief, decision, ASK, replies, and statistics |
| POST | `/api/inject` | Red-team runs: `rumour_wave`, `gateway_outage`, `camera_cutout` |
| GET | `/api/results` | `results/eval_summary.json`; returns 404 until the eval has been run |

`lam` is the cost weight for false alarms: higher values make the engine alert less readily.

## Evaluation status

The evaluation code is in `eval/`, but **no evaluation results are committed in this repository**. `results/` is not checked in, so `/api/results` returns 404 and no DEV or EVAL table is reported here.

Parameter choices that were made:

- **`reply_weight`** in the default engine is 1.0. A sweep on DEV seeds 1–10 (twin pairs, honest sealed responder, mean Brier score of P(C) over minutes 12–22) gave 0.491 at 1.0, 0.476 at 4.0 (best), and 0.611 at 8.0. The default stays at 1.0 so the DEV behaviour is unchanged.
- **The demo uses 16**, which is not the DEV-tuned value. The demo setting is labelled as scripted, and it is kept out of the default engine.

## Known limitations

- Live twins do not split on the current generated data. The Twin B stream looks like a cascade on passive channels, and the belief saturates to P(C) above 0.95 within a few minutes.
- The scripted demo's split is driven by the scripted answer, not by the sensors.
- The 3D ward view is a schematic. The data has no coordinates, so the layout is not surveyed geometry, and the water level is the engine's P(cascade), not a measured depth.
- The hosted build contains only the scripted demo streams.

## Tests

`python -m pytest` runs 48 tests. They cover:

- belief updates, trust, the silence rule for gateway outages, and the outage hold (`test_outage_hold.py` compares a replay with and without the silence step);
- decision ladder and hysteresis;
- causality (a reply cannot change minutes it arrived after) and live-versus-batch parity;
- metric functions, ingest schema, rumour-wave clustering, and twin prefix checks.

## Credits

See [`CREDITS.md`](CREDITS.md) for libraries (numpy, FastAPI, uvicorn, pytest, httpx, Chart.js), the public rainfall figures used for scale, and the concepts behind the metrics.
