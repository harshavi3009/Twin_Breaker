import json
from pathlib import Path
import pytest

PREFIX_S = 420
PAIRS = ['P1', 'P2', 'P3']
SEEDS = [7, 1, 2]


def prefix_view(lines: list[str]) -> list[dict]:
    result = []
    for line in lines:
        if not line.strip():
            continue
        obj = json.loads(line)
        if obj['kind'] != 'reply' and obj['event_time_s'] < 420:
            del obj['episode_id']
            result.append(obj)
    return result


def assert_same_prefix(a_lines: list[str], b_lines: list[str]) -> None:
    va = prefix_view(a_lines)
    vb = prefix_view(b_lines)
    assert len(va) > 0, 'empty prefix'
    if va != vb:
        idx = next(i for i, (x, y) in enumerate(zip(va, vb)) if x != y)
        raise AssertionError(f"Difference at index {idx}: A={va[idx]} B={vb[idx]}")


def test_helper_accepts_identical():
    base_a = [
        json.dumps({"event_id": "e1", "episode_id": "P1A-s0007", "kind": "observation", "channel": "rain", "source_id": "g2", "gateway_id": "G2", "event_time_s": 100, "received_time_s": 110, "value": 0.5}),
        json.dumps({"event_id": "e2", "episode_id": "P1A-s0007", "kind": "citizen", "channel": "citizen", "source_id": "c1", "event_time_s": 300, "received_time_s": 310, "text": "water over road", "text_hash": "000000"}),
        json.dumps({"event_id": "e3", "episode_id": "P1A-s0007", "kind": "reply", "channel": "reply", "source_id": "marshal-W9-01", "gateway_id": "G2", "question_id": "Q1", "answer": "yes", "event_time_s": 365, "received_time_s": 400}),
    ]
    base_b = [
        json.dumps({"event_id": "e1", "episode_id": "P1B-s0007", "kind": "observation", "channel": "rain", "source_id": "g2", "gateway_id": "G2", "event_time_s": 100, "received_time_s": 110, "value": 0.5}),
        json.dumps({"event_id": "e2", "episode_id": "P1B-s0007", "kind": "citizen", "channel": "citizen", "source_id": "c1", "event_time_s": 300, "received_time_s": 310, "text": "water over road", "text_hash": "000000"}),
        json.dumps({"event_id": "e3", "episode_id": "P1B-s0007", "kind": "reply", "channel": "reply", "source_id": "marshal-W9-01", "gateway_id": "G2", "question_id": "Q1", "answer": "no", "event_time_s": 365, "received_time_s": 400}),
    ]
    assert_same_prefix(base_a, base_b)


def test_helper_rejects_difference():
    line_obs = json.dumps({"event_id": "e1", "episode_id": "P1A-s0007", "kind": "observation", "channel": "rain", "source_id": "g2", "gateway_id": "G2", "event_time_s": 100, "received_time_s": 110, "value": 0.5})
    other = [line_obs]
    diff_obs = json.dumps({"event_id": "e1", "episode_id": "P1B-s0007", "kind": "observation", "channel": "rain", "source_id": "g2", "gateway_id": "G2", "event_time_s": 100, "received_time_s": 110, "value": 0.6})
    lines_b = [diff_obs]
    with pytest.raises(AssertionError):
        assert_same_prefix(other, lines_b)


@pytest.mark.parametrize('pair', PAIRS)
@pytest.mark.parametrize('seed', SEEDS)
def test_twin_prefix(pair, seed, tmp_path):
    from generator.gen import generate
    generate(world='B', split='dev', seed=seed, episode=f'{pair}A-s{seed:04d}', out_dir=str(tmp_path))
    generate(world='B', split='dev', seed=seed, episode=f'{pair}B-s{seed:04d}', out_dir=str(tmp_path))
    a_file = Path(tmp_path) / f'{pair}A-s{seed:04d}.jsonl'
    b_file = Path(tmp_path) / f'{pair}B-s{seed:04d}.jsonl'
    a_lines = a_file.read_text().splitlines()
    b_lines = b_file.read_text().splitlines()
    assert_same_prefix(a_lines, b_lines)
