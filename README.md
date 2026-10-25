# Twin-Breaker — Team Obsidian · CASCADE '26

PS 2.1 *The First 10 Minutes* · Theme 2 *Crisis Before Crisis*

A calibrated crisis-belief engine for a city duty officer. It can **ASK** one well-chosen question to split look-alike "twin" episodes before the data does. Its belief holds against rumour waves, gateway outages and camera cut-outs.

All data is **SYNTHETIC / SIMULATED** and labelled as such.

- Plans: `plans/twin-breaker/MAIN_BUILD_PLAN.md`
- Members: `plans/members/harshavi.md`, `plans/members/aditya.md` (+ `plans/members/aditya/` cards)
- Credits: `CREDITS.md`

## Fallback (section 15a)

Switch trigger: the 14:00 go/no-go fails.

**Keep**
- The grey config (naive Bayes engine path)
- ASK with Q1 only
- One twin pair (DEV seed 7) with pre-rendered traces
- The three red-team cases as pre-rendered traces
- DEV 10-seed table
- SYNTHETIC banner

**Drop**
- VOI for Q2 and Q3
- Foresight beyond top-1
- Prior shift
- MISSPEC
- Live server

## Setup log

Stream sizes, measured on Aditya's generated DEV files (`python -m generator.gen --world B --split dev --seeds 1-10`). Setup Step 8 estimated about 400,000 bytes per file; the measured size is about twice that.

| File | Bytes |
|---|---|
| `P1A-s0007.jsonl` | 829,732 |
| `P1B-s0007.jsonl` | 832,717 |
| `N-s0007.jsonl` | 823,730 |
| `C-s0007.jsonl` | 824,466 |

Average over all 40 DEV files (seeds 1–10, 4 episodes each): 825,493 bytes, about 33 MB in total.
