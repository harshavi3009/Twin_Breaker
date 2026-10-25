# Aditya's Build Plan: Twin-Breaker (Pod B), INDEX
**You own:** `generator/`, `eval/`, `scenarios/`, `tests/` (not `tests/test_engine_*.py`), `data/episodes/`, `results/` (not `results/dev/`), `docs/twin-breaker/` (copy)
**AI:** Qwen 35B IQ3 (cards marked 35B) and Qwen 9B coder (cards marked 9B). One model loaded at a time. **Machine:** Linux CachyOS, RTX 3050 6 GB, 16 GB RAM.
**Job:** the sealed synthetic world (twin streams, responder, red-team scenarios) and the eval code, so Harshavi's engine is judged on data it never sees.

**Use the cards:** one fresh Qwen chat per card. Paste only that card's "Qwen prompt" block, save the output to the path in the card, run its check, then its git block. Card files: `plans/members/aditya/NN-name.md`.

## Rules
1. Never open `engine/`. Never paste `world_spec.json` values (only the sha line goes out). `grep -rn "engine" generator/` must print nothing.
2. Git from `~/dev/Twin_Breaker`, on **your branch `aditya`** (never commit to `main`). One named file per `git add`. Never `git add .` or `--force`. If a push is rejected, run `git pull --no-edit origin main`, then `git push`.

## Git: Twin_Breaker repo, branch + pull request
- **Repo:** https://github.com/harshavi3009/Twin_Breaker. The repo root IS the project (`generator/`, `eval/`, `tests/`, …). There is no `twin-breaker/` folder.
- **Wait for Harshavi's "main is up" message**, then accept the GitHub collaborator invite in your email.
- **One-time (bash):**
```bash
mkdir -p ~/dev && cd ~/dev
git clone https://github.com/harshavi3009/Twin_Breaker.git
cd Twin_Breaker
git config pull.rebase false            # git pull merges, no rebase questions
git config push.autoSetupRemote true    # plain `git push` works on a new branch
git switch -c aditya                    # your branch
```
- **Every card's git block:** `git switch aditya`, `git add <file>`, `git commit`, `git pull --no-edit origin main`, then `git push`.
- **Open a pull request:**
  1. The first time, and again after Harshavi merges, open https://github.com/harshavi3009/Twin_Breaker.
  2. Click **Compare & pull request** on the yellow "aditya had recent pushes" bar.
  3. Check that it says base `main` ← compare `aditya`, then **Create pull request**.
  4. After that, every push updates the same PR.
- **Harshavi merges your PR** at the gates, and when you tell her "card NN pushed". **Never merge it yourself. Never delete your branch.**
- **To use Harshavi's merged code** (e.g. `engine/ingest.py`, `requirements.txt`), run `git pull --no-edit origin main` on your branch.

## Setup (13:05–13:20, bash)
```bash
cd ~/dev/Twin_Breaker && git switch aditya && git pull --no-edit origin main   # needs Harshavi's setup PR merged for requirements.txt
python3 -m venv .venv && source .venv/bin/activate
pip download -r requirements.txt -d vendor/wheels                       # Wi-Fi, once (no file? tell Harshavi)
pip install --no-index --find-links vendor/wheels -r requirements.txt   # must work offline
git check-ignore -v data/streams/x.jsonl generator/sealed/x.json .venv/x # each prints a rule
```

## Card index (build order)
| # | Card file | Model | Slot | Done when (check) |
|---|---|---|---|---|
| 01 | `01-test-twin-prefix.md` | 35B | 13:20–13:45 | `9 failed, 2 passed` (red is correct) |
| 02 | `02-world-spec.md` | 35B | 13:45–13:55 | `sha256sum -c` says OK |
| 03 | `03-rng.md` | 9B | 14:05–14:15 | prints `True True ambazari lake wall breached 6` |
| 04 | `04-latent.md` | 9B | 14:15–14:35 | prints `C <onset 8–10> True True N` |
| 05 | `05-passive.md` | 9B | 14:35–14:55 | prints count, `True`, kinds |
| 06 | `06-gen.md` | 9B | 14:55–15:15 | P1A, P1B, N, C for seed 7; `cmp` says SAME |
| 07 | `07-test-schema.md` | 35B | 15:15–15:30 | `3 passed` |
| 08 | `08-test-metrics.md` | 35B | 15:30–15:45 | red: ImportError (until card 10) |
| 09 | `09-mock-minutes.md` | 35B | 15:45–16:00 | prints `10 True True True` |
| 10 | `10-eval-metrics.md` | 9B | 16:00–16:20 | `10 passed` |
| 11 | `11-eval-collect.md` | 9B | 16:20–16:40 | prints `3 True 0` |
| 12 | `12-eval-sweep.md` | 9B | 16:40–17:10 | 40 DEV lines, seeds 1–10 (mock) |
| 13 | `13-passive-more.md` | 9B | 17:10–17:35 | twin test green after hand edit |
| 14 | `14-responder.md` | 9B | 17:35–18:00 | `marshal-W9-01 True True True` |
| 15 | `15-rumour-json.md` | 35B | 18:00–18:15 | prints `400 12` and ~30 words |
| 16 | `16-outage-json.md` | 35B | 18:15–18:20 | prints `G3 300 600` |
| 17 | `17-test-rumour.md` | 35B | 18:20–18:35 | `3 passed` |
| 18 | `18-scenarios-py.md` | 9B | 18:35–18:55 | prints `400 12` then `True True` |
| 19 | `19-latent-s-i.md` | 9B | 19:00–19:30 | hypothesis I, S ok; twin and schema still green |
| 20 | `20-eval-sensitivity.md` | 9B | 19:30–20:00 | 3 rows: VOI const 0.5, 0.7, 0.9 |
| 21 | `21-test-outage-hold.md` | 35B | 20:00–20:30 | `1 passed` (forget off) |
| 22 | `22-precompute.md` | 9B | 21:00–21:30 | `--dry-run` prints 24 lines |
| 23 | `23-check-stats.md` | 9B | 21:30–22:00 | ASSERT line on fake file, exit 1 |
| 24 | `24-copy.md` | 35B | 06:00–07:00 | `grep` prints the banner line |

