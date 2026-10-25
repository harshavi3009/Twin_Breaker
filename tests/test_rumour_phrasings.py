"""Test rumour phrasings form one cluster under shingle-overlap rules."""
import json
from pathlib import Path

PHR = json.loads((Path(__file__).parents[1] / 'scenarios' / 'rumour_wave.json').read_text())['phrasings']


def normalise(text):
    text = re.sub(r'[^a-z0-9]', ' ', text.lower())
    return ' '.join(text.split())


def shingles(text):
    words = normalise(text).split()
    return {tuple(words[i:i+3]) for i in range(len(words) - 2)}


def jaccard(a, b):
    return len(a & b) / len(a | b) if (a | b) else 0.0


import re


def test_has_12_phrasings():
    assert len(PHR) == 12


def test_each_phrasing_close_to_base():
    base_sh = shingles(PHR[0])
    for i in range(1, 12):
        j = jaccard(base_sh, shingles(PHR[i]))
        assert j >= 0.8, f'phrasing {i} has Jaccard {j:.3f} to phrasing 0'


def test_one_cluster_single_linkage():
    clusters = []
    for s in PHR:
        sh = shingles(s)
        found = False
        for cluster in clusters:
            if any(jaccard(sh, m) >= 0.8 for m in cluster):
                cluster.append(sh)
                found = True
                break
        if not found:
            clusters.append([sh])
    assert len(clusters) == 1
