# Card 20: eval/sensitivity.py (VOI constant sweep)
- **Model:** 9B coder · **Slot:** 19:30–20:00 · **Gate:** the DEV table shows the VOI constant is not doing the work (Harshavi's decided item 5)
- **File:** `eval/sensitivity.py`
- **Goal:** Re-run DEV seeds with the hand-set VOI constant at three values, and write one row per value. Judges can ask about the constant; this table answers.

## Contract (copied in)
- The VOI constant in the engine is `0.5 + 0.2 * 1.0` (hand-set prior weight, default 0.7). The sweep uses the values 0.5, 0.7 (default) and 0.9.
- Engine call (ask Harshavi, index ASK 4): `run_episode(jsonl_path, lam=1.0, ask_enabled=True, grey=False, overrides={'voi_const': v})`. Until that exists, `--mock` is used, and every row then shows the same numbers. Say so on the slide.
- Episodes: `episodes_for('B', 'dev', seed)` from `generator/gen.py` gives N, C, P1A, P1B per seed. Use seeds 1 to 10.
- Truth: `generator/sealed/<episode>.truth.json`. Records: `eval.collect.episode_record`.
- Output: `results/dev/sensitivity.json` with a list of rows `{"voi_const", "brier_C_mean", "lead_median", "flips_mean", "ask_fired"}`. `ask_fired` = count of episodes with any decision that has an `ask` set.

## Signature (exact)
```python
def run_sensitivity(seeds: list[int], values: tuple[float, ...] = (0.5, 0.7, 0.9), mock: bool = False) -> list[dict]
def main(argv: list[str] | None = None) -> int   # --seeds 1-10 [--mock]
```

## Qwen prompt (paste into a fresh chat)
```text
You write one Python file for a hackathon demo. Synthetic data only. Python 3.11, standard library only, plus the local modules below. No network. Output only the full file in one code block, under 110 lines, no commentary. Use type hints.

Write eval/sensitivity.py. Imports: argparse, json, statistics, pathlib.Path; from generator.gen import episodes_for, parse_seeds; from eval.collect import episode_record. Import engine only inside the non-mock branch: from engine.run import run_episode.
1. def _minutes_mock(ep: str) -> list[dict]: data = json.loads(Path('tests/fixtures/mock_minutes.json').read_text()); return [{'minute': d['minute'], 'p': d['p'], 'action': d['action']} for d in data].
2. def _minutes_engine(ep: str, v: float) -> list[dict]: raw = run_episode(f'data/streams/{ep}.jsonl', lam=1.0, ask_enabled=True, grey=False, overrides={'voi_const': v}); keep only dicts with 'action' (decision lines) and dicts with 'p' (belief lines); group by 'minute' into [{'minute': m, 'p': belief['p'], 'action': decision['action'], 'ask': decision.get('ask')}]; return them sorted by minute.
3. def run_sensitivity(seeds, values=(0.5, 0.7, 0.9), mock=False) -> list[dict]: for each v in values: records = []; for seed in seeds: for ep in episodes_for('B', 'dev', seed): truth = json.loads(Path('generator/sealed', f'{ep}.truth.json').read_text()); minutes = _minutes_mock(ep) if mock else _minutes_engine(ep, v); records.append(episode_record(ep, truth, minutes)). Row = {'voi_const': v, 'brier_C_mean': round(statistics.mean(r['brier_C'] for r in records), 4), 'lead_median': statistics.median([r['lead_min'] for r in records if r['lead_min'] is not None]) if any(r['lead_min'] is not None for r in records) else None, 'flips_mean': round(statistics.mean(r['flips'] for r in records), 3), 'ask_fired': sum(asks), where asks is a parallel list: for each episode, append True if any(m.get('ask') for m in minutes) else False. Append the row.
4. def main(argv=None) -> int: argparse: --seeds (str, required), --mock (flag). rows = run_sensitivity(parse_seeds(args.seeds), mock=args.mock). Write results/dev/sensitivity.json (mkdir parents) with the rows. Print one line per row. Return 0. Add the __main__ guard.
Output the whole file.
```

## Check (bash)
```bash
cd ~/dev/Twin_Breaker && source .venv/bin/activate
python -m generator.gen --world B --split dev --seeds 1-10 --out data/streams/ >/dev/null
python -m eval.sensitivity --seeds 1-10 --mock
python -c "import json; r=json.load(open('results/dev/sensitivity.json')); print(len(r), sorted(x['voi_const'] for x in r))"
```
Expected: three printed lines, then `3 [0.5, 0.7, 0.9]`.

## Done when
- [ ] The file has three rows with the three constants.
- [ ] Note on the slide: "with --mock, every row is the same; the real sweep is after run_episode(overrides) lands."

## Then (git, from the repo root)
```bash
cd ~/dev/Twin_Breaker
git switch aditya          # your branch (never commit on main)
git add eval/sensitivity.py
git commit -m "eval: VOI constant sensitivity sweep"
git pull --no-edit origin main
git push                    # updates your open PR (open one if none: see aditya.md)
```
