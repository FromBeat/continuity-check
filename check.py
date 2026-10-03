#!/usr/bin/env python3
from __future__ import annotations
"""Check that a continuity folder has the expected markdown files.

Prints a short wake-up card (first non-empty lines) for each file that
exists, and lists any that are missing. Exit 0 when every expected file
is present, 1 when any are missing.
"""

import argparse
import json
import sys
from pathlib import Path

DEFAULT_FILES = (
    "IDENTITY.md",
    "RAILS.md",
    "BOUNDARIES.md",
    "CURRENT.md",
    "HANDOFF.md",
)

MAX_LINES = 12
MAX_LINE_LEN = 100


class ConfigError(Exception):
    """The config path cannot be used. The CLI turns this into exit code 2."""


def load_expected(config_path: Path | None) -> list[str]:
    if config_path is None:
        return list(DEFAULT_FILES)
    try:
        raw = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"cannot read config {config_path}: {exc}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"config is not JSON: {exc}") from exc
    files = data.get("files") if isinstance(data, dict) else data
    if not isinstance(files, list) or not files or not all(
        isinstance(name, str) and name.strip() and "/" not in name and "\\" not in name
        for name in files
    ):
        raise ConfigError(
            'config must be {"files": ["IDENTITY.md", ...]} with bare filenames'
        )
    return [name.strip() for name in files]


def collect(folder: Path, expected: list[str]) -> tuple[list[tuple[str, list[str]]], list[str]]:
    """Return (present name/lines pairs, missing names). Does not print."""
    missing: list[str] = []
    present: list[tuple[str, list[str]]] = []
    for name in expected:
        path = folder / name
        if path.is_file():
            present.append((name, wake_lines(path)))
        else:
            missing.append(name)
    return present, missing


def wake_lines(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"(unreadable: {exc})"]
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if len(line) > MAX_LINE_LEN:
            line = line[: MAX_LINE_LEN - 1] + "…"
        lines.append(line)
        if len(lines) >= MAX_LINES:
            break
    return lines or ["(empty)"]


def check(folder: Path, expected: list[str]) -> int:
    present, missing = collect(folder, expected)

    print(f"folder: {folder}")
    print(f"expected: {len(expected)}  present: {len(present)}  missing: {len(missing)}")
    print()

    if missing:
        print("missing:")
        for name in missing:
            print(f"  - {name}")
        print()

    if present:
        print("wake-up:")
        for name, lines in present:
            print(f"--- {name} ---")
            for line in lines:
                print(line)
            print()

    if missing:
        print("result: incomplete")
        return 1
    print("result: all present")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check a continuity folder for expected markdown files "
        "and print a short wake-up card for each one that exists."
    )
    parser.add_argument("folder", type=Path, help="folder to check")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help='JSON file with {"files": ["NAME.md", ...]}. '
        "Defaults to IDENTITY, RAILS, BOUNDARIES, CURRENT, HANDOFF.",
    )
    args = parser.parse_args(argv)

    if not args.folder.is_dir():
        print(f"error: not a folder: {args.folder}", file=sys.stderr)
        return 2

    try:
        expected = load_expected(args.config)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return check(args.folder, expected)


if __name__ == "__main__":
    sys.exit(main())
