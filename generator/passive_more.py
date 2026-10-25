"""Passive event channels with lagged response: traffic, calls, hospital."""
from __future__ import annotations

import hashlib

import numpy as np

from generator.latent import Latent
from generator.rng import channel_rng, episode_rng


def lagged(depth: list[float], minute: int, lag: int) -> float:
    return depth[max(0, minute - lag)]


def _lag(seed: int, latent: Latent, world: dict, name: str) -> int:
    lo, hi = world['lags_min'][name]
    key = f"{latent.pair or 'C'}:lag:{name}"
    return int(episode_rng(seed, key).integers(lo, hi + 1))


def _ev(episode: str, seed: int, minute: int, kind: str, channel=None, source_id='', gateway_id=None, event_time_s=0, delay=0, value=None):
    d = {k: None for k in (
        "event_id", "episode_id", "kind", "channel", "source_id",
        "gateway_id", "event_time_s", "received_time_s", "value",
        "text", "text_hash", "question_id", "answer", "retracts",
    )}
    d['event_id'] = f"ev-s{seed:04d}-{(channel or kind)}-m{minute:03d}-{source_id}"
    d['episode_id'] = episode
    d['kind'] = kind
    d['channel'] = channel
    d['source_id'] = source_id
    d['gateway_id'] = gateway_id
    d['event_time_s'] = event_time_s
    d['received_time_s'] = event_time_s + delay
    d['value'] = value
    return d


def more_events(episode: str, seed: int, minute: int, latent: Latent, world: dict) -> list[dict]:
    cap = world['cascade']['cap_cm']

    # TRAFFIC
    lag_t = _lag(seed, latent, world, 'drain_to_traffic')
    d = lagged(latent.depth_cm, minute, lag_t)
    rng = channel_rng(seed, 'traffic', minute)
    z = float(rng.standard_normal())
    value = round(min(1.5, max(0.0, 1.0 - world['traffic']['slow_gain'] * min(1.0, d / cap) + 0.05 * z)), 2)
    delay = min(90, int(abs(float(rng.standard_normal())) * 10))
    traffic = _ev(episode, seed, minute, 'observation', 'traffic', 'traffic-G1-01', 'G1', minute*60+30, delay, value)

    # CALLS
    lag_c = _lag(seed, latent, world, 'traffic_to_calls')
    d_c = lagged(latent.depth_cm, minute, lag_c)
    rng_c = channel_rng(seed, 'calls', minute)
    lam = world['calls']['base_per_min'] + world['calls']['gain_per_min'] * min(1.0, d_c / cap)
    n = int(rng_c.poisson(lam))
    calls = []
    if n > 0:
        calls.append(_ev(episode, seed, minute, 'dispatch', 'calls', 'dispatch-W9', None, minute*60+20, 0, float(n)))

    # HOSPITAL
    lag_h = _lag(seed, latent, world, 'calls_to_hospital')
    d_h = lagged(latent.depth_cm, minute, lag_h)
    rng_h = channel_rng(seed, 'hospital', minute)
    lam_h = world['hospital']['base_per_min'] + world['hospital']['gain_per_min'] * min(1.0, d_h / cap)
    n_h = int(rng_h.poisson(lam_h))
    hospital = []
    if n_h > 0:
        hospital.append(_ev(episode, seed, minute, 'hospital', 'hospital', 'hosp-H1', None, minute*60+50, 0, float(n_h)))

    return [traffic] + calls + hospital
