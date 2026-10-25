# Card 23: eval/check_stats.py (EVAL assertion and §10 table)
- **Model:** 9B coder · **Slot:** 21:30–22:00 (ready before the 06:00 freeze) · **Gate:** 06:00 EVAL run
- **File:** `eval/check_stats.py`
- **Goal:** Read `results/eval_summary.json`, assert the episode counts (150 cascade, 300 non-cascade), and print the §10 table.

## Contract (copied in)
- Summary shape (index ASK 8; Harshavi's `/api/results` serves it): `{"episodes": [{"episode_id", "hypothesis", "pair", "role", ...}], "metrics": {"1": {"name", "ours", "grey", "target"}, ..., "13": {...}}}`.
- Cascade = episodes with hypothesis `"C"` (the 3 A-roles per seed × 50 seeds = 150). Non-cascade = all others (3 B-roles + N + S + I per seed × 50 = 300).
- Table columns: `#`, `metric`, `ours`, `grey`, `target`. Missing values print `n/a`.

## Signatures (exact)
```python
def check_counts(episodes: list[dict]) -> tuple[int, int]     # (cascade, non_cascade)
def render(summary: dict) -> str
def main(argv: list[str] | None = None) -> int                # argv[0] = path, default results/eval_summary.json
```

## Qwen prompt (paste into a fresh chat)
```text
You write one Python file for a hackathon demo. Synthetic data only. Python 3.11, standard library only (json, sys, pathlib). No network. Output only the full file in one code block, under 70 lines, no commentary.

Write eval/check_stats.py.
1. def check_counts(episodes: list[dict]) -> tuple[int, int]: cascade = sum(1 for e in episodes if e.get('hypothesis') == 'C'); return (cascade, len(episodes) - cascade).
2. def render(summary: dict) -> str: header line: '#  metric                 ours      grey      target'. For k in range(1, 14): m = summary.get('metrics', {}).get(str(k), {}); lines.append(f"{k:<3}{m.get('name','n/a'):<24}{str(m.get('ours','n/a')):<10}{str(m.get('grey','n/a')):<10}{m.get('target','n/a')}"). Return '\n'.join(lines).
3. def main(argv: list[str] | None = None) -> int: args = argv or []; path = Path(args[0]) if args else Path('results/eval_summary.json'); summary = json.loads(path.read_text()); c, n = check_counts(summary.get('episodes', [])); if (c, n) != (150, 300): print(f'ASSERT FAILED: need 150 cascade and 300 non-cascade, got {c} and {n}'); return 1. Otherwise print(render(summary)); return 0.
4. if __name__ == '__main__': raise SystemExit(main(sys.argv[1:])).
Use pathlib.Path; add 'from pathlib import Path' and 'import sys'.
Output the whole file.
```

## Check (bash)
```bash
cd ~/dev/Twin_Breaker && source .venv/bin/activate
python -m eval.check_stats results/eval_summary.json; echo "exit $?"
```
Expected before the 06:00 run (no file yet): a traceback or `FileNotFoundError`. The assertion path is tested with a fake file:
```bash
mkdir -p ~/aditya-scratch && python -c "import json,os; p=os.path.expanduser('~/aditya-scratch/x.json'); json.dump({'episodes':[{'hypothesis':'C'}]*2}, open(p,'w'))"
python -m eval.check_stats ~/aditya-scratch/x.json; echo "exit $?"
```
Expected: `ASSERT FAILED: need 150 cascade and 300 non-cascade, got 2 and 0` then `exit 1`.

## Done when
- [ ] The fake-file check prints the ASSERT line and `exit 1`.

## Then (git, from the repo root)
```bash
cd ~/dev/Twin_Breaker
git switch aditya          # your branch (never commit on main)
git add eval/check_stats.py
git commit -m "eval: check_stats (150/300 assertion and table)"
git pull --no-edit origin main
git push                    # updates your open PR (open one if none: see aditya.md)
```
