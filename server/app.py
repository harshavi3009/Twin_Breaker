import os
from collections import defaultdict
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from engine.belief import Trust, replay
from engine.decide import ACTIONS
from engine.ingest import Ingestor, new_clusters_by_minute, parse_line
from engine.run import REGISTERED_RESPONDERS, load_spec
from engine.types import Event
from server.live import run_live

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(ROOT, "web")
FIXTURE = os.path.join(ROOT, "engine", "fixtures", "seed7_mock.jsonl")
PRIOR = {h: 0.25 for h in ("N", "S", "I", "C")}

# STAND-IN attacks built from plan section 4. Aditya's scenarios/*.json are not on the remote yet.
RUMOUR_PHRASINGS = [
    "Ambazari lake wall has breached and the underpass is flooding now urgent",
    "Ambazari lake wall has breached and the underpass is flooding now share",
    "Ambazari lake wall has breached and the underpass is flooding now confirmed",
    "Ambazari lake wall has breached and the underpass is flooding now breaking",
    "Ambazari lake wall has breached and the underpass is flooding now pls",
    "Ambazari lake wall has breached and the underpass is flooding now omg",
    "forward Ambazari lake wall has breached and the underpass is flooding now",
    "urgent Ambazari lake wall has breached and the underpass is flooding now",
    "alert Ambazari lake wall has breached and the underpass is flooding now",
    "news Ambazari lake wall has breached and the underpass is flooding now",
    "breaking Ambazari lake wall has breached and the underpass is flooding now",
    "video Ambazari lake wall has breached and the underpass is flooding now",
]
RUMOUR_REPORTS = 400
OUTAGE_READINGS = 100
CUTOUT_LEN_S = 240

app = FastAPI(title="Twin-Breaker (SYNTHETIC)")
app.mount("/vendor", StaticFiles(directory=os.path.join(WEB_DIR, "vendor")), name="vendor")


class InjectRequest(BaseModel):
    episode_id: str
    scenario: Literal["rumour_wave", "gateway_outage", "camera_cutout"]
    at_s: int = 300


def _episode_events(episode_id: str) -> tuple[list, str]:
    stream = os.path.join(ROOT, "data", "streams", f"{episode_id}.jsonl")
    if os.path.exists(stream):
        path, source = stream, "stream"
    else:
        path, source = FIXTURE, "MOCK fixture"
    with open(path, encoding="utf-8") as f:
        events = [parse_line(line) for line in f.read().splitlines() if line.strip()]
    return [ev for ev in events if ev.episode_id == episode_id], source


def _payload(episode_id: str, events: list, lam: float, source: str) -> dict:
    belief_rows, decision_rows, arrivals = run_live(events, lam=lam)

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


def _rumour_events(episode_id: str, at_s: int) -> list[Event]:
    out = []
    for i in range(RUMOUR_REPORTS):
        t = at_s + (i * 40) // RUMOUR_REPORTS  # 400 forwards over 40 s
        out.append(Event(event_id=f"ev-{episode_id}-rumour-{i:03d}", episode_id=episode_id, kind="citizen",
                         source_id=f"phone-r{i:03d}", event_time_s=t, received_time_s=t + 5, value=None,
                         channel="citizen", text=RUMOUR_PHRASINGS[i % len(RUMOUR_PHRASINGS)],
                         text_hash=f"rumour-{i % len(RUMOUR_PHRASINGS)}"))
    return out


def _outage_events(episode_id: str, at_s: int) -> list[Event]:
    # 100 drain readings from gateway G3, all before at_s; after that G3 is silent
    out = []
    for i in range(OUTAGE_READINGS):
        t = (i * at_s) // OUTAGE_READINGS
        out.append(Event(event_id=f"ev-{episode_id}-g3-{i:03d}", episode_id=episode_id, kind="observation",
                         channel="drain", source_id="drain-G3-001", gateway_id="G3", event_time_s=t,
                         received_time_s=t + 5, value=0.3))
    return out


def _cutout_events(episode_id: str, at_s: int) -> list[Event]:
    # Traffic readings every 30 s, none during the 4-minute cut-out (no gateway id: cameras are not gated)
    out = []
    for t in range(0, at_s + 1200, 30):
        if at_s <= t < at_s + CUTOUT_LEN_S:
            continue
        out.append(Event(event_id=f"ev-{episode_id}-cam-{t:05d}", episode_id=episode_id, kind="observation",
                         channel="traffic", source_id="traffic-T1-001", event_time_s=t, received_time_s=t + 5,
                         value=0.85))
    return out


def _clock_events(episode_id: str, at_s: int) -> list[Event]:
    # Heartbeats from a healthy gateway (G1): no evidence, but they keep the clock running past the attack
    return [Event(event_id=f"ev-{episode_id}-hb-{t:05d}", episode_id=episode_id, kind="heartbeat",
                  source_id="hb-G1", gateway_id="G1", event_time_s=t, received_time_s=t, value=None)
            for t in range(0, at_s + 900 + 1, 60)]


def _max_step(values: list[float]) -> float:
    return max((abs(b - a) for a, b in zip(values, values[1:])), default=0.0)


def _action_rank(action: str) -> int:
    return ACTIONS.index(action)


def _scenario_result(scenario: str, episode_id: str, at_s: int, payload: dict, injected: list[Event]) -> dict:
    minutes = payload["minutes"]
    onset = at_s // 60
    window = [x for x in minutes if x["minute"] >= onset]
    pc = [x["belief"]["p"]["C"] for x in minutes]
    if scenario == "rumour_wave":
        rumour = [e for e in injected if e.event_id.startswith(f"ev-{episode_id}-rumour-")]
        clusters = sum(new_clusters_by_minute(rumour).values())
        max_action = max((x["decision"]["action"] for x in minutes), key=_action_rank)
        passed = clusters == 1 and _action_rank(max_action) <= _action_rank("PREPARE")
        return {"ui": f"{len(rumour)} reports · {clusters} cluster{'' if clusters == 1 else 's'} · eff. n ≈ {clusters}",
                "checks": {"reports": len(rumour), "clusters": clusters, "max_action": max_action,
                           "pass": passed, "rule": "1 cluster and max action <= PREPARE"}}
    if scenario == "gateway_outage":
        dpc = _max_step([x["belief"]["p"]["C"] for x in minutes if x["minute"] >= onset - 1])
        actions = [x["decision"]["action"] for x in minutes if x["minute"] >= onset - 1]
        flips = sum(1 for a, b in zip(actions, actions[1:]) if a != b)
        return {"ui": "1 gateway outage · drain sensors UNKNOWN (not all-clear)",
                "checks": {"max_step_pC": round(dpc, 4), "flips_after_onset": flips,
                           "pass": dpc <= 0.001 and flips == 0,
                           "rule": "max per-minute |dP(C)| <= 0.001 and 0 flips (forget step is ON)"}}
    # camera_cutout
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
    builders = {"rumour_wave": _rumour_events, "gateway_outage": _outage_events, "camera_cutout": _cutout_events}
    injected = builders[req.scenario](req.episode_id, req.at_s)
    # Each attack runs on its own, with no flood evidence behind it, so its effect is not mixed with the flood
    run_events = injected + _clock_events(req.episode_id, req.at_s)
    payload = _payload(req.episode_id, run_events, 1.0, f"{req.scenario} standalone (no flood evidence)")
    result = _scenario_result(req.scenario, req.episode_id, req.at_s, payload, injected)
    return {"ok": True, "injected": len(injected), "scenario": req.scenario, "stand_in": True,
            "ui": result["ui"], "checks": result["checks"], "trace": {"minutes": payload["minutes"]}}
