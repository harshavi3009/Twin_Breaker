import itertools
import json
import os

import pytest

from engine.belief import HYPS, Belief, Trust, step
from engine.ingest import jaccard, new_clusters_by_minute, shingles
from engine.types import Event

SPEC_PATH = os.path.join(os.path.dirname(__file__), "..", "engine", "config", "belief_spec.json")
UNIFORM = {h: 0.25 for h in HYPS}

BASE_RUMOUR = "Ambazari lake wall has breached and the underpass is flooding now"
# One extra word at the front or back keeps every pair at Jaccard >= 0.8 on 3-word shingles
RUMOUR_PHRASINGS = [BASE_RUMOUR + " " + w for w in ("urgent", "share", "confirmed", "breaking", "pls", "omg")] + \
                   [w + " " + BASE_RUMOUR for w in ("forward", "urgent", "alert", "news", "breaking", "video")]


def load_spec() -> dict:
    with open(SPEC_PATH, encoding="utf-8") as f:
        return json.load(f)


def citizen(idx: int, text: str, t: int) -> Event:
    return Event(event_id=f"ev-c-{idx:03d}", episode_id="P1A-s0007", kind="citizen", source_id=f"phone-{idx}",
                 event_time_s=t, received_time_s=t + 5, value=None, channel="citizen", text=text,
                 text_hash=f"hash-{idx}")


def test_silence_moves_n_to_s_only():
    spec = load_spec()
    spec["eps"] = 0.0  # forget step OFF: this checks the silence step alone
    prev = Belief(minute=0, p={"N": 0.35, "S": 0.15, "I": 0.10, "C": 0.40})

    out = step(prev, [], spec, Trust(spec), UNIFORM, silent=["G3"])

    assert out.p["N"] == pytest.approx(0.25)
    assert out.p["S"] == pytest.approx(0.25)
    assert out.p["I"] == pytest.approx(0.10)
    assert out.p["C"] == pytest.approx(0.40)
    assert abs(out.p["C"] - prev.p["C"]) <= 0.001


def test_twelve_phrasings_form_one_cluster():
    phrasings = RUMOUR_PHRASINGS
    assert len(phrasings) == 12
    for a, b in itertools.combinations(phrasings, 2):
        assert jaccard(shingles(a), shingles(b)) >= 0.8, (a, b)

    events = [citizen(i, text, 300 + 3 * i) for i, text in enumerate(phrasings)]  # inside 40 s
    counts = new_clusters_by_minute(events)

    assert sum(counts.values()) == 1
    assert counts == {5: 1}


def test_trust_reset_restores_prior():
    spec = load_spec()
    trust = Trust(spec)
    reading = Event(event_id="ev-d-1", episode_id="P1A-s0007", kind="observation", source_id="drain-G2-031",
                    event_time_s=60, received_time_s=90, value=0.9, channel="drain", gateway_id="G2")
    prior_mean = trust.mean("drain-G2-031")

    trust.end_episode("C", [reading])
    assert trust.mean("drain-G2-031") > prior_mean

    trust.reset()
    assert trust.mean("drain-G2-031") == pytest.approx(prior_mean)
