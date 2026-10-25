"""DEV table runner – runs seeds through engine (or mock), writes summary."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from generator.gen import episodes_for, parse_seeds
from eval.collect import episode_record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--world', required=True)
    parser.add_argument('--split', required=True)
    parser.add_argument('--seeds', required=True)
    parser.add_argument('--out', default='results/dev/')
    parser.add_argument('--mock', action='store_true')
    args = parser.parse_args(argv)

    records = []
    for seed in parse_seeds(args.seeds):
        for ep in episodes_for(args.world, args.split, seed):
            truth_path = Path('generator/sealed') / f'{ep}.truth.json'
            if not truth_path.exists():
                print(f"run the generator first: {truth_path}")
                return 1
            truth = json.loads(truth_path.read_text())

            if args.mock:
                mock_data = json.loads(Path('tests/fixtures/mock_minutes.json').read_text())
                minutes = [{'minute': d['minute'], 'p': d['p'], 'action': d['action']}
                           for d in mock_data]
                # reassign episode_id for each minute to match ep
                for m in minutes:
                    m.setdefault('_episode', ep)
            else:
                from engine.run import run_episode
                raw = run_episode(f'data/streams/{ep}.jsonl', lam=1.0, ask_enabled=True, grey=False)
                # run_episode emits a belief row (has 'p') and a decision row (has 'action') per minute; join them
                by_minute: dict[int, dict] = {}
                for r in raw:
                    slot = by_minute.setdefault(r['minute'], {'minute': r['minute']})
                    if 'p' in r:
                        slot['p'] = r['p']
                    if 'action' in r:
                        slot['action'] = r['action']
                minutes = [by_minute[m] for m in sorted(by_minute) if 'p' in by_minute[m] and 'action' in by_minute[m]]

            records.append(episode_record(ep, truth, minutes))

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    summary_path = out / f'{args.split}_summary.json'
    summary_path.write_text(json.dumps({
        'split': args.split,
        'world': args.world,
        'seeds': args.seeds,
        'episodes': records,
    }, indent=1))

    for r in records:
        print(f"{r['episode_id']} hypothesis={r['hypothesis']} lead={r['lead_min']} flips={r['flips']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
