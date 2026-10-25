from collections import Counter, defaultdict
from dataclasses import dataclass, field

import numpy as np

from engine.types import Event

HYPS = ("N", "S", "I", "C")
PASSIVE = ("rain", "drain", "traffic", "calls", "hospital")
COVERAGE_GROUPS = PASSIVE + ("citizen",)
GREY_R = 0.8
CROWD_BIN_CAP = 2


@dataclass
class Belief:
    minute: int
    p: dict[str, float]
    eff_n: dict[str, float] = field(default_factory=dict)
    coverage: dict[str, str] = field(default_factory=dict)


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


def step(prev: Belief, minute_events: list[Event], spec: dict, trust: Trust,
         prior: dict[str, float], grey: bool = False) -> Belief:
    tau = 1.0 if grey else spec["tau"]
    rho = spec["rho"]
    tables, bins = spec["tables"], spec["bins"]
    questions = spec.get("questions", {})

    logp = np.log(np.array([prev.p[h] for h in HYPS]))
    pi = np.array([prior[h] for h in HYPS])
    if not grey:
        # Forget step: p <- (1 - eps) p + eps pi
        p = (1 - spec["eps"]) * np.exp(logp) + spec["eps"] * pi
        logp = np.log(p)

    gateway_counts = Counter(ev.gateway_id for ev in minute_events if ev.gateway_id is not None)
    citizen_count = sum(1 for ev in minute_events if ev.channel == "citizen")

    for ev in minute_events:
        if ev.channel in PASSIVE:
            b = bin_index(ev.channel, ev.value, bins)
            r = GREY_R if grey else trust.mean(ev.source_id)
            k = gateway_counts[ev.gateway_id] if ev.gateway_id is not None else 1
            w = 1.0 if grey else 1.0 / (1.0 + (k - 1) * rho)
            lik = np.array([r * tables[ev.channel][h][b] + (1 - r) / 3 for h in HYPS])
        elif ev.channel == "citizen":
            # Placeholder bin until clustering (P5): min(2, reports this minute)
            b = CROWD_BIN_CAP if grey else min(CROWD_BIN_CAP, citizen_count)
            r = GREY_R if grey else spec["crowd_r"]
            w = 1.0
            lik = np.array([r * tables["citizen"][h][b] + (1 - r) / 3 for h in HYPS])
        elif ev.kind == "reply" and not grey and ev.question_id in questions:
            r = trust.mean(ev.source_id)
            py = questions[ev.question_id]
            p_yes = np.array([r * py[h] + (1 - r) * 0.5 for h in HYPS])
            lik = p_yes if ev.answer == "yes" else 1 - p_yes
            w = 1.0
        else:
            continue
        logp = logp + tau * w * np.log(lik)

    post = np.exp(logp - logp.max())
    post = post / post.sum()

    eff_n = {f"gw-{gw}": k / (1 + (k - 1) * rho) for gw, k in gateway_counts.items()}

    return Belief(minute=prev.minute + 1, p={h: float(v) for h, v in zip(HYPS, post)}, eff_n=eff_n)


def replay(buckets: dict[int, list[Event]], spec: dict, trust: Trust, prior: dict[str, float],
           upto_min: int, grey: bool = False) -> list[Belief]:
    per_minute: dict[int, list[Event]] = defaultdict(list)
    for t, events in buckets.items():
        per_minute[t // 60].extend(events)

    prev = Belief(minute=-1, p=dict(prior))
    out = []
    for m in range(upto_min + 1):
        prev = step(prev, per_minute.get(m, []), spec, trust, prior, grey=grey)
        recent = per_minute.get(m, []) + per_minute.get(m - 1, [])
        seen = {ev.channel for ev in recent}
        prev.coverage = {ch: ("ok" if ch in seen else "unknown") for ch in COVERAGE_GROUPS}
        out.append(prev)
    return out
