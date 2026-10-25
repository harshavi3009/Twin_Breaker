"""G3 outage hold: P(C) must not drift > 0.001 per minute during silence."""
from __future__ import annotations

import json

import pytest
from pathlib import Path


def test_outage_hold(tmp_path):
    from generator.gen import generate
    from generator.scenarios import apply_silence
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
    beliefs = replay(buckets, spec, trust, prior, upto)
    p_c = {b.minute: b.p['C'] for b in beliefs}

    # Check P(C) drift during outage window [minute 6 .. minute 14] (300s–900s)
    for m in range(300 // 60 + 1, 900 // 60):
        assert m in p_c and m - 1 in p_c, f'no belief at minute {m}'
        assert abs(p_c[m] - p_c[m - 1]) <= 0.001, \
            f'm={m}: |p({m})-p({m-1})|=|{round(p_c[m],6)}-{round(p_c[m-1],6)}| > 0.001'
