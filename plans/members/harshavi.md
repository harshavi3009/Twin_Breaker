# Harshavi's Build Plan — Twin-Breaker  (Pod B, with Aditya)
**You own:** `engine/` (incl. `config/`, `fixtures/`), `server/`, `web/`, `requirements.txt`, `.gitignore`, `README.md`, `docs/twin-breaker/screens/`, and new files `tests/test_engine_*.py` (see ⚠️ below)   **Your AI:** Claude Code   **Your machine:** Windows · i5 · RTX 3050 4 GB (no model runs in the demo path; the GPU is not needed)

**Your one job in one sentence:** Build the engine (ingest, belief, decide) and the one-page server and web view, so Twin P1 plays live with an ASK that splits the twins, the grey naive line sits beside it, and both red-team attacks are visibly held.

**Who depends on you, and when:**
- **Aditya:** `engine/types.py` and `ingest.py` (`parse_line`) by 14:00 for his schema checks. `engine/config/*.json` frozen 13:45. `engine/run.py` batch function by 16:30 so his `eval/sweep.py` can run the DEV table at 16:00 onward (⚠️ see Contracts §9).
- **Rishi and the team:** the 14:00 go/no-go, the 18:00 integration gate, and the 23:00 mid-eval slice (you are the demo laptop).

**You depend on:**
- **Aditya:** DEV streams `data/streams/P1A-s0007.jsonl` and `data/streams/P1B-s0007.jsonl` by 14:00 (Pass 1, rain/drain/citizen only). Full passive streams plus twin pairs by 18:00. Responder `generator/responder.py` `reply()` by 18:00. Scenario JSON `scenarios/*.json` by 18:00. Pre-rendered traces `data/episodes/` by 22:00. DEV 1–10 table by 22:30.
- **Until then, use the mocks:** your hand-written stream `engine/fixtures/seed7_mock.jsonl` (replaces his streams) and `server/responder_mock.py` (replaces his responder). Print `MOCK` on every mock call. Remove both before the 22:00 E2E gate.

---

## Setup (Windows PowerShell; run one line at a time)

### 🔀 Git workflow: the `Twin_Breaker` repo (overrides every other git note in the plans)
- **Repo:** https://github.com/harshavi3009/Twin_Breaker. **You own it.** The repo root IS the project: `engine/`, `server/`, `web/`, `generator/` and the rest sit directly in it. There is no `twin-breaker/` sub-folder. Plans live in `plans/` inside the repo.
- **Your working folder:** `C:\dev\Twin_Breaker`, outside OneDrive. Every command runs from there.
- **Branches:** you work on `harshavi` and Aditya on `aditya`. **Nobody commits to `main`**, except the one bootstrap push in Step 1.
- **Pull requests (PRs):** each branch has one open PR into `main`. Every `git push` updates it automatically.
- **Merging:** you merge PRs in the browser at each gate (14:00, 16:00, 18:00, 22:00, 06:00, 10:45), and also whenever Aditya says "card NN pushed" and you need his code.
- **Every `git pull` in this plan** means `git pull --no-edit origin main`: bring the latest merged `main` into your branch.

**How to open a PR (once per branch, again after each merge):**
1. After `git push`, open https://github.com/harshavi3009/Twin_Breaker. A yellow bar says "**harshavi had recent pushes**". Click **Compare & pull request**.
2. Check **base: `main`** ← **compare: `harshavi`**, give it a short title, and click **Create pull request**.

