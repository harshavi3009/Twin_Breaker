# Card 15: scenarios/rumour_wave.json
- **Model:** 35B (copy) · **Slot:** 18:00–18:15 · **Gate:** 18:00 integration (scenario JSON validated)
- **File:** `scenarios/rumour_wave.json`
- **Goal:** Red team 1. 400 citizen forwards in 40 seconds, 12 phrasings. The engine clusters them by shingle overlap, so the phrasings must be near-identical.

## Contract (copied in)
Schema (exact keys): `{"name": "rumour_wave", "kind": "citizen_burst", "count": 400, "window_s": 40, "phrasings": [12 strings]}`
- `phrasings[0]` is a base text of about 30 words, fictional, no real people or businesses.
- `phrasings[1..11]` each equal the base with exactly ONE word changed, each changed at a different MIDDLE position (not the first or last 3 words).
- Why: the rule is 3-word shingles at Jaccard ≥ 0.8. One changed word in a 30-word text keeps Jaccard about 0.8 to the base. Two variants can be lower to each other, but each one joins the cluster through the base.

## Example (shape only)
`{"name":"rumour_wave","kind":"citizen_burst","count":400,"window_s":40,"phrasings":["<base 30 words>","<base with word 7 changed>", "... 12 items"]}`

## Qwen prompt (paste into a fresh chat)
```text
Output only one JSON object, no prose, no code fence. It must be:
{"name":"rumour_wave","kind":"citizen_burst","count":400,"window_s":40,"phrasings":[...12 strings...]}
Rules for the strings:
- phrasings[0] is one fictional English forward of about 30 words about a flooded underpass in a city ward. No real names of people or businesses.
- phrasings[1] to phrasings[11] are copies of phrasings[0] word for word, except exactly ONE word is changed in each. Use a different middle word position for each of the 11 (positions 4 to 27 when counting from 1; never the first 3 or last 3 words). Replace the word with a different English word of the same length class.
- Do not add punctuation differences beyond the original; keep the same punctuation as phrasings[0].
```

## Check (bash)
```bash
cd ~/dev/Twin_Breaker && python3 -c "
import json; d=json.load(open('scenarios/rumour_wave.json'))
print(d['count'], len(d['phrasings']), len(d['phrasings'][0].split()))"
```
Expected: `400 12 <about 30>` (25 to 35 words). The Jaccard test is card 17.

## Done when
- [ ] The check prints `400 12` with a word count from 25 to 35.

## Then (git, from the repo root)
```bash
cd ~/dev/Twin_Breaker
git switch aditya          # your branch (never commit on main)
git add scenarios/rumour_wave.json
git commit -m "scenarios: rumour wave (red team 1)"
git pull --no-edit origin main
git push                    # updates your open PR (open one if none: see aditya.md)
```
