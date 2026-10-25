"""Scenario injection and G3 silence application."""
from __future__ import annotations

import json
from pathlib import Path

from generator.rng import text_hash

SCEN = Path(__file__).resolve().parents[1] / 'scenarios'


def _load(name: str) -> dict:
    return json.loads((SCEN / f'{name}.json').read_text())


ALL_KEYS = (
    "event_id", "episode_id", "kind", "channel", "source_id",
    "gateway_id", "event_time_s", "received_time_s", "value",
    "text", "text_hash", "question_id", "answer", "retracts",
)


def build_injection(name: str, episode_id: str, at_s: int, seed: int) -> list[dict]:
    if name != 'rumour_wave':
        raise ValueError(f'unsupported injection {name}')
    sc = _load(name)
    phrasings = sc['phrasings']
    count = sc['count']
    window = sc['window_s']
    events = []
    for i in range(count):
        t = at_s + int(i * window / count)
        text = phrasings[i % len(phrasings)]
        d = {k: None for k in ALL_KEYS}
        d['event_id'] = f'ev-inj-{episode_id}-{i:04d}'
        d['episode_id'] = episode_id
        d['kind'] = 'citizen'
        d['channel'] = 'citizen'
        d['source_id'] = f'phone-r{i:04d}'
        d['gateway_id'] = None
        d['event_time_s'] = t
        d['received_time_s'] = t + 5
        d['value'] = None
        d['text'] = text
        d['text_hash'] = text_hash(text)
        events.append(d)
    return events


def apply_silence(events: list[dict], name: str, episode_id: str) -> list[dict]:
    sc = _load(name)
    if sc.get('kind') != 'silence':
        raise ValueError('not a silence scenario')
    s = sc['start_s']
    e = sc['start_s'] + sc['duration_s']
    gw = sc['gateway_id']
    ch = sc['channel']
    def silenced(evt):
        in_window = s <= evt['event_time_s'] < e
        same_gw = evt.get('gateway_id') == gw
        is_obs = evt['kind'] == 'observation' and evt.get('channel') == ch
        is_hb = evt['kind'] == 'heartbeat'
        return in_window and same_gw and (is_obs or is_hb)
    return [ev for ev in events if not silenced(ev)]
