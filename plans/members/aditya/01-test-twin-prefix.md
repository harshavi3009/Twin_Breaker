# Card 01: tests/test_twin_prefix.py
- **Model:** 35B · **Slot:** 13:20–13:45 · **Gate:** first deliverable (Harshavi sees it at 13:20)
- **File:** `tests/test_twin_prefix.py`
- **Goal:** Test that the cascade twin (A) and the storm twin (B) have identical non-reply events before minute 7 (t < 420 s). It is red until card 06 is done.

## Contract (copied in)
Each generated file is one JSON object per line with exactly these keys: `event_id, episode_id, kind, channel, source_id, gateway_id, event_time_s, received_time_s, value, text, text_hash, question_id, answer, retracts`. Missing values are null.
Twin episodes: `P1A-s0007` (A, cascade) and `P1B-s0007` (B, storm). Pairs: P1, P2, P3. Seeds used: 7, 1, 2.
Rule: for `event_time_s < 420`, every line with `kind != "reply"` is identical in A and B, including `event_id`. Only `episode_id` differs.
Generator call: `from generator.gen import generate`, then `generate(world: str, split: str, seed: int, episode: str, out_dir: str) -> dict`. It writes `<out_dir>/<episode>.jsonl`.

## Example
Input lines A and B differ only in `episode_id` → the test passes.
An observation at `event_time_s` 100 has `value` 0.50 in A and 0.51 in B → the test fails with the index of the first difference.

## Qwen prompt (paste into a fresh chat)
```text
You write one Python file for a hackathon demo. Synthetic data only. Python 3.11, pytest, standard library only (json, pathlib, pytest). No network. Output only the full file in one code block, under 120 lines, no commentary.

Write tests/test_twin_prefix.py with these steps, in order:
1. Module-level imports: json, pathlib.Path, pytest. Do NOT import generator at module level.
2. Constants: PREFIX_S = 420; PAIRS = ['P1', 'P2', 'P3']; SEEDS = [7, 1, 2].
3. def prefix_view(lines: list[str]) -> list[dict]: for each non-empty line, json.loads it. Keep it only if obj['kind'] != 'reply' and obj['event_time_s'] < 420. Delete the key 'episode_id' from the kept dict. Return the kept dicts in file order.
4. def assert_same_prefix(a_lines: list[str], b_lines: list[str]) -> None: va = prefix_view(a_lines); vb = prefix_view(b_lines); assert len(va) > 0, 'empty prefix'; if va != vb, fail with a message giving the first index where they differ and both dicts at that index (assert with message, or pytest.fail).
5. def test_helper_accepts_identical(): build two line lists by hand. Each has three events: an observation at event_time_s 100 (value 0.5), a citizen at 300 (text 'water over road', text_hash '000000'), and a reply at 365 (question_id 'Q1', answer 'yes'). The two lists differ only in episode_id ('P1A-s0007' vs 'P1B-s0007'). Call assert_same_prefix. It must not raise. Make the reply in list B answer 'no' (replies may differ) and confirm it still does not raise.
6. def test_helper_rejects_difference(): same as step 5, but in list B change the observation's value to 0.6. Wrap assert_same_prefix in pytest.raises(AssertionError).
7. @pytest.mark.parametrize('pair', PAIRS) and @pytest.mark.parametrize('seed', SEEDS) on def test_twin_prefix(pair, seed, tmp_path). Inside the body: from generator.gen import generate. Call generate(world='B', split='dev', seed=seed, episode=f'{pair}A-s{seed:04d}', out_dir=str(tmp_path)), then the same for episode f'{pair}B-s{seed:04d}'. Read each file with Path(...).read_text().splitlines(). Call assert_same_prefix(a_lines, b_lines).
Output the whole file.
```

## Check (bash)
```bash
cd ~/dev/Twin_Breaker && source .venv/bin/activate
python -m pytest -q tests/test_twin_prefix.py 2>&1 | tail -n 1
```
Expected now: `9 failed, 2 passed` (the 9 pair tests fail with ModuleNotFoundError; the 2 helper tests pass). If you see `error` lines during collection, fix the imports. The 9 pair tests must be FAIL, not ERROR.

## Done when
- [ ] The file is under 120 lines and imports `generator` only inside the test function.
- [ ] The check prints `9 failed, 2 passed`.

## Then (git, from the repo root)
```bash
cd ~/dev/Twin_Breaker
git switch aditya          # your branch (never commit on main)
git add tests/test_twin_prefix.py
git commit -m "tests: twin prefix test (red until generator passes)"
git pull --no-edit origin main
git push                    # updates your open PR (open one if none: see aditya.md)
```
Tell Harshavi: "Card 01 pushed. First deliverable is in."
