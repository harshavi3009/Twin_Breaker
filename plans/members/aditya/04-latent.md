# Card 04: generator/latent.py
- **Model:** 9B coder · **Slot:** 14:15–14:35 · **Gate:** twin rule (minutes 0–6 identical)
- **File:** `generator/latent.py`
- **Goal:** The hidden state of one episode: hypothesis, role, onset, and depth and rain per minute. The twin rule is built in here.

## Contract (copied in)
Episode names match `^(N|C|P[1-3][AB])-s(\d{4})$`.
- `N-s0007`: hypothesis N, no pair, no role (no flood).
- `C-s0007`: hypothesis C, no pair (a plain cascade).
- `P1A-s0007`: cascade twin: hypothesis C, pair P1, role A.
- `P1B-s0007`: storm twin: hypothesis N, pair P1, role B.
Twin rule: onset (cascade) is in [8, 10]; storm starts at `storm.start_min` (7 or more). So minutes 0 to 6 have depth 0 in both twins, and every passive draw for those minutes is identical.
World values come from the `world` dict (keys in card 02): `episode_minutes`, `cascade.onset_min` ([lo,hi]), `cascade.slope_cm_per_min`, `cascade.cap_cm`, `storm.start_min`, `storm.peak_cm`, `storm.ramp_min`, `storm.rain_peak_mm_h`.

## Signatures (exact)
```python
@dataclass(frozen=True)
class Latent:
    episode: str
    hypothesis: str           # "N" or "C" (card 19 adds "S" and "I")
    pair: str | None          # "P1" ... or None
    role: str | None          # "A", "B" or None
    onset_min: int | None
    depth_cm: list[float]     # index = sim minute, length episode_minutes
    rain_extra_mm_h: list[float]

def parse_episode(episode: str) -> tuple[str, str | None, str | None, int]   # (hypothesis, pair, role, seed); ValueError if no match
def make_latent(seed: int, episode: str, world: dict) -> Latent
```

## Examples
- `make_latent(7,'P1A-s0007',spec)`: hypothesis `C`, onset_min 8, 9 or 10, `depth_cm[:7]` all 0.0.
- `make_latent(7,'P1B-s0007',spec)`: hypothesis `N`, onset_min None, `depth_cm[:7]` all 0.0, rising from minute `storm.start_min`.
- `parse_episode('P1B-s0007')` → `('N', 'P1', 'B', 7)`

## Qwen prompt (paste into a fresh chat)
```text
You write one Python file for a hackathon demo. Synthetic data only. Python 3.11, standard library only plus numpy. No network. Output only the full file in one code block, under 120 lines, no commentary. Use type hints.

Write generator/latent.py. Imports: re, dataclasses (dataclass), and from generator.rng import episode_rng.
1. @dataclass(frozen=True) class Latent with fields: episode: str; hypothesis: str; pair: str | None; role: str | None; onset_min: int | None; depth_cm: list[float]; rain_extra_mm_h: list[float].
2. def parse_episode(episode: str) -> tuple[str, str | None, str | None, int]. Use re.fullmatch(r'(N|C|P[1-3][AB])-s(\d{4})', episode). No match: raise ValueError(f'bad episode {episode}'). If the code is N: return ('N', None, None, seed). If C: ('C', None, None, seed). If it is P<k>A: ('C', 'P<k>', 'A', seed). If P<k>B: ('N', 'P<k>', 'B', seed). seed = int of the 4 digits.
3. def make_latent(seed: int, episode: str, world: dict) -> Latent. Steps:
   a. hyp, pair, role, parsed_seed = parse_episode(episode). If parsed_seed != seed raise ValueError.
   b. T = world['episode_minutes'].
   c. If hyp == 'C': key = f"{pair or 'C'}:onset"; lo, hi = world['cascade']['onset_min']; onset = int(episode_rng(seed, key).integers(lo, hi + 1)). For m in range(T): depth = 0.0 if m < onset else min(cap, slope * (m - onset + 1)) with cap = world['cascade']['cap_cm'] and slope = world['cascade']['slope_cm_per_min']. rain_extra all 0.0.
   d. If role == 'B' (storm twin): onset_min = None. start = world['storm']['start_min']. For m < start: depth 0.0 and rain 0.0. For m >= start: ramp = min(1.0, (m - start + 1) / world['storm']['ramp_min']); depth = world['storm']['peak_cm'] * ramp; rain = world['storm']['rain_peak_mm_h'] * ramp.
   e. Otherwise (N with no role): onset_min None, all depth 0.0, all rain 0.0.
   Return Latent(episode, hyp, pair, role, onset_min, depth, rain).
4. Use only the world dict for numbers. The only random draw is the onset. Do not read any other file.
Output the whole file.
```

## Check (bash)
```bash
cd ~/dev/Twin_Breaker && source .venv/bin/activate
python -c "
import json; from generator.latent import make_latent
s=json.load(open('generator/world_spec.json'))
a=make_latent(7,'P1A-s0007',s); b=make_latent(7,'P1B-s0007',s)
print(a.hypothesis, a.onset_min, all(d==0 for d in a.depth_cm[:7]), all(d==0 for d in b.depth_cm[:7]), b.hypothesis)"
```
Expected: `C 8 True True N` (the onset may be 8, 9 or 10).

## Done when
- [ ] The check prints the expected pattern.
- [ ] `grep -n "engine" generator/latent.py` prints nothing.

## Then (git, from the repo root)
```bash
cd ~/dev/Twin_Breaker
git switch aditya          # your branch (never commit on main)
git add generator/latent.py
git commit -m "generator: latent episode state with twin rule"
git pull --no-edit origin main
git push                    # updates your open PR (open one if none: see aditya.md)
```
