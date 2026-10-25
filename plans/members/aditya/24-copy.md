# Card 24: docs/twin-breaker/copy.md (banner and slide copy)
- **Model:** 35B (copy) · **Slot:** 06:00–07:00 · **Gate:** slides and screens (08:30 video)
- **File:** `docs/twin-breaker/copy.md` (copy only; this folder is shared, so append your section under a new heading and never rewrite others' text)
- **Goal:** The exact banner, the ASK question, three slide headlines and one sentence per red team.

## Contract (copied in, exact)
- Banner (character for character): `SYNTHETIC. Scale inspired by a published 2005 Mumbai rainfall figure (NIDM). Not real telemetry. Fictional event at a real location.`
- ASK question (character for character): `Water above ankle at Ambazari underpass? 1=yes 2=no`
- Do not claim real rainfall, real events or real deaths. Do not state any Ambazari figure (the figures are unverified).

## Qwen prompt (paste into a fresh chat)
```text
Write Markdown with exactly these four headings, in this order, and no other text.
## Banner
The banner text, character for character: SYNTHETIC. Scale inspired by a published 2005 Mumbai rainfall figure (NIDM). Not real telemetry. Fictional event at a real location.
## ASK question
The question, character for character: Water above ankle at Ambazari underpass? 1=yes 2=no
## Slide headlines
Three headlines, each under 8 words, one each for: (a) the twin test, (b) asking as value of information, (c) silence is UNKNOWN, not all-clear.
## Red teams
One sentence each for: rumour wave (400 forwards, one cluster), G3 gateway outage (UNKNOWN, not all-clear), camera cut-out (traffic UNKNOWN, coverage 5/6). No real numbers beyond these.
```

## Check (bash)
```bash
cd ~/dev/Twin_Breaker && grep -n "SYNTHETIC. Scale inspired by a published 2005 Mumbai rainfall figure (NIDM). Not real telemetry. Fictional event at a real location." docs/twin-breaker/copy.md
```
Expected: one line printed, with its line number.

## Done when
- [ ] The grep prints one line.

## Then (git, from the repo root)
```bash
cd ~/dev/Twin_Breaker
git switch aditya          # your branch (never commit on main)
git add docs/twin-breaker/copy.md
git commit -m "docs: synthetic banner and slide copy (Aditya section)"
git pull --no-edit origin main
git push                    # updates your open PR (open one if none: see aditya.md)
```
