import re
from dataclasses import dataclass

from generator.rng import episode_rng


@dataclass(frozen=True)
class Latent:
    episode: str
    hypothesis: str
    pair: str | None
    role: str | None
    onset_min: int | None
    depth_cm: list[float]
    rain_extra_mm_h: list[float]


def parse_episode(episode: str) -> tuple[str, str | None, str | None, int]:
    m = re.fullmatch(r"(N|C|P[1-3][AB])-s(\d{4})", episode)
    if not m:
        raise ValueError(f"bad episode {episode}")
    prefix = m.group(1)
    seed = int(m.group(2))
    if prefix == "N":
        return ("N", None, None, seed)
    if prefix == "C":
        return ("C", None, None, seed)
    pair_num = prefix[1:-1]  # strip N/C/P and the role letter
    role = prefix[-1]
    hyp = "C" if role == "A" else "N"
    return (hyp, f"P{pair_num}", role, seed)


def make_latent(seed: int, episode: str, world: dict) -> Latent:
    hyp, pair, role, parsed_seed = parse_episode(episode)
    if parsed_seed != seed:
        raise ValueError("seed mismatch")

    T = world["episode_minutes"]

    if hyp == "C":
        key = f"{pair or 'C'}:onset"
        lo, hi = world["cascade"]["onset_min"]
        onset = int(episode_rng(seed, key).integers(lo, hi + 1))
        slope = world["cascade"]["slope_cm_per_min"]
        cap = world["cascade"]["cap_cm"]
        depth: list[float] = []
        rain: list[float] = [0.0] * T
        for m in range(T):
            d = 0.0 if m < onset else min(cap, slope * (m - onset + 1))
            depth.append(d)
        return Latent(episode, hyp, pair, role, onset, depth, rain)

    elif role == "B":
        start = world["storm"]["start_min"]
        ramp_min_val = world["storm"]["ramp_min"]
        peak_cm = world["storm"]["peak_cm"]
        peak_mm = world["storm"]["rain_peak_mm_h"]
        depth: list[float] = []
        rain: list[float] = []
        for m in range(T):
            if m < start:
                depth.append(0.0)
                rain.append(0.0)
            else:
                ramp = min(1.0, (m - start + 1) / ramp_min_val)
                depth.append(peak_cm * ramp)
                rain.append(peak_mm * ramp)
        return Latent(episode, hyp, pair, role, None, depth, rain)

    else:
        return Latent(episode, hyp, pair, role, None, [0.0] * T, [0.0] * T)
