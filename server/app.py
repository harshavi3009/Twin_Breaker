import json
import os
import re
from collections import defaultdict
from dataclasses import asdict, replace
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from engine.belief import PASSIVE, Trust, bin_index, replay, silent_gateways
from engine.decide import ACTIONS, Question, voi
from engine.ingest import Ingestor, new_clusters_by_minute, parse_line
from engine.live import REGISTERED_RESPONDERS, RESPONDER_ID, closure_instant, load_spec, run_live
from engine.types import Event
# The server wires the responder into the engine as a function (MAIN §8.4); the engine itself stays free of these imports.
from generator.responder import reply as sealed_reply
from generator.scenarios import apply_silence, build_injection
from server.demo import DEMO_ASK_MIN, DEMO_DIR, DEMO_LABEL, DEMO_SPEC, scripted_reply

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(ROOT, "web")
FIXTURE = os.path.join(ROOT, "engine", "fixtures", "seed7_mock.jsonl")
RESULTS = os.path.join(ROOT, "results", "eval_summary.json")  # MAIN §8.4 contract
PRIOR = {h: 0.25 for h in ("N", "S", "I", "C")}
CUTOUT_LEN_S = 240
CUTOUT_OBS_EVERY_S = 30
MOCK_B_SOURCE = "MOCK: no B stream on this machine, so B repeats A's passive events"
GATEWAY_STATES = ("calm", "elevated", "high")  # engine drain bins: below lo, below hi, at or above hi
TWIN_B = re.compile(r"^(P\d)B-")

app = FastAPI(title="Twin-Breaker (SYNTHETIC)")
app.mount("/vendor", StaticFiles(directory=os.path.join(WEB_DIR, "vendor")), name="vendor")


class InjectRequest(BaseModel):
    episode_id: str
    scenario: Literal["rumour_wave", "gateway_outage", "camera_cutout"]
    at_s: int = 300


def _truth_path(episode_id: str) -> str:
    return os.path.join(ROOT, "generator", "sealed", f"{episode_id}.truth.json")


def _twin_a_id(episode_id: str) -> str:
    return TWIN_B.sub(r"\1A-", episode_id)


def _opposite_reply(twin_a: str):
    # MOCK B's marshal answers the opposite of twin A's sealed answer, so the two twins split at the reply
    def reply(episode_id: str, question_id: str, asked_at_s: int) -> dict:
        answer = sealed_reply(twin_a, question_id, asked_at_s)
        return {**answer, "answer": "no" if answer["answer"] == "yes" else "yes"}
    return reply


def _responder_for(episode_id: str, source: str):
    # The responder needs the episode's sealed truth file. Without it (fresh clone), ASKs are logged but unanswered.
    if source == MOCK_B_SOURCE:
        twin_a = _twin_a_id(episode_id)
        return _opposite_reply(twin_a) if os.path.exists(_truth_path(twin_a)) else None
    return sealed_reply if os.path.exists(_truth_path(episode_id)) else None


def _read_stream(path: str, episode_id: str) -> list[Event]:
    with open(path, encoding="utf-8") as f:
        events = [parse_line(line) for line in f.read().splitlines() if line.strip()]
    return [ev for ev in events if ev.episode_id == episode_id]


def _episode_events(episode_id: str) -> tuple[list, str]:
    stream = os.path.join(ROOT, "data", "streams", f"{episode_id}.jsonl")
    if os.path.exists(stream):
        return _read_stream(stream, episode_id), "stream"
    # Streams are gitignored. The fixture holds only P1A-s0007, so a missing B stream used to come back empty.
    twin_a = _twin_a_id(episode_id)
    if twin_a != episode_id:
        a_events, _ = _episode_events(twin_a)
        if a_events:
            # Same event times as A, so B matches A's passive events until the ASK reply
            return [replace(ev, episode_id=episode_id, event_id=f"mock-{ev.event_id}") for ev in a_events], MOCK_B_SOURCE
    return _read_stream(FIXTURE, episode_id), "MOCK fixture"


def _config(name: str):
    with open(os.path.join(ROOT, "engine", "config", name), encoding="utf-8") as f:
        return json.load(f)


