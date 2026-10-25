# Card 08: tests/test_metrics.py (hand-computed values)
- **Model:** 35B · **Slot:** 15:30–15:45 · **Gate:** red until card 10 (eval/metrics.py)
- **File:** `tests/test_metrics.py`
- **Goal:** Test the five metric functions with values worked out by hand. These tests import only `eval.metrics`, never engine code.

## Contract (copied in)
```python
def brier_binary(p: list[float], y: list[int]) -> float          # mean of (p_i - y_i)^2
def brier_multi(P: list[list[float]], labels: list[str]) -> float # per row: sum over HYPS=(N,S,I,C) of (P - onehot)^2; mean over rows
def ece(p: list[float], y: list[int], bins: int = 10) -> tuple[float, list[dict]]
def lead_time_min(actions: list[str], onset_min: int) -> int | None   # onset - index of first ALERT/ESCALATE; None if none
def flip_count(actions: list[str], window_min: int = 3) -> int
```
Flip rule (ours): a change point is a minute k where actions[k] != actions[k-1]. Change point k is a flip if actions[k] == actions[prev-1] (it returns to the action before the previous change point, prev) and k - prev <= window_min.

## Worked values (hand-computed; do not change)
1. `brier_binary([0.2, 0.8], [0, 1])` = 0.04
2. `brier_multi([[0.1,0.2,0.3,0.4]], ['C'])` = 0.01+0.04+0.09+0.36 = 0.50
3. `brier_multi([[0.1,0.2,0.3,0.4],[0.25,0.25,0.25,0.25]], ['C','N'])` = (0.50 + 0.75) / 2 = 0.625
4. `ece([0.1,0.1,0.9,0.9],[0,0,1,0], bins=10)[0]` = 0.05 + 0.20 = 0.25; the bin list has 10 entries; entry 1 has n 2; entry 9 has n 2
5. `lead_time_min(['WATCH','WATCH','WATCH','ALERT','ALERT','ALERT'], 8)` = 8 - 3 = 5
6. `lead_time_min(['WATCH']*6, 8)` = None
7. `flip_count(['WATCH','PREPARE','WATCH','WATCH','WATCH'], 3)` = 1
8. `flip_count(['WATCH','PREPARE','ALERT','WATCH'], 3)` = 0
9. `flip_count(['WATCH','PREPARE','WATCH','PREPARE','WATCH'], 1)` = 3
10. `flip_count(['WATCH','PREPARE','WATCH','PREPARE','WATCH'], 0)` = 0

## Qwen prompt (paste into a fresh chat)
```text
You write one pytest file for a hackathon demo. Synthetic data only. Python 3.11; pytest and the standard library only. No network. Output only the full file in one code block, under 90 lines, no commentary.

Write tests/test_metrics.py. Import pytest and: from eval.metrics import brier_binary, brier_multi, ece, lead_time_min, flip_count.
Write exactly these 10 tests, one function each, using pytest.approx for floats:
1. brier_binary([0.2, 0.8], [0, 1]) == approx(0.04)
2. brier_multi([[0.1, 0.2, 0.3, 0.4]], ['C']) == approx(0.50)
3. brier_multi([[0.1, 0.2, 0.3, 0.4], [0.25, 0.25, 0.25, 0.25]], ['C', 'N']) == approx(0.625)
4. ece([0.1, 0.1, 0.9, 0.9], [0, 0, 1, 0], bins=10): value approx(0.25); the second return value has length 10; entry index 1 has 'n' == 2; entry index 9 has 'n' == 2.
5. lead_time_min(['WATCH','WATCH','WATCH','ALERT','ALERT','ALERT'], 8) == 5
6. lead_time_min(['WATCH']*6, 8) is None
7. flip_count(['WATCH','PREPARE','WATCH','WATCH','WATCH'], 3) == 1
8. flip_count(['WATCH','PREPARE','ALERT','WATCH'], 3) == 0
9. flip_count(['WATCH','PREPARE','WATCH','PREPARE','WATCH'], 1) == 3
10. flip_count(['WATCH','PREPARE','WATCH','PREPARE','WATCH'], 0) == 0
Output the whole file.
```

## Check (bash)
```bash
cd ~/dev/Twin_Breaker && source .venv/bin/activate
python -m pytest -q tests/test_metrics.py 2>&1 | tail -n 1
python -m py_compile tests/test_metrics.py && echo COMPILES
```
Expected now: an ImportError or `10 errors` (eval/metrics.py does not exist yet). `COMPILES` must print. After card 10: `10 passed`.

## Done when
- [ ] The file compiles and has 10 tests.

## Then (git, from the repo root)
```bash
cd ~/dev/Twin_Breaker
git switch aditya          # your branch (never commit on main)
git add tests/test_metrics.py
git commit -m "tests: hand-computed metric checks"
git pull --no-edit origin main
git push                    # updates your open PR (open one if none: see aditya.md)
```
