import pytest

from eval.metrics import brier_binary, brier_multi, ece, lead_time_min, flip_count


def test_brier_binary():
    assert brier_binary([0.2, 0.8], [0, 1]) == pytest.approx(0.04)


def test_brier_multi_1():
    assert brier_multi([[0.1, 0.2, 0.3, 0.4]], ['C']) == pytest.approx(0.50)


def test_brier_multi_2():
    assert brier_multi([[0.1, 0.2, 0.3, 0.4], [0.25, 0.25, 0.25, 0.25]], ['C', 'N']) == pytest.approx(0.625)


def test_ece():
    value, bins = ece([0.1, 0.1, 0.9, 0.9], [0, 0, 1, 0], bins=10)
    assert value == pytest.approx(0.25)
    assert len(bins) == 10
    assert bins[1]['n'] == 2
    assert bins[9]['n'] == 2


def test_lead_time_min_alert():
    assert lead_time_min(['WATCH', 'WATCH', 'WATCH', 'ALERT', 'ALERT', 'ALERT'], 8) == 5


def test_lead_time_min_no_alert():
    assert lead_time_min(['WATCH'] * 6, 8) is None


def test_flip_count_3():
    assert flip_count(['WATCH', 'PREPARE', 'WATCH', 'WATCH', 'WATCH'], 3) == 1


def test_flip_count_0_window():
    assert flip_count(['WATCH', 'PREPARE', 'ALERT', 'WATCH'], 3) == 0


def test_flip_count_1():
    assert flip_count(['WATCH', 'PREPARE', 'WATCH', 'PREPARE', 'WATCH'], 1) == 3


def test_flip_count_0():
    assert flip_count(['WATCH', 'PREPARE', 'WATCH', 'PREPARE', 'WATCH'], 0) == 0