def _minute_stats(accepted: list[Event], arrivals: list[Event], belief_rows: list[dict], spec: dict,
                  lam: float) -> list[dict]:
    # Same rules the engine applies at each closure: an event counts only if it arrived before that minute closed.
    # Arrivals come in arrival order, so a repeated event_id is a duplicate the ingest dropped.
    minutes = len(belief_rows)
    cost = _config("cost.json")
    questions = [Question(q["qid"], q["text"], q["p_yes"]) for q in _config("questions.json")]
    text_of = {q.qid: q.text for q in questions}
    # The engine never updates trust during a live run (end_episode is not called), so one value serves every minute
    trust_resp = Trust(spec).mean(RESPONDER_ID)
    seen: set[str] = set()
    duplicates: dict[int, int] = defaultdict(int)
    events_in: dict[int, int] = defaultdict(int)
    for ev in arrivals:
        if ev.event_id in seen:
            duplicates[ev.received_time_s // 60] += 1
        seen.add(ev.event_id)
        if ev.kind != "reply":
            events_in[ev.received_time_s // 60] += 1
    clusters = new_clusters_by_minute([ev for ev in accepted if ev.channel == "citizen"])
    gateways = sorted({ev.gateway_id for ev in accepted if ev.channel == "drain"})

    out = []
    for m in range(minutes):
        known: dict[int, list[Event]] = defaultdict(list)
        for ev in accepted:
            if ev.received_time_s <= closure_instant(m):
                known[ev.event_time_s // 60].append(ev)
        first_minute: dict[str, int] = {}
        for t in sorted(known):
            for ev in known[t]:
                if ev.gateway_id is not None:
                    first_minute.setdefault(ev.gateway_id, t)
        silent = silent_gateways(first_minute, known, m)
        window = [ev for t in (m - 2, m - 1, m) for ev in known.get(t, [])]
        state = {}
        for gw in gateways:
            if gw in silent:
                state[gw] = "UNKNOWN"
                continue
            bins = [bin_index("drain", ev.value, spec["bins"]) for ev in window
                    if ev.channel == "drain" and ev.gateway_id == gw]
            state[gw] = GATEWAY_STATES[max(bins)] if bins else "no reading"
        p = belief_rows[m]["p"]
        best = max(((voi(p, q, lam, cost, trust_resp), q.qid) for q in questions), key=lambda x: x[0])
        out.append({"events_in": events_in.get(m, 0), "duplicates_dropped": duplicates.get(m, 0),
                    "clusters_new": clusters.get(m, 0), "silent_gateways": silent, "gateway_state": state,
                    "corroborating_channels": sorted({ev.channel for ev in window if ev.channel in PASSIVE
                                                      and bin_index(ev.channel, ev.value, spec["bins"]) >= 1}),
                    "voi_best": round(best[0], 3), "voi_question": best[1], "voi_text": text_of[best[1]], "ask_threshold": spec["ask_threshold"]})
    return out


def _payload(episode_id: str, events: list, lam: float, source: str, forget: bool = True,
             ask_enabled: bool = True, demo: bool = False) -> dict:
    if demo:
        # SCRIPTED DEMO: scripted answers, raised reply weight, forced ASK minute. See server/demo.py
        responder = scripted_reply
        belief_rows, decision_rows, arrivals = run_live(events, lam=lam, ask_enabled=True, responder=responder,
                                                        forget=forget, spec_overrides=DEMO_SPEC,
                                                        forced_ask_min=DEMO_ASK_MIN)
    else:
        responder = _responder_for(episode_id, source) if ask_enabled else None
        belief_rows, decision_rows, arrivals = run_live(events, lam=lam, ask_enabled=ask_enabled,
                                                        responder=responder, forget=forget)

    ingestor = Ingestor(REGISTERED_RESPONDERS)
    for ev in arrivals:
        ingestor.push(ev)
    upto = ingestor.closed_upto(max(ev.received_time_s for ev in arrivals))
    spec = load_spec()
    grey = replay(ingestor.buckets(), spec, Trust(spec), PRIOR, upto, grey=True)
    accepted = [ev for evs in ingestor.buckets().values() for ev in evs]
    stats = _minute_stats(accepted, arrivals, belief_rows, spec, lam)

    replies: dict[int, list] = defaultdict(list)
    for ev in arrivals:
        if ev.kind == "reply":
            replies[ev.received_time_s // 60].append({"question_id": ev.question_id, "answer": ev.answer,
                                                      "received_time_s": ev.received_time_s})

    minutes = [{"minute": b["minute"], "belief": b, "decision": d,
                "grey": {"p": {h: round(g.p[h], 4) for h in g.p}}, "replies": replies.get(b["minute"], []),
                "stats": s}
               for b, d, g, s in zip(belief_rows, decision_rows, grey, stats)]
    payload = {"episode_id": episode_id, "lam": lam, "minutes": minutes, "synthetic": True, "source": source,
               "mode": "demo" if demo else "live"}
    if demo:
        payload["demo_label"] = DEMO_LABEL
    return payload


def _to_events(rows: list[dict]) -> list[Event]:
    # Scenario builders return plain dicts with every Event field present; keep only the dataclass fields
    fields = Event.__dataclass_fields__
    return [Event(**{k: v for k, v in row.items() if k in fields}) for row in rows]


def _rumour_events(episode_id: str, at_s: int) -> list[Event]:
    # 400 forwards over 40 s from scenarios/rumour_wave.json (Aditya's file)
    seed = int(episode_id.rsplit("-s", 1)[1])
    return _to_events(build_injection("rumour_wave", episode_id, at_s, seed))


def _clock_events(episode_id: str, at_s: int) -> list[Event]:
    # Heartbeats from a healthy gateway (G1): no evidence, but they keep the clock running past the attack
    return [Event(event_id=f"ev-{episode_id}-hb-{t:05d}", episode_id=episode_id, kind="heartbeat",
                  source_id="hb-G1", gateway_id="G1", event_time_s=t, received_time_s=t, value=None)
            for t in range(0, at_s + 900 + 1, 60)]


def _cutout_events(episode_id: str, at_s: int) -> list[Event]:
    # STAND-IN: scenarios/camera_cutout.json is not on main yet (Pass 3). Traffic readings every 30 s, none during the cut-out.
    out = []
    for t in range(0, at_s + 1200, CUTOUT_OBS_EVERY_S):
        if at_s <= t < at_s + CUTOUT_LEN_S:
            continue
        out.append(Event(event_id=f"ev-{episode_id}-cam-{t:05d}", episode_id=episode_id, kind="observation",
                         channel="traffic", source_id="traffic-T1-001", event_time_s=t, received_time_s=t + 5,
                         value=0.85))
    return out


def _max_step(values: list[float]) -> float:
    return max((abs(b - a) for a, b in zip(values, values[1:])), default=0.0)


def _action_rank(action: str) -> int:
    return ACTIONS.index(action)


def _outage_check(episode_id: str) -> dict:
    # Real scenario: gateway_outage.json silences G3 drain and heartbeat from start_s. Compare the same twin with
    # and without the silence. Forget is OFF and ASK is OFF, so only the silence step differs (12:55 decision).
    events, _ = _episode_events(episode_id)
    with open(os.path.join(ROOT, "scenarios", "gateway_outage.json"), encoding="utf-8") as f:
        sc = json.load(f)
    silenced_rows = apply_silence([asdict(ev) for ev in events], "gateway_outage", episode_id)
    silenced = _to_events(silenced_rows)
    base_belief, base_dec, _ = run_live(events, ask_enabled=False, forget=False)
    sil_belief, sil_dec, _ = run_live(silenced, ask_enabled=False, forget=False)
    onset = sc["start_s"] // 60
    diffs_c = [abs(s["p"]["C"] - b["p"]["C"]) for s, b in zip(sil_belief, base_belief) if s["minute"] >= onset]
    s_rise = max((s["p"]["S"] - b["p"]["S"] for s, b in zip(sil_belief, base_belief) if s["minute"] >= onset), default=0.0)
    actions = [d["action"] for d in sil_dec if d["minute"] >= onset - 1]
    flips = sum(1 for a, b in zip(actions, actions[1:]) if a != b)
    max_dc = max(diffs_c, default=0.0)
    return {"ui": "1 gateway outage · drain sensors UNKNOWN (not all-clear)",
            "checks": {"max_abs_dP_C_vs_no_outage": round(max_dc, 4), "max_P_S_rise": round(s_rise, 4),
                       "flips_after_onset": flips, "pass": max_dc <= 0.001 and flips == 0,
                       "rule": "max |dP(C)| vs the same twin without the outage <= 0.001 and 0 flips (forget OFF)"}}


def _scenario_result(scenario: str, injected: list[Event], payload: dict, at_s: int) -> dict:
    minutes = payload["minutes"]
    onset = at_s // 60
    window = [x for x in minutes if x["minute"] >= onset]
    if scenario == "rumour_wave":
        clusters = sum(new_clusters_by_minute(injected).values())
        max_action = max((x["decision"]["action"] for x in minutes), key=_action_rank)
        passed = clusters == 1 and _action_rank(max_action) <= _action_rank("PREPARE")
        return {"ui": f"{len(injected)} reports · {clusters} cluster{'' if clusters == 1 else 's'} · eff. n ≈ {clusters}",
                "checks": {"reports": len(injected), "clusters": clusters, "max_action": max_action,
                           "pass": passed, "rule": "1 cluster and max action <= PREPARE"}}
    # camera_cutout (stand-in)
    dpc = _max_step([x["belief"]["p"]["C"] for x in window])
    cov = window[0]["belief"]["coverage"] if window else {}
    ok = sum(1 for v in cov.values() if v == "ok")
    return {"ui": f"traffic UNKNOWN · coverage {ok}/6",
            "checks": {"max_step_pC": round(dpc, 4), "coverage_at_onset": f"{ok}/6",
                       "pass": dpc <= 0.05, "rule": "max per-minute |dP(C)| <= 0.05 during the cut-out"}}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(os.path.join(WEB_DIR, "index.html"))


@app.get("/twin")
def twin() -> FileResponse:
    return FileResponse(os.path.join(WEB_DIR, "twin.html"))


@app.get("/ward3d.js")
def ward3d_js() -> FileResponse:
    return FileResponse(os.path.join(WEB_DIR, "ward3d.js"), media_type="application/javascript")


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "mode": "live", "synthetic": True}


@app.get("/api/episodes")
def episodes() -> list[dict]:
    return [
        {"episode_id": "P1A-s0007", "pair": "P1", "role": "A"},
        {"episode_id": "P1B-s0007", "pair": "P1", "role": "B"},
    ]


@app.get("/api/episodes/{episode_id}")
def episode(episode_id: str, lam: float = 1.0, mode: Literal["live", "demo"] = "live") -> dict:
    if mode == "demo":
        path = os.path.join(DEMO_DIR, f"{episode_id}.jsonl")
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="demo streams not built: run python -m server.demo")
        return _payload(episode_id, _read_stream(path, episode_id), lam, "SCRIPTED DEMO streams", demo=True)
    events, source = _episode_events(episode_id)
    if not events:
        return {"episode_id": episode_id, "lam": lam, "minutes": [], "synthetic": True,
                "source": f"no data for {episode_id}: data/streams/{episode_id}.jsonl not found"}
    return _payload(episode_id, events, lam, source)


