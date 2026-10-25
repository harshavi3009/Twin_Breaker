from dataclasses import dataclass

ACTIONS = ("WATCH", "PREPARE", "ALERT", "ESCALATE")
HYPS = ("N", "S", "I", "C")
CAPPED_ACTIONS = ("ALERT", "ESCALATE")
MAX_ASKS = 3
MIN_ASK_GAP_MIN = 3
# Hand-set prior weight for the cost of asking (0.5 + 0.2 * 1.0); the plan does not explain it
ASK_COST = 0.5 + 0.2 * 1.0


@dataclass
class Question:
    qid: str
    text: str
    p_yes: dict[str, float]  # assumed response model


@dataclass
class Decision:
    minute: int
    action: str
    candidate: str
    changed: bool
    ask: dict | None
    expected_cost: dict[str, float]


def expected_costs(p: dict[str, float], lam: float, cost: dict) -> dict[str, float]:
    # L[a, H] = c_a + d_H (1 - m_a) + lam f_a 1[H in {N, S}]
    out = {}
    for a in ACTIONS:
        total = 0.0
        for h in HYPS:
            loss = cost["c"][a] + cost["d"][h] * (1 - cost["m"][a])
            if a in cost["f"] and h in ("N", "S"):
                loss += lam * cost["f"][a]
            total += p[h] * loss
        out[a] = total
    return out


def voi(p: dict[str, float], q: Question, lam: float, cost: dict, trust_resp: float) -> float:
    # VOI = min_a E[L] - (ASK_COST + sum_r P(r) min_a E[L | r])
    base = min(expected_costs(p, lam, cost).values())
    p_yes_h = {h: trust_resp * q.p_yes[h] + (1 - trust_resp) * 0.5 for h in HYPS}
    after = 0.0
    for answer in ("yes", "no"):
        like = {h: p_yes_h[h] if answer == "yes" else 1 - p_yes_h[h] for h in HYPS}
        p_answer = sum(p[h] * like[h] for h in HYPS)
        if p_answer <= 0:
            continue
        posterior = {h: p[h] * like[h] / p_answer for h in HYPS}
        after += p_answer * min(expected_costs(posterior, lam, cost).values())
    return base - (ASK_COST + after)


def decide(p, prev_action: str, minutes_in_action: int, minute: int, lam: float, cost: dict, hyst: dict,
           questions: list[Question], asks_so_far: int, last_ask_min: int | None, trust_resp: float,
           corroborated: bool, ask_threshold: float = 0.3) -> Decision:
    losses = expected_costs(p, lam, cost)

    # Candidate is the cheapest action, capped at PREPARE without a passive corroboration
    candidate = min(ACTIONS, key=lambda a: losses[a])
    if not corroborated and candidate in CAPPED_ACTIONS:
        candidate = "PREPARE"

    # Hysteresis with minimum dwell: a move needs its cost gain to beat h
    action = prev_action
    if candidate != prev_action and minutes_in_action >= hyst["dwell_min"]:
        moving_up = ACTIONS.index(candidate) > ACTIONS.index(prev_action)
        h = hyst["h_up"] if moving_up else hyst["h_down"]
        if losses[prev_action] - losses[candidate] > h:
            action = candidate

    # ASK never changes the action; it only proposes a question
    best_q, best_voi = None, None
    for q in questions:
        v = voi(p, q, lam, cost, trust_resp)
        if best_voi is None or v > best_voi:
            best_q, best_voi = q, v
    ask = None
    gap_ok = last_ask_min is None or minute - last_ask_min >= MIN_ASK_GAP_MIN
    if best_q is not None and best_voi > ask_threshold and asks_so_far < MAX_ASKS and gap_ok:
        ask = {"question_id": best_q.qid, "text": best_q.text, "voi_net": round(best_voi, 3)}

    return Decision(minute=minute, action=action, candidate=candidate, changed=action != prev_action,
                    ask=ask, expected_cost=losses)
