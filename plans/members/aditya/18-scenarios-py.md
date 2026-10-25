# Card 18: generator/scenarios.py (injection and G3 silence)
- **Model:** 9B coder · **Slot:** 18:35–18:55 · **Gate:** 18:00 integration (Harshavi's `/api/inject`)
- **File:** `generator/scenarios.py`
- **Goal:** Two functions the server calls. `build_injection` makes the rumour events. `apply_silence` removes the G3 gateway events during the outage.

## Contract (copied in)
- Scenario files: `scenarios/<name>.json`. Read them through `Path(__file__).parents[1] / 'scenarios'`.
- Rumour (`rumour_wave.json`): keys `count` (400), `window_s` (40), `phrasings` (12 strings).
- Outage (`gateway_outage.json`): keys `kind` ('silence'), `gateway_id` ('G3'), `channel` ('drain'), `start_s`, `duration_s`.
- Event dict: the 14 keys (`event_id, episode_id, kind, channel, source_id, gateway_id, event_time_s, received_time_s, value, text, text_hash, question_id, answer, retracts`).
- `text_hash` = first 6 hex of sha1 of normalised text (from `generator.rng.text_hash`).

## Signatures (exact)
```python
def build_injection(name: str, episode_id: str, at_s: int, seed: int) -> list[dict]
def apply_silence(events: list[dict], name: str, episode_id: str) -> list[dict]
```
- `build_injection`: only `'rumour_wave'` is supported; anything else raises ValueError. Returns `count` events.
- `apply_silence`: loads the named silence file; drops an event when it is an observation with the scenario gateway and channel, or a heartbeat from the scenario gateway, AND `start_s <= event_time_s < start_s + duration_s`. Keeps the order of the rest.

## Example
`build_injection('rumour_wave', 'N-s0007', 300, 7)` → 400 dicts, `text_hash` takes 12 distinct values; `event_time_s` runs from 300 to 339.

## Qwen prompt (paste into a fresh chat)
```text
You write one Python file for a hackathon demo. Synthetic data only. Python 3.11, standard library and the local module below only. No network. Output only the full file in one code block, under 110 lines, no commentary. Use type hints.

Write generator/scenarios.py. Imports: json, pathlib.Path; from generator.rng import text_hash.
SCEN = Path(__file__).resolve().parents[1] / 'scenarios'.
1. def _load(name: str) -> dict: return json.loads((SCEN / f'{name}.json').read_text()).
2. def build_injection(name: str, episode_id: str, at_s: int, seed: int) -> list[dict]:
   if name != 'rumour_wave': raise ValueError(f'unsupported injection {name}'). sc = _load(name). Phrasings = sc['phrasings']; count = sc['count']; window = sc['window_s'].
   For i in range(count): t = at_s + int(i * window / count); text = phrasings[i % len(phrasings)]; build the dict: event_id = f'ev-inj-{episode_id}-{i:04d}'; episode_id; kind 'citizen'; channel 'citizen'; source_id = f'phone-r{i:04d}'; gateway_id None; event_time_s = t; received_time_s = t + 5; value None; text = text; text_hash = text_hash(text); question_id None; answer None; retracts None.
   Return the list.
3. def apply_silence(events: list[dict], name: str, episode_id: str) -> list[dict]:
   sc = _load(name); if sc.get('kind') != 'silence': raise ValueError('not a silence scenario'). Define a predicate silenced(e): in_window = sc['start_s'] <= e['event_time_s'] < sc['start_s'] + sc['duration_s']; same_gw = e.get('gateway_id') == sc['gateway_id']; is_obs = e['kind'] == 'observation' and e.get('channel') == sc['channel']; is_hb = e['kind'] == 'heartbeat'; return in_window and same_gw and (is_obs or is_hb).
   Return [e for e in events if not silenced(e)] (keep order). episode_id is not used for filtering; keep it in the signature.
Do not use the word "engine" in the file. Output the whole file.
```

## Check (bash)
```bash
cd ~/dev/Twin_Breaker && source .venv/bin/activate
python -m generator.gen --world B --split dev --seeds 7 --out data/streams/ >/dev/null
python -c "
import json
from generator.scenarios import build_injection, apply_silence
ev = build_injection('rumour_wave', 'N-s0007', 300, 7)
print(len(ev), len({e['text_hash'] for e in ev}))
s = [json.loads(l) for l in open('data/streams/N-s0007.jsonl')]
kept = apply_silence(s, 'gateway_outage', 'N-s0007')
print(len(s) - len(kept) > 0, all(not (e['gateway_id']=='G3' and e['kind']=='observation' and e['channel']=='drain' and 300<=e['event_time_s']<900) for e in kept))"
```
Expected: `400 12` then `True True`.

## Done when
- [ ] `400 12`.
- [ ] `True True` (silence removed some events; no G3 drain events remain in the window).
- [ ] `grep -n "engine" generator/scenarios.py` prints nothing.

## Then (git, from the repo root)
```bash
cd ~/dev/Twin_Breaker
git switch aditya          # your branch (never commit on main)
git add generator/scenarios.py
git commit -m "generator: rumour injection and G3 silence"
git pull --no-edit origin main
git push                    # updates your open PR (open one if none: see aditya.md)
```
Tell Harshavi the two signatures in the message.
