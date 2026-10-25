import hashlib
import json
import re

import pytest

KEYS = ['event_id', 'episode_id', 'kind', 'channel', 'source_id', 'gateway_id',
        'event_time_s', 'received_time_s', 'value', 'text', 'text_hash',
        'question_id', 'answer', 'retracts']
KINDS = {'observation', 'citizen', 'heartbeat', 'reply', 'retraction', 'dispatch', 'hospital'}


def normalise(text: str) -> str:
    text = re.sub(r'[^a-z0-9]', ' ', text.lower())
    return re.sub(r'\s+', ' ', text).strip()


def check_line(obj: dict, file_stem: str) -> list[str]:
    errors: list[str] = []
    for key in KEYS:
        if key not in obj:
            errors.append(f'missing {key!r}')
    kind = obj.get('kind')
    if kind not in KINDS:
        errors.append(f'bad kind {kind!r}')
    if kind == 'observation':
        ch = obj.get('channel')
        if ch not in ('rain', 'drain', 'traffic'):
            errors.append("observation channel must be rain/drain/traffic")
        if obj.get('gateway_id') is None:
            errors.append("observation gateway_id is None")
    if kind == 'citizen':
        if obj.get('channel') != 'citizen':
            errors.append("citizen channel != citizen")
        if obj.get('text') is None:
            errors.append("citizen text is None")
        else:
            expected_th = hashlib.sha1(normalise(obj['text']).encode()).hexdigest()[:6]
            if obj.get('text_hash') != expected_th:
                errors.append(f"text_hash mismatch {obj['text_hash']!r}")
    ets = obj.get('event_time_s')
    rts = obj.get('received_time_s')
    if rts is not None and ets is not None and rts < ets:
        errors.append("received_time_s < event_time_s")
    if obj.get('episode_id') != file_stem:
        errors.append("episode_id != file_stem")
    return errors


def test_check_line_accepts_valid():
    obs = dict(event_id='e1', episode_id='N-s0007', kind='observation', channel='drain',
               source_id='drain-G2-031', gateway_id='G2', event_time_s=300, received_time_s=331, value=0.91)
    for k in KEYS:
        obs.setdefault(k, None)
    assert check_line(obs, 'N-s0007') == []

    txt = "Water over the road near the underpass"
    cit = dict(event_id='e2', episode_id='N-s0007', kind='citizen',
               channel='citizen', text=txt,
               text_hash=hashlib.sha1(normalise(txt).encode()).hexdigest()[:6])
    for k in KEYS:
        cit.setdefault(k, None)
    assert check_line(cit, 'N-s0007') == []


def test_check_line_rejects_bad():
    a = dict(event_id='e1', episode_id='N-s0007', kind='observation', channel='drain',
             source_id='x', gateway_id=None, event_time_s=300)
    for k in KEYS:
        a.setdefault(k, None)
    assert len(check_line(a, 'N-s0007')) > 0

    b = dict(kind='observation', channel='rain', gateway_id='G1', event_time_s=300, received_time_s=299)
    for k in KEYS:
        b.setdefault(k, None)
    assert len(check_line(b, 'N-s0007')) > 0


def test_generated_file_schema(tmp_path):
    from generator.gen import generate
    generate('B', 'dev', 7, 'N-s0007', str(tmp_path))
    path = tmp_path / 'N-s0007.jsonl'
    lines = path.read_text().splitlines()
    errors: list[str] = []
    seen_ids: set[str] = set()
    for i, line in enumerate(lines):
        obj = json.loads(line)
        errs = check_line(obj, 'N-s0007')
        if errs:
            errors.extend(f'line {i}: {e}' for e in errs)
        eid = obj['event_id']
        assert eid not in seen_ids, f'duplicate event_id at line {i}'
        seen_ids.add(eid)
    assert len(errors) == 0, '\n'.join(errors[:20])
    assert len(seen_ids) > 100
