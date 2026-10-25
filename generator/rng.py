import hashlib
import re

import numpy


CHANNEL_IDS: dict[str, int] = {
    "rain": 1,
    "drain": 2,
    "citizen": 3,
    "heartbeat": 4,
    "traffic": 5,
    "calls": 6,
    "hospital": 7,
    "reply": 8,
    "episode": 9,
}


def channel_rng(seed: int, channel: str, minute: int) -> numpy.random.Generator:
    if channel not in CHANNEL_IDS:
        raise ValueError(f"unknown channel {channel}")
    if minute < 0:
        raise ValueError("minute must be >= 0")
    return numpy.random.default_rng([seed, CHANNEL_IDS[channel], minute])


def episode_rng(seed: int, key: str) -> numpy.random.Generator:
    return numpy.random.default_rng(
        [
            seed,
            CHANNEL_IDS["episode"],
            int(hashlib.sha1(key.encode()).hexdigest()[:8], 16),
        ]
    )


def normalise_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def text_hash(text: str) -> str:
    return hashlib.sha1(normalise_text(text).encode()).hexdigest()[:6]
