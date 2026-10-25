# Card 19: generator/latent.py rewrite with hypotheses S and I (pass 2)
- **Model:** 9B coder · **Slot:** 19:00–19:30 · **Gate:** EVAL needs S (outage) and I (cut-out); pass 2 cut candidate (index ASK 9)
- **File:** `generator/latent.py` (full rewrite; same names as card 04, plus S and I)
- **Goal:** Add hypothesis S (sensor failure: depth stays 0, drains get stuck) and hypothesis I (a short, shallow flood, peak below the responder threshold). Both come from world keys you add by hand.

## Contract (copied in)
Episode names: `^(N|C|I|S|P[1-3][AB])-s(\d{4})$`.
- `N-s####` → ('N', None, None). `C-s####` → ('C', None, None). `I-s####` → ('I', None, None). `S-s####` → ('S', None, None).
- `P<k>A-s####` → ('C', 'P<k>', 'A'). `P<k>B-s####` → ('N', 'P<k>', 'B').
Depths (cm), index = sim minute, length `episode_minutes`:
- N, no role: all 0.0.
- C (plain or role A): onset in `cascade.onset_min` (key `"<pair or C>:onset"`, from `episode_rng`); depth = 0 before onset, then `min(cap_cm, slope_cm_per_min * (m - onset + 1))`.
- Role B (storm): 0 before `storm.start_min`, then `storm.peak_cm * min(1, (m - start + 1) / storm.ramp_min)`. rain_extra = `storm.rain_peak_mm_h` times the same ramp.
- I: onset from `shallow.onset_min` ([lo, hi]), key `"I:onset"`. Depth = `shallow.peak_cm` for `shallow.hold_min` minutes from onset, then 0. Must be below `responder.threshold_cm` (check in the world file).
- S: depth all 0.0. `stuck_drain_from` = `sensor_fail.start_min` (int). Otherwise None.
- All rain_extra zeros except role B.
- Twin rule: for pairs, minutes 0 to 6 have depth 0 in both twins (onsets are ≥ 8; storm starts ≥ 7).

World keys to add by hand to `generator/world_spec.json` first (new keys; leave the rest): `"shallow": {"onset_min": [lo, hi], "peak_cm": x, "hold_min": 3}`. `shallow.peak_cm` must be below `responder.threshold_cm`. `shallow.onset_min` lower bound must be 8 or more.

## Signatures (exact)
```python
@dataclass(frozen=True)
class Latent:
    episode: str; hypothesis: str; pair: str | None; role: str | None; onset_min: int | None
    depth_cm: list[float]; rain_extra_mm_h: list[float]
    stuck_drain_from: int | None = None
def parse_episode(episode: str) -> tuple[str, str | None, str | None, int]   # ValueError if no match
def make_latent(seed: int, episode: str, world: dict) -> Latent
```

