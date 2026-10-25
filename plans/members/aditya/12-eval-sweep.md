# Card 12: eval/sweep.py (DEV table runner)
- **Model:** 9B coder · **Slot:** 16:40–17:10 · **Gate:** DEV table prints (mock until Harshavi's `run_episode`)
- **File:** `eval/sweep.py`
- **Goal:** Run a set of seeds through the engine (or the mock), attach sealed truth, and write one summary file. Only `eval/` reads sealed truth. The engine never sees it.

## Contract (copied in)
- Episodes per seed (pass 1 and 2): `N-s<seed>`, `C-s<seed>`, `P1A-s<seed>`, `P1B-s<seed>`. The helper `episodes_for(world, split, seed)` in `generator/gen.py` returns them. `parse_seeds(text)` turns `"1-10"` into a list.
- Truth file: `generator/sealed/<episode>.truth.json`.
- Engine call (Harshavi's P8, contract ⚠️): `from engine.run import run_episode`; `run_episode(jsonl_path: str, lam: float = 1.0, ask_enabled: bool = True, grey: bool = False) -> list[dict]`. Each dict per minute has keys `minute`, `p` and `action` (the belief and decision shapes of §8.2 are flattened to these three keys by the sweep). Until it exists, use `--mock`.
- Output: `results/dev/<split>_summary.json` (gitignored), shape `{"split","world","seeds","episodes":[records]}` where each record is the output of `eval.collect.episode_record`.

## Signature (exact)
```python
def main(argv: list[str] | None = None) -> int
```
CLI: `python -m eval.sweep --world B --split dev --seeds 1-10 [--out results/dev/] [--mock]`

## Example output (mock)
```
N-s0001 hypothesis=N lead=None flips=0
C-s0001 hypothesis=C lead=3 flips=0
P1A-s0001 hypothesis=C lead=3 flips=0
P1B-s0001 hypothesis=N lead=None flips=0
...
```
(40 lines for seeds 1 to 10: four episodes per seed.)

## Qwen prompt (paste into a fresh chat)
```text
You write one Python file for a hackathon demo. Synthetic data only. Python 3.11, standard library only, plus the local modules below. No network. Output only the full file in one code block, under 120 lines, no commentary. Use type hints.

Write eval/sweep.py. Imports: argparse, json, pathlib.Path, sys; from generator.gen import episodes_for, parse_seeds; from eval.collect import episode_record. Do not import engine at module level.
Define def main(argv: list[str] | None = None) -> int with argparse flags: --world (required), --split (required), --seeds (required, string), --out (default 'results/dev/'), --mock (store_true).
Steps:
1. records = []. For seed in parse_seeds(args.seeds): for ep in episodes_for(args.world, args.split, seed):
   a. truth_path = Path('generator/sealed') / f'{ep}.truth.json'. If it does not exist: print('run the generator first: ' + str(truth_path)); return 1. truth = json.loads(truth_path.read_text()).
   b. If args.mock: minutes = json.loads(Path('tests/fixtures/mock_minutes.json').read_text()); then for each minute dict set its episode_id to ep; keep only keys minute, p, action. Else: from engine.run import run_episode (import inside this branch); raw = run_episode(f'data/streams/{ep}.jsonl', lam=1.0, ask_enabled=True, grey=False); minutes = [{'minute': r['minute'], 'p': r['p'], 'action': r['action']} for r in raw if 'action' in r] (ignore lines without an action).
   c. records.append(episode_record(ep, truth, minutes)).
2. out = Path(args.out); out.mkdir(parents=True, exist_ok=True); (out / f'{args.split}_summary.json').write_text(json.dumps({'split': args.split, 'world': args.world, 'seeds': args.seeds, 'episodes': records}, indent=1)).
3. For each record print: f"{r['episode_id']} hypothesis={r['hypothesis']} lead={r['lead_min']} flips={r['flips']}".
4. Return 0. Add: if __name__ == '__main__': raise SystemExit(main()).
Output the whole file.
```

## Check (bash)
```bash
cd ~/dev/Twin_Breaker && source .venv/bin/activate
python -m generator.gen --world B --split dev --seeds 1-10 --out data/streams/
python -m eval.sweep --world B --split dev --seeds 1-10 --out results/dev/ --mock | wc -l
ls results/dev/dev_summary.json
```
Expected: `40` (four episodes times ten seeds) and the file path printed by `ls`. If the count is 20, `episodes_for` in card 06 is missing P1A and P1B; fix card 06 first.

## Done when
- [ ] The count is 40 and the summary file exists.
- [ ] `--mock` works without `engine/` present.

## Then (git, from the repo root)
```bash
cd ~/dev/Twin_Breaker
git switch aditya          # your branch (never commit on main)
git add eval/sweep.py
git commit -m "eval: sweep runner (mock until run_episode lands)"
git pull --no-edit origin main
git push                    # updates your open PR (open one if none: see aditya.md)
```
Tell Harshavi: "sweep takes `run_episode(jsonl_path, lam, ask_enabled, grey)`; send me the function when it exists."
