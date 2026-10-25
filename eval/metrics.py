"""Pure metric functions for Twin Breaker eval."""
from __future__ import annotations


HYPS = ('N', 'S', 'I', 'C')


def brier_binary(p: list[float], y: list[int]) -> float:
    """Return mean of (p_i - y_i)^2.

    Raises ValueError if lengths differ or are empty.
    """
    n = len(p)
    if n == 0 or n != len(y):
        raise ValueError('length mismatch or zero')
    return sum((pi - yi) ** 2 for pi, yi in zip(p, y)) / n


def brier_multi(P: list[list[float]], labels: list[str]) -> float:
    """Mean Brier score over rows for multi-hypothesis case."""
    n_rows = len(P)
    if n_rows == 0 or len(labels) != n_rows:
        raise ValueError('length mismatch or zero rows')
    total = 0.0
    for i in range(n_rows):
        row_total = 0.0
        for j, h in enumerate(HYPS):
            target = 1.0 if labels[i] == h else 0.0
            row_total += (P[i][j] - target) ** 2
        total += row_total
    return total / n_rows


def ece(p: list[float], y: list[int], bins: int = 10) -> tuple[float, list[dict]]:
    """Expected Calibration Error with configurable bins."""
    n = len(p)
    if n != len(y):
        raise ValueError('length mismatch')
    bin_list = []
    for k in range(bins):
        bin_list.append({'lo': k / bins, 'hi': (k + 1) / bins,
                         'n': 0, 'sum_p': 0.0, 'sum_y': 0.0})
    for pi, yi in zip(p, y):
        b = min(bins - 1, int(pi * bins))
        bin_list[b]['n'] += 1
        bin_list[b]['sum_p'] += pi
        bin_list[b]['sum_y'] += yi
    ece_value = 0.0
    result_bins: list[dict] = []
    for bl in bin_list:
        conf = bl['sum_p'] / bl['n'] if bl['n'] > 0 else None
        acc = bl['sum_y'] / bl['n'] if bl['n'] > 0 else None
        result_bins.append({'lo': bl['lo'], 'hi': bl['hi'], 'n': bl['n'],
                            'conf': conf, 'acc': acc})
        if bl['n'] > 0:
            ece_value += (bl['n'] / n) * abs(acc - conf)
    return (ece_value, result_bins)


def lead_time_min(actions: list[str], onset_min: int) -> int | None:
    """Minutes between first ALERT/ESCALATE and onset."""
    for i, a in enumerate(actions):
        if a in ('ALERT', 'ESCALATE'):
            return onset_min - i
    return None


def flip_count(actions: list[str], window_min: int = 3) -> int:
    """Count flips per the twin-swap rule.

    A change point k is a flip if actions[k] == actions[prev-1]
    (it returned to the action before prev) and k - prev <= window_min.
    """
    if window_min == 0:
        return 0
    changes = [k for k in range(1, len(actions)) if actions[k] != actions[k - 1]]
    count = 0
    for idx in range(1, len(changes)):
        prev = changes[idx - 1]
        curr = changes[idx]
        if actions[curr] == actions[prev - 1] and (curr - prev) <= window_min:
            count += 1
    return count
