# Card 03: generator/rng.py
- **Model:** 9B coder · **Slot:** 14:05–14:15 · **Gate:** feeds card 04–06
- **File:** `generator/rng.py`
- **Goal:** Keyed random generators, so each draw depends only on (seed, channel, minute), never on hidden state. Also text normalising and hashing.

## Contract (copied in)
- Every passive draw is keyed on `(seed, channel, minute)`.
- `text_hash` = first 6 hex characters of sha1 of `normalise_text(text)`. Normalise = lowercase, every character that is not a letter, digit or space becomes a space, runs of spaces collapse to one, strip the ends.

## Signatures (exact)
```python
CHANNEL_IDS: dict[str, int] = {"rain": 1, "drain": 2, "citizen": 3, "heartbeat": 4,
                               "traffic": 5, "calls": 6, "hospital": 7, "reply": 8, "episode": 9}
def channel_rng(seed: int, channel: str, minute: int) -> numpy.random.Generator
def episode_rng(seed: int, key: str) -> numpy.random.Generator
def normalise_text(text: str) -> str
def text_hash(text: str) -> str
```
- `channel_rng` returns `np.random.default_rng([seed, CHANNEL_IDS[channel], minute])`. Unknown channel: ValueError. minute < 0: ValueError.
- `episode_rng` returns `np.random.default_rng([seed, CHANNEL_IDS["episode"], int(hashlib.sha1(key.encode()).hexdigest()[:8], 16)])`.

## Examples
- `channel_rng(7,'rain',3).random() == channel_rng(7,'rain',3).random()` → True
- `normalise_text('Ambazari  Lake, WALL breached!')` → `'ambazari lake wall breached'`
- `len(text_hash('x'))` → 6

## Qwen prompt (paste into a fresh chat)
```text
You write one Python file for a hackathon demo. Synthetic data only. Python 3.11, numpy and the standard library only (hashlib, re). No network. Output only the full file in one code block, under 60 lines, no commentary. Use type hints.

Write generator/rng.py with exactly this API:
- CHANNEL_IDS: dict[str, int] = {"rain": 1, "drain": 2, "citizen": 3, "heartbeat": 4, "traffic": 5, "calls": 6, "hospital": 7, "reply": 8, "episode": 9}
- def channel_rng(seed: int, channel: str, minute: int): return numpy.random.default_rng([seed, CHANNEL_IDS[channel], minute]). If channel is not in CHANNEL_IDS raise ValueError(f"unknown channel {channel}"). If minute < 0 raise ValueError.
- def episode_rng(seed: int, key: str): return numpy.random.default_rng([seed, CHANNEL_IDS["episode"], int(hashlib.sha1(key.encode()).hexdigest()[:8], 16)]).
- def normalise_text(text: str) -> str: lowercase; replace every character that is not a letter, digit or space with a space (use re.sub(r"[^a-z0-9 ]", " ", ...) after lowercasing); collapse runs of spaces with re.sub(r"\s+", " "); strip.
- def text_hash(text: str) -> str: return the first 6 hex characters of hashlib.sha1(normalise_text(text).encode()).hexdigest().
Do not use the word "engine" anywhere in the file.
```

## Check (bash)
```bash
cd ~/dev/Twin_Breaker && source .venv/bin/activate
python -c "from generator.rng import channel_rng, text_hash, normalise_text as n; print(channel_rng(7,'rain',3).random()==channel_rng(7,'rain',3).random(), channel_rng(7,'rain',3).random()!=channel_rng(7,'rain',4).random(), n('Ambazari  Lake, WALL breached!'), len(text_hash('x')))"
```
Expected: `True True ambazari lake wall breached 6`

## Done when
- [ ] The check line matches exactly.
- [ ] `grep -n engine generator/rng.py` prints nothing.

## Then (git, from the repo root)
```bash
cd ~/dev/Twin_Breaker
git switch aditya          # your branch (never commit on main)
git add generator/rng.py
git commit -m "generator: keyed rng and text hash"
git pull --no-edit origin main
git push                    # updates your open PR (open one if none: see aditya.md)
```
Also create two empty package files once, in this same step: `touch generator/__init__.py eval/__init__.py`, then `git add` both paths before the commit.
