# Card 10: eval/metrics.py
- **Model:** 9B coder · **Slot:** 16:00–16:20 · **Gate:** 16:00 DEV table needs this
- **File:** `eval/metrics.py`
- **Goal:** Five pure metric functions. They must pass the 10 hand-computed tests from card 08.

## Contract (copied in, exact signatures)
```python
HYPS = ("N", "S", "I", "C")
def brier_binary(p: list[float], y: list[int]) -> float
def brier_multi(P: list[list[float]], labels: list[str]) -> float
def ece(p: list[float], y: list[int], bins: int = 10) -> tuple[float, list[dict]]
def lead_time_min(actions: list[str], onset_min: int) -> int | None
def flip_count(actions: list[str], window_min: int = 3) -> int
```
Definitions:
- `brier_multi`: for each row, sum over HYPS of (P[i][j] - 1 if labels[i] == h else P[i][j] - 0)^2; then mean over rows.
- `ece`: bin index = min(bins - 1, int(p * bins)). Each bin dict: `{"lo", "hi", "n", "conf", "acc"}`; conf = mean p, acc = mean y, both None if empty. ECE = sum over non-empty bins of (n / N) * |acc - conf|.
- `lead_time_min`: first index i with actions[i] in ("ALERT", "ESCALATE"); return onset_min - i; None if none.
- `flip_count`: see the flip rule in card 08.

## Qwen prompt (paste into a fresh chat)
```text
You write one Python file for a hackathon demo. Pure functions, synthetic data only. Python 3.11, standard library only (math, typing). No network. Output only the full file in one code block, under 120 lines, no commentary. Use type hints and short docstrings.

Write eval/metrics.py with HYPS = ('N', 'S', 'I', 'C') and these five functions, exact names and signatures:
1. def brier_binary(p: list[float], y: list[int]) -> float: raise ValueError if the lengths differ or are zero. Return the mean of (p_i - y_i)^2.
2. def brier_multi(P: list[list[float]], labels: list[str]) -> float: raise ValueError on length mismatch or zero rows. For each row i: total = sum over j in 0..3 of (P[i][j] - (1.0 if labels[i] == HYPS[j] else 0.0))^2. Return the mean of the row totals.
3. def ece(p: list[float], y: list[int], bins: int = 10) -> tuple[float, list[dict]]: raise ValueError on length mismatch. Build a list of bins dicts for k in 0..bins-1 with keys lo (k/bins), hi ((k+1)/bins), n (0), sum_p (0.0), sum_y (0.0). For each item: k = min(bins - 1, int(p_i * bins)); n += 1; sum_p += p_i; sum_y += y_i. Then for each bin: conf = sum_p / n if n else None; acc = sum_y / n if n else None; remove sum_p and sum_y, add conf and acc. ece_value = sum over bins with n > 0 of (n / N) * abs(acc - conf). Return (ece_value, bin list).
4. def lead_time_min(actions: list[str], onset_min: int) -> int | None: find the first index i where actions[i] is 'ALERT' or 'ESCALATE'. None if there is none. Else return onset_min - i.
5. def flip_count(actions: list[str], window_min: int = 3) -> int: compute change points: indices k >= 1 where actions[k] != actions[k-1]. Walk the change points in order. For each change point k with an immediately previous change point prev: if actions[k] == actions[prev - 1] and k - prev <= window_min, count one flip. Return the count. With window_min 0 there are no flips.
Output the whole file.
```

## Check (bash)
```bash
cd ~/dev/Twin_Breaker && source .venv/bin/activate
python -m pytest -q tests/test_metrics.py 2>&1 | tail -n 1
```
Expected: `10 passed`. If one fails, print the failing assertion and fix only that function.

## Done when
- [ ] `10 passed`.

## Then (git, from the repo root)
```bash
cd ~/dev/Twin_Breaker
git switch aditya          # your branch (never commit on main)
git add eval/metrics.py
git commit -m "eval: metrics (brier, ece, lead time, flips)"
git pull --no-edit origin main
git push                    # updates your open PR (open one if none: see aditya.md)
```
