# Card 22: eval/precompute.py (offline demo traces)
- **Model:** 9B coder · **Slot:** 21:00–21:30 (write); run at 22:00 after E2E is green · **Gate:** 22:00 E2E + red team (Wi-Fi off)
- **File:** `eval/precompute.py`
- **Goal:** Write the demo traces to `data/episodes/`, so the page works with Wi-Fi off. Plain traces: 2 episodes × 4 λ = 8 files. Scenario traces: 2 episodes × 4 λ × 2 scenarios (rumour_wave, gateway_outage) = 16 files. Camera cut-out is pass 3; it is skipped if not built. Total 24 (32 if pass 3 is built).

## Contract (copied in)
- File name (Harshavi decided): `data/episodes/<episode_id>__lam<λ>.json` for plain traces. For scenario traces: `data/episodes/<episode_id>__lam<λ>__<scenario>.json` (index ASK 5).
- File shape (§8.4): `{"episode_id": str, "lam": float, "minutes": [{"belief": {...}, "decision": {...}}], "synthetic": true}`.
- Engine call: `from engine.run import run_episode`; `run_episode(jsonl_path: str, lam: float = 1.0, ask_enabled: bool = True, grey: bool = False) -> list[dict]`. Its list has one dict per belief line (has key `p`) and one per decision line (has key `action`), each with `minute`. Pair them by minute.
- Scenario streams: `data/streams/<episode>.jsonl`. Rumour: read the stream, add `build_injection('rumour_wave', ep, 300, seed)`, sort by `event_time_s`, write to a temp file, run it. Outage: `apply_silence(events, 'gateway_outage', ep)` then write to a temp file. Use `tempfile` in the scratch folder `~/aditya-scratch/`.
- λ values: 0.5, 1.0, 2.0, 4.0. Episodes: `P1A-s0007`, `P1B-s0007`.

## Signatures (exact)
```python
def plan() -> list[tuple[str, float, str]]        # (episode, lam, scenario); scenario in {'none','rumour_wave','gateway_outage'}
def out_name(episode: str, lam: float, scenario: str) -> str
def main(argv: list[str] | None = None) -> int    # --dry-run
```

## Qwen prompt (paste into a fresh chat)
```text
You write one Python file for a hackathon demo. Synthetic data only. Python 3.11, standard library only, plus the local modules below. No network. Output only the full file in one code block, under 120 lines, no commentary. Use type hints.

Write eval/precompute.py. Imports: argparse, json, pathlib.Path, tempfile; from generator.scenarios import build_injection, apply_silence. Import engine only inside main's non-dry-run branch: from engine.run import run_episode.
1. EPISODES = ['P1A-s0007', 'P1B-s0007']; LAMS = [0.5, 1.0, 2.0, 4.0]; SCENARIOS = ['none', 'rumour_wave', 'gateway_outage'].
2. def plan() -> list[tuple[str, float, str]]: return [(ep, lam, sc) for ep in EPISODES for lam in LAMS for sc in SCENARIOS].
3. def out_name(episode, lam, scenario) -> str: base = f'{episode}__lam{lam:g}'; return base + ('.json' if scenario == 'none' else f'__{scenario}.json'). (Use :g so 1.0 prints as 1.)
4. def _events_for(episode: str, scenario: str) -> list[dict] | None: read data/streams/<episode>.jsonl as dicts (json.loads per line). seed = int(episode.split('-s')[1]). If scenario == 'none': return the list. If 'rumour_wave': return sorted(events + build_injection('rumour_wave', episode, 300, seed), key=lambda e: (e['event_time_s'], e['event_id'])). If 'gateway_outage': return apply_silence(events, 'gateway_outage', episode). Else return None.
5. def _pair(raw: list[dict]) -> list[dict]: group by minute: {'minute': m, 'belief': <dict with key p>, 'decision': <dict with key action>}; return sorted by minute; skip minutes missing either.
6. def main(argv=None) -> int: argparse with --dry-run (flag). Out = Path('data/episodes'); mkdir. For (ep, lam, sc) in plan(): if dry-run: print(out / out_name(ep, lam, sc)); continue. events = _events_for(ep, sc); write events to a temp JSONL under ~/aditya-scratch/ (Path.home() / 'aditya-scratch'), one line each; raw = run_episode(str(tmp), lam=lam, ask_enabled=True, grey=False); minutes = _pair(raw); (out / out_name(ep, lam, sc)).write_text(json.dumps({'episode_id': ep, 'lam': lam, 'minutes': minutes, 'synthetic': True}, indent=1)); print the path. Return 0.
7. if __name__ == '__main__': raise SystemExit(main()).
Output the whole file.
```

## Check (bash)
```bash
cd ~/dev/Twin_Breaker && source .venv/bin/activate
python -m eval.precompute --dry-run | wc -l
```
Expected: `24` (8 plain + 16 scenario). If pass 3 cut-out is built later, the count becomes 32 and a `camera_cutout` scenario is added to `SCENARIOS`.

## Done when
- [ ] `--dry-run` prints 24 lines.
- [ ] At 22:00 (after Harshavi says E2E is green): `python -m eval.precompute` writes the files; `ls data/episodes | wc -l` prints 24.

## Then (git, from the repo root)
```bash
cd ~/dev/Twin_Breaker
git switch aditya          # your branch (never commit on main)
git add eval/precompute.py
git commit -m "eval: precompute script for offline traces"
git pull --no-edit origin main
git push                    # updates your open PR (open one if none: see aditya.md)
```
At 22:00 after the run:
```bash
cd ~/dev/Twin_Breaker
git add data/episodes
git commit -m "demo: pre-rendered episode traces (24 files)"
git pull --no-edit origin main
git push                    # updates your open PR (open one if none: see aditya.md)
```
Tell Harshavi: "24 traces in data/episodes/; open one with Wi-Fi off."
