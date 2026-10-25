import argparse
import json
import os
import sys
import time
from collections import defaultdict

from engine import belief, decide
from engine.belief import HYPS, PASSIVE, Trust
from engine.ingest import Ingestor, parse_line

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(HERE, "config")
FIXTURE = os.path.join(HERE, "fixtures", "seed7_mock.jsonl")
REGISTERED_RESPONDERS = {"marshal-W9-01"}
PAIR_ROLES = (("P1A", "A"), ("P1B", "B"))


def load_spec() -> dict:
    with open(os.path.join(CONFIG_DIR, "belief_spec.json"), encoding="utf-8") as f:
        spec = json.load(f)
    with open(os.path.join(CONFIG_DIR, "questions.json"), encoding="utf-8") as f:
        questions = json.load(f)
    spec["questions"] = {q["qid"]: q["p_yes"] for q in questions}
    return spec


def run_episode(jsonl_path: str, lam: float = 1.0, ask_enabled: bool = True, grey: bool = False,
                episode_id: str | None = None) -> list[dict]:
    # Returns one belief dict and one decision dict per closed minute (section 8.2 shapes)
    with open(jsonl_path, encoding="utf-8") as f:
        events = [parse_line(line) for line in f.read().splitlines() if line.strip()]
    if episode_id is not None:
        events = [ev for ev in events if ev.episode_id == episode_id]
    if not events:
        return []

    ingestor = Ingestor(REGISTERED_RESPONDERS)
    for ev in events:
        ingestor.push(ev)
    upto = ingestor.closed_upto(max(ev.received_time_s for ev in events))
    if upto < 0:
        return []

    spec = load_spec()
    prior = {h: 1.0 / len(HYPS) for h in HYPS}
    buckets = ingestor.buckets()
    trust = Trust(spec)
    beliefs = belief.replay(buckets, spec, trust, prior, upto, grey=grey)

    per_minute: dict[int, list] = defaultdict(list)
    for t, evs in buckets.items():
        per_minute[t // 60].extend(evs)

    rows = []
    for b in beliefs:
        sources = sorted({ev.source_id for ev in per_minute.get(b.minute, [])
                          if ev.channel in PASSIVE or ev.kind == "reply"})
        rows.append({
            "episode_id": events[0].episode_id,
            "minute": b.minute,
            "p": {h: round(v, 4) for h, v in b.p.items()},
            "eff_n": {k: round(v, 3) for k, v in b.eff_n.items()},
            "coverage": b.coverage,
            "trust": {s: round(trust.mean(s), 4) for s in sources},
            "synthetic": True,
        })
        rows.append({
            "episode_id": events[0].episode_id,
            "minute": b.minute,
            "action": decide.stub_action(b.minute),
            "candidate": decide.stub_action(b.minute),
            "changed": False,
            "minutes_in_action": b.minute + 1,
            "expected_cost": None,
            "ask": None,
            "reason": b.reasons,
            "foresight": [],
            "lam": lam,
            "ask_enabled": ask_enabled,
            "stub": True,
            "synthetic": True,
        })
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
