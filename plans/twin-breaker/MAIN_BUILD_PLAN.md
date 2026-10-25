# MAIN BUILD PLAN — Twin-Breaker  (Pod B: Harshavi lead + Aditya support)
Slug `twin-breaker` (repo: `Twin_Breaker`, repo root = project) · Locked 12:15, 25 Oct · Rev 2 (fixes for PLAN_REVIEW BLOCKERS 1–6) · **Fallback: in-project reduced Twin-Breaker (§15a)**. Holdout is not planned.

## 1. One-liner, themes, deployment
**One-liner:** Calibrated crisis belief that asks one well-chosen question to split the twins before the data does.
- **Primary:** PS 2.1 *The First 10 Minutes* → Theme 2 *Crisis Before Crisis*. **Stack theme:** none.
- **Mechanism:** ASK as a priced fifth action in the stopping rule (value of information).
- **Deployment (criterion 4):** a duty officer's control-room laptop. numpy only, no per-call cost, no network. First 100 users: control-room duty officers in one municipal corporation (pitch claim, unverified).
- **Say on stage:** "Synthetic world. The marshal is our simulated responder. PS 2.1 has no official chain; ours is mapped from its Requirements list. The forecaster's lags are estimated from data, not copied from the simulator."

## 2. Demo flow (north star)
Banner on every screen: `SYNTHETIC. Scale inspired by a published 2005 Mumbai rainfall figure (NIDM). Not real telemetry. Fictional event at a real location.`

| # | Step | Clock |
|---|---|---|
| 1 | Pick **Twin P1** (DEV seed 7, tuning set; A = cascade, B = storm-noise). Two panels, identical passive traces. Play: 7-min prefix at 4 s/min. Belief bars (N,S,I,C) move identically; grey line (naive, ALERT if P(C) ≥ 0.7) beside them. | 0:00–0:40 |
| 2 | Both twins fire **ASK** at the minute VOI first clears 0.3: "Asking Ward 9 marshal: 'Water above ankle at Ambazari underpass? 1=yes 2=no' · expected gain 0.41". | ~0:40 |
| 3 | Reply after ~1 min. Twin A "yes", Twin B "no". Responder trust shown. Twin A reaches ALERT only when the corroboration rule (§8.5) is met, and the banner says which passive channel corroborated it. Grey flips. Banner: "Lead time gained: X min (paired median, DEV 10 seeds)". | ~1:00 |
| 4 | Click any minute → **Reason** log ("+2.1 bits: 3 hospitals reporting", "eff. n = 1.7 (gateway G2, 100 sensors)"). Foresight line: "next: drain ≥ 0.85 in 3–8 min (lags estimated from DEV data)". | 1:10 |
| 5 | Red team 1, **rumour wave** (400 forwards in 40 s): "400 reports · 1 cluster · eff. n ≈ 1". Ours: no ALERT, max PREPARE. Grey jumps to ALERT. | 1:30 |
| 6 | Red team 2, **gateway outage** G3 (100 drains silent): "1 gateway outage · drain sensors UNKNOWN (not all-clear)". P(S) rises; P(C) unchanged; flips 0. | 1:45 |
| 7 | Red team 3, **camera cut-out** (all traffic cams, 4 min): "traffic UNKNOWN · coverage 5/6". No crash; ΔP(C) ≤ 0.05/min. | 2:00 |
| 8 | Eval table (§10) against grey. Labels say DEV or EVAL. Close: "Asking splits the twins before the data does. Silence is UNKNOWN, not all-clear." | 2:15 |

