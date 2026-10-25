# Card 14: generator/responder.py (the marshal)
- **Model:** 9B coder · **Slot:** 17:35–18:00 · **Gate:** 18:00 integration (Harshavi replaces his mock with this)
- **File:** `generator/responder.py`
- **Goal:** The sealed marshal. Answers from the latent depth at the time asked, with a sealed error rate. Deterministic for the same inputs.

## Contract (copied in)
Server calls (exact): `reply(episode_id: str, question_id: str, asked_at_s: int) -> {"answer": "yes" | "no", "responder_id": "marshal-W9-01", "delay_s": 55}`.
- Delay: integer in `responder.delay_s` ([30, 90]).
- Error: default is the midpoint of `responder.error_default` (in [0.10, 0.25]). The sweep can pass `error=` (0.10, 0.25, 0.40). Sensitivity is 0.40.
- Truth: `generator/sealed/<episode_id>.truth.json` key `latent_depth_cm` (list, index = sim minute). `truth_yes = depth >= responder.threshold_cm`.
- Only this file (and `eval/`) reads sealed truth.

## Signature (exact)
```python
def reply(episode_id: str, question_id: str, asked_at_s: int, error: float | None = None) -> dict
```

## Example
`reply('C-s0007', 'Q1', 600)` → `{"answer": "yes", "responder_id": "marshal-W9-01", "delay_s": 47}` (answer and delay vary by seed and time; the same call always returns the same dict).

## Qwen prompt (paste into a fresh chat)
```text
You write one Python file for a hackathon demo. Synthetic data only. Python 3.11, standard library and the local module below only. No network. Output only the full file in one code block, under 80 lines, no commentary. Use type hints.

Write generator/responder.py. Imports: json, re, pathlib.Path; from generator.rng import episode_rng.
Define def reply(episode_id: str, question_id: str, asked_at_s: int, error: float | None = None) -> dict. Steps:
1. m = re.search(r'-s(\d{4})$', episode_id); if m is None raise ValueError; seed = int(m.group(1)).
2. truth = json.loads((Path(__file__).parent / 'sealed' / f'{episode_id}.truth.json').read_text()).
3. spec = json.loads(Path(__file__).with_name('world_spec.json').read_text()); R = spec['responder'].
4. minute = min(asked_at_s // 60, len(truth['latent_depth_cm']) - 1); depth = truth['latent_depth_cm'][minute]; truth_yes = depth >= R['threshold_cm'].
5. if error is None: error = (R['error_default'][0] + R['error_default'][1]) / 2.
6. rng = episode_rng(seed, f'reply:{question_id}:{asked_at_s}'). flip = rng.random() < error. answer_yes = truth_yes != flip.
7. lo, hi = R['delay_s']; delay = int(rng.integers(lo, hi + 1)).
8. Return {'answer': 'yes' if answer_yes else 'no', 'responder_id': 'marshal-W9-01', 'delay_s': delay}.
Do not use the word "engine" in the file. Output the whole file.
```

## Check (bash)
```bash
cd ~/dev/Twin_Breaker && source .venv/bin/activate
python -c "
from generator.responder import reply
r = reply('C-s0007','Q1',600)
print(r['responder_id'], 30 <= r['delay_s'] <= 90, reply('C-s0007','Q1',600) == r, reply('C-s0007','Q1',600, error=0.0)['answer'] in ('yes','no'))"
```
Expected: `marshal-W9-01 True True True`. (Needs the card 06 run for C-s0007 first.)

## Done when
- [ ] The check prints `marshal-W9-01 True True True`.
- [ ] `grep -n "engine" generator/responder.py` prints nothing.

## Then (git, from the repo root)
```bash
cd ~/dev/Twin_Breaker
git switch aditya          # your branch (never commit on main)
git add generator/responder.py
git commit -m "generator: sealed responder reply()"
git pull --no-edit origin main
git push                    # updates your open PR (open one if none: see aditya.md)
```
Tell Harshavi: "`from generator.responder import reply`; signature `reply(episode_id, question_id, asked_at_s, error=None)`."
