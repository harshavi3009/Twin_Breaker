from collections import Counter, defaultdict
from dataclasses import dataclass, field

import numpy as np

from engine.ingest import new_clusters_by_minute
from engine.types import Event

HYPS = ("N", "S", "I", "C")
PASSIVE = ("rain", "drain", "traffic", "calls", "hospital")
COVERAGE_GROUPS = PASSIVE + ("citizen",)
GREY_R = 0.8
CROWD_BIN_CAP = 2
SILENCE_CAP = 0.10
REASON_COUNT = 3


@dataclass
class Belief:
    minute: int
    p: dict[str, float]
    eff_n: dict[str, float] = field(default_factory=dict)
    coverage: dict[str, str] = field(default_factory=dict)
    reasons: list[dict] = field(default_factory=list)


def bin_index(channel: str, value: float, bins: dict) -> int:
    lo, hi = bins[channel]
    if channel == "traffic":  # speed ratio: high is calm
        return 0 if value >= hi else (1 if value >= lo else 2)
    if channel in ("calls", "hospital"):  # counts: elevated band includes hi
        return 0 if value < lo else (1 if value <= hi else 2)
    return 0 if value < lo else (1 if value < hi else 2)  # rain, drain


class Trust:
    def __init__(self, spec: dict) -> None:
        self._spec = spec
        self._prior = tuple(spec["trust_prior"])
        self._counts: dict[str, list[float]] = {}
        self.reset()

    def reset(self) -> None:
        self._counts = {}

    def _ab(self, source_id: str) -> list[float]:
        if source_id not in self._counts:
            self._counts[source_id] = [float(self._prior[0]), float(self._prior[1])]
        return self._counts[source_id]

    def mean(self, source_id: str) -> float:
        a, b = self._ab(source_id)
        return a / (a + b)

    def end_episode(self, final_label: str, readings: list[Event], decay: float = 0.9) -> None:
        # Label is used only to score sources after the episode; never read truth here
        for counts in self._counts.values():
            counts[0] *= decay
            counts[1] *= decay
        tables, bins = self._spec["tables"], self._spec["bins"]
        for ev in readings:
            if ev.channel not in PASSIVE:
                continue
            col = tables[ev.channel][final_label]
            modal = int(np.argmax(col))
            consistent = bin_index(ev.channel, ev.value, bins) == modal
            counts = self._ab(ev.source_id)
            counts[0 if consistent else 1] += 1


def _mix(table: dict, channel: str, b: int, r: float) -> np.ndarray:
    # P_mix(b|H) = r P(b|H, ch) + (1 - r) / 3
    return np.array([r * table[channel][h][b] + (1 - r) / 3 for h in HYPS])


def _softmax(logp: np.ndarray) -> np.ndarray:
    q = np.exp(logp - logp.max())
    return q / q.sum()


