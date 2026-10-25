"""Pre-compute offline demo traces."""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

EPISODES = ['P1A-s0007', 'P1B-s0007']
LAMS = [0.5, 1.0, 2.0, 4.0]
SCENARIOS = ['none', 'rumour_wave', 'gateway_outage']


def plan():
    return [(ep, lam, sc) for ep in EPISODES for lam in LAMS for sc in SCENARIOS]


def out_name(episode: str, lam: float, scenario: str) -> str:
    base = f'{episode}__lam{lam:g}'
    if scenario == 'none':
        return f'{base}.json'
    return f'{base}__{scenario}.json'


def _events_for(episode: str, scenario: str):
    from generator.scenarios import build_injection, apply_silence

    path = Path('data/streams', f'{episode}.jsonl')
    events = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    seed = int(episode.split('-s')[1])
    if scenario == 'rumour_wave':
        injected = build_injection('rumour_wave', episode, 300, seed)
        merged = sorted(events + injected, key=lambda e: (e['event_time_s'], e.get('event_id', '')))
        return merged
    if scenario == 'gateway_outage':
        return apply_silence(events, 'gateway_outage', episode)
    return events


def _pair(raw):
    by_minute: dict[int, dict] = {}
    for row in raw:
        m = row['minute']
        if 'p' in row:
            by_minute.setdefault(m, {})['belief'] = row
        elif 'action' in row:
            by_minute.setdefault(m, {})['decision'] = row
    pairs = []
    for m in sorted(by_minute):
        entry = by_minute[m]
        if 'belief' in entry and 'decision' in entry:
            pairs.append({'minute': m, 'belief': entry['belief'], 'decision': entry['decision']})
    return pairs


def main(argv=None):
    parser = argparse.ArgumentParser(description='Pre-compute offline demo traces')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)

    out_dir = Path('data/episodes')
    out_dir.mkdir(parents=True, exist_ok=True)

    for ep, lam, sc in plan():
        name = out_name(ep, lam, sc)
        target = out_dir / name
        if args.dry_run:
            print(target)
            continue
        events = _events_for(ep, sc)
        with tempfile.NamedTemporaryFile(suffix='.jsonl', dir=Path.home() / 'aditya-scratch',
                                          mode='w', delete=False) as f:
            for ev in events:
                f.write(json.dumps(ev))
                f.write('\n')
            tmp_path = f.name
        from engine.run import run_episode
        raw = run_episode(tmp_path, lam=lam, ask_enabled=True, grey=False)
        minutes = _pair(raw)
        target.write_text(
            json.dumps({'episode_id': ep, 'lam': lam, 'minutes': minutes, 'synthetic': True}, indent=1)
        )
        print(target)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
