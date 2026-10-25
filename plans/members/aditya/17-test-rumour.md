# Card 17: tests/test_rumour_phrasings.py
- **Model:** 35B · **Slot:** 18:20–18:35 · **Gate:** rumour pass check (red team 1)
- **File:** `tests/test_rumour_phrasings.py`
- **Goal:** Check the 12 phrasings form ONE cluster under the engine's rule. Each phrasing must be at Jaccard ≥ 0.8 to phrasing 0, and single-linkage clustering must give exactly one cluster.

## Contract (copied in)
- Normalise: lowercase; each non-alphanumeric character becomes a space; collapse runs of spaces; strip.
- Shingles: the set of tuples of 3 consecutive words.
- Jaccard: |A ∩ B| / |A ∪ B|.
- Single-linkage cluster: process phrasings in order. A phrasing joins the first existing cluster that has any member with Jaccard ≥ 0.8; otherwise it starts a new cluster. Expect 1 cluster.
- File: `scenarios/rumour_wave.json` (path from the test file: `Path(__file__).parents[1] / 'scenarios' / 'rumour_wave.json'`).

## Example
Phrasing 0 vs phrasing 1 (one word changed in the middle of 30 words): Jaccard about 0.8 or above → passes. A phrasing with a changed word in its first 3 words may fall below 0.8 → the test names it.

## Qwen prompt (paste into a fresh chat)
```text
You write one pytest file for a hackathon demo. Synthetic data only. Python 3.11; pytest and the standard library (json, re, pathlib) only. No network. Output only the full file in one code block, under 80 lines, no commentary.

Write tests/test_rumour_phrasings.py.
1. def normalise(text: str) -> str: lowercase; re.sub(r'[^a-z0-9]', ' ', text.lower()); collapse spaces with ' '.join(s.split()); return the string.
2. def shingles(text: str) -> set[tuple[str, ...]]: words = normalise(text).split(); return {tuple(words[i:i+3]) for i in range(len(words) - 2)}.
3. def jaccard(a: set, b: set) -> float: return len(a & b) / len(a | b) if (a | b) else 0.0.
4. PHR = json.loads((Path(__file__).parents[1] / 'scenarios' / 'rumour_wave.json').read_text())['phrasings'].
5. def test_has_12_phrasings(): assert len(PHR) == 12.
6. def test_each_phrasing_close_to_base(): base = shingles(PHR[0]); for i in range(1, 12): j = jaccard(base, shingles(PHR[i])); assert j >= 0.8, f'phrasing {i} has Jaccard {j:.3f} to phrasing 0'.
7. def test_one_cluster_single_linkage(): clusters = []; for each phrasing s (in order): sh = shingles(s); find the first cluster c where any(jaccard(sh, m) >= 0.8 for m in c); if found, append sh to c; else start a new cluster [sh]. assert len(clusters) == 1.
Output the whole file.
```

## Check (bash)
```bash
cd ~/dev/Twin_Breaker && source .venv/bin/activate && python -m pytest -q tests/test_rumour_phrasings.py 2>&1 | tail -n 3
```
Expected: `3 passed`. If the close-to-base test fails for phrasing i, the changed word is at the edge of the text or the change is a whole word that alters three shingles. Re-run card 15 with a middle position for that phrasing, or edit that one word by hand so that the word is a near-synonym of the same length.

## Done when
- [ ] `3 passed`.

## Then (git, from the repo root)
```bash
cd ~/dev/Twin_Breaker
git switch aditya          # your branch (never commit on main)
git add tests/test_rumour_phrasings.py
git commit -m "tests: rumour phrasings form one cluster"
git pull --no-edit origin main
git push                    # updates your open PR (open one if none: see aditya.md)
```