def step(prev: Belief, minute_events: list[Event], spec: dict, trust: Trust,
         prior: dict[str, float], grey: bool = False, new_clusters: int = 0,
         silent: list[str] | tuple = (), forget: bool = True) -> Belief:
    tau = 1.0 if grey else spec["tau"]
    rho = spec["rho"]
    tables, bins = spec["tables"], spec["bins"]
    questions = spec.get("questions", {})

    p = np.array([prev.p[h] for h in HYPS])
    pi = np.array([prior[h] for h in HYPS])
    if not grey and forget:
        # 1. Forget: p <- (1 - eps) p + eps pi (off in the outage check, per the 12:55 decision)
        p = (1 - spec["eps"]) * p + spec["eps"] * pi
    logp = np.log(p)

    # 2. Sensor readings: trust-mixed likelihoods, gateway ESS weights
    gateway_counts = Counter(ev.gateway_id for ev in minute_events if ev.gateway_id is not None)
    citizen_events = [ev for ev in minute_events if ev.channel == "citizen"]
    sensor = []  # (event, bin, likelihood over HYPS, weight)
    for ev in minute_events:
        if ev.channel in PASSIVE:
            b = bin_index(ev.channel, ev.value, bins)
            r = GREY_R if grey else trust.mean(ev.source_id)
            k = gateway_counts[ev.gateway_id] if ev.gateway_id is not None else 1
            w = 1.0 if grey else 1.0 / (1.0 + (k - 1) * rho)
            sensor.append((ev, b, _mix(tables, ev.channel, b, r), w))
    if grey:
        for ev in citizen_events:
            sensor.append((ev, CROWD_BIN_CAP, _mix(tables, "citizen", CROWD_BIN_CAP, GREY_R), 1.0))
    elif citizen_events:
        # One crowd vote per minute: bin = min(2, new clusters this minute)
        b = min(CROWD_BIN_CAP, new_clusters)
        sensor.append((citizen_events[0], b, _mix(tables, "citizen", b, spec["crowd_r"]), 1.0))
    for _, _, lik, w in sensor:
        logp = logp + tau * w * np.log(lik)
    p = _softmax(logp)

    # 4. Silent gateway: no likelihood; move delta of N to S per silent minute
    if not grey:
        n, s = HYPS.index("N"), HYPS.index("S")
        for _ in silent:
            delta = min(SILENCE_CAP, 0.5 * p[n])
            p[n] -= delta
            p[s] += delta

    # 5. Reply: P(yes|H) = r p_yes(H) + (1 - r) 0.5, tau applied as for sensors
    if not grey:
        for ev in minute_events:
            if ev.kind != "reply" or ev.question_id not in questions:
                continue
            r = trust.mean(ev.source_id)
            py = questions[ev.question_id]
            p_yes = np.array([r * py[h] + (1 - r) * 0.5 for h in HYPS])
            lik = p_yes if ev.answer == "yes" else 1 - p_yes
            p = p * lik ** tau
    p = p / p.sum()

    # 6. Reason bits: tau w log2(P_mix(b|top) / P_mix(b|second)), top 3 by |bits|
    top, second = np.argsort(p)[::-1][:2]
    reasons = []
    for ev, b, lik, w in sensor:
        bits = tau * w * np.log2(lik[top] / lik[second])
        if ev.channel == "citizen":
            text = f"citizen reports, {new_clusters} new cluster(s)"
        else:
            text = f"{ev.channel} reading, bin {b}"
        reasons.append({"event_id": ev.event_id, "bits": round(float(bits), 3), "text": text})
    reasons.sort(key=lambda r: abs(r["bits"]), reverse=True)

    eff_n = {f"gw-{gw}": k / (1 + (k - 1) * rho) for gw, k in gateway_counts.items()}
    return Belief(minute=prev.minute + 1, p={h: float(v) for h, v in zip(HYPS, p)},
                  eff_n=eff_n, reasons=reasons[:REASON_COUNT])


def silent_gateways(first_minute: dict[str, int], per_minute: dict[int, list[Event]], m: int) -> list[str]:
    # Silent in minute m: seen before, no gateway event this minute, no heartbeat in m-1 or m
    now, before = per_minute.get(m, []), per_minute.get(m - 1, [])
    silent = []
    for gw, first in sorted(first_minute.items()):
        if first > m or first == m:
            continue
        if any(ev.gateway_id == gw for ev in now):
            continue
        if any(ev.kind == "heartbeat" and ev.gateway_id == gw for ev in before + now):
            continue
        silent.append(gw)
    return silent


def replay(buckets: dict[int, list[Event]], spec: dict, trust: Trust, prior: dict[str, float],
           upto_min: int, grey: bool = False, forget: bool = True) -> list[Belief]:
    per_minute: dict[int, list[Event]] = defaultdict(list)
    for t, events in buckets.items():
        per_minute[t // 60].extend(events)

    citizen = [ev for events in buckets.values() for ev in events if ev.channel == "citizen"]
    clusters = new_clusters_by_minute(citizen)

    first_minute: dict[str, int] = {}
    for m in sorted(per_minute):
        for ev in per_minute[m]:
            if ev.gateway_id is not None:
                first_minute.setdefault(ev.gateway_id, m)

    prev = Belief(minute=-1, p=dict(prior))
    out = []
    for m in range(upto_min + 1):
        events = per_minute.get(m, [])
        silent = [] if grey else silent_gateways(first_minute, per_minute, m)
        prev = step(prev, events, spec, trust, prior, grey=grey,
                    new_clusters=clusters.get(m, 0), silent=silent, forget=forget)
        recent = per_minute.get(m, []) + per_minute.get(m - 1, [])
        seen = {ev.channel for ev in recent}
        prev.coverage = {ch: ("ok" if ch in seen else "unknown") for ch in COVERAGE_GROUPS}
        out.append(prev)
    return out