## 3. Evaluation chain → component (**our mapping**; PS 2.1 has no official chain)
| # | Link (PS source) | Component | 23:00 | 11:00 | Shown as |
|---|---|---|---|---|---|
| 1 | Ingest: async, dupes, out-of-order, retractions | `engine/ingest.py` | REAL | REAL | 400 forwards → 1 cluster |
| 2 | Source trust across episodes + gateway ESS (Learning; Adversity) | `engine/belief.py` | REAL | REAL | eff. n, trust per source |
| 3 | 4-hypothesis calibrated belief (Honest probabilities) | `belief.step()` | REAL | REAL | belief bars |
| 4 | Twin Test: Brier pre-split, commit post-split, reliability | `eval/metrics.py`, `eval/sweep.py` | PARTIAL (P1, 10 DEV seeds) | REAL (P1–P3, 50 EVAL seeds) | eval table, reliability chart |
| 5 | Optimal stopping + cost incl. ASK/VOI (Optimal stopping) | `engine/decide.py` | REAL (1 question) | REAL (3) | cost line, ASK gain |
| 6 | Stability: hysteresis + min dwell | `decide.py` | REAL | REAL | flip count vs grey |
| 7 | Foresight: next events with windows (lags estimated from DEV) | `belief.py` + `config/lags.json` | PARTIAL (top-1) | REAL (top-3, hit rate) | foresight line |
| 8 | Prior shift, no retraining | `belief.py` prior update | MOCKED | REAL | prior chart |
| 9 | Cutouts + common-cause lies (Adversity) | ingest coverage; silence rule | REAL (gateway) | REAL (+ cameras) | red teams 2–3 |
| 10 | Explain: why I changed my mind | `decide.py` reason log | REAL | REAL | bits log |

## 4. Red-team scenarios
| Attack | Injected by | Detection | UI shows | Pass check |
|---|---|---|---|---|
| Rumour wave (400 forwards, 12 phrasings, 40 s) | `scenarios/rumour_wave.json` | Jaccard ≥ 0.8 within 120 s → 1 cluster; cluster = 1 vote | "400 reports · 1 cluster · eff. n ≈ 1"; no ALERT, max PREPARE | 12 phrasings: pairwise Jaccard ≥ 0.8, one cluster (test); max action ≤ PREPARE |
| Gateway outage (G3 silent, 100 drains) | `scenarios/gateway_outage.json` | Silent channels carry no likelihood; ESS discount | "UNKNOWN not all-clear"; P(S) up; P(C) unchanged | ΔP(C) ≤ 0.001 on fixture; flips 0 |
| Camera cut-out (all traffic, 4 min) | `scenarios/camera_cutout.json` | Coverage UNKNOWN; forgetting only | "traffic UNKNOWN · coverage 5/6" | ΔP(C) ≤ 0.05/min |
| Optional (cut 3rd): 50 YES from unregistered numbers | `scenarios/reply_flood.json` | Whitelist in ingest | "50 replies ignored" | P unchanged |

## 5. Architecture
```
[1 GEN B + responder] --JSONL--> [2 INGEST] --minute buckets--> [3 BELIEF] --P(N,S,I,C)--> [4 DECIDE]
 sealed truth, sealed errors      dedupe, retract,             tempered Bayes,           WATCH/PREPARE/
        ^                         whitelist, 90 s grace        Beta trust, gateway ESS   ALERT/ESCALATE/ASK
        | ASK -> server -> responder -> reply event (30–90 s) -> back into [2]              |
        +-------------------------------------- [6 SERVER + WEB PAGE] <--- reason log -------+
[5 EVAL, Aditya] reads sealed truth after a run only. Boxes 2–4 never import generator/ or read sealed/.
```
| # | Box | Owner |
|---|---|---|
| 1 | Generator B + responder (sealed) | Aditya (Qwen) |
| 2 | Ingest | Harshavi (Claude Code) |
| 3 | Belief | Harshavi (Claude Code) |
| 4 | Decide (costs, VOI, hysteresis, reasons) | Harshavi (Claude Code) |
| 5 | Eval + sweeps + precompute | Aditya |
| 6 | Server + one HTML page | Harshavi |

Harshavi owns boxes 2, 3, 4, 6. Aditya owns 1 and 5.

## 6. Tech stack
| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.10+ (3.11 preferred; check `py -0`) | Both laptops; numpy |
| Maths | numpy only | No scipy, no ML |
| Generator | Seeded `numpy.random` (Student-t via `standard_t`) | Reproducible from seed |
| Data | JSONL streams, JSON config and results | Offline; diffable |
| Server | FastAPI + uvicorn, port 8000 | Fast; Harshavi knows it |
| Web | One HTML page, vanilla JS, Chart.js in `web/vendor/` | Offline; verify file exists at 13:05 |
| Tests | pytest; hand-computed fixtures | Independent of engine author |
| Models | **None in demo path.** Qwen writes code, copy, tests only | No GPU; no network |
| Fallback | Pre-rendered traces in `data/episodes/` for λ ∈ {0.5, 1, 2, 4} and each red-team case | Wi-Fi off |

