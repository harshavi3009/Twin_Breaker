# Card 13: generator/passive_more.py (traffic, calls, hospital)
- **Model:** 9B coder · **Slot:** 17:10–17:35 · **Gate:** pass 2 channels for the 18:00 gate
- **File:** `generator/passive_more.py` (plus one hand edit in `generator/gen.py`)
- **Goal:** Three more channels, with lagged response to the depth. The lag is drawn per episode, not per minute.

## Contract (copied in)
- Same 14 event keys as card 05 (`event_id, episode_id, kind, channel, source_id, gateway_id, event_time_s, received_time_s, value, text, text_hash, question_id, answer, retracts`), None when absent.
- Traffic: kind `observation`, channel `traffic`, source `traffic-G1-01`, gateway `G1`, value = speed ratio (0 to 1.5), event_time offset 30.
- Calls: kind `dispatch`, channel `calls`, source `dispatch-W9`, value = count (float), emitted only when count > 0, offset 20.
- Hospital: kind `hospital`, channel `hospital`, source `hosp-H1`, value = count (float), emitted only when count > 0, offset 50.
- World keys used: `lags_min.drain_to_traffic`, `lags_min.traffic_to_calls`, `lags_min.calls_to_hospital` (each [lo, hi]); `traffic.slow_gain`; `calls.base_per_min`, `calls.gain_per_min`; `hospital.base_per_min`, `hospital.gain_per_min`; `cascade.cap_cm`.
- Event ids: `ev-s{seed:04d}-{channel_or_kind}-m{minute:03d}-{source_id}`.
- Twin rule still holds: lagged depth for minutes below 7 is 0 in both twins.

## Signature (exact)
```python
def more_events(episode: str, seed: int, minute: int, latent: Latent, world: dict) -> list[dict]
```
Returns `[traffic, calls (if any), hospital (if any)]`.

## Qwen prompt (paste into a fresh chat)
```text
You write one Python file for a hackathon demo. Synthetic data only. Python 3.11, numpy and the standard library (hashlib). No network. Output only the full file in one code block, under 120 lines, no commentary. Use type hints.

Write generator/passive_more.py. Imports: hashlib; from generator.rng import channel_rng, episode_rng, text_hash; from generator.latent import Latent. Define:
1. def lagged(depth: list[float], minute: int, lag: int) -> float: return depth[max(0, minute - lag)].
2. def _lag(seed: int, latent: Latent, world: dict, name: str) -> int: lo, hi = world['lags_min'][name]; key = f"{latent.pair or 'C'}:lag:{name}"; return int(episode_rng(seed, key).integers(lo, hi + 1)).
3. def _ev(episode: str, seed: int, minute: int, kind: str, channel: str | None, source_id: str, gateway_id: str | None, event_time_s: int, delay: int, value: float | None) -> dict: build the dict with exactly these keys: event_id, episode_id, kind, channel, source_id, gateway_id, event_time_s, received_time_s (= event_time_s + delay), value, text (None), text_hash (None), question_id (None), answer (None), retracts (None). event_id = f"ev-s{seed:04d}-{(channel or kind)}-m{minute:03d}-{source_id}".
4. def more_events(episode: str, seed: int, minute: int, latent: Latent, world: dict) -> list[dict]. cap = world['cascade']['cap_cm']. Steps:
   a. TRAFFIC: lag_t = _lag(seed, latent, world, 'drain_to_traffic'); d = lagged(latent.depth_cm, minute, lag_t); rng = channel_rng(seed, 'traffic', minute); z = float(rng.standard_normal()); value = round(min(1.5, max(0.0, 1.0 - world['traffic']['slow_gain'] * min(1.0, d / cap) + 0.05 * z)), 2); delay = min(90, int(abs(float(rng.standard_normal())) * 10)). Event: kind 'observation', channel 'traffic', source 'traffic-G1-01', gateway 'G1', event_time_s minute*60+30.
   b. CALLS: lag_c = _lag(seed, latent, world, 'traffic_to_calls'); d = lagged(latent.depth_cm, minute, lag_c); rng = channel_rng(seed, 'calls', minute); lam = world['calls']['base_per_min'] + world['calls']['gain_per_min'] * min(1.0, d / cap); n = int(rng.poisson(lam)); if n > 0: event kind 'dispatch', channel 'calls', source 'dispatch-W9', gateway None, value float(n), event_time_s minute*60+20, delay 0.
   c. HOSPITAL: lag_h = _lag(seed, latent, world, 'calls_to_hospital'); d = lagged(latent.depth_cm, minute, lag_h); rng = channel_rng(seed, 'hospital', minute); lam = world['hospital']['base_per_min'] + world['hospital']['gain_per_min'] * min(1.0, d / cap); n = int(rng.poisson(lam)); if n > 0: event kind 'hospital', channel 'hospital', source 'hosp-H1', value float(n), event_time_s minute*60+50, delay 0.
   d. Return [traffic] + calls (if any) + hospital (if any).
Output the whole file.
```

## Hand edit (you, not Qwen): `generator/gen.py`
1. Add at the top: `from generator.passive_more import more_events`
2. In the minute loop, directly after the `events.extend(minute_events(...))` line, add: `events.extend(more_events(episode, seed, m, latent, spec))`
3. Re-run card 06's check; `cmp` must still say SAME for P1A (it will still match because both twins share the prefix).

## Check (bash)
```bash
cd ~/dev/Twin_Breaker && source .venv/bin/activate
python -c "
import json; from generator.latent import make_latent; from generator.passive_more import more_events
s=json.load(open('generator/world_spec.json'))
a=more_events('P1A-s0007',7,2,make_latent(7,'P1A-s0007',s),s)
b=more_events('P1B-s0007',7,2,make_latent(7,'P1B-s0007',s),s)
print([e['kind'] for e in a], [e['event_id'] for e in a]==[e['event_id'] for e in b])"
python -m generator.gen --world B --split dev --seeds 7 --out data/streams/ >/dev/null && python -m pytest -q tests/test_twin_prefix.py 2>&1 | tail -n 1
```
Expected: a kinds list starting with `['observation']` (traffic), `True`, and `11 passed`.

## Done when
- [ ] The check prints the expected pattern.
- [ ] The twin test is green after the gen.py edit.
- [ ] `grep -n "engine" generator/passive_more.py` prints nothing.

## Then (git, from the repo root)
```bash
cd ~/dev/Twin_Breaker
git switch aditya          # your branch (never commit on main)
git add generator/passive_more.py generator/gen.py
git commit -m "generator: pass 2 traffic, calls, hospital"
git pull --no-edit origin main
git push                    # updates your open PR (open one if none: see aditya.md)
```
