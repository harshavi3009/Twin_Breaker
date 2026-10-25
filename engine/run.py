import argparse
import json
import os
import sys
import time

from engine.belief import HYPS, Trust, replay
from engine.ingest import Ingestor, parse_line
from engine.live import PRIOR, REGISTERED_RESPONDERS, load_spec, run_live  # noqa: F401 (load_spec, REGISTERED_RESPONDERS re-exported)

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "fixtures", "seed7_mock.jsonl")
PAIR_ROLES = (("P1A", "A"), ("P1B", "B"))
GREY_ALERT_LINE = 0.7  # naive baseline: ALERT iff naive P(C) >= 0.7 (MAIN §8.5)


def _read_events(jsonl_path: str, episode_id: str | None):
    with open(jsonl_path, encoding="utf-8") as f:
        events = [parse_line(line) for line in f.read().splitlines() if line.strip()]
    if episode_id is not None:
        events = [ev for ev in events if ev.episode_id == episode_id]
    return events


def _grey_rows(events, lam: float, ask_enabled: bool) -> list[dict]:
    # Naive baseline: same tables with r = 0.8, no hysteresis, no ASK. Row shapes match the live path.
    spec = load_spec()
    ingestor = Ingestor(REGISTERED_RESPONDERS)
    for ev in events:
        ingestor.push(ev)
    upto = ingestor.closed_upto(max(ev.received_time_s for ev in events))
    beliefs = replay(ingestor.buckets(), spec, Trust(spec), PRIOR, upto, grey=True)
    rows = []
    for b in beliefs:
        action = "ALERT" if b.p["C"] >= GREY_ALERT_LINE else "WATCH"
        rows.append({"episode_id": events[0].episode_id, "minute": b.minute,
                     "p": {h: round(b.p[h], 4) for h in HYPS}, "eff_n": {k: round(v, 3) for k, v in b.eff_n.items()},
                     "coverage": b.coverage, "trust": {}, "synthetic": True})
        rows.append({"episode_id": events[0].episode_id, "minute": b.minute, "action": action, "candidate": action,
                     "changed": False, "ask": None, "expected_cost": None, "reason": b.reasons, "foresight": [],
                     "lam": lam, "ask_enabled": ask_enabled, "grey": True, "synthetic": True})
    return rows


def run_episode(jsonl_path: str, lam: float = 1.0, ask_enabled: bool = True, grey: bool = False,
                episode_id: str | None = None, responder=None) -> list[dict]:
    # One belief row and one decision row per closed minute (MAIN §8.2 shapes).
    # responder: callable(episode_id, question_id, asked_at_s) -> {"answer", "responder_id", "delay_s"}.
    # The engine has no access to ground truth; the caller passes any responder in. With responder=None, ASKs are logged but not answered.
    events = _read_events(jsonl_path, episode_id)
    if not events:
        return []
    if grey:
        return _grey_rows(events, lam, ask_enabled)
    belief_rows, decision_rows, _ = run_live(events, lam=lam, ask_enabled=ask_enabled, responder=responder)
    rows = []
    for b, d in zip(belief_rows, decision_rows):
        rows.append(b)
        rows.append(d)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Twin-Breaker engine on a twin pair (SYNTHETIC data).")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--split", default="dev")
    args = parser.parse_args()

    started = time.time()
    for episode_prefix, _ in PAIR_ROLES:
        episode_id = f"{episode_prefix}-s{args.seed:04d}"
        path = os.path.join("data", "streams", f"{episode_id}.jsonl")
        if os.path.exists(path):
            rows = run_episode(path)
        else:
            # Mock input goes to stderr so stdout stays pure JSON lines
            print(f"MOCK INPUT: {path} not found, using {FIXTURE}", file=sys.stderr)
            rows = run_episode(FIXTURE, episode_id=episode_id)
        if not rows:
            print(f"no input for {episode_id}, skipped", file=sys.stderr)
        for row in rows:
            print(json.dumps(row))
    print(f"elapsed={time.time() - started:.2f}s", file=sys.stderr)


if __name__ == "__main__":
    main()
