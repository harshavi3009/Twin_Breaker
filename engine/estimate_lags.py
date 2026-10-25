import argparse
import glob
import json
import os
import re

import numpy as np

from engine.ingest import parse_line

MAX_LAG = 15
WINDOW_HALF = 2
DEV_SEEDS = range(1, 11)
SEED_RE = re.compile(r"-s(\d{4})\.jsonl$")
DEFAULT_STREAMS = os.path.join("data", "streams")
DEFAULT_OUT = os.path.join("engine", "config", "lags.json")


def dev_files(streams_dir: str) -> list[str]:
    files = []
    for path in sorted(glob.glob(os.path.join(streams_dir, "*.jsonl"))):
        match = SEED_RE.search(os.path.basename(path))
        if match and int(match.group(1)) in DEV_SEEDS:
            files.append(path)
    return files


def minute_means(path: str, channel: str) -> dict[int, float]:
    # Mean observed value per minute for one channel; no truth data is read
    sums: dict[int, float] = {}
    counts: dict[int, int] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            ev = parse_line(line)
            if ev.kind != "observation" or ev.channel != channel:
                continue
            minute = ev.event_time_s // 60
            sums[minute] = sums.get(minute, 0.0) + ev.value
            counts[minute] = counts.get(minute, 0) + 1
    return {m: sums[m] / counts[m] for m in sums}


def pearson(x: list[float], y: list[float]) -> float:
    if len(x) < 3 or np.std(x) == 0 or np.std(y) == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def estimate(streams_dir: str) -> tuple[list[tuple[int, int, float]], int]:
    pairs_by_lag: dict[int, tuple[list[float], list[float]]] = {L: ([], []) for L in range(MAX_LAG + 1)}
    files = dev_files(streams_dir)
    if not files:
        raise SystemExit(f"no DEV seed 1-10 stream files in {streams_dir}")
    for path in files:
        rain = minute_means(path, "rain")
        drain = minute_means(path, "drain")
        for lag in range(MAX_LAG + 1):
            xs, ys = pairs_by_lag[lag]
            for t, r in rain.items():
                if t + lag in drain:
                    xs.append(r)
                    ys.append(drain[t + lag])

    table = []
    for lag in range(MAX_LAG + 1):
        xs, ys = pairs_by_lag[lag]
        table.append((lag, len(xs), pearson(xs, ys)))
    valid = [row for row in table if not np.isnan(row[2])]
    if not valid:
        raise SystemExit("no lag has a usable correlation")
    best_lag = max(valid, key=lambda row: row[2])[0]
    return table, best_lag


def main() -> None:
    parser = argparse.ArgumentParser(description="Estimate rain-to-drain lag from DEV seeds 1-10 (no truth).")
    parser.add_argument("--streams-dir", default=DEFAULT_STREAMS)
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args()

    table, best = estimate(args.streams_dir)
    print("lag_min  pairs  pearson_r")
    for lag, n, r in table:
        marker = "  <- best" if lag == best else ""
        print(f"{lag:7d}  {n:5d}  {r:9.4f}{marker}")

    window = [max(1, best - WINDOW_HALF), best + WINDOW_HALF]
    config = {"rain>drain": {"lag_min": best, "window_min": window, "method": "lagged_corr_DEV_1_10"}}
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.write("\n")
    print(f"wrote {args.out}: lag_min={best} window_min={window}")


if __name__ == "__main__":
    main()
