import argparse
import json
import os
import time

from engine import belief, decide
from engine.belief import HYPS, Trust
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


def read_lines(episode_id: str) -> list[str]:
    path = os.path.join("data", "streams", f"{episode_id}.jsonl")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return [line for line in f.read().splitlines() if line.strip()]
    print(f"MOCK INPUT: {path} not found, using {FIXTURE}")
    with open(FIXTURE, encoding="utf-8") as f:
        lines = [line for line in f.read().splitlines() if line.strip()]
    return [line for line in lines if parse_line(line).episode_id == episode_id]


def run_role(episode_id: str, role: str, spec: dict, prior: dict[str, float]) -> None:
    lines = read_lines(episode_id)
    if not lines:
        print(f"no input for {episode_id}, skipped")
        return

    events = [parse_line(line) for line in lines]
    ingestor = Ingestor(REGISTERED_RESPONDERS)
    for ev in events:
        ingestor.push(ev)
    latest_received = max(ev.received_time_s for ev in events)
    upto = ingestor.closed_upto(latest_received)
    if upto < 0:
        print(f"role={role} no minute closed yet")
        return

    buckets = ingestor.buckets()
    ours = belief.replay(buckets, spec, Trust(spec), prior, upto)
    grey = belief.replay(buckets, spec, Trust(spec), prior, upto, grey=True)
    for o, g in zip(ours, grey):
        action = decide.stub_action(o.minute)
        print(f"role={role} minute={o.minute} P(C) ours={o.p['C']:.3f} P(C) grey={g.p['C']:.3f} action={action}")
    print(f"role={role} dropped_late={ingestor.dropped_late}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Twin-Breaker engine on a twin pair (SYNTHETIC data).")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--split", default="dev")
    args = parser.parse_args()

    started = time.time()
    print(f"SYNTHETIC. seed={args.seed} split={args.split}")
    spec = load_spec()
    prior = {h: 1.0 / len(HYPS) for h in HYPS}
    for episode_prefix, role in PAIR_ROLES:
        run_role(f"{episode_prefix}-s{args.seed:04d}", role, spec, prior)
    print(f"elapsed={time.time() - started:.2f}s")


if __name__ == "__main__":
    main()
