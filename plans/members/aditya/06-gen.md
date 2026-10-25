# Card 06: generator/gen.py (writer, CLI, DEV seed 7)
- **Model:** 9B coder · **Slot:** 14:55–15:15 · **Gate:** Harshavi's streams (his 14:00 gate slips, see index ASK 2)
- **File:** `generator/gen.py`
- **Goal:** Write one episode's JSONL and its sealed truth file. Pass 1 covers dev only: N, C, P1A, P1B per seed.

## Contract (copied in)
```python
def generate(world: str, split: str, seed: int, episode: str, out_dir: str) -> dict
# writes <out_dir>/<episode>.jsonl (one event dict per line)
# writes generator/sealed/<episode>.truth.json: {"hypothesis","onset_min","pair","role","latent_depth_cm"}
# CLI: python -m generator.gen --world {B,C} --split {dev,eval,misspec} --seeds 1-10 --out data/streams/
```
Event keys are the 14 from card 05. Events are sorted by `(event_time_s, event_id)`.
Pass 1 dev episodes per seed: `N-s<seed>`, `C-s<seed>`, `P1A-s<seed>`, `P1B-s<seed>`.

## Signatures (exact)
```python
def parse_seeds(text: str) -> list[int]          # "7" -> [7]; "1-10" -> [1..10]; else ValueError
def episodes_for(world: str, split: str, seed: int) -> list[str]
def generate(world: str, split: str, seed: int, episode: str, out_dir: str) -> dict
def main(argv: list[str] | None = None) -> int
```
- `episodes_for`: world must be 'B' (else ValueError). split 'dev' → the four episodes above. split 'eval' or 'misspec' → NotImplementedError('pass 1: dev only').
- `generate` returns `{"episode_id", "n_events", "path", "truth_path"}`.

## Example
`python -m generator.gen --world B --split dev --seeds 7 --out data/streams/` prints:
```
wrote data/streams/N-s0007.jsonl (2140 events)
wrote data/streams/C-s0007.jsonl (2155 events)
wrote data/streams/P1A-s0007.jsonl (...)
wrote data/streams/P1B-s0007.jsonl (...)
```

## Qwen prompt (paste into a fresh chat)
```text
You write one Python file for a hackathon demo. Synthetic data only. Python 3.11, standard library and the local modules below only. No network. Output only the full file in one code block, under 120 lines, no commentary. Use type hints.

Write generator/gen.py. Imports: argparse, json, pathlib.Path; from generator.latent import make_latent; from generator.passive import minute_events.
1. def parse_seeds(text: str) -> list[int]: if '-' in text, split into lo and hi and return list(range(lo, hi + 1)); else return [int(text)]. Anything that does not parse: raise ValueError.
2. def episodes_for(world: str, split: str, seed: int) -> list[str]: if world != 'B': raise ValueError('world must be B in pass 1'). If split != 'dev': raise NotImplementedError('pass 1: dev only'). Return [f'N-s{seed:04d}', f'C-s{seed:04d}', f'P1A-s{seed:04d}', f'P1B-s{seed:04d}'].
3. def generate(world: str, split: str, seed: int, episode: str, out_dir: str) -> dict:
   a. Same world and split checks as step 2 (call episodes_for-style checks; do not require the episode to be in the list).
   b. spec = json.loads(Path(__file__).with_name('world_spec.json').read_text()).
   c. latent = make_latent(seed, episode, spec).
   d. events = []; for m in range(spec['episode_minutes']): events.extend(minute_events(episode, seed, m, latent, spec)).
   e. events.sort(key=lambda e: (e['event_time_s'], e['event_id'])).
   f. out = Path(out_dir); out.mkdir(parents=True, exist_ok=True); jsonl_path = out / f'{episode}.jsonl'; write one json.dumps(e) per line with a trailing newline.
   g. sealed = Path(__file__).parent / 'sealed'; sealed.mkdir(parents=True, exist_ok=True); truth_path = sealed / f'{episode}.truth.json'; write json.dumps({'hypothesis': latent.hypothesis, 'onset_min': latent.onset_min, 'pair': latent.pair, 'role': latent.role, 'latent_depth_cm': latent.depth_cm}).
   h. return {'episode_id': episode, 'n_events': len(events), 'path': str(jsonl_path), 'truth_path': str(truth_path)}.
4. def main(argv: list[str] | None = None) -> int: argparse with required --world, --split, --seeds (str), --out (str). For each seed in parse_seeds(args.seeds), for each episode in episodes_for(args.world, args.split, seed): r = generate(args.world, args.split, seed, episode, args.out); print(f"wrote {r['path']} ({r['n_events']} events)"). Return 0.
5. if __name__ == '__main__': raise SystemExit(main()).
Do not use the word "engine" anywhere in the file.
Output the whole file.
```

## Check (bash)
```bash
cd ~/dev/Twin_Breaker && source .venv/bin/activate
python -m generator.gen --world B --split dev --seeds 7 --out data/streams/
wc -l data/streams/C-s0007.jsonl && du -h data/streams/C-s0007.jsonl
python -m generator.gen --world B --split dev --seeds 7 --out ~/aditya-scratch/run2/ >/dev/null && cmp data/streams/P1A-s0007.jsonl ~/aditya-scratch/run2/P1A-s0007.jsonl && echo SAME
python -m pytest -q tests/test_twin_prefix.py 2>&1 | tail -n 1
```
Expected: four files written; a C-s0007 line count around 2,000; `SAME`; the twin test now `11 passed` (the 9 pair tests and the 2 helper tests).
If the pair tests still fail, run this to see the first difference:
```bash
python -c "
import json
a=[json.loads(l) for l in open('data/streams/P1A-s0007.jsonl')]
b=[json.loads(l) for l in open('data/streams/P1B-s0007.jsonl')]
fa=[x for x in a if x['kind']!='reply' and x['event_time_s']<420]; fb=[x for x in b if x['kind']!='reply' and x['event_time_s']<420]
print(len(fa), len(fb), next(((x,y) for x,y in zip(fa,fb) if {k:v for k,v in x.items() if k!='episode_id'}!={k:v for k,v in y.items() if k!='episode_id'}), None))"
```

## Done when
- [ ] Four DEV 7 files exist in `data/streams/` (P1A, P1B, N, C).
- [ ] `cmp` prints SAME.
- [ ] Twin test is green (11 passed).
- [ ] Send Harshavi the file sizes: `du -h data/streams/*s0007.jsonl`.

## Then (git, from the repo root; streams are NOT committed, the code is)
```bash
cd ~/dev/Twin_Breaker
git switch aditya          # your branch (never commit on main)
git add generator/gen.py
git commit -m "generator: pass 1 writer and CLI (DEV seed 7 ready)"
git pull --no-edit origin main
git push                    # updates your open PR (open one if none: see aditya.md)
```
Tell Harshavi: "DEV 7 ready. Regenerate with `python -m generator.gen --world B --split dev --seeds 1-10 --out data/streams/`. Sizes: <paste du output>."
