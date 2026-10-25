import dataclasses
import json

from engine.types import Event

BASE_FIELDS = ("event_id", "episode_id", "kind", "source_id", "event_time_s", "received_time_s", "value")

# Per kind: allowed channels (empty = no channel) and extra required fields (section 8.1)
KINDS = {
    "observation": {"channels": ("rain", "drain", "traffic"), "required": ("gateway_id",)},
    "dispatch": {"channels": ("calls",), "required": ()},
    "hospital": {"channels": ("hospital",), "required": ()},
    "citizen": {"channels": ("citizen",), "required": ("text", "text_hash")},
    "reply": {"channels": ("reply",), "required": ("question_id", "answer")},
    "heartbeat": {"channels": (), "required": ("gateway_id",)},
    "retraction": {"channels": (), "required": ("retracts",)},
}

GRACE_S = 90


def parse_line(line: str) -> Event:
    try:
        raw = json.loads(line)
    except (json.JSONDecodeError, TypeError) as err:
        raise ValueError(f"bad JSON: {err}") from err
    if not isinstance(raw, dict):
        raise ValueError("line is not a JSON object")

    kind = raw.get("kind")
    if kind not in KINDS:
        raise ValueError(f"unknown kind: {kind!r}")
    rule = KINDS[kind]

    missing = [f for f in BASE_FIELDS + rule["required"] if f not in raw]
    if missing:
        raise ValueError(f"{kind} event missing fields: {missing}")
    if rule["channels"] and raw.get("channel") not in rule["channels"]:
        raise ValueError(f"{kind} event has bad channel: {raw.get('channel')!r}")
    if kind == "reply" and raw["answer"] not in ("yes", "no"):
        raise ValueError(f"reply answer must be yes or no: {raw['answer']!r}")
    if not isinstance(raw["event_time_s"], int) or not isinstance(raw["received_time_s"], int):
        raise ValueError("event_time_s and received_time_s must be integers")
    if raw["received_time_s"] < raw["event_time_s"]:
        raise ValueError("received_time_s is before event_time_s")

    names = {f.name for f in dataclasses.fields(Event)}
    return Event(**{k: v for k, v in raw.items() if k in names})


class Ingestor:
    def __init__(self, registered_responders: set[str]) -> None:
        self._registered = set(registered_responders)
        self._seen: set[str] = set()
        self._retracted: set[str] = set()
        self._accepted: dict[str, Event] = {}
        self.dropped_late = 0

    def push(self, ev: Event) -> bool:
        if ev.event_id in self._seen:
            return False
        if ev.kind == "retraction":
            # Retractions are always accepted so a late one can still remove its target
            self._seen.add(ev.event_id)
            if ev.retracts in self._retracted:
                return False
            self._retracted.add(ev.retracts)
            self._accepted.pop(ev.retracts, None)
            return True
        if ev.event_id in self._retracted:
            return False
        if ev.kind == "reply" and ev.source_id not in self._registered:
            return False
        if ev.kind != "heartbeat" and ev.event_time_s // 60 <= self.closed_upto(ev.received_time_s):
            self.dropped_late += 1
            return False
        self._seen.add(ev.event_id)
        self._accepted[ev.event_id] = ev
        return True

    def buckets(self) -> dict[int, list[Event]]:
        out: dict[int, list[Event]] = {}
        for ev in self._accepted.values():
            out.setdefault(ev.event_time_s, []).append(ev)
        return out

    def closed_upto(self, now_s: int) -> int:
        # Last minute m with now_s >= (m + 1) * 60 + GRACE_S
        return (now_s - GRACE_S) // 60 - 1
