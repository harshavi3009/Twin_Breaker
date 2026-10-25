"""eval/check_stats.py — assert episode counts and print §10 table."""

import json
import sys
from pathlib import Path


def check_counts(episodes: list[dict]) -> tuple[int, int]:
    """Return (cascade, non_cascade) counts."""
    cascade = sum(1 for e in episodes if e.get("hypothesis") == "C")
    return cascade, len(episodes) - cascade


def render(summary: dict) -> str:
    """Render the §10 metrics table as a string."""
    lines = ["#   metric                 ours      grey      target"]
    metrics = summary.get("metrics", {})
    for k in range(1, 14):
        m = metrics.get(str(k), {})
        name = m.get("name", "n/a")
        ours = str(m.get("ours", "n/a"))
        grey = str(m.get("grey", "n/a"))
        target = m.get("target", "n/a")
        lines.append(f"{k:<3}{name:<24}{ours:<10}{grey:<10}{target}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Run checks and print the table."""
    args = argv or []
    path = Path(args[0]) if args else Path("results/eval_summary.json")
    summary = json.loads(path.read_text())
    episodes = summary.get("episodes", [])
    c, n = check_counts(episodes)
    if (c, n) != (150, 300):
        print(f"ASSERT FAILED: need 150 cascade and 300 non-cascade, got {c} and {n}")
        return 1
    print(render(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
