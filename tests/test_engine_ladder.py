import json
import os

import pytest

from engine.decide import ACTIONS, Question, decide, expected_costs, voi

CONFIG = os.path.join(os.path.dirname(__file__), "..", "engine", "config")


def load(name: str):
    with open(os.path.join(CONFIG, name), encoding="utf-8") as f:
        return json.load(f)


COST = load("cost.json")
HYST = load("hyst.json")
QUESTIONS = [Question(q["qid"], q["text"], q["p_yes"]) for q in load("questions.json")]


def belief_with_c(c: float) -> dict[str, float]:
    # I = 0, so N and S split the rest evenly; with I = 0 the ladder depends only on P(C)
    return {"N": (1 - c) / 2, "S": (1 - c) / 2, "I": 0.0, "C": c}


def cheapest(c: float) -> str:
    losses = expected_costs(belief_with_c(c), 1.0, COST)
    return min(ACTIONS, key=lambda a: losses[a])


def test_cost_table_matches_section_8_5():
    table = {
        "WATCH":    [0.0, 0.0, 15.0, 100.0],
        "PREPARE":  [2.0, 2.0, 12.5, 72.0],
        "ALERT":    [15.0, 15.0, 11.0, 45.0],
        "ESCALATE": [28.0, 28.0, 11.0, 28.0],
    }
    for action, row in table.items():
        for h, expected in zip("NSIC", row):
            point = {x: float(x == h) for x in "NSIC"}
            assert expected_costs(point, 1.0, COST)[action] == pytest.approx(expected)


@pytest.mark.parametrize("c, expected", [
    (0.05, "WATCH"),      # below the PREPARE threshold (~0.067)
    (0.10, "PREPARE"),    # between ~0.067 and ~0.325
    (0.30, "PREPARE"),
    (0.35, "ALERT"),      # between ~0.325 and ~0.433
    (0.40, "ALERT"),
    (0.45, "ESCALATE"),   # above ~0.433
])
def test_ladder_points_on_each_side(c, expected):
    assert cheapest(c) == expected


def test_ladder_thresholds_are_exact():
    # Break-even points: 2/30, 13/40, 13/30
    assert cheapest(2 / 30 - 0.001) == "WATCH"
    assert cheapest(2 / 30 + 0.001) == "PREPARE"
    assert cheapest(13 / 40 - 0.001) == "PREPARE"
    assert cheapest(13 / 40 + 0.001) == "ALERT"
    assert cheapest(13 / 30 - 0.001) == "ALERT"
    assert cheapest(13 / 30 + 0.001) == "ESCALATE"


def test_corroboration_caps_candidate_at_prepare():
    p = belief_with_c(0.9)
    capped = decide(p, "WATCH", 5, 10, 1.0, COST, HYST, [], 0, None, 0.8, corroborated=False)
    free = decide(p, "WATCH", 5, 10, 1.0, COST, HYST, [], 0, None, 0.8, corroborated=True)
    assert capped.candidate == "PREPARE"
    assert free.candidate == "ESCALATE"
    assert free.action == "ESCALATE"


def test_upward_hysteresis_boundary():
    # Moving WATCH -> PREPARE needs a cost gain above h_up = 1.0
    below = decide(belief_with_c(0.099), "WATCH", 5, 10, 1.0, COST, HYST, [], 0, None, 0.8, True)
    above = decide(belief_with_c(0.102), "WATCH", 5, 10, 1.0, COST, HYST, [], 0, None, 0.8, True)
    assert below.candidate == "PREPARE" and below.action == "WATCH"
    assert above.action == "PREPARE" and above.changed


def test_minimum_dwell_blocks_early_move():
    p = belief_with_c(0.5)
    early = decide(p, "WATCH", 2, 10, 1.0, COST, HYST, [], 0, None, 0.8, True)
    ready = decide(p, "WATCH", 3, 10, 1.0, COST, HYST, [], 0, None, 0.8, True)
    assert early.action == "WATCH"
    assert ready.action == "ESCALATE"


def test_downward_hysteresis_is_stricter():
    # Moving PREPARE -> WATCH needs a gain above h_down = 2.0; the gain here is 1.4
    p = belief_with_c(0.02)
    d = decide(p, "PREPARE", 3, 10, 1.0, COST, HYST, [], 0, None, 0.8, True)
    assert d.candidate == "WATCH"
    assert d.action == "PREPARE"
    assert not d.changed


def test_asking_is_not_worth_it_when_certain():
    certain = {"N": 0.0, "S": 0.0, "I": 0.0, "C": 1.0}
    assert voi(certain, QUESTIONS[0], 1.0, COST, 0.8) == pytest.approx(-0.7)
    d = decide(certain, "ESCALATE", 5, 10, 1.0, COST, HYST, QUESTIONS, 0, None, 0.8, True)
    assert d.ask is None


def test_ask_fires_when_ambiguous_and_respects_limits():
    ambiguous = {"N": 0.3, "S": 0.2, "I": 0.2, "C": 0.3}
    fired = decide(ambiguous, "WATCH", 5, 10, 1.0, COST, HYST, QUESTIONS, 0, None, 0.8, True)
    no_questions = decide(ambiguous, "WATCH", 5, 10, 1.0, COST, HYST, [], 0, None, 0.8, True)
    assert fired.ask is not None and fired.ask["question_id"] == "Q1"
    assert fired.action == no_questions.action  # ASK never changes the action by itself

    maxed = decide(ambiguous, "WATCH", 5, 10, 1.0, COST, HYST, QUESTIONS, 3, None, 0.8, True)
    too_soon = decide(ambiguous, "WATCH", 5, 10, 1.0, COST, HYST, QUESTIONS, 1, 9, 0.8, True)
    assert maxed.ask is None
    assert too_soon.ask is None
