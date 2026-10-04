#!/usr/bin/env python3
"""Print one dry line from lines.txt (next to this script).

  python3 line.py         # one random line
  python3 line.py --list  # every line, numbered

Blank lines and lines starting with # are ignored.
No network. No state file. No server. Stdlib only.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

LINES_FILE = Path(__file__).resolve().parent / "lines.txt"


def load_lines(path: Path) -> list[str]:
    """Read lines.txt: skip blanks and # comments."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"cannot read {path}: {exc}", file=sys.stderr)
        sys.exit(2)

    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        lines.append(line)
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Print one dry line from lines.txt next to this script."
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="print every line with a number instead of picking one",
    )
    args = parser.parse_args()

    lines = load_lines(LINES_FILE)
    if not lines:
        print(f"no lines in {LINES_FILE}", file=sys.stderr)
        sys.exit(1)

    if args.list:
        for i, line in enumerate(lines, start=1):
            print(f"{i}. {line}")
        return

    print(random.choice(lines))


if __name__ == "__main__":
    main()
