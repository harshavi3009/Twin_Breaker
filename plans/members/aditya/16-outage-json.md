# Card 16: scenarios/gateway_outage.json
- **Model:** 35B (copy) · **Slot:** 18:15–18:20 · **Gate:** 18:00 integration (scenario JSON validated)
- **File:** `scenarios/gateway_outage.json`
- **Goal:** Red team 2. Gateway G3 goes silent for 600 seconds from t = 300 s. Its drain sensors and heartbeat stop. The belief must not move on P(C); the output must say UNKNOWN, not all-clear.

## Contract (copied in)
Schema (exact keys):
```json
{"name": "gateway_outage", "kind": "silence", "gateway_id": "G3", "channel": "drain", "start_s": 300, "duration_s": 600,
 "note": "G3 drain sensors and heartbeat go silent. Silence is UNKNOWN, not all-clear."}
```
`apply_silence` (card 18) removes observations with that gateway and channel, and heartbeats from that gateway, when `start_s <= event_time_s < start_s + duration_s`.

## Qwen prompt (paste into a fresh chat)
```text
Output only this JSON, exactly, with no changes and no prose:
{"name": "gateway_outage", "kind": "silence", "gateway_id": "G3", "channel": "drain", "start_s": 300, "duration_s": 600, "note": "G3 drain sensors and heartbeat go silent. Silence is UNKNOWN, not all-clear."}
```

## Check (bash)
```bash
cd ~/dev/Twin_Breaker && python3 -c "import json; d=json.load(open('scenarios/gateway_outage.json')); print(d['gateway_id'], d['start_s'], d['duration_s'])"
```
Expected: `G3 300 600`

## Done when
- [ ] The check prints `G3 300 600`.

## Then (git, from the repo root)
```bash
cd ~/dev/Twin_Breaker
git switch aditya          # your branch (never commit on main)
git add scenarios/gateway_outage.json
git commit -m "scenarios: G3 gateway outage (red team 2)"
git pull --no-edit origin main
git push                    # updates your open PR (open one if none: see aditya.md)
```
