# Card 02: generator/world_spec.json (+ hash)
- **Model:** 35B (skeleton only; you type the numbers yourself) · **Slot:** 13:45–13:55 · **Gate:** hash committed before 14:00
- **Files:** `generator/world_spec.json` and `generator/world_spec.sha`
- **Goal:** The private world values. The engine never reads this file. Values must NOT be copied from the engine's tables or from PLAN_REVIEW.md item 4. You choose the numbers by hand.

## Contract (copied in)
The generator reads these keys. Keep every key name exactly.
- `episode_minutes` (int, 20 to 30)
- `drain_sensors_total` (100), `gateways` (["G1","G2","G3"])
- `noise`: `t_df` (3 to 6), `rain_scale_mm_h`, `drain_scale`, `delay_scale_s`
- `rain.base_mm_h`; `drain.base_fill`, `drain.per_cm_fill`
- `citizen`: `base_rate`, `cascade_rate` (0 to 1), `texts` (3 short fictional English reports)
- `cascade`: `onset_min` ([lo, hi], lo must be 8 or more, hi 10 or less), `slope_cm_per_min`, `cap_cm`
- `storm`: `start_min` (must be 7 or more), `peak_cm`, `ramp_min`, `rain_peak_mm_h`
- `traffic.slow_gain`; `calls`: `base_per_min`, `gain_per_min`; `hospital`: `base_per_min`, `gain_per_min`
- `responder`: `threshold_cm`, `error_default` ([lo, hi] inside [0.10, 0.25]), `error_sensitivity` (0.40), `delay_s` ([30, 90])
- `lags_min`: `drain_to_traffic`, `traffic_to_calls`, `calls_to_hospital` (each [lo, hi]; pick your own ranges)
- `sensor_fail`: `start_min` (int), `stuck_fill` (0 to 1)
- `twin_prefix_s`: 420, `version`: "pass1-1"

## Skeleton (Qwen writes this; then you type the numbers by hand)
Qwen prompt:
```text
Output ONLY this JSON, valid, with every null kept as null. Do not add or remove keys.
{"version":"pass1-1","episode_minutes":null,"drain_sensors_total":100,"gateways":["G1","G2","G3"],
"noise":{"t_df":null,"rain_scale_mm_h":null,"drain_scale":null,"delay_scale_s":null},
"rain":{"base_mm_h":null},"drain":{"base_fill":null,"per_cm_fill":null},
"citizen":{"base_rate":null,"cascade_rate":null,"texts":["","",""]},
"cascade":{"onset_min":[null,null],"slope_cm_per_min":null,"cap_cm":null},
"storm":{"start_min":null,"peak_cm":null,"ramp_min":null,"rain_peak_mm_h":null},
"traffic":{"slow_gain":null},
"calls":{"base_per_min":null,"gain_per_min":null},
"hospital":{"base_per_min":null,"gain_per_min":null},
"responder":{"threshold_cm":null,"error_default":[null,null],"error_sensitivity":0.40,"delay_s":[30,90]},
"lags_min":{"drain_to_traffic":[null,null],"traffic_to_calls":[null,null],"calls_to_hospital":[null,null]},
"sensor_fail":{"start_min":null,"stuck_fill":null},
"twin_prefix_s":420}
```

## What you type by hand
Open the file in your editor and replace each null with a number you choose. Constraints: episode_minutes 20–30; t_df 3–6; error_default two values in [0.10, 0.25]; storm.start_min ≥ 7; cascade.onset_min lower bound ≥ 8, upper ≤ 10; citizen rates between 0 and 1 with cascade_rate > base_rate; texts: three short fictional English sentences with no real names of people or businesses.

## Check (bash)
```bash
cd ~/dev/Twin_Breaker && source .venv/bin/activate
python3 -c "import json; d=json.load(open('generator/world_spec.json')); print(d['twin_prefix_s'], d['drain_sensors_total'], d['storm']['start_min']>=7, d['cascade']['onset_min'][0]>=8)"
sha256sum generator/world_spec.json > generator/world_spec.sha && sha256sum -c generator/world_spec.sha
grep -rn "engine" generator/ ; echo "grep done"
```
Expected: `420 100 True True`, then `generator/world_spec.json: OK`, then `grep done` with no grep lines above it.

## Done when
- [ ] Every null is a number (the check line runs without a KeyError or TypeError).
- [ ] `sha256sum -c` prints OK.

## Then (git, from the repo root)
```bash
cd ~/dev/Twin_Breaker
git switch aditya          # your branch (never commit on main)
git add generator/world_spec.json generator/world_spec.sha
git commit -m "generator: world spec frozen (hash in world_spec.sha)"
git pull --no-edit origin main
git push                    # updates your open PR (open one if none: see aditya.md)
```
Tell Harshavi the hash line only: `cat generator/world_spec.sha`. Never send the values.
