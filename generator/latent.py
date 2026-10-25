"""Synthetic episode latent structure."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from generator.rng import episode_rng


@dataclass(frozen=True)
class Latent:
    episode: str
    hypothesis: str
    pair: str | None
    role: str | None
    onset_min: int | None
    depth_cm: list[float] = field(default_factory=list)
    rain_extra_mm_h: list[float] = field(default_factory=list)
    stuck_drain_from: int | None = None


def parse_episode(episode: str) -> tuple[str, str | None, str | None, int]:
    m = re.fullmatch(r'(N|C|I|S|P[1-3][AB])-s(\d{4})', episode)
    if not m:
        raise ValueError(f'bad episode {episode}')
    code = m.group(1)
    seed = int(m.group(2))
    if code in ('N', 'C', 'I', 'S'):
        return (code, None, None, seed)
    pair = code[:2]
    role = code[2]
    hyp = 'C' if role == 'A' else 'N'
    return (hyp, pair, role, seed)


def make_latent(seed: int, episode: str, world: dict) -> Latent:
    hyp, pair, role, parsed_seed = parse_episode(episode)
    if parsed_seed != seed:
        raise ValueError('seed mismatch')

    T = world['episode_minutes']
    zeros = [0.0] * T

    if hyp == 'C' and role in ('A', None):
        key = f'{pair or "C"}:onset'
        lo, hi = world['cascade']['onset_min']
        onset = int(episode_rng(seed, key).integers(lo, hi + 1))
        cap = world['cascade']['cap_cm']
        slope = world['cascade']['slope_cm_per_min']
        depth = [0.0 if m < onset else min(cap, slope * (m - onset + 1)) for m in range(T)]
        return Latent(episode, hyp, pair, role, onset, depth, zeros[:], None)

    if role == 'B':
        start = world['storm']['start_min']
        ramp_min_val = world['storm']['ramp_min']
        peak_cm = world['storm']['peak_cm']
        peak_mm = world['storm']['rain_peak_mm_h']
        depth: list[float] = []
        rain: list[float] = []
        for m in range(T):
            if m < start:
                depth.append(0.0)
                rain.append(0.0)
            else:
                r = min(1.0, (m - start + 1) / ramp_min_val)
                depth.append(peak_cm * r)
                rain.append(peak_mm * r)
        return Latent(episode, hyp, pair, role, None, depth, rain, None)

    if hyp == 'I':
        lo, hi = world['shallow']['onset_min']
        onset = int(episode_rng(seed, 'I:onset').integers(lo, hi + 1))
        hold = world['shallow']['hold_min']
        peak = world['shallow']['peak_cm']
        depth = [peak if onset <= m < onset + hold else 0.0 for m in range(T)]
        return Latent(episode, 'I', None, None, onset, depth, zeros[:], None)

    if hyp == 'S':
        stuck = world.get('sensor_fail', {}).get('start_min')
        return Latent(episode, 'S', None, None, None, zeros[:], zeros[:], stuck)

    # N with no role
    return Latent(episode, 'N', None, None, None, zeros[:], zeros[:], None)
