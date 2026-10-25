"""Sealed marshal responder."""
from __future__ import annotations

import json
import re
from pathlib import Path

from generator.rng import episode_rng


def reply(episode_id: str, question_id: str, asked_at_s: int, error=None) -> dict:
    m = re.search(r'-s(\d{4})$', episode_id)
    if m is None:
        raise ValueError(f'bad episode_id {episode_id!r}')
    seed = int(m.group(1))
    truth = json.loads((Path(__file__).parent / 'sealed' / f'{episode_id}.truth.json').read_text())
    spec = json.loads(Path(__file__).with_name('world_spec.json').read_text())
    R = spec['responder']
    minute = min(asked_at_s // 60, len(truth['latent_depth_cm']) - 1)
    depth = truth['latent_depth_cm'][minute]
    truth_yes = depth >= R['threshold_cm']
    if error is None:
        error = (R['error_default'][0] + R['error_default'][1]) / 2
    rng = episode_rng(seed, f'reply:{question_id}:{asked_at_s}')
    flip = rng.random() < error
    answer_yes = truth_yes != flip
    lo, hi = R['delay_s']
    delay = int(rng.integers(lo, hi + 1))
    return {
        'answer': 'yes' if answer_yes else 'no',
        'responder_id': 'marshal-W9-01',
        'delay_s': delay,
    }
