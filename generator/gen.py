import argparse
import json
from pathlib import Path

from generator.latent import make_latent
from generator.passive import minute_events


def parse_seeds(text: str) -> list[int]:
    if '-' in text:
        lo, hi = text.split('-', 1)
        return list(range(int(lo), int(hi) + 1))
    return [int(text)]


def episodes_for(world: str, split: str, seed: int) -> list[str]:
    if world != 'B':
        raise ValueError('world must be B in pass 1')
    if split != 'dev':
        raise NotImplementedError('pass 1: dev only')
    return [f'N-s{seed:04d}', f'C-s{seed:04d}', f'P1A-s{seed:04d}', f'P1B-s{seed:04d}']


def generate(world: str, split: str, seed: int, episode: str, out_dir: str) -> dict:
    episodes_for(world, split, seed)
    spec = json.loads(Path(__file__).with_name('world_spec.json').read_text())
    latent = make_latent(seed, episode, spec)
    events: list[dict] = []
    for m in range(spec['episode_minutes']):
        events.extend(minute_events(episode, seed, m, latent, spec))
    events.sort(key=lambda e: (e['event_time_s'], e['event_id']))
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    jsonl_path = out / f'{episode}.jsonl'
    with open(jsonl_path, 'w') as fh:
        for ev in events:
            fh.write(json.dumps(ev) + '\n')
    sealed = Path(__file__).parent / 'sealed'
    sealed.mkdir(parents=True, exist_ok=True)
    truth_path = sealed / f'{episode}.truth.json'
    with open(truth_path, 'w') as fh:
        json.dump({
            'hypothesis': latent.hypothesis,
            'onset_min': latent.onset_min,
            'pair': latent.pair,
            'role': latent.role,
            'latent_depth_cm': latent.depth_cm,
        }, fh)
    return {'episode_id': episode, 'n_events': len(events),
            'path': str(jsonl_path), 'truth_path': str(truth_path)}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--world', required=True)
    parser.add_argument('--split', required=True)
    parser.add_argument('--seeds', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    for seed in parse_seeds(args.seeds):
        for ep in episodes_for(args.world, args.split, seed):
            r = generate(args.world, args.split, seed, ep, args.out)
            print(f"wrote {r['path']} ({r['n_events']} events)")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