## 7. Folder ownership inside the `Twin_Breaker` repo (repo root = project)
| Folder / file | Owner | Purpose | Talks to |
|---|---|---|---|
| `engine/` (`types.py`, `ingest.py`, `belief.py`, `decide.py`, `config/` schemas) | Harshavi | Inference path; numpy only; never reads `generator/` or `sealed/` | Called by `server/` |
| `eval/` (`metrics.py`, `sweep.py`, `check_stats.py`, `precompute.py`) | Aditya | Metrics, sweeps, results, pre-rendered traces. **Only code that reads sealed truth** | Reads `data/streams/`, `generator/sealed/`; writes `results/`, `data/episodes/` |
| `server/` | Harshavi | Routes, live ASK loop | `engine/`; `generator.responder` |
| `web/` | Harshavi | One HTML page + Chart.js | Server routes; `data/episodes/` offline |
| `generator/` (`gen.py`, `responder.py`, `world_spec.json`, `sealed/`) | Aditya | World, streams, responder, sealed truth | Writes `data/streams/`, `sealed/` |
| `scenarios/` | Aditya | Twin pairs, rumour, outage, cut-out, prior shift, question copy | Read by generator and server |
| `tests/` | Aditya | `test_twin_prefix.py` (first deliverable), metric tests, schema checks | Any folder |
| `data/streams/`, `data/episodes/`, `results/` | Aditya | Generated data. Streams gitignored; pre-rendered demo traces committed | Read by engine and web |
| `docs/twin-breaker/` (repo root) | Aditya (copy); `screens/` Harshavi | Slides, screenshots, backup video | Team |
| `requirements.txt`, `.gitignore`, `README.md` | Harshavi | Dependencies and ignores | All |

## 8. Interface contracts (exact)
### 8.1 Event line (one JSON object per line)
Shared fields: `event_id` (stable: derived from seed, channel, minute, source), `episode_id`, `kind`, `source_id`, `event_time_s` (int sim-seconds), `received_time_s` (≥ event_time_s), `value`.
```json
{"event_id":"ev-P1A-000123","episode_id":"P1A-s0007","kind":"observation","channel":"drain","source_id":"drain-G2-031","gateway_id":"G2","event_time_s":200,"received_time_s":231,"value":0.91}
{"event_id":"ev-P1A-000140","episode_id":"P1A-s0007","kind":"citizen","channel":"citizen","source_id":"phone-88ac","text":"Ambazari lake wall breached","text_hash":"4f1c9a","event_time_s":300,"received_time_s":305,"value":null}
{"event_id":"ev-P1A-000181","episode_id":"P1A-s0007","kind":"reply","channel":"reply","source_id":"marshal-W9-01","question_id":"Q1","answer":"yes","event_time_s":365,"received_time_s":365,"value":null}
{"event_id":"ev-P1A-000190","episode_id":"P1A-s0007","kind":"retraction","source_id":"drain-G2-031","retracts":"ev-P1A-000123","event_time_s":380,"received_time_s":381,"value":null}
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

### 8.2 Outputs (per closed minute)
```json
{"episode_id":"P1A-s0007","minute":5,"p":{"N":0.50,"S":0.15,"I":0.02,"C":0.33},"eff_n":{"gw-G2":1.66,"citizen":1.0},
 "coverage":{"rain":"ok","drain":"ok","traffic":"ok","calls":"ok","hospital":"ok","citizen":"ok"},"trust":{"marshal-W9-01":0.80}}
{"episode_id":"P1A-s0007","minute":5,"action":"PREPARE","candidate":"ALERT","changed":false,"minutes_in_action":3,
 "expected_cost":{"WATCH":33.3,"PREPARE":25.3,"ALERT":24.8,"ESCALATE":27.7},
 "ask":{"question_id":"Q1","text":"Water above ankle at Ambazari underpass? 1=yes 2=no","voi_net":0.41},
 "reason":[{"event_id":"ev-P1A-000123","bits":2.1,"text":"3 hospitals reporting"}],
 "foresight":[{"event":"drain>=0.85 (G2)","window_min":[3,8],"p":0.55}],"synthetic":true}
