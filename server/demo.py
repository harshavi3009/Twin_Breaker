"""SCRIPTED DEMO for the twin test. Not measured results; not used by DEV or EVAL.

- Streams: data/demo/P1{A,B}-s0007.jsonl, built by build_streams() with the depth overrides in DEMO_WORLD.
- Answers: the marshal's reply is scripted per twin (DEMO_ANSWERS), not read from the sealed truth.
- Engine: reply_weight is raised so one officer's answer can outweigh the correlated sensors (DEMO_SPEC).
- ASK: Q1 is asked at DEMO_ASK_MIN for both twins.
"""
from __future__ import annotations

import json
import os

from generator.latent import make_latent
from generator.passive import minute_events
from generator.passive_more import more_events

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO_DIR = os.path.join(ROOT, "data", "demo")
SEED = 7
EPISODES = ("P1A-s0007", "P1B-s0007")
DEMO_ANSWERS = {"P1A-s0007": "yes", "P1B-s0007": "no"}
DEMO_ASK_MIN = 7
DEMO_SPEC = {"reply_weight": 16.0}
# Both twins above 20 cm by minute 7 (the responder threshold); A is the cascade, B the false alarm
DEMO_WORLD = {"cascade": {"onset_min": [2, 2], "slope_cm_per_min": 5.0},
              "storm": {"start_min": 2, "ramp_min": 3}}
DEMO_LABEL = "SCRIPTED DEMO: officer answers are scripted and reply weight is raised (16). Not a measured result."


def _world() -> dict:
    with open(os.path.join(ROOT, "generator", "world_spec.json"), encoding="utf-8") as f:
        spec = json.load(f)
    return {**spec, **{k: {**spec[k], **v} for k, v in DEMO_WORLD.items()}}


def build_streams(out_dir: str = DEMO_DIR) -> None:
    os.makedirs(out_dir, exist_ok=True)
    world = _world()
    for ep in EPISODES:
        latent = make_latent(SEED, ep, world)
        events: list[dict] = []
        for m in range(world["episode_minutes"]):
            events.extend(minute_events(ep, SEED, m, latent, world))
            events.extend(more_events(ep, SEED, m, latent, world))
        events.sort(key=lambda e: (e["event_time_s"], e["event_id"]))
        with open(os.path.join(out_dir, f"{ep}.jsonl"), "w", encoding="utf-8") as f:
            for e in events:
                f.write(json.dumps(e) + "\n")


def scripted_reply(episode_id: str, question_id: str, asked_at_s: int) -> dict:
    # Twin A's marshal says yes, twin B's says no. Scripted, so it does not read sealed truth.
    return {"answer": DEMO_ANSWERS[episode_id], "responder_id": "marshal-W9-01", "delay_s": 60}


if __name__ == "__main__":
    build_streams()
    print("wrote", DEMO_DIR)
