# Card 07: tests/test_schema.py
- **Model:** 35B · **Slot:** 15:15–15:30 · **Gate:** generated lines obey the §8.1 contract
- **File:** `tests/test_schema.py`
- **Goal:** Check each generated line against the contract. The test does its own normalising, so it does not depend on generator code.

## Contract (copied in)
Each line is a JSON object with keys: `event_id, episode_id, kind, channel, source_id, gateway_id, event_time_s, received_time_s, value, text, text_hash, question_id, answer, retracts`.
- Allowed kinds: `observation, citizen, heartbeat, reply, retraction, dispatch, hospital`.
- `observation`: channel in `rain, drain, traffic`; `gateway_id` not null.
- `citizen`: channel `citizen`; `text` not null; `text_hash` = first 6 hex chars of sha1 of normalised text. Normalise: lowercase; each non-alphanumeric becomes a space; collapse spaces; strip.
- All kinds: `received_time_s >= event_time_s`; `episode_id` equals the file name without `.jsonl`.
- Within a file, `event_id` values are unique.

## Example
- Valid observation: `{"event_id":"ev-s0007-drain-m005-drain-G2-031","episode_id":"N-s0007","kind":"observation","channel":"drain","source_id":"drain-G2-031","gateway_id":"G2","event_time_s":300,"received_time_s":331,"value":0.91,"text":null,"text_hash":null,"question_id":null,"answer":null,"retracts":null}` → no errors.
- Bad: same line with `"gateway_id":null` → at least one error.

## Qwen prompt (paste into a fresh chat)
```text
You write one pytest file for a hackathon demo. Synthetic data only. Python 3.11; pytest and the standard library (hashlib, json, re, pathlib) only. No network. Output only the full file in one code block, under 120 lines, no commentary.

Write tests/test_schema.py.
1. def normalise(text: str) -> str: lowercase; replace each non-alphanumeric character with a space (re.sub(r'[^a-z0-9]', ' ', text.lower())); collapse runs of spaces; strip. Written in this file, not imported.
2. KEYS = ['event_id','episode_id','kind','channel','source_id','gateway_id','event_time_s','received_time_s','value','text','text_hash','question_id','answer','retracts']; KINDS = {'observation','citizen','heartbeat','reply','retraction','dispatch','hospital'}.
3. def check_line(obj: dict, file_stem: str) -> list[str]: return a list of error strings (empty = OK). Errors: a missing key from KEYS; kind not in KINDS; for kind 'observation': channel not in {'rain','drain','traffic'} or gateway_id is None; for kind 'citizen': channel != 'citizen' or text is None or text_hash != hashlib.sha1(normalise(text).encode()).hexdigest()[:6]; received_time_s < event_time_s; episode_id != file_stem.
4. def test_check_line_accepts_valid(): build one observation dict (drain, gateway G2, value 0.91, episode_id 'N-s0007', event_time_s 300, received 331) and one citizen dict (text 'Water over the road near the underpass', text_hash computed in the test with the same rules). check_line(obj, 'N-s0007') == [] for both.
5. def test_check_line_rejects_bad(): (a) the observation with gateway_id None; (b) an observation with received_time_s 299. Each must return at least one error.
6. def test_generated_file_schema(tmp_path): from generator.gen import generate (inside the function). generate('B', 'dev', 7, 'N-s0007', str(tmp_path)). Read tmp_path/'N-s0007.jsonl' lines, json.loads each, collect check_line errors with file_stem 'N-s0007'. Assert no errors. Assert len(set(event_ids)) == number of lines. Assert more than 100 lines.
Output the whole file.
```

## Check (bash)
```bash
cd ~/dev/Twin_Breaker && source .venv/bin/activate
python -m pytest -q tests/test_schema.py 2>&1 | tail -n 2
```
Expected: `3 passed`. If the generated-file test fails, the message shows the first bad line.

## Done when
- [ ] `3 passed`.

## Then (git, from the repo root)
```bash
cd ~/dev/Twin_Breaker
git switch aditya          # your branch (never commit on main)
git add tests/test_schema.py
git commit -m "tests: schema checks for generated lines"
git pull --no-edit origin main
git push                    # updates your open PR (open one if none: see aditya.md)
```