```
Illustrative values. `coverage` counts the six channel groups with ≥ 1 event in the last 2 minutes (`reply` is not counted). Hold because the 0.5 gain is below h_up = 1.0.

### 8.3 Python signatures (engine, exact)
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

### 8.4 HTTP routes (port 8000; `/` serves `web/index.html`)
| Method | Route | Response |
|---|---|---|
| GET | `/api/health` | `{"ok":true,"mode":"live"\|"precomputed","synthetic":true}` |
| GET | `/api/episodes` | `[{"episode_id":"P1A-s0007","pair":"P1","role":"A"}, ...]` |
| GET | `/api/episodes/{id}?lam=1.0` | `{"episode_id","lam","minutes":[{"belief":{...},"decision":{...}}],"synthetic":true}` |
| POST | `/api/inject` `{"episode_id","scenario":"rumour_wave"\|"gateway_outage"\|"camera_cutout","at_s":300}` | `{"ok":true,"injected":400,"trace":{...}}` |
| GET | `/api/results` | `results/eval_summary.json` |

Responder (server → generator, function call): `reply(episode_id: str, question_id: str, asked_at_s: int) -> {"answer":"yes"|"no","responder_id":"marshal-W9-01","delay_s":55}`.

### 8.5 Engine model spec (our design; no world-spec values)
- **Clock:** sim time drives everything. Playback is 4 wall-seconds per sim-minute. A reply has `received_time_s = asked_at_s + delay_s`. The engine consumes an event only after `closed_upto` allows it. Buckets use `event_time_s`; closure uses `received_time_s` with a 90 s grace. Causality test: a reply received at t cannot change any minute closed before t. Parity test: live and batch replay give the same beliefs.
- **Resets:** `Trust` and π reset at the start of every seed. `eval/sweep.py` passes only the final label into `end_episode`. The engine never opens `generator/sealed/`.
- **Per closed minute m:**
  1. Forget: `p ← 0.98·p + 0.02·π`.
  2. Each reading: `P_mix(b|H) = r·P(b|H,ch) + (1−r)/3`, r = Beta mean of its source. Add `τ·w·log P_mix`, τ = 0.7 (DEV-tuned).
  3. Gateway ESS: `w = 1/(1+(k−1)·ρ)`, ρ = 0.6. k readings give `n_eff = k/(1+(k−1)ρ)`.
  4. **Silent gateway** (no events and no heartbeat for 60 s): its channels add **no likelihood** (factor 1 on all H). Its share of N moves to S: `δ = min(0.10, 0.5·P(N))` per silent minute. C and I are untouched.
     - Hand-check: prior N .35, S .15, I .10, C .40 → after one silent minute N .25, S .25, I .10, C .40. ΔP(C) = 0. Fixture test: |ΔP(C)| ≤ 0.001.
  5. Reply: `P(yes|H) = r·p_yes(H) + (1−r)·0.5`, with τ applied as for sensors.
     - Hand-check: prior N .40, S .20, I .10, C .30; one trusted yes (r = 0.8, p_yes .10/.05/.55/.90). With τ = 0.7, P(C) ≈ 0.53, above the 0.33 ALERT line. That is why the corroboration rule below is required.
  6. Normalise. Citizen bin = min(2, **new** clusters this minute). Cluster = Jaccard ≥ 0.8 on 3-word shingles within 120 s. Crowd r = 0.6.
- **Corroboration rule (decide):** the candidate may be ALERT or ESCALATE only if a passive channel (rain, drain, traffic, calls, hospital) has bin ≥ elevated in the last 3 minutes. Otherwise cap the candidate at PREPARE. This covers citizen-only and reply-only evidence.
- **Bins** (0 calm · 1 elevated · 2 high): rain <5 / 5–25 / ≥25 mm/h · drain <0.5 / 0.5–0.85 / ≥0.85 · traffic ≥0.7 / 0.4–0.7 / <0.4 · calls <3 / 3–8 / >8 · hospital <4 / 4–9 / ≥10.
```
P(bin|H)   N              S              I              C
rain       [.70,.25,.05]  [.34,.33,.33]  [.55,.35,.10]  [.30,.40,.30]
drain      [.75,.20,.05]  [.34,.33,.33]  [.60,.30,.10]  [.10,.30,.60]
traffic    [.80,.15,.05]  [.80,.15,.05]  [.45,.40,.15]  [.10,.35,.55]
calls      [.75,.20,.05]  [.75,.20,.05]  [.50,.35,.15]  [.10,.35,.55]
hospital   [.75,.18,.07]  [.75,.18,.07]  [.60,.30,.10]  [.15,.35,.50]
citizen    [.85,.12,.03]  [.85,.12,.03]  [.60,.30,.10]  [.25,.35,.40]
```
- **Trust:** Beta(2,1) per source. `end_episode`: decay counts by 0.9. A reading is consistent if its bin is the modal bin under `final_label`. Add (consistent, inconsistent) counts.
- **Prior π:** uniform at start; after each episode `π ← 0.7·π + 0.3·final posterior` (label-free; α = 0.3).
- **Foresight lags:** not in this plan. Estimated from DEV streams by lagged cross-correlation of observed events, with no truth. Frozen at 16:00 as `engine/config/lags.json`. Until then, foresight shows top-1 only.
- **Cost:** `L[a,H] = c_a + d_H·(1−m_a) + λ·f_a·1[H∈{N,S}]`; c = {W 0, P 2, A 5, E 8}; m = {0, .3, .6, .8}; d = {N 0, S 0, I 15, C 100}; f = {A 10, E 20}; λ default 1.0 (slider 0.5/1/2/4).

| action \ H | N | S | I | C |
|---|---|---|---|---|
| WATCH | 0 | 0 | 15 | 100 |
| PREPARE | 2 | 2 | 12.5 | 72 |
| ALERT | 15 | 15 | 11 | 45 |
| ESCALATE | 28 | 28 | 11 | 28 |

At λ = 1, I ≈ 0: ladder thresholds on P(C) are **≈0.07 (PREPARE), ≈0.33 (ALERT), ≈0.43 (ESCALATE)**. Unit-tested.
- **ASK / VOI:** `VOI(q) = min_a E[L] − (0.5 + 0.2·1.0 + Σ_r P(r)·min_a E[L|r])`. Fire if max VOI > 0.3, asks < 3 per episode, ≥ 3 min since last ask. Questions in `engine/config/questions.json`: Q1 "Water above ankle at Ambazari underpass?" (P(yes) N .10, S .05, I .55, C .90); Q2 "Ward 9 drain outfall visibly overflowing?" (.15/.10/.40/.85); Q3 "Ambulances queued at Ward 9 hospital?" (.10/.10/.25/.60).
- **Hysteresis:** `candidate = argmin E[L]`, then the corroboration cap. Move u→c only if `E[L(u)] − E[L(c)] > h`, with h = 1.0 up and 2.0 down. Minimum dwell 3 min. ASK never changes the action alone.
- **Config schemas, frozen 13:35:** `belief_spec.json` {tau, rho, eps, alpha_prior, bins, tables, trust_prior, crowd_r}; `cost.json` {c, m, d, f, lam_default}; `hyst.json` {h_up, h_down, dwell_min}; `questions.json` [{qid, text, p_yes}]; `lags.json` (16:00).
- **Grey baseline:** equal-weight naive Bayes with the same tables. r = 0.8 for all; w = 1; τ = 1; every citizen report is a high-bin vote; no hysteresis; ALERT iff naive P(C) ≥ 0.7; no ASK.
- **Reason log:** per event `bits = τ·w·log2(P_mix(b|top)/P_mix(b|second))`; top 3 per minute by |bits|.

## 9. Synthetic data / generator (Aditya; his own spec file)
- **Scope cut, explicit.** Pass 1 (by 14:00): rain, drain, citizen; hypotheses N and C; DEV 1–10 (includes seed 7). Pass 2 (by 18:00): calls, hospital, traffic, responder, sensor-failure S, twin pairs P1–P3, rumour, G3 outage. Pass 3 (after 18:00, cut first): camera cut-out, prior shift, MISSPEC world.
- **Exact interface.** `generator/gen.py`: `generate(world: str, split: str, seed: int, episode: str, out_dir: str) -> dict` writes `<out_dir>/<episode>.jsonl` and `generator/sealed/<episode>.truth.json`. CLI: `python -m generator.gen --world {B,C} --split {dev,eval,misspec} --seeds 1-10 --out data/streams/`.
- **RNG rule:** every passive draw is keyed on `(seed, channel, minute)`, never on hidden state. Hidden-state-dependent parameters may be read only for minutes ≥ 7 in twin pairs.
- **Twin pairs:** same seed gives identical passive streams for non-reply kinds with `event_time_s < 420`. Cascade onset for the cascade twin is in [8, 10] min, so the prefix stays identical by construction. Replies differ from about 05:00 by design.
- **First deliverable: `tests/test_twin_prefix.py`.** It asserts identical non-reply events (ids included) for t < 420 in every pair. It fails until the generator passes. Check: `pytest -q tests/test_twin_prefix.py`.
- **World values** (distribution families, lag ranges, noise scale, responder error) live only in `generator/world_spec.json`. Aditya chooses values that differ from the engine's own numbers. Hash recorded in `generator/world_spec.sha` before 14:00. The plan does not list them, so the engine author never sees them. Check: `grep -rn "engine" generator/` prints nothing.
- **Responder (sealed):** `marshal-W9-01` answers from latent depth with a sealed error. Default in the range [0.10, 0.25]; sensitivity at 0.40. Delay 30–90 s. Unregistered numbers spam "yes".
- **Seeds:** DEV 1–50 (tuning; not reported as results). EVAL 1001–1050 (Gen B; opened once at 06:00). MISSPEC 2001–2050 (Gen C; once at 06:00).
- **EVAL per seed (9 eps):** 3 twin pairs + N with rumour + S with G3 outage + I with cut-out. Gives 150 cascade and 300 non-cascade.
- **Sealed truth fields:** `{"hypothesis","onset_min","pair","role","latent_depth_cm"}`. Only `eval/` reads it.
- **Model split:** Qwen 9B coder writes code. The 35B writes copy and tests. Both are unloaded before any sweep (16 GB RAM).

## 10. Evaluation numbers
Ours = engine with ASK. No-ASK = same engine, ASK off. Grey = §8.5 baseline. Targets are goals; we print what we get.

| # | Metric | Computed as | On | Target |
|---|---|---|---|---|
| 1 | Brier, P(C) | mean (p_C − y)² over minutes | EVAL 450 eps | < grey |
| 2 | Brier pre-split | same, minutes 0–6 | EVAL twin **A-role** only, 150 | ≤ grey |
| 3 | ECE, 10 bins | `ece()`; reliability chart | EVAL | < 0.10 |
| 4 | Lead time | onset − first ALERT/ESCALATE; median, IQR | EVAL cascade | ≥ 2 min |
| 5 | **Lead time gained by ASK** | paired per seed: commit(no-ASK) − commit(ASK), A-role; median of 50 | P1–P3 | ≥ +1 min; shown at responder error 0.10 / 0.25 / 0.40, ASK on/off |
| 6 | FAR | non-cascade eps reaching ALERT+ | EVAL 300 | Report. Show λ = 2 and 4 next to it |
| 7 | Flips | `flip_count()` mean per episode | all 450 | ≤ grey; 0 in outage and cut-out |
| 8 | Realized cost | `L[highest action, H_true]` mean; simplified | EVAL | < grey |
| 9 | Outage hold | max per-min \|ΔP(C)\| in G3 outage | S-standalone | ≤ 0.001 |
| 10 | Rumour | max action; eff. n | N + rumour | ≤ PREPARE; eff. n ≤ 2 |
| 11 | Misspecification | Brier(MISSPEC) − Brier(EVAL) | 50 + 50 | ≤ 0.03 |
| 12 | Prior shift | \|π̂_C − 0.40\| at ep 15 | prior-shift | ≤ 0.10 |
| 13 | Foresight hit | top-3 forecasts landing in window | C eps | ≥ 0.5 (11:00 only) |

## 11. Milestones (lead Harshavi · support Aditya)
| By | Lead | Support | Gate check |
|---|---|---|---|
| 13:05 | Measure one smoke-episode file size and record it here; `py -0`; confirm `web/vendor/` Chart.js exists | `pip download` own-OS wheels; smoke seed | Size and paths recorded in this plan |
| 13:35 | Config schemas frozen (§8.5); `ingest.py` skeleton | Pass 1 generator starts | Schemas committed |
| **14:00 go/no-go** | `ingest.py` + `belief.step()` + decide stub | Pass 1 DEV seed 7 + DEV 1–10 | `python -m engine.run --seed 7 --split dev` runs ingest → step → stub; prints P(C) ours and grey per minute; no crash; < 1 min. **FAIL → §15a** |
| 15:30 | `decide.py` + VOI + hysteresis + corroboration; ladder tests | Pass 2 starts; `test_twin_prefix` green | Ladder thresholds ≈0.07 / 0.33 / 0.43 |
| 16:00 | `lags.json` frozen from DEV (no truth) | `eval/metrics.py`, `sweep.py`; 50-seed DEV table starts; ECE | DEV table prints |
| **18:00 integration** | `/api/inject`; P1 trace; page plays it | Pass 2 complete; scenario JSON validated | P1 plays; ASK fires in seed 7; both grep checks pass |
| **22:00 E2E + red team** | 3 buttons live + pre-rendered fallback | `eval/precompute.py` runs (~32 traces) after E2E passes | Each banner shows; works Wi-Fi off; Harshavi checks one trace |
| **22:30** | 60-s backup screen capture of P1 | DEV 1–10 sweep (`eval/sweep.py`) | Capture saved in `docs/twin-breaker/`; DEV table ≥ 10 seeds |
| **23:00 mid-eval** | Slice + diagram + DEV 10-seed table | Rehearse explanations | P1 live; "DEV, 10 seeds" labelled; SYNTHETIC banner |
| 00:00–04:00 | Tune τ and ASK threshold on DEV only | 3 pairs × 50 DEV; prior shift | `results/dev/` saved |
| **06:00 freeze** | Harshavi: no changes after this line | EVAL + MISSPEC run once → `eval_summary.json`; `check_stats` | No tuning after this |
| 06:00–08:30 | Screenshots; backup video | Slides; `docs/twin-breaker/` | Videos saved |
| 08:30–10:30 | Rehearse ×3; Q&A | Q&A drill | Each member answers 5 questions |
| **10:45 final push** | `git pull --no-edit origin main`, then `git push` | Same | Nothing after 10:45 |

`eval/check_stats.py` (Aditya, three lines of logic): loads `eval_summary.json`, asserts 150 cascade and 300 non-cascade episodes, prints the §10 table.

## 12. Setup commands
> **Repo (updated 13:25):** https://github.com/harshavi3009/Twin_Breaker. The repo root = the project (no `twin-breaker/` sub-folder). Clone to `C:devTwin_Breaker` / `~/dev/Twin_Breaker`. Harshavi works on branch `harshavi`, Aditya on `aditya`. Both merge into `main` by pull request, and only Harshavi merges. The exact steps are in the "Git workflow" box of `plans/members/harshavi.md` and the "Git" section of `plans/members/aditya.md`; those win over the commands below.
**Git, plain steps (Harshavi).** `git pull --no-edit origin main` gets the team's latest; do it before you start and before every push. Add only your folders, never `git add .`. If push says "rejected", run `git pull --no-edit origin main`, then `git push`. Never `--force`. Streams, venv and wheels stay out of git through `.gitignore`: `.venv/`, `__pycache__/`, `vendor/wheels/`, `data/streams/`, `generator/sealed/`, `results/dev/`. Streams regenerate from the seed. Only pre-rendered traces in `data/episodes/` are committed.
```powershell
cd C:\dev\Twin_Breaker; git pull --no-edit origin main
py -0                                  # list installed Pythons; use any 3.10+
py -3.11 -m venv .venv                 # or: py -3 -m venv .venv
.venv\Scripts\activate
pip download -r requirements.txt -d vendor\wheels    # on Wi-Fi, before 13:05
pip install -r requirements.txt
python -m pytest -q tests
git add engine server web requirements.txt .gitignore
git commit -m "engine: ingest"; git pull --no-edit origin main; git push
findstr /S /N /C:"generator" /C:"sealed" engine\ingest.py engine\belief.py engine\decide.py   # must print NOTHING
```
**Aditya (Linux bash).** Stop the 35B model before sweeps.
```bash
cd ~/dev/Twin_Breaker && git pull --no-edit origin main
python3 -m venv .venv && source .venv/bin/activate
pip download -r requirements.txt -d vendor/wheels        # on Wi-Fi, own OS only
pip install --no-index --find-links vendor/wheels -r requirements.txt
python -m pytest -q tests/test_twin_prefix.py
python -m generator.gen --world B --split dev --seeds 1 --out data/streams/
grep -n "generator\|sealed" engine/ingest.py engine/belief.py engine/decide.py   # must print NOTHING
grep -rn "engine" generator/                                                     # must print NOTHING
```
Wheels are OS-specific: each laptop downloads its own into its own ignored folder. `requirements.txt` (Harshavi): numpy, fastapi, uvicorn, pytest, httpx.

## 13. Cut list (in order)
1. Stars game (not in build) · 2. Foresight → top-1 + lag table · 3. Prior-shift chart (keep code and test) · 4. Q3 · 5. MISSPEC run (say "not run") · 6. Reply-flood button (keep whitelist test) · 7. Live server → pre-rendered only · 8. Outage and cut-out buttons → pre-rendered only · 9. Camera cut-out (Pass 3).
**Never cut:** twin split by ASK · gateway ESS · rumour dedupe · the 50-seed table.

## 14. Wow-upgrades (only if ahead at 02:00)
Learned cry-wolf price suggestion for λ · live reply-flood (Sybil on ASK) · phone view on LAN (if venue allows) · per-responder reliability over episodes.

## 15. Fallback and risks
### 15a. In-project fallback (Harshavi; one page; written by 13:05; triggered at 14:00 if the gate fails)
- Keep: the grey config (naive Bayes engine path), ASK with Q1 only, one twin pair (DEV seed 7) with pre-rendered traces, the three red-team cases as pre-rendered traces, DEV 10-seed table, banner.
- Drop: VOI for Q2 and Q3, foresight beyond top-1, prior shift, MISSPEC, live server.
- Holdout (PS 3.3) is not planned. It is considered only if organisers confirm the per-theme PS rule (still open in PORTFOLIO.md) and this fallback cannot be built.

### 15b. Risks
| Risk | Fallback / mitigation |
|---|---|
| Engine not green at 14:00 | §15a |
| Corroboration rule suppresses the demo ALERT | Demo banner shows the corroborating channel. If none fires in seed 7, the ALERT moment moves to the first corroboration; say so |
| ALERT near P(C) 0.33 vs grey 0.7 raises FAR | Report it; show λ = 2 and 4 next to it. Never hide |
| Brier worse than grey | Report it. Tune τ on DEV only |
| "You built the responder too" | Sealed error; sensitivity at 0.10 / 0.25 / 0.40; trust learned across episodes; "our responder" on stage |
| VOI never > 0.3 | Lower to 0.1; show the gain number |
| Harshavi overloaded | Boxes 6 and 4 reduced to CLI output and static page; Aditya runs sweeps |
| Qwen generator wrong | `test_twin_prefix.py` first; Aditya runs `tests/`; Harshavi reviews the diff |
| RAM 16 GB | Unload the 35B before sweeps, or use the 9B coder |
| Wi-Fi down | No runtime network; Chart.js vendored; traces pre-rendered |
| Ambazari figures and BMC/CAG pitch facts unverified | Check before any slide, or drop |

## 16. Mid-eval checklist (23:00)
- [ ] Demo laptop = Harshavi's (i5, RTX 3050). Charged. One full run with Wi-Fi off at 22:30.
- [ ] P1 plays: prefix, ASK, split, banner. Grey line beside ours with flip counter.
- [ ] One red-team button live (or pre-rendered). DEV table (≥ 10 seeds) labelled DEV.
- [ ] SYNTHETIC banner. Architecture diagram printed. Backup capture (22:30) saved.
- [ ] Harshavi explains belief, ESS, hysteresis, VOI, corroboration. Aditya explains the sealed generator and responder.
- [ ] Mentor feedback → `outputs/03-mid-eval-feedback.md`.

## 17. CREDITS.md entries (appended to root under the Team Obsidian heading)
- numpy (BSD-3), FastAPI (MIT), uvicorn (BSD-3), pytest (MIT), httpx (BSD-3), Chart.js (MIT, vendored), Python 3.11 stdlib (PSF).
- Mumbai 2005 rainfall (944 mm/24 h; peak reported as above 190 mm/h): NIDM case study. Used as "inspired by" scale only. 944 mm/24 h is not converted to a rate, and 190 mm/h is not derived from it.
- Pitch facts, to check before slide: Mumbai Live (BMC/IFLOWS, 2020); CAG via The News Minute (Chennai 2015).
- Concepts from memory, not re-checked: Brier 1950; ECE (Naeini et al. 2015); n_eff = k/(1+(k−1)ρ) (Kish 1965).
- AI assistance: Claude Code (engine, server); Qwen (generator, tests, eval).
- **Not verified:** Ambazari Sept-2023 figures. Do not use on slides until checked.
