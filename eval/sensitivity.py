"""VOI constant sensitivity sweep (mock or engine)."""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from generator.gen import episodes_for, parse_seeds


def _minutes_mock(ep: str) -> list[dict]:
    data = json.loads(Path('tests/fixtures/mock_minutes.json').read_text())
    return [{'minute': d['minute'], 'p': d['p'], 'action': d['action'],
             'ask': d.get('ask')} for d in data]


def run_sensitivity(seeds: list[int],
                    values: tuple[float, ...] = (0.5, 0.7, 0.9),
                    mock: bool = True) -> list[dict]:
    from eval.collect import episode_record

    rows: list[dict] = []
    for v in values:
        records: list[dict] = []
        asks: list[bool] = []
        for seed in seeds:
            for ep in episodes_for('B', 'dev', seed):
                truth = json.loads(
                    Path('generator/sealed', f'{ep}.truth.json').read_text()
                )
                minutes = _minutes_mock(ep) if mock else []
                records.append(episode_record(ep, truth, minutes))
                asks.append(any(m.get('ask') for m in minutes))
        row = {
            'voi_const': v,
            'brier_C_mean': round(statistics.mean(r['brier_C'] for r in records), 4),
            'lead_median': statistics.median([r['lead_min'] for r in records if r['lead_min'] is not None])
                            if any(r['lead_min'] is not None for r in records) else None,
            'flips_mean': round(statistics.mean(r['flips'] for r in records), 3),
            'ask_fired': sum(asks),
        }
        rows.append(row)
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='VOI constant sensitivity sweep')
    parser.add_argument('--seeds', type=str, required=True)
    parser.add_argument('--mock', action='store_true')
    args = parser.parse_args(argv)
    rows = run_sensitivity(parse_seeds(args.seeds), mock=args.mock)
    out = Path('results/dev/sensitivity.json')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=2))
    for row in rows:
        print(row)
    return 0


if __name__ == '__main__':
    main()
