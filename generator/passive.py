import hashlib

import numpy as np

from generator.latent import Latent
from generator.rng import channel_rng, text_hash


ALL_KEYS = (
    "event_id", "episode_id", "kind", "channel", "source_id",
    "gateway_id", "event_time_s", "received_time_s", "value",
    "text", "text_hash", "question_id", "answer", "retracts",
)


def _make_dict(episode: str, seed: int, kind: str, channel, source_id,
               gateway_id: str | None, event_time_s: float, value=None,
               text=None, **extra) -> dict:
    eid = f"ev-s{seed:04d}-{(channel or kind)}-m{int(event_time_s):03d}-{source_id}"
    d = {k: None for k in ALL_KEYS}
    d["event_id"] = eid
    d["episode_id"] = episode
    d["kind"] = kind
    d["channel"] = channel
    d["source_id"] = source_id
    d["gateway_id"] = gateway_id
    d["event_time_s"] = event_time_s
    d["received_time_s"] = int(extra.get("received", event_time_s))
    d["value"] = value
    d["text"] = text
    if "text" in extra or extra.get("_th") is not None:
        d["text_hash"] = extra.get("_th", "")
    d["question_id"] = None
    d["answer"] = None
    d["retracts"] = []
    return d


def minute_events(episode: str, seed: int, minute: int, latent: Latent,
                  world: dict) -> list[dict]:
    d_val = latent.depth_cm[minute]
    rx = latent.rain_extra_mm_h[minute]
    cap = world["cascade"]["cap_cm"]
    nz = world["noise"]
    gws = world["gateways"]
    n_drain = world["drain_sensors_total"]  # 100

    events: list[dict] = []

    # RAIN
    rng = channel_rng(seed, "rain", minute)
    z = rng.standard_t(nz["t_df"], size=2)
    value = round(max(0.0, world["rain"]["base_mm_h"] + nz["rain_scale_mm_h"] * z[0] + rx), 2)
    delay = min(90, int(abs(z[1]) * nz["delay_scale_s"]))
    ets = minute * 60 + 30
    events.append(_make_dict(episode, seed, "observation", "rain",
                             "rain-G1-001", "G1", ets, value, received=ets + delay))

    # DRAINS
    rng = channel_rng(seed, "drain", minute)
    z = rng.standard_t(nz["t_df"], size=(n_drain, 2))
    for i in range(n_drain):
        gw = gws[i % len(gws)]
        source = f"drain-{gw}-{i+1:03d}"
        value = round(min(1.0, max(0.0, world["drain"]["base_fill"] + world["drain"]["per_cm_fill"] * d_val + nz["drain_scale"] * z[i, 0])), 3)
        delay = min(90, int(abs(z[i, 1]) * nz["delay_scale_s"]))
        events.append(_make_dict(episode, seed, "observation", "drain",
                                 source, gw, ets, value, received=ets + delay))

    # CITIZEN
    rng = channel = channel_rng(seed, "citizen", minute)
    u = rng.random(3)
    idx = rng.integers(0, 3, size=3)
    dl = rng.integers(0, 91, size=3)
    crates = world["citizen"]
    base_rate = crates["base_rate"]
    cascade_rate = crates["cascade_rate"]
    texts_list = crates["texts"]
    for k in range(3):
        p = base_rate if d_val <= 0 else base_rate + (cascade_rate - base_rate) * min(1.0, d_val / cap)
        if u[k] < p:
            text = texts_list[int(idx[k])]
            source = "phone-" + hashlib.sha1(f"{seed}-{k}".encode()).hexdigest()[:4]
            th = text_hash(text)
            ets2 = minute * 60 + 40
            events.append(_make_dict(episode, seed, "citizen", "citizen",
                                     source, None, ets2, text=text, _th=th, received=int(ets2 + dl[k])))

    # HEARTBEATS
    for gw in gws:
        src = f"gw-{gw}"
        eh = minute * 60
        events.append(_make_dict(episode, seed, "heartbeat", None,
                                 src, gw, eh))

    return events
