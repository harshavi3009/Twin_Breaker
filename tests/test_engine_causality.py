import json
import os

import pytest

from engine.belief import Trust, replay
from engine.ingest import Ingestor, parse_line
from engine.live import REGISTERED_RESPONDERS, load_spec
from engine.types import Event
from engine.live import run_live
from generator.responder import reply

ROOT = os.path.join(os.path.dirname(__file__), "..")
FIXTURE = os.path.join(ROOT, "engine", "fixtures", "seed7_mock.jsonl")
PRIOR = {h: 0.25 for h in "NSIC"}


def fixture_events() -> list[Event]:
    with open(FIXTURE, encoding="utf-8") as f:
        return [parse_line(line) for line in f.read().splitlines() if line.strip()]


def batch_beliefs(events: list[Event], upto: int):
    ingestor = Ingestor(REGISTERED_RESPONDERS)
    for ev in events:
        ingestor.push(ev)
    return replay(ingestor.buckets(), load_spec(), Trust(load_spec()), PRIOR, upto)


def test_reply_cannot_change_minutes_closed_before_it_arrives():
    arrive_at = 400
    late_reply = Event(event_id="ev-P1A-s0007-test-reply", episode_id="P1A-s0007", kind="reply",
                       source_id="marshal-W9-01", event_time_s=arrive_at, received_time_s=arrive_at,
                       value=None, channel="reply", question_id="Q1", answer="no")
    base = fixture_events()
    horizon = 7

    without = batch_beliefs(base, horizon)
    with_reply = batch_beliefs(base + [late_reply], horizon)

    closed_before = Ingestor(REGISTERED_RESPONDERS).closed_upto(arrive_at)  # minutes closed at arrival (4)
    for m in range(closed_before + 1):
        assert with_reply[m].p == pytest.approx(without[m].p), f"minute {m} changed by a reply that arrived later"
    assert with_reply[horizon].p != pytest.approx(without[horizon].p), "the reply should move later minutes"


def test_reply_arriving_after_its_minute_closed_is_rejected():
    ingestor = Ingestor(REGISTERED_RESPONDERS)
    stale = Event(event_id="ev-P1A-s0007-stale", episode_id="P1A-s0007", kind="reply",
                  source_id="marshal-W9-01", event_time_s=60, received_time_s=500,
                  value=None, channel="reply", question_id="Q1", answer="yes")
    assert ingestor.push(stale) is False
    assert ingestor.dropped_late == 1


def test_live_loop_and_batch_replay_agree_including_asks():
    belief_rows, decision_rows, arrivals = run_live(fixture_events(), responder=reply)

    asked = [d for d in decision_rows if d["ask"] is not None]
    replies = [ev for ev in arrivals if ev.kind == "reply" and ev.event_id not in
               {e.event_id for e in fixture_events()}]
    assert asked, "the loop should ask at least once on this fixture"
    assert replies, "the mock responder's answers should arrive as reply events"

    ingestor = Ingestor(REGISTERED_RESPONDERS)
    for ev in arrivals:
        ingestor.push(ev)
    upto = ingestor.closed_upto(max(ev.received_time_s for ev in arrivals))
    batch = replay(ingestor.buckets(), load_spec(), Trust(load_spec()), PRIOR, upto)

    assert len(belief_rows) == upto + 1
    for row in belief_rows:
        expected = {h: round(batch[row["minute"]].p[h], 4) for h in "NSIC"}
        assert row["p"] == expected, f"minute {row['minute']} differs between live and batch"
