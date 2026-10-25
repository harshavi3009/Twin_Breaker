# Card 05: generator/passive.py
- **Model:** 9B coder · **Slot:** 14:35–14:55 · **Gate:** feeds card 06 (DEV 7 at 15:15)
- **File:** `generator/passive.py`
- **Goal:** Passive events for one sim minute: rain, drain (100 sensors), citizen reports, and one heartbeat per gateway. Draw count is fixed, so the output never depends on hidden state inside a minute.

## Contract (copied in)
Event line: one dict per event, exactly these 14 keys (None when absent):
`event_id, episode_id, kind, channel, source_id, gateway_id, event_time_s, received_time_s, value, text, text_hash, question_id, answer, retracts`
- Rain: kind `observation`, channel `rain`, source `rain-G1-001`, gateway `G1`, value in mm/h.
- Drain (100 per minute): kind `observation`, channel `drain`, source `drain-<gw>-<NNN>` (NNN = 001 to 100), gateway from `gateways[i % 3]`, value fill 0 to 1.
- Citizen: kind `citizen`, channel `citizen`, source `phone-<4 hex>`, `text` from `citizen.texts`, `text_hash` from `text_hash(text)`, value None.
- Heartbeat: kind `heartbeat`, channel None, source `gw-<gw>`, gateway_id `<gw>`, value None.
- Times: `event_time_s = minute*60 + offset` (rain 30, drain 30, citizen 40, heartbeat 0). `received_time_s = event_time_s + delay`, delay 0 to 90.
- `event_id = f"ev-s{seed:04d}-{channel_or_kind}-m{minute:03d}-{source_id}"` where channel_or_kind is the channel if not None, else the kind.

## Signature (exact)
```python
def minute_events(episode: str, seed: int, minute: int, latent: Latent, world: dict) -> list[dict]
```
`Latent` comes from `generator/latent.py` (fields: `depth_cm`, `rain_extra_mm_h`, `pair`, `role`).

## Example
`minute_events('N-s0007', 7, 0, latent, spec)` returns about 105 dicts (100 drain + rain + 3 heartbeats, plus any citizen). Calling it twice gives equal lists.

## Qwen prompt (paste into a fresh chat)
```text
You write one Python file for a hackathon demo. Synthetic data only. Python 3.11, numpy and the standard library only (hashlib). No network. Output only the full file in one code block, under 130 lines, no commentary. Use type hints.

Write generator/passive.py. Imports: hashlib; numpy as np; from generator.rng import channel_rng, text_hash; from generator.latent import Latent.
Define def minute_events(episode: str, seed: int, minute: int, latent: Latent, world: dict) -> list[dict]. Steps, in this order:
1. d = latent.depth_cm[minute]; rx = latent.rain_extra_mm_h[minute]; cap = world['cascade']['cap_cm']; nz = world['noise']; gws = world['gateways']; n_drain = world['drain_sensors_total'] (100).
2. RAIN: rng = channel_rng(seed, 'rain', minute). z = rng.standard_t(nz['t_df'], size=2). value = round(max(0.0, world['rain']['base_mm_h'] + nz['rain_scale_mm_h'] * z[0] + rx), 2). delay = min(90, int(abs(z[1]) * nz['delay_scale_s'])). One observation dict: kind 'observation', channel 'rain', source_id 'rain-G1-001', gateway_id 'G1', event_time_s = minute*60+30, received_time_s = event_time_s + delay.
3. DRAINS: rng = channel_rng(seed, 'drain', minute). z = rng.standard_t(nz['t_df'], size=(n_drain, 2)). For i in range(n_drain): gw = gws[i % len(gws)]; source = f'drain-{gw}-{i+1:03d}'; value = round(min(1.0, max(0.0, world['drain']['base_fill'] + world['drain']['per_cm_fill'] * d + nz['drain_scale'] * z[i, 0])), 3); delay = min(90, int(abs(z[i, 1]) * nz['delay_scale_s'])). Observation dict: channel 'drain', gateway_id gw, event_time_s = minute*60+30.
4. CITIZEN: rng = channel_rng(seed, 'citizen', minute). u = rng.random(3); idx = rng.integers(0, 3, size=3); dl = rng.integers(0, 91, size=3). For k in range(3): p = base_rate if d <= 0 else base_rate + (cascade_rate - base_rate) * min(1.0, d / cap), with rates from world['citizen']. If u[k] < p: text = world['citizen']['texts'][int(idx[k])]; source = 'phone-' + hashlib.sha1(f'{seed}-{k}'.encode()).hexdigest()[:4]; kind 'citizen', channel 'citizen', text, text_hash = text_hash(text), event_time_s = minute*60+40, received_time_s = event_time_s + int(dl[k]). Draws happen for all k even when no report is emitted.
5. HEARTBEATS: for gw in gws: kind 'heartbeat', channel None, source_id f'gw-{gw}', gateway_id gw, value None, event_time_s = minute*60, received_time_s = event_time_s.
6. Every dict has exactly these keys: event_id, episode_id, kind, channel, source_id, gateway_id, event_time_s, received_time_s, value, text, text_hash, question_id, answer, retracts. Use None for missing. episode_id = episode. event_id = f"ev-s{seed:04d}-{(channel or kind)}-m{minute:03d}-{source_id}".
7. Return the list in this order: rain, drains (i ascending), citizens (k ascending), heartbeats (gateway order).
Output the whole file.
```

## Check (bash)
```bash
cd ~/dev/Twin_Breaker && source .venv/bin/activate
python -c "
import json; from generator.latent import make_latent; from generator.passive import minute_events
s=json.load(open('generator/world_spec.json')); L=make_latent(7,'N-s0007',s)
a=minute_events('N-s0007',7,0,L,s); b=minute_events('N-s0007',7,0,L,s)
print(len(a), a==b, sorted({e['kind'] for e in a}))"
```
Expected: a count around 105 (more if citizens), `True`, and kinds that include `'heartbeat'` and `'observation'`.

## Done when
- [ ] The check prints the expected pattern.
- [ ] `grep -n "engine" generator/passive.py` prints nothing.

## Then (git, from the repo root)
```bash
cd ~/dev/Twin_Breaker
git switch aditya          # your branch (never commit on main)
git add generator/passive.py
git commit -m "generator: passive rain, drain, citizen, heartbeat"
git pull --no-edit origin main
git push                    # updates your open PR (open one if none: see aditya.md)
```
