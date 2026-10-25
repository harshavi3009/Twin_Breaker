import sys

# MOCK: stands in for the simulated responder until its real module lands (card 14)


def reply(episode_id: str, question_id: str, asked_at_s: int) -> dict:
    print("MOCK RESPONDER", file=sys.stderr)
    return {"answer": "yes" if "P1A" in episode_id else "no", "responder_id": "marshal-W9-01", "delay_s": 55}
