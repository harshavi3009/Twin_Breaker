from dataclasses import dataclass


@dataclass(frozen=True)
class Event:
    event_id: str; episode_id: str; kind: str; source_id: str
    event_time_s: int; received_time_s: int; value: float | None
    channel: str | None = None; gateway_id: str | None = None
    text_hash: str | None = None; text: str | None = None
    question_id: str | None = None; answer: str | None = None; retracts: str | None = None