## Gates and hours (13:05 → 11:00)
- **13:45:** `world_spec.sha` pushed (card 02). **14:00 gate:** my DEV files are not ready yet (ASK 2).
- **15:15:** DEV 7 pushed (`P1A-s0007`, `P1B-s0007`, `N-s0007`, `C-s0007`); send Harshavi the sizes.
- **15:30:** twin test green, 11 passed. **16:00:** Harshavi's lags frozen; sweeps run `--mock` until `run_episode` lands.
- **18:00 gate:** responder, scenario JSONs, `build_injection` and `apply_silence` pushed.
- **22:00 gate:** after E2E is green, `python -m eval.precompute` (24 traces). **22:30:** DEV 1–10 sweep and `eval.sensitivity`.
- **23:00 mid-eval.** **00:00–03:00:** DEV-only tuning for τ and `ask_threshold`. Never seeds 1001–1050.
- **03:00:** take Harshavi's handover (bottom of `README.md`). He sleeps 03:00–04:30; you are awake.
- **04:30–06:00: SLEEP (you).** Unload Qwen, push, and send Harshavi a 3-line status first.
- **06:00 freeze:** `python -m eval.sweep --world B --split eval --seeds 1001-1050 | tee results/eval_run.log`; check with card 23; push `results/eval_summary.json`. MISSPEC: write "not run" unless pass 3 exists.
- **06:00–08:30:** card 24; screenshots; backup video of your part. **08:30–10:30:** rehearse ×3, Q&A. **10:45:** final push. **11:00:** hack ends.

## Handoffs with Harshavi
| When | You give | His check |
|---|---|---|
| 13:20 | `test_twin_prefix.py` and sha line | pytest red, as planned; `sha256sum -c` |
| 15:15 | DEV 7 command and sizes, `mock_minutes.json` | `python -m engine.run --seed 7 --split dev` |
| 18:00 | `generator/responder.py` `reply(episode_id, question_id, asked_at_s, error=None)` | `from generator.responder import reply` |
| 18:55 | `build_injection`, `apply_silence` | `/api/inject` stub |
| 22:00 | 24 traces in `data/episodes/` | open one with Wi-Fi off |

## Open questions (⚠️ ASK Harshavi). Default applies if no answer.
1. §8.1's sample id `ev-P1A-000123` has the role letter. Twin ids must match. **Default:** ids from seed, channel, minute, source only; test skips `episode_id`.
2. The 14:00 gate needs Pass 1 DEV files. My realistic time is 15:15. **Default:** §15a at 14:00 if you need it.
3. Team entry lists only the 35B for me. **Default:** if no 9B file, run every card on the 35B.
4. Sensitivity, τ and `ask_threshold` tuning need `run_episode(..., overrides: dict | None = None)`. **Default:** `--mock` until it lands.
5. Scenario trace names: `<ep>__lam<λ>__<scenario>.json` (suffix proposed; plain names are decided). **Default:** that.
6. Hypothesis I has no definition in §9. **Default:** shallow flood below the responder threshold, 3 minutes (card 19).
7. Rumour check: "pairwise ≥ 0.8" cannot hold for varied wording. **Default:** each phrasing ≥ 0.8 to phrasing 0, one cluster (card 17).
8. `eval_summary.json` shape feeds `/api/results`. **Default:** card 23's shape.
9. Pass 2 is tight. **Default:** keep responder, rumour, G3 outage, calls, S; move traffic, hospital and cut-out to pass 3 if 18:00 is at risk. Decide by 17:00.

## Mid-eval (2 lines)
1. **Show:** the twin test going red to green, then the DEV 10-seed table labelled "DEV, 10 seeds" under the SYNTHETIC banner.
2. **Say:** "The world is synthetic and the marshal is our simulated responder with a sealed 10–25% error; the forecaster never reads my generator, and grep proves it."