**How to merge a PR (yours or Aditya's):**
1. Open the **Pull requests** tab and open the PR.
2. Click **Merge pull request**, then **Confirm merge**. Keep the default "Create a merge commit", not squash.
3. **Do NOT click "Delete branch"**, because you both keep using your branches.
4. Then, on your laptop, run `git pull --no-edit origin main` to get the merged code into your branch.
5. A merged PR is closed, so the next `git push` needs a new PR (steps 1–2 above).

**One-time, only if the commands fail:**

```powershell
git --version
```
What this does: prints Git's version. If you see "not recognized", install Git for Windows from git-scm.com (accept defaults), then close and reopen PowerShell.

```powershell
git config --global user.name "Harshavi"
git config --global user.email "<the email on your GitHub account>"
```
What this does: stores your name and email on the commits you make. Run once per laptop.

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
What this does: lets PowerShell run the activation script for the virtual environment (step 3). It affects only your user account. If asked, type `Y`. Run once per laptop.

**Step 1. Get the latest code (repo root).**

```powershell
mkdir C:\dev -Force
cd C:\dev
git clone https://github.com/harshavi3009/Twin_Breaker.git
cd Twin_Breaker
```
- `mkdir` makes `C:\dev` (outside OneDrive). `git clone` downloads the repo into `C:\dev\Twin_Breaker`. It's empty right now, so a warning "You appear to have cloned an empty repository" is normal.
- **Now copy in the handoff files:** put everything from the `Twin_Breaker-handoff` folder you were sent (`plans\`, `CREDITS.md`, `README.md`) into `C:\dev\Twin_Breaker`.

**Step 1b. Bootstrap `main` (the ONLY direct push to `main`, done once by you).**
```powershell
git add plans CREDITS.md README.md
git commit -m "Bootstrap: plans and credits"
git push -u origin main
git config pull.rebase false
git config push.autoSetupRemote true
git switch -c harshavi
```
- The first three lines create `main` on GitHub with the plans in it. Aditya can only start once this is done, so **tell him "main is up"**.
- The two `git config` lines make `git pull` merge (no confusing rebase questions) and let a plain `git push` set up your branch the first time.
- `git switch -c harshavi` creates your own branch and moves you onto it. Everything you commit from now on goes there.
- **Add Aditya:** on GitHub, open **Settings → Collaborators → Add people**, then enter his GitHub username. He must accept the email invite.

**Every later session starts with:**
```powershell
cd C:\dev\Twin_Breaker
git switch harshavi
git status
git pull --no-edit origin main
```
- `git status` lists files you changed but did not commit. If it lists files you don't recognise, **stop and ask Rishi**. Do not delete anything.
- `git pull --no-edit origin main` brings the latest merged work (including Aditya's merged cards) into your branch.

**Step 2. Check Python.**

```powershell
py -0
```
What this does: lists installed Python versions. You need 3.10 or newer, 3.11 preferred. If nothing is listed, install Python 3.11 from python.org and tick "Add python.exe to PATH".

**Step 3. Create and activate the project environment.**

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```
- Line 2 creates `.venv`, a private copy of Python just for this project. It is gitignored.
- Line 3 switches this window to that environment. The prompt starts with `(.venv)`. Every new PowerShell window needs this line again.
- If `py -3.11` fails, use `py -3 -m venv .venv`.
- Note: the main plan writes `.venv\Scripts\activate`, which is the cmd form. In PowerShell use `Activate.ps1`. In Git Bash use `source .venv/Scripts/activate`.

**Step 4. Create the two small files (ask Claude Code, prompt P2 below, or type them by hand).**
Result must be `.gitignore` and `requirements.txt`.

**Step 5. Download the packages while Wi-Fi works (in `C:devTwin_Breaker`, venv active).**

```powershell
pip download -r requirements.txt -d vendor\wheels
```
What this does: saves the package files into `vendor\wheels` so the project installs with no internet later. The folder is gitignored, so nothing gets pushed.

**Step 6. Install, then test the offline install.**

```powershell
pip install -r requirements.txt
pip install --no-index --find-links vendor\wheels -r requirements.txt
```
- Line 1 installs from the internet.
- Line 2 installs only from the saved files. It should print "Requirement already satisfied" lines. This proves the venue Wi-Fi failure case works.

**Step 7. Check the test folder and Chart.js.**

```powershell
python -m pytest -q tests
dir web\vendor
```
- Pytest at 13:35 may say "file or directory not found" (Aditya has not pushed `tests/` yet) or "no tests ran". Both are fine now.
- `dir web\vendor` must list a Chart.js file (MIT licence, vendored, committed). If it is empty, tell Rishi now and download the Chart.js UMD build on Wi-Fi.

**Step 8. Measure one smoke file (after Aditya's smoke seed lands).**

```powershell
Get-ChildItem data\streams -Filter *.jsonl | Select-Object Name, Length
```
What this does: lists each stream file and its size in bytes. The estimate is about 400,000 bytes (0.4 MB) per episode. Write the numbers into `README.md` under a "Setup log" heading, and tell Rishi to copy them into MAIN §11 (that file is locked; do not edit it yourself).

**Step 9. First commit (from the repo root).**

```powershell
cd ..
git status
```
- You are already in `C:\dev\Twin_Breaker` on branch `harshavi`. If you typed `cd ..` above, skip it.
- `git status` shows new files. **Check:** `.venv` and `vendor/wheels` must NOT appear. If either appears, stop and tell Rishi, because `.gitignore` is wrong.
- Optional check: `git check-ignore -v .venv` prints the rule that hides it.

```powershell
git add .gitignore requirements.txt README.md
git commit -m "twin-breaker: setup, gitignore, requirements"
git pull --no-edit origin main
git push
```
What each line does:
- `git add` **stages** the files you name, ready to commit. Never use `git add .`, because it adds everything in the folder.
- `git commit` saves a snapshot with a message, on your laptop only.
- `git pull --no-edit origin main` brings in anyone else's changes first.
- `git push` uploads your commit to **your branch** on GitHub. **First time:** open the PR (see "How to open a PR" at the top of Setup). After that, each push updates the same PR until you merge it.
- If push says "rejected", run `git pull --no-edit origin main` and then `git push` again. **Never** use `--force`.
- A Windows window may pop up asking you to sign in to GitHub. Sign in there.

---

## Timeline (13:05 → 11:00, IST)

Gates are in **bold**. Prompt numbers (P1–P13) are in the Claude Code prompts section. Work from `repo root` unless the row says otherwise.

| Time block | Task | Done when | Push to |
|---|---|---|---|
| **13:05–13:15** | Write the §15a fallback one-pager (the plan said 13:05, so do it first; it is a page, not code). Prompt **P1**. | `README.md` has a "Fallback (§15a)" section with Keep and Drop lists | `README.md` |
| 13:15–13:35 | Setup Steps 1–8 (pull, venv, `requirements.txt` and `.gitignore` via **P2**, wheels, offline install, Chart.js check, smoke size) | `pip install` works offline; `dir web\vendor` lists Chart.js | local only |
| **13:35–13:45** | Config schemas and types. Prompt **P3**. | 4 JSON files in `engine/config/` match §8.5; `engine/types.py` has `Event` | `engine/config`, `engine/types.py` (Step 9 commands) |
| **13:45–14:00** | **Gate sprint.** Prompt **P4**: `ingest.py`, `belief.py` (grey + ours), `decide.py` stub, `run.py`, mock fixture. | `python -m engine.run --seed 7 --split dev` runs, no crash, under 60 s | engine/ |
| **14:00** | **GO/NO-GO.** Gate: ingest → step → stub, prints P(C) ours and grey per minute. **FAIL → §15a.** | Decision made at 14:00 sharp. Message Aditya (and post in the team chat) the result. | — |
| 14:00–14:15 | If PASS: commit and push engine/. If FAIL: switch to §15a (grey + ASK Q1 + pre-rendered traces); tell Aditya (and the team chat) that you are on §15a. | Commit pushed, or §15a note in README | `engine/`, `README.md` |
| 14:15–15:00 | Belief hardening. Prompt **P5**: silence rule, reply update, citizen clusters, reason bits, trust reset. | Silence test passes (step 4 alone, see ⚠️); Jaccard test on 12 phrasings passes | `engine/`, `tests/test_engine_belief.py` |
| **15:00** | **Check on your partner.** Pull; `dir data\streams`; run `python -m engine.run --seed 7 --split dev` on his files. If a file fails your parser, send him the exact error. If he is stuck more than 20 min, split the task with him (you write the fixture, he writes the test). Then start P6 (server + page skeleton). | You know his status in writing (one message) | — |
| 15:00–15:30 | Server and minimal page. Prompt **P6**: `/api/health`, `/api/episodes`, `/api/episodes/{id}`, banner, Chart.js from `web/vendor`. | `http://127.0.0.1:8000/api/health` returns `{"ok":true,...}`; banner visible | `server/`, `web/` |
| 15:30–16:00 | Lags for rain→drain only. Prompt **P7**. | `engine/config/lags.json` committed | `engine/config/` |
| **16:00** | **Lags frozen (rain→drain only; see ⚠️).** Aditya starts the 50-seed DEV table. | `lags.json` pushed by 16:00 | — |
| 16:00–16:30 | `run.py` prints the §8.2 JSON shape per closed minute, and exposes `run_episode` for Aditya. Prompt **P8**. | Two JSON lines per minute (belief and decision) for seed 7 | `engine/` |
| 16:30–17:30 | Decide: costs, ladder, VOI, ASK, hysteresis, corroboration. Prompt **P9**. | `tests/test_engine_ladder.py` green (thresholds 0.067 / 0.325 / 0.433); ASK fires or is logged as "not fired" | `engine/decide.py` |
| **17:00** | **Check on your partner** (during the decide block, 10 min). Ask Aditya for his Pass 2 status and whether `generator/responder.py` exists. | Status written down; his blockers listed | — |
| **17:30** | **Risk point.** If VOI or hysteresis is not green, cut to Q1 only with no dwell change, and tell Aditya. Do not skip the corroboration cap (it is a rule, not a cut). | Decision noted in README | `README.md` |
| **18:00** | **INTEGRATION GATE.** `/api/inject` works (stub is fine), P1 trace returns as JSON, the page plays it, ASK fires on seed 7, both grep checks print nothing (Step below). | Gate check list (below) all ticked | `repo root` |
| 18:00–19:00 | ASK loop. Prompt **P10**: reply event with `received_time_s = asked_at_s + delay_s`; causality and parity tests. | `tests/test_engine_causality.py` green | `server/`, `engine/`, `tests/test_engine_causality.py` |
| **19:00** | **Check on your partner.** Pull; run his Pass 2 test (`pytest -q tests/test_twin_prefix.py`, Aditya's file); check his scenario JSON validates. | His test status known; scenario JSON loads in `/api/inject` | — |
| 19:15–20:15 | Full page. Prompt **P11**: banner, belief bars, grey line, ASK card, reason log, foresight (top-1, labelled "lag-table based"), λ selector. | P1 plays in the browser with reason log and ASK card | `web/` |
| 20:15–21:15 | Red-team buttons. Prompt **P12**: rumour, outage, cut-out. | Each button shows its §4 text and passes its pass check (see table in red-team section) | `web/`, `server/` |
| **21:00** | **Check on your partner** (inside the red-team block). Ask Aditya whether his responder replaces the mock. | Responder status known | — |
| 21:15–22:00 | Remove the mocks once his files work. Dry run with Wi-Fi off. | `server/responder_mock.py` deleted or unused; `engine/fixtures/` only used by tests | `server/`, `engine/` |
| **22:00** | **E2E + red team gate.** 3 buttons live, pre-rendered fallback present. Aditya starts `eval/precompute.py` (~32 traces). | Gate list below | — |
| 22:00–22:30 | Open one precomputed trace in the page with Wi-Fi off. | P1 plays from `data/episodes/` | — |
| **22:30** | 60-second backup screen capture of P1 (you own the demo laptop). Aditya's DEV 1–10 sweep runs in parallel. | `docs/twin-breaker/screens/` has the capture | `docs/twin-breaker/screens/` |
| 22:30–23:00 | Charge the laptop. Print the architecture diagram (MAIN §5). Run the demo once with Wi-Fi off. | Laptop above 80 percent; printout in hand | — |
| **23:00** | **MID-EVAL.** Show P1 live, labelled "DEV, 10 seeds" with the SYNTHETIC banner. Explain belief, ESS, hysteresis, VOI, corroboration. | Mentor feedback written down | — |
| 23:15–00:00 | Append mentor feedback to `outputs/03-mid-eval-feedback.md` (append only). `/replan twin-breaker` if mentor feedback needs it. | Feedback file appended and pushed | `outputs/03-mid-eval-feedback.md` |
| **00:00–00:15** | **Side Quest decision** (team call, 15 min). | Decision logged | — |
| 00:15–01:00 | Tune τ on DEV only (3 pairs × 50 DEV seeds). Prompt **P13**. | `results/dev/` saved; τ values written in README tuning log | `engine/config/belief_spec.json`, `README.md` |
| **01:00** | **Check on your partner.** Pull; check the DEV table file exists. | Results visible | — |
| 01:00–03:00 | Finish tuning. Lock τ (and the ASK threshold only if it is in a config file; see ⚠️). Prior-shift check (α = 0.3) on DEV episodes 11 to 15 if time allows (it is cut-first). | Values locked by 03:00 | `engine/config/`, `README.md` |
| **03:00** | **Handover to Aditya.** Pull, push your last change, and write a handover note at the bottom of `README.md`: last commit, what Aditya may run, and "no edits to `engine/` from now until 06:00 unless you OK it". | Handover note pushed | `README.md` |
| 03:00–04:30 | **SLEEP** (proposed in ⚠️; Aditya is awake). | — | — |
| 04:30–05:00 | Wake. `git pull --no-edit origin main`. Run both grep checks (Step below). | Checks print nothing | — |
| **05:00** | **Check on your partner.** Aditya is awake, so ask him what he ran and what it produced. | Notes written | — |
| 05:00–06:00 | Freeze prep: list every file you changed since 18:00 (`git log --oneline --since=18:00`). No new code. Confirm the EVAL command with Aditya. | List written in README | — |
| **06:00** | **FEATURE FREEZE.** No changes to `engine/`, `server/`, `web/` after this line. Bugs only, and each fix is announced to Aditya. Aditya runs EVAL + MISSPEC once. | Freeze noted in README | — |
| 06:00–07:00 | Polish: labels, banner text, page copy. Check every number on screen says DEV or EVAL. | Screen check list ticked | `web/` |
| **07:00** | **Check on your partner.** Pull; confirm `eval_summary.json` exists (his output). | File seen | — |
| 07:00–08:30 | Backup video of the full demo (under 3 min) and screenshots. | Videos in `docs/twin-breaker/` and on 2 laptops | `docs/twin-breaker/`, `docs/twin-breaker/screens/` |
| 08:30–10:30 | Rehearse the demo three times. Q&A drill on your five questions (see "How I know I'm done"). | Five answers spoken aloud | — |
| **09:00** | **Check on your partner** (during rehearsal). | Notes written | — |
| 10:30–10:45 | Laptop charged. `git status` clean. | Clean status | — |
| **10:45** | **Final push.** `git pull --no-edit origin main`, then `git push` from the repo root. Nothing after 10:45. | `git status` says clean after push | repo root |
| **11:00** | **Hack ends.** | — | — |

---

## Claude Code prompts (paste one per block)

Open Claude Code in `Twin_Breaker`. For P4, P5, P9 and P10, press Shift+Tab to enter Plan mode first, so Claude shows you the plan before it writes files. Always end a prompt with "Show me the output of the command, then stop."

**P1 (13:05, fallback page).**
```
Read plans/twin-breaker/MAIN_BUILD_PLAN.md section 15a and plans/members/harshavi.md section "Timeline". Create README.md if it does not exist. Add a section "## Fallback (section 15a)" with two lists copied exactly from section 15a: "Keep" and "Drop". Add one line: "Switch trigger: the 14:00 go/no-go fails." Do not create or edit any other file. Do not touch generator/, scenarios/, tests/, eval/ or data/. Keep the section under 30 lines.
```

**P2 (13:15, ignore and requirements).**
```
In repo root create exactly two files. (1) requirements.txt with these five lines and no version numbers: numpy, fastapi, uvicorn, pytest, httpx. (2) .gitignore with these six lines: .venv/ __pycache__/ vendor/wheels/ data/streams/ generator/sealed/ results/dev/ (one per line, no spaces, no other entries). Do not create any other file. Do not add web/vendor to .gitignore, because Chart.js must be committed.
```

**P3 (13:35, config schemas and types).**
```
Read plans/twin-breaker/MAIN_BUILD_PLAN.md sections 8.3 and 8.5. Use the exact numbers. Create these files, and nothing else:
1. engine/config/belief_spec.json with:
{"tau":0.7,"rho":0.6,"eps":0.02,"alpha_prior":0.3,"trust_prior":[2,1],"crowd_r":0.6,
 "bins":{"rain":[5,25],"drain":[0.5,0.85],"traffic":[0.4,0.7],"calls":[3,8],"hospital":[4,9]},
 "tables":{
  "rain":{"N":[0.70,0.25,0.05],"S":[0.34,0.33,0.33],"I":[0.55,0.35,0.10],"C":[0.30,0.40,0.30]},
  "drain":{"N":[0.75,0.20,0.05],"S":[0.34,0.33,0.33],"I":[0.60,0.30,0.10],"C":[0.10,0.30,0.60]},
  "traffic":{"N":[0.80,0.15,0.05],"S":[0.80,0.15,0.05],"I":[0.45,0.40,0.15],"C":[0.10,0.35,0.55]},
  "calls":{"N":[0.75,0.20,0.05],"S":[0.75,0.20,0.05],"I":[0.50,0.35,0.15],"C":[0.10,0.35,0.55]},
  "hospital":{"N":[0.75,0.18,0.07],"S":[0.75,0.18,0.07],"I":[0.60,0.30,0.10],"C":[0.15,0.35,0.50]},
  "citizen":{"N":[0.85,0.12,0.03],"S":[0.85,0.12,0.03],"I":[0.60,0.30,0.10],"C":[0.25,0.35,0.40]}}}
2. engine/config/cost.json: {"c":{"WATCH":0,"PREPARE":2,"ALERT":5,"ESCALATE":8},"m":{"WATCH":0,"PREPARE":0.3,"ALERT":0.6,"ESCALATE":0.8},"d":{"N":0,"S":0,"I":15,"C":100},"f":{"ALERT":10,"ESCALATE":20},"lam_default":1.0}
3. engine/config/hyst.json: {"h_up":1.0,"h_down":2.0,"dwell_min":3}
4. engine/config/questions.json: a list with Q1, Q2, Q3 exactly as section 8.5 (qid, text, p_yes with keys N,S,I,C). Q1 p_yes = {"N":0.10,"S":0.05,"I":0.55,"C":0.90}.
5. engine/types.py: the Event dataclass from section 8.3, exactly, with frozen=True.
Rules: numpy only. Do not import anything from generator/ or sealed/. Run: python -c "import json,glob; [json.load(open(f)) for f in glob.glob('engine/config/*.json')]; print('ok')". Show me the output, then stop.
```

**P4 (13:45, gate sprint: ingest, belief, stub, run).**
```
Read plans/twin-breaker/MAIN_BUILD_PLAN.md sections 8.1, 8.2, 8.3, 8.5 and the files in engine/config/. Write only these files: engine/ingest.py, engine/belief.py, engine/decide.py (stub only), engine/run.py, engine/fixtures/seed7_mock.jsonl.
- ingest.py: parse_line(line: str) -> Event. Raise ValueError on bad JSON or a missing required field for its kind (section 8.1 table). class Ingestor with __init__(registered_responders: set[str]), push(ev) -> bool (False for duplicate event_id, unregistered reply source, retracted event, or late beyond closed_upto grace), buckets() -> dict[int, list[Event]] keyed by event_time_s, closed_upto(now_s) = last m with now_s >= (m+1)*60 + 90, and attribute dropped_late (int).
- belief.py: HYPS, Belief, Trust (reset, mean = a/(a+b), end_episode), step(prev, minute_events, spec, trust, prior) per section 8.5 steps 1 to 6, and a grey flag for the naive baseline (section 8.5 "Grey baseline").
- decide.py: stub only: ACTIONS and a function that returns "WATCH" every minute.
- run.py: CLI "python -m engine.run --seed 7 --split dev". For pair P1, read data/streams/P1A-s0007.jsonl and data/streams/P1B-s0007.jsonl. If a file is missing, read engine/fixtures/seed7_mock.jsonl and print "MOCK INPUT". For each closed minute print: role, minute, P(C) ours, P(C) grey. Must finish in under 60 seconds.
- seed7_mock.jsonl: 12 lines in the section 8.1 format for P1A-s0007: drain observations from gateway G2 rising from 0.2 to 0.9, one citizen line, one reply line, one retraction line.
No network. No generator/ imports, and do not write the words "generator" or "sealed" anywhere in engine/ (not even in comments). Show me the output of: python -m engine.run --seed 7 --split dev. Then stop.
```

**P5 (14:15, belief hardening).**
```
Read plans/twin-breaker/MAIN_BUILD_PLAN.md section 8.5 (steps 1 to 6, Silent gateway, Citizen clusters, Reason log) and plans/twin-breaker/PLAN_REVIEW.md items 5 and 23. Edit only engine/belief.py and engine/ingest.py.
1. Silent gateway (step 4 only): a gateway with no events and no heartbeat for 60 s adds factor 1 on all H. Move delta = min(0.10, 0.5*P(N)) from N to S per silent minute. C and I are untouched.
2. Reply (step 5): P(yes|H) = r*p_yes(H) + (1-r)*0.5, with tau applied as for sensors. Accept replies only from registered responders.
3. Citizen clusters: Jaccard >= 0.8 on 3-word shingles of normalised text, within 120 s. Citizen bin = min(2, number of NEW clusters this minute).
4. Reason log: bits = tau*w*log2(P_mix(b|top)/P_mix(b|second)); return the top 3 per minute by absolute bits.
Write tests/test_engine_belief.py (new file only):
(a) Silence hand-check: prior N .35, S .15, I .10, C .40, one silent minute, with the forget step OFF. Expect N .25, S .25, I .10, C .40 and |dP(C)| <= 0.001.
(b) Twelve phrasings of one rumour have pairwise Jaccard >= 0.8 on 3-word shingles and form exactly one cluster.
Run: python -m pytest -q tests/test_engine_belief.py. Show me the output, then stop.
```

**P6 (15:00 block, server and page skeleton).**
```
Read plans/twin-breaker/MAIN_BUILD_PLAN.md sections 2 (banner), 6, 7 and 8.4. Create server/app.py (FastAPI) and web/index.html (one page, vanilla JS, Chart.js loaded only from web/vendor/, no CDN, no network calls). Routes exactly as section 8.4:
- GET /api/health returns {"ok":true,"mode":"live","synthetic":true}.
- GET /api/episodes returns [{"episode_id":"P1A-s0007","pair":"P1","role":"A"},{"episode_id":"P1B-s0007","pair":"P1","role":"B"}].
- GET /api/episodes/{id}?lam=1.0 returns the section 8.4 shape. For now, return {"episode_id","lam","minutes":[],"synthetic":true} with a note "STUB".
- GET / serves web/index.html.
- POST /api/inject returns {"ok":true,"injected":0,"trace":{}} as a stub.
The page shows this banner at the top, exactly: SYNTHETIC. Scale inspired by a published 2005 Mumbai rainfall figure (NIDM). Not real telemetry. Fictional event at a real location.
Do not import from generator/. Do not read generator/sealed/. Run: python -m uvicorn server.app:app --port 8000, then open http://127.0.0.1:8000/api/health. Show me the output, then stop.
```

**P7 (15:30, lags, rain to drain only).**
```
Read plans/twin-breaker/MAIN_BUILD_PLAN.md section 8.5 ("Foresight lags") and plans/twin-breaker/PLAN_REVIEW.md item 4. Create engine/estimate_lags.py. It reads only data/streams/*.jsonl for DEV seeds 1 to 10 (file names P1A-s00NN.jsonl and similar). It must never read generator/ or sealed/.
Algorithm, in order:
1. For each file, bucket observation events of channel "rain" and channel "drain" by event_time_s // 60 (minute). Per minute use the mean value. Use no truth data.
2. For lag L from 0 to 15 minutes, compute the Pearson correlation between rain[t] and drain[t+L], pooled over all files.
3. Lag = argmax of correlation. Window = [lag-2, lag+2] with the low end clipped to 1. (This window rule is a proposal; see ⚠️.)
4. Write engine/config/lags.json as {"rain>drain":{"lag_min":L,"window_min":[lo,hi],"method":"lagged_corr_DEV_1_10"}}.
Pure numpy. Print the table of correlations for the best lag. Show me the output, then stop.
```

**P8 (16:00, run.py output shape).**
```
Edit engine/run.py only. Read plans/twin-breaker/MAIN_BUILD_PLAN.md section 8.2. Print one JSON line per closed minute with the belief shape, then one JSON line with the decision shape (for now action WATCH is fine). Keep the command python -m engine.run --seed 7 --split dev. Also expose a function run_episode(jsonl_path: str, lam: float = 1.0, ask_enabled: bool = True, grey: bool = False) -> list[dict] that returns the same dicts. Aditya's sweep will call run_episode. Do not change any other file. Show me the first 3 lines of output, then stop.
```

**P9 (16:30, decide).**
```
Read plans/twin-breaker/MAIN_BUILD_PLAN.md section 8.3 (decide signatures) and section 8.5 (Cost, Ladder, ASK/VOI, Hysteresis, Corroboration). Edit engine/decide.py only, and create tests/test_engine_ladder.py (new file).
- expected_costs(p, lam, cost): L[a,H] = c_a + d_H*(1-m_a) + lam*f_a*1[H in {N,S}] using engine/config/cost.json. Return {action: sum over H of p[H]*L[a,H]}. Check: at lam=1, L matches the 4x4 table in section 8.5.
- Ladder test: with I=0 and lam=1, the thresholds on P(C) are 0.067 (PREPARE), 0.325 (ALERT), 0.433 (ESCALATE). Test points on both sides of each.
- voi(p, q, lam, cost, trust_resp): VOI = min_a E[L] - (0.5 + 0.2*1.0 + sum over r of P(r)*min_a E[L|r]). P(yes|H) = trust_resp*p_yes(H) + (1-trust_resp)*0.5. Implement the constant 0.5 + 0.2*1.0 exactly as written and add a comment that it is unexplained (see ⚠️).
- decide(...): candidate = argmin E[L]. Corroboration cap: ALERT or ESCALATE only if the corroborated flag is True, else cap at PREPARE. Hysteresis: move from prev_action to candidate only if E[L(prev)] - E[L(candidate)] > h, with h = 1.0 moving up and 2.0 moving down. Minimum dwell 3 minutes. ASK fires if max VOI > 0.3, asks_so_far < 3 and minute - last_ask_min >= 3. ASK never changes the action by itself.
- Return the Decision dataclass from section 8.3 with expected_cost for all four actions.
No generator/ or sealed/ imports. Run: python -m pytest -q tests/test_engine_ladder.py. Show me the output, then stop.
```

**P10 (18:00, ASK loop and causality test).**
```
Read plans/twin-breaker/MAIN_BUILD_PLAN.md sections 5, 8.1 (reply event), 8.4 (responder function) and 8.5 (causality). Edit server/ only, and create tests/test_engine_causality.py (new file).
1. Create server/responder_mock.py with reply(episode_id: str, question_id: str, asked_at_s: int) -> dict returning {"answer": "yes" if "P1A" in episode_id else "no", "responder_id": "marshal-W9-01", "delay_s": 55}. Print "MOCK RESPONDER" on every call. It is replaced later by generator/responder.py from Aditya.
2. When the engine decides to ASK, call reply(), build a reply Event with received_time_s = asked_at_s + delay_s, and push it into the Ingestor. The engine consumes it only once closed_upto allows.
3. tests/test_engine_causality.py: (a) a reply received at time t cannot change any minute closed before t; (b) parity: live ingestion and batch replay give identical beliefs.
Run: python -m pytest -q tests/test_engine_causality.py. Show me the output, then stop.
```

**P11 (19:15, full page).**
```
Edit web/index.html only. Read plans/twin-breaker/MAIN_BUILD_PLAN.md sections 2 (demo flow steps 1 to 4, and 8) and 8.2. Build:
(a) The banner from P6, at the top, unchanged.
(b) Two panels, Twin A and Twin B, playing from /api/episodes/{id}?lam=1.0 at 4 wall-seconds per sim-minute.
(c) Belief bars for N, S, I, C, and a grey line beside them (naive ALERT when P(C) >= 0.7), with a flip counter.
(d) ASK card: the question text, expected gain, and the reply when it arrives.
(e) Reason log: clicking a minute shows its reason list.
(f) Foresight line: top-1 only, labelled "lag-table based".
(g) Selector for lam: 0.5, 1, 2, 4.
Vanilla JS, no external URLs. Label any mock data "MOCK". Show me a screenshot description of what renders, then stop.
```

**P12 (20:15, red-team buttons).**
```
Edit web/index.html and server/app.py only. Read section 4 of plans/twin-breaker/MAIN_BUILD_PLAN.md and any scenarios/*.json from Aditya. Add three buttons that call POST /api/inject with {"episode_id":"P1A-s0007","scenario":"rumour_wave"|"gateway_outage"|"camera_cutout","at_s":300}. Show these texts exactly:
- rumour: "400 reports · 1 cluster · eff. n ≈ 1", max action PREPARE, no ALERT.
- outage: "1 gateway outage · drain sensors UNKNOWN (not all-clear)".
- cut-out: "traffic UNKNOWN · coverage 5/6".
Check each against its pass check in section 4 and print the measured numbers. Do not change engine thresholds to make a check pass. If a check fails, report it. Show me the output, then stop.
```

**P13 (00:15, tuning log, no code changes).**
```
Do not change any code. Only change the value tau in engine/config/belief_spec.json. Run: python -m eval.sweep --split dev --seeds 1-50 (Aditya's script; if it is missing, tell me). Try tau in {0.5, 0.7, 1.0} only. Record each run in README.md under "Tuning log": tau, Brier(P(C)) on DEV, ECE, and the lead time. Pick the best on DEV only. Never open generator/sealed/ and never use EVAL seeds (1001 to 1050). Show me the table, then stop.
```

---

## Contracts you must follow (copied from MAIN §8)

### 1. Event line (§8.1). Aditya's files, read by `ingest.py`
Shared fields: `event_id`, `episode_id`, `kind`, `source_id`, `event_time_s` (int sim-seconds), `received_time_s` (≥ `event_time_s`), `value`.
```json
{"event_id":"ev-P1A-000123","episode_id":"P1A-s0007","kind":"observation","channel":"drain","source_id":"drain-G2-031","gateway_id":"G2","event_time_s":200,"received_time_s":231,"value":0.91}
{"event_id":"ev-P1A-000181","episode_id":"P1A-s0007","kind":"reply","channel":"reply","source_id":"marshal-W9-01","question_id":"Q1","answer":"yes","event_time_s":365,"received_time_s":365,"value":null}
```

| kind | channel / value | Extra required |
|---|---|---|
| observation | `rain` mm/h · `drain` fill 0–1 · `traffic` speed ratio | `gateway_id` |
| dispatch | `calls` per ward-minute (count) | `source_id` `dispatch-W9` |
| hospital | `hospital` arrivals per minute (count) | `source_id` `hosp-H1` |
| citizen | `citizen`, value null | `text`, `text_hash` (sha1 of normalised text) |
| reply | `reply`, value null | `question_id`, `answer` yes/no |
| heartbeat | — | `gateway_id` (every 60 s) |
| retraction | — | `retracts` |

Bad schema → `ValueError`. Duplicates and retractions are idempotent.

### 2. Python signatures (§8.3). Exact
```python
# engine/types.py
@dataclass(frozen=True)
class Event:
    event_id: str; episode_id: str; kind: str; source_id: str
    event_time_s: int; received_time_s: int; value: float | None
    channel: str | None = None; gateway_id: str | None = None
    text_hash: str | None = None; text: str | None = None
    question_id: str | None = None; answer: str | None = None; retracts: str | None = None
# engine/ingest.py
def parse_line(line: str) -> Event                                  # ValueError on bad schema
class Ingestor:
    dropped_late: int                                               # late beyond grace, reported
    def __init__(self, registered_responders: set[str]) -> None: ...
    def push(self, ev: Event) -> bool                               # False: duplicate/unregistered/retracted/late
    def buckets(self) -> dict[int, list[Event]]                     # keyed by event_time_s
    def closed_upto(self, now_s: int) -> int                        # last m with now_s >= (m+1)*60 + 90
# engine/belief.py
HYPS = ("N", "S", "I", "C")
@dataclass
class Belief:
    minute: int; p: dict[str, float]; eff_n: dict[str, float]; coverage: dict[str, str]
class Trust:
    def reset(self) -> None: ...                                    # called per seed
    def mean(self, source_id: str) -> float: ...                    # a/(a+b)
    def end_episode(self, final_label: str, readings: list[Event], decay: float = 0.9) -> None: ...
def step(prev: Belief, minute_events: list[Event], spec: dict, trust: Trust, prior: dict[str, float]) -> Belief
def replay(buckets: dict[int, list[Event]], spec: dict, trust: Trust, prior: dict[str, float], upto_min: int) -> list[Belief]
# engine/decide.py
ACTIONS = ("WATCH", "PREPARE", "ALERT", "ESCALATE")
@dataclass
class Question:
    qid: str; text: str; p_yes: dict[str, float]                   # ASSUMED response model
@dataclass
class Decision:
    minute: int; action: str; candidate: str; changed: bool; ask: dict | None; expected_cost: dict[str, float]
def expected_costs(p: dict[str, float], lam: float, cost: dict) -> dict[str, float]
def voi(p: dict[str, float], q: Question, lam: float, cost: dict, trust_resp: float) -> float
def decide(p, prev_action: str, minutes_in_action: int, minute: int, lam: float, cost: dict, hyst: dict,
           questions: list[Question], asks_so_far: int, last_ask_min: int | None, trust_resp: float,
           corroborated: bool) -> Decision
# eval/metrics.py (Aditya; pure functions, hand-computed tests)
def brier_binary(p: list[float], y: list[int]) -> float
def brier_multi(P: list[list[float]], labels: list[str]) -> float
def ece(p: list[float], y: list[int], bins: int = 10) -> tuple[float, list[dict]]
def lead_time_min(actions: list[str], onset_min: int) -> int | None  # onset − first ALERT/ESCALATE minute
def flip_count(actions: list[str], window_min: int = 3) -> int
```

### 3. Per-minute outputs (§8.2)
Belief line (one per closed minute):
```json
{"episode_id":"P1A-s0007","minute":5,"p":{"N":0.50,"S":0.15,"I":0.02,"C":0.33},"eff_n":{"gw-G2":1.66,"citizen":1.0},
 "coverage":{"rain":"ok","drain":"ok","traffic":"ok","calls":"ok","hospital":"ok","citizen":"ok"},"trust":{"marshal-W9-01":0.80}}
```
Decision line:
```json
{"episode_id":"P1A-s0007","minute":5,"action":"PREPARE","candidate":"ALERT","changed":false,"minutes_in_action":3,
 "expected_cost":{"WATCH":33.3,"PREPARE":25.3,"ALERT":24.8,"ESCALATE":27.7},
 "ask":{"question_id":"Q1","text":"Water above ankle at Ambazari underpass? 1=yes 2=no","voi_net":0.41},
 "reason":[{"event_id":"ev-P1A-000123","bits":2.1,"text":"3 hospitals reporting"}],
 "foresight":[{"event":"drain>=0.85 (G2)","window_min":[3,8],"p":0.55}],"synthetic":true}
```
Coverage counts the six channel groups with ≥ 1 event in the last 2 minutes (`reply` is not counted).

### 4. HTTP routes (§8.4, port 8000, `/` serves `web/index.html`)
| Method | Route | Response |
|---|---|---|
| GET | `/api/health` | `{"ok":true,"mode":"live"\|"precomputed","synthetic":true}` |
| GET | `/api/episodes` | `[{"episode_id":"P1A-s0007","pair":"P1","role":"A"}, ...]` |
| GET | `/api/episodes/{id}?lam=1.0` | `{"episode_id","lam","minutes":[{"belief":{...},"decision":{...}}],"synthetic":true}` |
| POST | `/api/inject` `{"episode_id","scenario":"rumour_wave"\|"gateway_outage"\|"camera_cutout","at_s":300}` | `{"ok":true,"injected":400,"trace":{...}}` |
| GET | `/api/results` | `results/eval_summary.json` |

Responder (server calls generator, function call): `reply(episode_id: str, question_id: str, asked_at_s: int) -> {"answer":"yes"|"no","responder_id":"marshal-W9-01","delay_s":55}`.

### 5. Engine model (§8.5, copied in order)
- **Clock:** sim time drives everything. Playback is 4 wall-seconds per sim-minute. A reply has `received_time_s = asked_at_s + delay_s`. The engine consumes an event only after `closed_upto` allows it. Buckets use `event_time_s`; closure uses `received_time_s` with a 90 s grace.
- **Resets:** `Trust` and π reset at the start of every seed. `eval/sweep.py` passes only the final label into `end_episode`. The engine never opens `generator/sealed/`.
- **Per closed minute m:**
  1. Forget: `p ← 0.98·p + 0.02·π`.
  2. Each reading: `P_mix(b|H) = r·P(b|H,ch) + (1−r)/3`, r = Beta mean of its source. Add `τ·w·log P_mix`, τ = 0.7 (DEV-tuned).
  3. Gateway ESS: `w = 1/(1+(k−1)·ρ)`, ρ = 0.6. k readings give `n_eff = k/(1+(k−1)ρ)`.
  4. **Silent gateway** (no events and no heartbeat for 60 s): its channels add **no likelihood** (factor 1 on all H). Its share of N moves to S: `δ = min(0.10, 0.5·P(N))` per silent minute. C and I are untouched.
  5. Reply: `P(yes|H) = r·p_yes(H) + (1−r)·0.5`, with τ applied as for sensors.
  6. Normalise. Citizen bin = min(2, **new** clusters this minute). Cluster = Jaccard ≥ 0.8 on 3-word shingles within 120 s. Crowd r = 0.6.
- **Corroboration rule (decide):** the candidate may be ALERT or ESCALATE only if a passive channel (rain, drain, traffic, calls, hospital) has bin ≥ elevated in the last 3 minutes. Otherwise cap the candidate at PREPARE.
- **Bins** (0 calm · 1 elevated · 2 high): rain <5 / 5–25 / ≥25 mm/h · drain <0.5 / 0.5–0.85 / ≥0.85 · traffic ≥0.7 / 0.4–0.7 / <0.4 · calls <3 / 3–8 / >8 · hospital <4 / 4–9 / ≥10.
- **Trust:** Beta(2,1) per source. `end_episode`: decay counts by 0.9. A reading is consistent if its bin is the modal bin under `final_label`. Add (consistent, inconsistent) counts.
- **Prior π:** uniform at start; after each episode `π ← 0.7·π + 0.3·final posterior`.
- **Cost:** `L[a,H] = c_a + d_H·(1−m_a) + λ·f_a·1[H∈{N,S}]`; c = {W 0, P 2, A 5, E 8}; m = {0, .3, .6, .8}; d = {N 0, S 0, I 15, C 100}; f = {A 10, E 20}; λ default 1.0 (slider 0.5/1/2/4).

| action \ H | N | S | I | C |
|---|---|---|---|---|
| WATCH | 0 | 0 | 15 | 100 |
| PREPARE | 2 | 2 | 12.5 | 72 |
| ALERT | 15 | 15 | 11 | 45 |
| ESCALATE | 28 | 28 | 11 | 28 |

At λ = 1 and I ≈ 0, ladder thresholds on P(C) are **≈0.067 (PREPARE), ≈0.325 (ALERT), ≈0.433 (ESCALATE)** (the review confirmed these; the plan's rounded 0.07, 0.33, 0.43 are fine for the slide).

- **ASK / VOI:** `VOI(q) = min_a E[L] − (0.5 + 0.2·1.0 + Σ_r P(r)·min_a E[L|r])`. Fire if max VOI > 0.3, asks < 3 per episode, ≥ 3 min since last ask. ASK never changes the action alone.
- **Hysteresis:** `candidate = argmin E[L]`, then the corroboration cap. Move u→c only if `E[L(u)] − E[L(c)] > h`, with h = 1.0 up and 2.0 down. Minimum dwell 3 min.
- **Grey baseline:** equal-weight naive Bayes with the same tables. r = 0.8 for all; w = 1; τ = 1; every citizen report is a high-bin vote; no hysteresis; ALERT iff naive P(C) ≥ 0.7; no ASK.

### 6. Config values (frozen 13:45)
- `engine/config/belief_spec.json`: `tau 0.7`, `rho 0.6`, `eps 0.02` (⚠️ my name for the forget rate), `alpha_prior 0.3`, `trust_prior [2,1]`, `crowd_r 0.6`, bins and tables (P3 prompt).
- `engine/config/cost.json`: c, m, d, f, `lam_default 1.0` (P3 prompt).
- `engine/config/hyst.json`: `h_up 1.0`, `h_down 2.0`, `dwell_min 3`.
- `engine/config/questions.json`: Q1 "Water above ankle at Ambazari underpass?" (P(yes) N .10, S .05, I .55, C .90); Q2 "Ward 9 drain outfall visibly overflowing?" (.15/.10/.40/.85); Q3 "Ambulances queued at Ward 9 hospital?" (.10/.10/.25/.60).
- `engine/config/lags.json`: frozen 16:00 (rain→drain only, see ⚠️).

### 7. Boundaries (non-circularity; these are your rules)
- `engine/` never imports `generator/` and never opens `generator/sealed/`.
- `engine/` never reads truth. Aditya's `eval/sweep.py` gives only the final label to `Trust.end_episode`.
- `server/` may import the responder (by design). The grep check excludes `server/`.
- Do not write the words "generator" or "sealed" inside `engine/`, not even in comments.

**Grep checks (run from `C:devTwin_Breaker`; empty output = pass):**
```powershell
findstr /S /N /C:"generator" /C:"sealed" engine\ingest.py engine\belief.py engine\decide.py
findstr /S /N /C:"generator" /C:"sealed" engine\*.py
```
What this does: `findstr` searches text for the words. Empty output is the pass. Run both at 18:00 and 04:30.

### 8. Hand-offs (who gives what, to whom)

| You give | To | When | Path |
|---|---|---|---|
| `Event` and `parse_line` | Aditya (his schema checks, sweep) | 14:00 | `engine/types.py`, `engine/ingest.py` |
| Config files (frozen values) | Aditya (sweep reads cost and spec) | 13:45, then frozen | `engine/config/*.json` |
| `run_episode(jsonl_path, lam, ask_enabled, grey) -> list[dict]` (⚠️ proposed) | Aditya's `eval/sweep.py` and `precompute.py` | 16:30 | `engine/run.py` |
| Trust and replay (`Trust.reset`, `Trust.end_episode`, `replay`) | Aditya (sweep) | 16:00 | `engine/belief.py` |
| Server routes and page | Team (23:00 demo) | 18:00 (stub), 22:00 (full) | `server/`, `web/` |

| You receive | From | When | Until then |
|---|---|---|---|
| `data/streams/P1A-s0007.jsonl`, `P1B-s0007.jsonl` (DEV, Pass 1) | Aditya | 14:00 | `engine/fixtures/seed7_mock.jsonl` |
| Full passive streams and twin pairs | Aditya | 18:00 | mock |
| `generator/responder.py` `reply()` | Aditya | 18:00 | `server/responder_mock.py` |
| `scenarios/*.json` | Aditya | 18:00 | your inject stub (§4 texts) |
| `data/episodes/` pre-rendered traces | Aditya (`eval/precompute.py`) | 22:00 | live server |
| `results/dev/` DEV 10-seed table | Aditya (`eval/sweep.py`) | 22:30 | print the run log |

---

## Your part of the red-team demo + evaluation chain

**Your chain links (MAIN §3):**

| # | Link | Your component | Shown as |
|---|---|---|---|
| 1 | Ingest: async, dupes, out-of-order, retractions | `engine/ingest.py` | "400 forwards → 1 cluster" |
| 2 | Source trust and gateway ESS | `engine/belief.py` | eff. n, trust per source |
| 3 | 4-hypothesis calibrated belief | `belief.step()` | belief bars |
| 5 | Optimal stopping with ASK / VOI | `engine/decide.py` | cost line, ASK gain |
| 6 | Stability: hysteresis and min dwell | `decide.py` | flip count vs grey |
| 7 | Foresight (top-1 until Pass 2 lags) | `belief.py` + `lags.json` | foresight line |
| 8 | Prior shift, no retraining | `belief.py` π update | prior chart (cut-first) |
| 9 | Silence is UNKNOWN, not all-clear | silence rule | red team 2 and 3 |
| 10 | Explain: why I changed my mind | `decide.py` reason log | bits log |

Aditya owns chain links 4 (metrics, Brier, ECE, lead time, FAR), 11 and 12 (misspecification and prior-shift numbers), and 13 (foresight hit). You expose the toggles he needs: `ask_enabled` (metric 5, ASK on and off) and `grey` (naive baseline), plus `lam` for FAR at λ = 2 and 4.

**Your three red-team attacks (MAIN §4):**

| Attack | Your detection | Pass check (must hold) | UI text |
|---|---|---|---|
| Rumour wave: 400 forwards, 12 phrasings, 40 s | Jaccard ≥ 0.8 within 120 s → one cluster; cluster = one vote | 12 phrasings form one cluster (test in P5); max action ≤ PREPARE | "400 reports · 1 cluster · eff. n ≈ 1" |
| Gateway outage: G3 silent, 100 drains | Silent channels add no likelihood; N → S only | |ΔP(C)| ≤ 0.001 on the fixture; flips 0 | "1 gateway outage · drain sensors UNKNOWN (not all-clear)" |
| Camera cut-out: all traffic, 4 min | Coverage UNKNOWN; forgetting only | ΔP(C) ≤ 0.05 per minute | "traffic UNKNOWN · coverage 5/6" |

**Your say-on-stage line (MAIN §1):** "Synthetic world. The marshal is our simulated responder. PS 2.1 has no official chain; ours is mapped from its Requirements list. The forecaster's lags are estimated from data, not copied from the simulator."

---

## If you're blocked

| Situation | What to do |
|---|---|
| Blocked more than 20 min | Message Rishi (team) with the exact error. For a contract question, message Aditya with the file path. |
| 14:00 gate fails | Switch to §15a at 14:00 sharp. Keep: grey config, ASK with Q1 only, one twin pair (seed 7), pre-rendered traces, DEV 10-seed table, banner. Tell Rishi and Aditya. |
| Aditya's streams are late | Use `engine/fixtures/seed7_mock.jsonl`. Label the page "MOCK". Do not block your own work on him. |
| Claude Code breaks a test you cannot fix | Stop. Paste the failing test output to Rishi. Do not run `git reset --hard`, `git checkout -- .` or `--force`. |
| Git says "rejected" on push | `git pull --no-edit origin main`, then `git push`. Never `--force`. |
| `git status` shows unexpected files | Do not add them. Ask Rishi. |
| Wi-Fi is down | Nothing needs the network at runtime. Chart.js is vendored. Use the pre-rendered traces. |
| Laptop battery under 30 percent before 23:00 | Plug in. Tell Rishi. |
| You are overloaded (after 20:00) | Drop the reason log's top-3 to top-1, and the foresight to a static line. Aditya runs the sweeps; you do not. |

---

## Mid-eval: what you'll show and say (2 lines)

1. "I'll play Twin P1 from the prefix. Both twins look the same until the marshal's reply, and the ASK fires at about minute 7 when the expected gain is above 0.3."
2. "Asking splits the twins before the data does, and silence is UNKNOWN, not all-clear. Labels say DEV or EVAL; the banner says SYNTHETIC."

---

## Sleep and partner rhythm (proposed; confirm with Aditya by 23:00)

- **Sleep 03:00–04:30.** You hand over at 03:00 (handover note in README). Aditya is awake. You do not edit `engine/` during sleep.
- **Awake 04:30–06:00.** You own the freeze. Aditya sleeps 04:30–06:00 and wakes at 06:00 to run EVAL and MISSPEC (his command, written in advance).
- **Check on your partner** every 2 hours: 15:00, 17:00, 19:00, 21:00, 23:00, 01:00, 03:00, 05:00, 07:00, 09:00.

---

## How I know I'm done

**At each gate:**
- [ ] **13:45:** `engine/config/*.json` parse (P3 check prints `ok`). `engine/types.py` committed.
- [ ] **14:00:** `python -m engine.run --seed 7 --split dev` prints per-minute P(C) for ours and grey, does not crash, runs in under 60 s.
- [ ] **16:00:** `engine/config/lags.json` is committed (rain→drain).
- [ ] **18:00:** `/api/inject` responds; the P1 trace returns as JSON; the page plays it; ASK fires on seed 7 (or is logged as "not fired", and you say so); both grep checks print nothing.
- [ ] **22:00:** three buttons live; `server/responder_mock.py` is unused or removed; the page works with Wi-Fi off.
- [ ] **22:30:** 60-second capture in `docs/twin-breaker/screens/`.
- [ ] **23:00:** P1 plays with the SYNTHETIC banner; "DEV, 10 seeds" is on the table.
- [ ] **06:00:** no `engine/`, `server/` or `web/` changes after the freeze line (check `git log --oneline --since="06:00"` for those paths; the list should be empty).
- [ ] **10:45:** `git status` clean; final push done.

**You can answer these five questions aloud (no notes):**
1. What happens to the belief in one minute (forget, each reading, ESS, silence, reply, normalise)?
2. Why is silence UNKNOWN and not all-clear?
3. What does hysteresis stop, and what does min dwell stop?
4. Why does ASK fire only when VOI is above 0.3?
5. Why does a single citizen cluster or a single reply never reach ALERT by itself?

---

## ✅ Decided (orchestrator, 12:55). You are Pod B lead, so these are yours to change. Rishi is busy on Ek Bill: ask him only about git emergencies.

1. **Forget step vs outage check:** the outage test (`|ΔP(C)| ≤ 0.001`) runs with the forget step **OFF** and tests the silence step alone (P5). Report the forget drift (~−0.003/min) separately in the README. Tell Aditya.
2. **Batch runner:** use the `run_episode(...)` signature proposed in P8. Send it to Aditya by 15:30; it becomes part of the contract.
3. **Episode files:** `data/episodes/<episode_id>__lam<λ>.json` in the §8.4 shape. Aditya follows this.
4. **Lags:** freeze rain→drain at 16:00 and the other three pairs at 18:00, with a ±2 min window.
5. **VOI constant `0.5 + 0.2·1.0`:** implement as written and add a one-line comment saying it's a hand-set prior weight. If a judge asks, say "hand-set, and the sweep shows the result is insensitive to it" (Aditya adds it to the sweep).
6. **ASK threshold 0.3:** move it into `config/belief_spec.json` as `ask_threshold` so it can be tuned there.
7. **Tests:** your engine tests go in `tests/test_engine_*.py`. Aditya owns the rest of `tests/`.
8. **Branch:** you work on `harshavi`, Aditya on `aditya`; both merge into `main` by PR (see the Git workflow box in Setup). Never commit to `main` after the bootstrap.
9. **Sleep:** Harshavi 03:00–04:30, Aditya 04:30–06:00.
10. **22:30 backup capture:** you own it (your laptop is the Twin-Breaker demo laptop).
11. **⚠️ My naming choices:** `server/app.py`, `server/responder_mock.py`, `engine/run.py`, `engine/estimate_lags.py`, `engine/fixtures/seed7_mock.jsonl`, `eps` in `belief_spec.json`. Change them only with Aditya's agreement.
12. **⚠️ Your clone path** in Step 1 is a placeholder. Fill in your own path.