## Qwen prompt (paste into a fresh chat)
```text
You write one Python file for a hackathon demo. Synthetic data only. Python 3.11, standard library and numpy only, plus the local module below. No network. Output only the full file in one code block, under 130 lines, no commentary. Use type hints.

Write generator/latent.py. Imports: re; dataclasses (dataclass); from generator.rng import episode_rng.
1. @dataclass(frozen=True) class Latent with fields in this order: episode: str; hypothesis: str; pair: str | None; role: str | None; onset_min: int | None; depth_cm: list[float]; rain_extra_mm_h: list[float]; stuck_drain_from: int | None = None.
2. def parse_episode(episode: str) -> tuple[str, str | None, str | None, int]: m = re.fullmatch(r'(N|C|I|S|P[1-3][AB])-s(\d{4})', episode); if not m: raise ValueError(f'bad episode {episode}'). code = m.group(1); seed = int(m.group(2)). If code in ('N','C','I','S'): return (code, None, None, seed). Else pair = code[:2]; role = code[2]; hyp = 'C' if role == 'A' else 'N'; return (hyp, pair, role, seed).
3. def make_latent(seed: int, episode: str, world: dict) -> Latent. Steps:
   a. hyp, pair, role, parsed = parse_episode(episode); if parsed != seed: raise ValueError. T = world['episode_minutes']. zeros = [0.0] * T.
   b. If hyp == 'C' and role in ('A', None): key = f"{pair or 'C'}:onset"; lo, hi = world['cascade']['onset_min']; onset = int(episode_rng(seed, key).integers(lo, hi + 1)); cap = world['cascade']['cap_cm']; slope = world['cascade']['slope_cm_per_min']; depth = [0.0 if m < onset else min(cap, slope * (m - onset + 1)) for m in range(T)]. Return Latent(episode, hyp, pair, role, onset, depth, zeros[:], None).
   c. If role == 'B': start = world['storm']['start_min']; ramp_min = world['storm']['ramp_min']; for each m: if m < start: depth 0.0, rain 0.0; else r = min(1.0, (m - start + 1) / ramp_min); depth = world['storm']['peak_cm'] * r; rain = world['storm']['rain_peak_mm_h'] * r. Return Latent(..., onset_min None, depth, rain, None).
   d. If hyp == 'I': lo, hi = world['shallow']['onset_min']; onset = int(episode_rng(seed, 'I:onset').integers(lo, hi + 1)); hold = world['shallow']['hold_min']; peak = world['shallow']['peak_cm']; depth = [peak if onset <= m < onset + hold else 0.0 for m in range(T)]. Return Latent(episode, 'I', None, None, onset, depth, zeros[:], None).
   e. If hyp == 'S': return Latent(episode, 'S', None, None, None, zeros[:], zeros[:], world['sensor_fail']['start_min']).
   f. Otherwise (N with no role): return Latent(episode, 'N', None, None, None, zeros[:], zeros[:], None).
4. Use only the world dict for numbers. The only random draws are onsets. Do not read any other file. Do not use the word "engine".
Output the whole file.
```

## Hand edit (you): `generator/passive.py`
In the drain loop, after computing `value` for each sensor: `if latent.stuck_drain_from is not None and minute >= latent.stuck_drain_from: value = round(world['sensor_fail']['stuck_fill'], 3)`. Keep the random draws unchanged, so the twin test is unaffected.

## Check (bash)
```bash
cd ~/dev/Twin_Breaker && source .venv/bin/activate
python -c "
import json; from generator.latent import make_latent
s=json.load(open('generator/world_spec.json'))
print(make_latent(7,'I-s0007',s).hypothesis, make_latent(7,'S-s0007',s).stuck_drain_from, make_latent(7,'P1A-s0007',s).hypothesis)"
python -m generator.gen --world B --split dev --seeds 7 --out data/streams/ >/dev/null && python -m pytest -q tests/test_twin_prefix.py tests/test_schema.py 2>&1 | tail -n 1
```
Expected: the first line prints `I` and the `sensor_fail.start_min` number and `C`. The second line ends with `passed` and shows no `failed` (the twin and schema tests still pass).
Note: `generate('B', 'dev', 7, 'S-s0007', dir)` works for any hypothesis name. `episodes_for` lists only N, C, P1A and P1B until pass 3. The check above calls `make_latent` directly.

## Done when
- [ ] The first line prints `I` followed by the number of `sensor_fail.start_min` and `C`.
- [ ] Twin and schema tests still green.
- [ ] `grep -n "engine" generator/latent.py` prints nothing.

## Then (git, from the repo root)
```bash
cd ~/dev/Twin_Breaker
git switch aditya          # your branch (never commit on main)
git add generator/latent.py generator/passive.py generator/world_spec.json
git commit -m "generator: hypotheses S and I, shallow flood keys"
git pull --no-edit origin main
git push                    # updates your open PR (open one if none: see aditya.md)
```
Note: `world_spec.json` changed after the hash in card 02. Re-run `sha256sum generator/world_spec.json > generator/world_spec.sha` first and tell Harshavi a new hash line was pushed (with the reason: new keys added in pass 2).
