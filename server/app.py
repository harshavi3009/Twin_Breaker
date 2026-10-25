import json
import os
from collections import defaultdict
from dataclasses import asdict
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from engine.belief import Trust, replay
from engine.decide import ACTIONS
from engine.ingest import Ingestor, new_clusters_by_minute, parse_line
from engine.live import REGISTERED_RESPONDERS, load_spec, run_live
from engine.types import Event
# The server calls the sealed responder as a function (MAIN §8.4). The engine itself never imports generator/.
from generator.responder import reply as sealed_reply
from generator.scenarios import apply_silence, build_injection

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(ROOT, "web")
FIXTURE = os.path.join(ROOT, "engine", "fixtures", "seed7_mock.jsonl")
RESULTS = os.path.join(ROOT, "results", "eval_summary.json")  # MAIN §8.4 contract
PRIOR = {h: 0.25 for h in ("N", "S", "I", "C")}
CUTOUT_LEN_S = 240
CUTOUT_OBS_EVERY_S = 30

app = FastAPI(title="Twin-Breaker (SYNTHETIC)")
app.mount("/vendor", StaticFiles(directory=os.path.join(WEB_DIR, "vendor")), name="vendor")


class InjectRequest(BaseModel):
    episode_id: str
    scenario: Literal["rumour_wave", "gateway_outage", "camera_cutout"]
    at_s: int = 300


def _responder_for(episode_id: str):
    # The sealed responder needs the episode's sealed truth. Without it (fresh clone), ASKs are logged but unanswered.
    truth = os.path.join(ROOT, "generator", "sealed", f"{episode_id}.truth.json")
    return sealed_reply if os.path.exists(truth) else None


def _episode_events(episode_id: str) -> tuple[list, str]:
    stream = os.path.join(ROOT, "data", "streams", f"{episode_id}.jsonl")
    if os.path.exists(stream):
        path, source = stream, "stream"
    else:
        path, source = FIXTURE, "MOCK fixture"
    with open(path, encoding="utf-8") as f:
        events = [parse_line(line) for line in f.read().splitlines() if line.strip()]
    return [ev for ev in events if ev.episode_id == episode_id], source


def _payload(episode_id: str, events: list, lam: float, source: str, forget: bool = True,
             ask_enabled: bool = True) -> dict:
    responder = _responder_for(episode_id) if ask_enabled else None
    belief_rows, decision_rows, arrivals = run_live(events, lam=lam, ask_enabled=ask_enabled,
                                                    responder=responder, forget=forget)

    ingestor = Ingestor(REGISTERED_RESPONDERS)
    for ev in arrivals:
        ingestor.push(ev)
    upto = ingestor.closed_upto(max(ev.received_time_s for ev in arrivals))
    spec = load_spec()
    grey = replay(ingestor.buckets(), spec, Trust(spec), PRIOR, upto, grey=True)

    replies: dict[int, list] = defaultdict(list)
    for ev in arrivals:
        if ev.kind == "reply":
            replies[ev.received_time_s // 60].append({"question_id": ev.question_id, "answer": ev.answer,
                                                      "received_time_s": ev.received_time_s})

    minutes = [{"minute": b["minute"], "belief": b, "decision": d,
                "grey": {"p": {h: round(g.p[h], 4) for h in g.p}}, "replies": replies.get(b["minute"], [])}
               for b, d, g in zip(belief_rows, decision_rows, grey)]
    return {"episode_id": episode_id, "lam": lam, "minutes": minutes, "synthetic": True, "source": source}


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
def episode(episode_id: str, lam: float = 1.0) -> dict:
    events, source = _episode_events(episode_id)
    if not events:
        return {"episode_id": episode_id, "lam": lam, "minutes": [], "synthetic": True,
                "source": "no data for this episode"}
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
