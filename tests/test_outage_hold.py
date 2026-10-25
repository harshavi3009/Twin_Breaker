"""G3 outage hold: the silence step alone must not move P(C) by more than 0.001 per minute."""
from __future__ import annotations

import json

import pytest
from pathlib import Path


def test_outage_hold(tmp_path, monkeypatch):
    from generator.gen import generate
    from generator.scenarios import apply_silence
    from engine import belief
    from engine.ingest import parse_line, Ingestor
    from engine.belief import replay, Trust

    # Generate an S (sensor-failure) episode with G3 outage scenario applied
    info = generate('B', 'dev', 7, 'S-s0007', str(tmp_path))

    # Load and apply silence: drops G3 drain observations & heartbeats in [300,900)
    raw = [json.loads(l) for l in Path(info['path']).read_text().splitlines() if l.strip()]
    kept = apply_silence(raw, 'gateway_outage', 'S-s0007')
    events = [parse_line(json.dumps(d)) for d in kept]

    ing = Ingestor(registered_responders=set())
    for ev in events:
        ing.push(ev)
    buckets = ing.buckets()

    spec = json.loads(Path('engine/config/belief_spec.json').read_text())
    spec['eps'] = 0.0  # forget OFF — silence step only (forget drift ~−0.003/min reported by Harshavi)

    trust = Trust(spec)
    trust.reset()
    prior = {'N': 0.25, 'S': 0.25, 'I': 0.25, 'C': 0.25}

    upto = max(buckets.keys()) // 60 if buckets else 0
    p_c_silent = {b.minute: b.p['C'] for b in replay(buckets, spec, trust, prior, upto)}

    # Same replay with the silence step switched off. Other gateways' real readings still move P(C)
    # (G1/G2 drain drops to the elevated bin at minute 12), so compare the two runs, not P(C) over time.
    monkeypatch.setattr(belief, 'silent_gateways', lambda *args, **kwargs: [])
    trust.reset()
    p_c_plain = {b.minute: b.p['C'] for b in replay(buckets, spec, trust, prior, upto)}

    # Check the silence step's effect on P(C) during outage window [minute 6 .. minute 14] (300s–900s)
    for m in range(300 // 60 + 1, 900 // 60):
        assert m in p_c_silent and m in p_c_plain, f'no belief at minute {m}'
        assert abs(p_c_silent[m] - p_c_plain[m]) <= 0.001, \
            f'm={m}: silence moved P(C) by {round(p_c_silent[m] - p_c_plain[m], 6)} > 0.001'
