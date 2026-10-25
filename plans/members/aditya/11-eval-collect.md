# Card 11: eval/collect.py (one record per episode)
- **Model:** 9B coder · **Slot:** 16:20–16:40 · **Gate:** feeds the DEV table (card 12)
- **File:** `eval/collect.py`
- **Goal:** Turn one episode's sealed truth and its per-minute outputs into one record for the table.

## Contract (copied in)
Input `truth` (from `generator/sealed/<episode>.truth.json`): `hypothesis` (N/S/I/C), `onset_min` (int or null), `pair`, `role`, `latent_depth_cm`.
Input `minutes`: list of dicts `{"minute": int, "p": {"N","S","I","C"}, "action": str}` in minute order.

## Signature (exact)
```python
def episode_record(episode: str, truth: dict, minutes: list[dict]) -> dict
```
Output keys: `episode_id, pair, role, hypothesis, onset_min, actions, p_C, reached_alert, lead_min, flips, brier_C, brier_C_pre`.
- `y` per minute = 1 if hypothesis == "C" else 0.
- `brier_C` = brier_binary over all minutes; `brier_C_pre` over minutes 0 to 6 only.
- `lead_min` = lead_time_min(actions, onset_min) if onset_min is not None else None.
- `reached_alert` = any action in ("ALERT", "ESCALATE").
- `flips` = flip_count(actions, 3).

## Example
Truth `{"hypothesis":"C","onset_min":8,"pair":"P1","role":"A","latent_depth_cm":[0]*10}` with the mock file from card 09 → `lead_min` 3, `reached_alert` True. With the mock, `flips` is 0.

## Qwen prompt (paste into a fresh chat)
```text
You write one Python file for a hackathon demo. Synthetic data only. Python 3.11, standard library only, plus the local module below. No network. Output only the full file in one code block, under 90 lines, no commentary. Use type hints.

Write eval/collect.py. Import: from eval.metrics import brier_binary, lead_time_min, flip_count.
Define def episode_record(episode: str, truth: dict, minutes: list[dict]) -> dict:
1. actions = [m['action'] for m in minutes]; p_C = [m['p']['C'] for m in minutes].
2. y_all = [1 if truth['hypothesis'] == 'C' else 0] * len(minutes) — use y = 1 or 0 for every minute.
3. brier_C = brier_binary(p_C, y_all). pre = minutes 0 to 6 (first 7 items): brier_C_pre = brier_binary(p_C[:7], y_all[:7]).
4. lead_min = lead_time_min(actions, truth['onset_min']) if truth['onset_min'] is not None else None.
5. reached_alert = any(a in ('ALERT', 'ESCALATE') for a in actions). flips = flip_count(actions, 3).
6. Return a dict with keys: episode_id (= episode), pair, role, hypothesis, onset_min, actions, p_C, reached_alert, lead_min, flips, brier_C, brier_C_pre.
Add a __main__ block: read argv[1] as a JSON file with keys 'episode', 'truth', 'minutes'; print json.dumps(episode_record(...)).
Output the whole file.
```

## Check (bash)
```bash
cd ~/dev/Twin_Breaker && source .venv/bin/activate && python -c "
import json; from eval.collect import episode_record
m=json.load(open('tests/fixtures/mock_minutes.json'))
t={'hypothesis':'C','onset_min':8,'pair':'P1','role':'A','latent_depth_cm':[0]*10}
r=episode_record('P1A-s0007',t,m); print(r['lead_min'], r['reached_alert'], r['flips'])"
```
Expected: `3 True 0`

## Done when
- [ ] The check prints `3 True 0`.

## Then (git, from the repo root)
```bash
cd ~/dev/Twin_Breaker
git switch aditya          # your branch (never commit on main)
git add eval/collect.py
git commit -m "eval: per-episode record"
git pull --no-edit origin main
git push                    # updates your open PR (open one if none: see aditya.md)
```
