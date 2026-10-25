import heapq
import json
import os

from engine.belief import HYPS, PASSIVE, Trust, bin_index, replay
from engine.decide import Question, decide
from engine.ingest import GRACE_S, Ingestor
from engine.run import REGISTERED_RESPONDERS, load_spec
from engine.types import Event
from server.responder_mock import reply as mock_reply

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine", "config")
PRIOR = {h: 1.0 / len(HYPS) for h in HYPS}
RESPONDER_ID = "marshal-W9-01"


def _load(name: str):
    with open(os.path.join(CONFIG_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def closure_instant(minute: int) -> int:
    # Minute m is closed once the clock reaches (m + 1) * 60 + grace (same rule as Ingestor.closed_upto)
    return (minute + 1) * 60 + GRACE_S


def corroborated(buckets: dict, spec: dict, m: int) -> bool:
    # A passive channel at bin >= elevated in the last 3 minutes (m-2 .. m)
    for t, events in buckets.items():
        if not (m - 2 <= t // 60 <= m):
            continue
        for ev in events:
            if ev.channel in PASSIVE and bin_index(ev.channel, ev.value, spec["bins"]) >= 1:
                return True
    return False


class LiveEpisode:
    def __init__(self, episode_id: str, lam: float, ask_enabled: bool, responder) -> None:
        self.episode_id = episode_id
        self.lam = lam
        self.ask_enabled = ask_enabled
        self.responder = responder
        self.spec = load_spec()
        self.cost = _load("cost.json")
        self.hyst = _load("hyst.json")
        self.questions = [Question(q["qid"], q["text"], q["p_yes"]) for q in _load("questions.json")]
        self.ingestor = Ingestor(REGISTERED_RESPONDERS)
        self.trust = Trust(self.spec)
        self.heap: list = []
        self.closed = -1
        self.prev_action = "WATCH"
        self.minutes_in_action = 0
        self.asks = 0
        self.last_ask_min: int | None = None
        self.belief_rows: list[dict] = []
        self.decision_rows: list[dict] = []

    def close_next(self) -> None:
        # Close the next minute: belief from what has arrived so far, then the decision
        self.closed += 1
        m = self.closed
        buckets = self.ingestor.buckets()
        b = replay(buckets, self.spec, self.trust, PRIOR, m)[-1]
        d = decide(b.p, self.prev_action, self.minutes_in_action, m, self.lam, self.cost, self.hyst,
                   self.questions, self.asks, self.last_ask_min, self.trust.mean(RESPONDER_ID),
                   corroborated(buckets, self.spec, m), ask_threshold=self.spec["ask_threshold"])

        self.minutes_in_action = 1 if d.action != self.prev_action else self.minutes_in_action + 1
        self.prev_action = d.action
        self.belief_rows.append({"episode_id": self.episode_id, "minute": m,
                                 "p": {h: round(b.p[h], 4) for h in HYPS}, "coverage": b.coverage})
        self.decision_rows.append({"episode_id": self.episode_id, "minute": m, "action": d.action,
                                   "candidate": d.candidate, "changed": d.changed, "ask": d.ask,
                                   "expected_cost": {a: round(v, 3) for a, v in d.expected_cost.items()}})
        if d.ask and self.ask_enabled:
            self._ask(m, d.ask)

    def _ask(self, m: int, ask: dict) -> None:
        self.asks += 1
        self.last_ask_min = m
        asked_at = closure_instant(m)
        answer = self.responder(self.episode_id, ask["question_id"], asked_at)
        received = asked_at + answer["delay_s"]
        # The reply is stamped with its arrival time, so it can only affect minutes not yet closed
        ev = Event(event_id=f"ev-{self.episode_id}-ask{self.asks:03d}", episode_id=self.episode_id,
                   kind="reply", source_id=answer["responder_id"], event_time_s=received,
                   received_time_s=received, value=None, channel="reply",
                   question_id=ask["question_id"], answer=answer["answer"])
        heapq.heappush(self.heap, (received, ev.event_id, ev))


def run_live(events: list[Event], lam: float = 1.0, ask_enabled: bool = True,
             responder=mock_reply) -> tuple[list[dict], list[dict], list[Event]]:
    # Replays the episode as a clock: arrivals and minute closures happen in time order.
    # Returns belief rows, decision rows, and every event that arrived (including replies).
    if not events:
        return [], [], []
    ep = LiveEpisode(events[0].episode_id, lam, ask_enabled, responder)
    ep.heap = [(ev.received_time_s, ev.event_id, ev) for ev in events]
    heapq.heapify(ep.heap)

    arrivals: list[Event] = []
    last_t = 0
    while True:
        if ep.heap and closure_instant(ep.closed + 1) <= ep.heap[0][0]:
            ep.close_next()
            continue
        if ep.heap:
            t, _, ev = heapq.heappop(ep.heap)
            last_t = max(last_t, t)
            ep.ingestor.push(ev)
            arrivals.append(ev)
            continue
        if ep.ingestor.closed_upto(last_t) > ep.closed:
            ep.close_next()
            continue
        break
    return ep.belief_rows, ep.decision_rows, arrivals
