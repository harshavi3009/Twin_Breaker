# Card 21: tests/test_outage_hold.py (silence step alone, forget OFF)
- **Model:** 35B · **Slot:** 20:00–20:30 · **Gate:** red team 2 pass check (ΔP(C) ≤ 0.001 per minute)
- **File:** `tests/test_outage_hold.py`
- **Goal:** During the G3 outage, P(C) must not move by more than 0.001 per minute. The test runs the engine with the forget step OFF, so only the silence step is tested. Forget drift (about −0.003 per minute) is reported separately by Harshavi.

## Contract (copied in)
- Stream: `generator/gen.py` writes `S-s0007` only when `--split eval` (pass 3). For this test, generate an S episode with `generate('B', 'dev', 7, 'S-s0007', tmp)` once card 19 is in: `generator.latent` accepts `S-s####`, and `episodes_for` is NOT needed.
- Silence: `from generator.scenarios import apply_silence`; `apply_silence(events, 'gateway_outage', 'S-s0007')` drops G3 drain observations and G3 heartbeats in [300, 900).
- Engine (Harshavi's files, read-only for you): `from engine.ingest import parse_line, Ingestor`; `from engine.belief import replay, Trust`; config `engine/config/belief_spec.json`. `Ingestor(registered_responders=set())`; `push(ev) -> bool`; `buckets() -> dict[int, list[Event]]`. `replay(buckets, spec, trust, prior, upto_min) -> list[Belief]`; each Belief has `minute` and `p` (dict N, S, I, C).
- Forget OFF: set `spec['eps'] = 0.0` in the test after loading belief_spec.json (the forget rate key is `eps`).
- Prior: uniform `{"N": 0.25, "S": 0.25, "I": 0.25, "C": 0.25}`. Trust: `Trust()` then `.reset()`.
- Check: for consecutive minutes, `abs(p[m]['C'] - p[m-1]['C']) <= 0.001` for every minute m from 300 // 60 + 1 up to the last minute of the outage (900 // 60 - 1).

## Qwen prompt (paste into a fresh chat)
```text
You write one pytest file for a hackathon demo. Synthetic data only. Python 3.11; pytest, the standard library, and these local modules: generator.gen (generate), generator.scenarios (apply_silence), engine.ingest (Ingestor, parse_line), engine.belief (replay, Trust). No network. Output only the full file in one code block, under 80 lines, no commentary.

Write tests/test_outage_hold.py.
1. Imports: json, pathlib.Path; pytest. Inside the test function, import the local modules (not at module level).
2. def test_outage_hold(tmp_path):
   a. from generator.gen import generate; from generator.scenarios import apply_silence; from engine.ingest import parse_line, Ingestor; from engine.belief import replay, Trust.
   b. info = generate('B', 'dev', 7, 'S-s0007', str(tmp_path)).
   c. lines = Path(info['path']).read_text().splitlines(); events = [parse_line(l) for l in lines if l.strip()] — but apply_silence works on dicts, so first load dicts: raw = [json.loads(l) for l in lines if l.strip()]; kept = apply_silence(raw, 'gateway_outage', 'S-s0007'); events = [parse_line(json.dumps(d)) for d in kept].
   d. ing = Ingestor(registered_responders=set()); for ev in events: ing.push(ev); buckets = ing.buckets().
   e. spec = json.loads(Path('engine/config/belief_spec.json').read_text()); spec['eps'] = 0.0 (forget OFF; say so in a comment).
   f. trust = Trust(); trust.reset(); prior = {'N': 0.25, 'S': 0.25, 'I': 0.25, 'C': 0.25}.
   g. upto = max(buckets) // 60 if buckets else 0; beliefs = replay(buckets, spec, trust, prior, upto). Build p_c = {b.minute: b.p['C'] for b in beliefs}.
   h. For minute m in range(300 // 60 + 1, 900 // 60): assert m in p_c and m - 1 in p_c; assert abs(p_c[m] - p_c[m-1]) <= 0.001, message with m and the two values.
Output the whole file.
```

## Check (bash)
```bash
cd ~/dev/Twin_Breaker && source .venv/bin/activate && python -m pytest -q tests/test_outage_hold.py 2>&1 | tail -n 3
```
Expected: `1 passed`. If it fails, the message gives the minute and the two values. Do NOT change engine code; tell Harshavi the minute and value (his files, his fix).

## Done when
- [ ] `1 passed`, or a message to Harshavi with the minute and the two P(C) values.

## Then (git, from the repo root)
```bash
cd ~/dev/Twin_Breaker
git switch aditya          # your branch (never commit on main)
git add tests/test_outage_hold.py
git commit -m "tests: G3 outage holds P(C) with forget off"
git pull --no-edit origin main
git push                    # updates your open PR (open one if none: see aditya.md)
```
Tell Harshavi: "outage test pushed; forget is OFF in the test (eps 0); the hold is the silence step alone."
