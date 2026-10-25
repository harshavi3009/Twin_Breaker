"""Turn sealed truth + per-minute outputs into one episode record."""
from __future__ import annotations

import json
import sys

from eval.metrics import brier_binary, lead_time_min, flip_count


def episode_record(episode: str, truth: dict, minutes: list[dict]) -> dict:
    actions = [m['action'] for m in minutes]
    p_C = [m['p']['C'] for m in minutes]
    y_all = [1 if truth['hypothesis'] == 'C' else 0] * len(minutes)
    brier_C = brier_binary(p_C, y_all)
    pre7 = min(len(minutes), 7)
    brier_C_pre = brier_binary(p_C[:pre7], y_all[:pre7])
    lead_min = lead_time_min(actions, truth['onset_min']) \
        if truth.get('onset_min') is not None else None
    reached_alert = any(a in ('ALERT', 'ESCALATE') for a in actions)
    flips = flip_count(actions, 3)
    return {
        'episode_id': episode, 'pair': truth['pair'],
        'role': truth['role'], 'hypothesis': truth['hypothesis'],
        'onset_min': truth['onset_min'], 'actions': actions,
        'p_C': p_C, 'reached_alert': reached_alert,
        'lead_min': lead_min, 'flips': flips,
        'brier_C': brier_C, 'brier_C_pre': brier_C_pre,
    }


if __name__ == '__main__':
    data = json.loads(sys.stdin.read())
    print(json.dumps(episode_record(data['episode'], data['truth'], data['minutes'])))
