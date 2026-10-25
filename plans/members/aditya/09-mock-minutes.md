# Card 09: tests/fixtures/mock_minutes.json
- **Model:** 35B · **Slot:** 15:45–16:00 · **Gate:** sweep runs before the engine exists
- **File:** `tests/fixtures/mock_minutes.json`
- **Goal:** One MOCK episode, 10 minutes, in the shape the sweep reads. It is labelled `"mock": true` so no one can mistake it for a result.

## Contract (copied in)
Each element is one minute, the merged belief and decision of §8.2:
```json
{"episode_id":"P1A-s0007","minute":5,"p":{"N":0.40,"S":0.10,"I":0.05,"C":0.45},"action":"ALERT","candidate":"ALERT","changed":true,
 "ask":{"question_id":"Q1","text":"Water above ankle at Ambazari underpass? 1=yes 2=no","voi_net":0.41},"synthetic":true,"mock":true}
```
`ask` is null except at minute 5. `p` values sum to 1 (2 decimals).

## Example
Minute 0: `p.C` = 0.10, action WATCH. Minute 9: `p.C` = 0.70, action ALERT.

## Qwen prompt (paste into a fresh chat)
```text
Output only a JSON array (no prose, no code fence). It has 10 objects, minutes 0 to 9, for episode_id 'P1A-s0007'. Each object has these keys in this order: episode_id (string), minute (int), p (object with keys N, S, I, C; numbers with 2 decimals that sum to 1.00), action (one of WATCH, PREPARE, ALERT, ESCALATE), candidate (same set), changed (true or false), ask (null, except minute 5 where it is {"question_id":"Q1","text":"Water above ankle at Ambazari underpass? 1=yes 2=no","voi_net":0.41}), synthetic (true), mock (true).
Rules: p.C rises from 0.10 at minute 0 to 0.70 at minute 9 in roughly equal steps. p.N falls by the same amount. p.S stays near 0.10 and p.I near 0.05. Actions: WATCH for minutes 0, 1, 2; PREPARE for minutes 3 and 4; ALERT for minutes 5 to 9. candidate equals action. changed is true at minutes 3 and 5 only.
```

## Check (bash)
```bash
cd ~/dev/Twin_Breaker && python3 -c "
import json; d=json.load(open('tests/fixtures/mock_minutes.json'))
print(len(d), all(abs(sum(x['p'].values())-1)<0.02 for x in d), d[5]['ask'] is not None, d[0]['mock'])"
```
Expected: `10 True True True`

## Done when
- [ ] The check prints `10 True True True`.

## Then (git, from the repo root)
```bash
cd ~/dev/Twin_Breaker
git switch aditya          # your branch (never commit on main)
git add tests/fixtures/mock_minutes.json
git commit -m "tests: mock minute outputs for sweep (MOCK)"
git pull --no-edit origin main
git push                    # updates your open PR (open one if none: see aditya.md)
```
Tell Harshavi the path.