@app.post("/api/inject")
def inject(req: InjectRequest) -> dict:
    base, _ = _episode_events(req.episode_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"no events for {req.episode_id}")
    if req.scenario == "gateway_outage":
        # Runs on the real twin stream, not a standalone stand-in. at_s is taken from scenarios/gateway_outage.json.
        result = _outage_check(req.episode_id)
        return {"ok": True, "injected": 0, "scenario": req.scenario, "stand_in": False,
                "ui": result["ui"], "checks": result["checks"]}
    if req.scenario == "rumour_wave":
        injected = _rumour_events(req.episode_id, req.at_s)
        stand_in = False
    else:
        injected = _cutout_events(req.episode_id, req.at_s)
        stand_in = True
    # Attacks run on their own, with no flood evidence behind them, so their effect is not mixed with the flood
    run_events = injected + _clock_events(req.episode_id, req.at_s)
    payload = _payload(req.episode_id, run_events, 1.0, f"{req.scenario} standalone (no flood evidence)",
                       ask_enabled=False)
    result = _scenario_result(req.scenario, injected, payload, req.at_s)
    return {"ok": True, "injected": len(injected), "scenario": req.scenario, "stand_in": stand_in,
            "ui": result["ui"], "checks": result["checks"], "trace": {"minutes": payload["minutes"]}}


@app.get("/api/results")
def results() -> dict:
    if not os.path.exists(RESULTS):
        raise HTTPException(status_code=404, detail="no results yet (results/eval_summary.json)")
    with open(RESULTS, encoding="utf-8") as f:
        return json.load(f)
