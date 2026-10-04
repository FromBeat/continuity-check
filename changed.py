#!/usr/bin/env python3
from __future__ import annotations
"""Report what changed in a continuity folder since the last look.

Reuses check.py for expected filenames, presence, and wake-up lines.
Keeps a small local state file next to this script (not in the shelf).
"""

import argparse
import json
import sys
from pathlib import Path

from check import ConfigError, collect, load_expected

# Lives next to this script, never inside the shelf being checked.
STATE_PATH = Path(__file__).resolve().parent / ".changed_state.json"


def build_snapshot(folder: Path, expected: list[str]) -> dict[str, dict]:
    """Map each expected name to present/missing plus wake-up lines."""
    present, missing = collect(folder, expected)
    files: dict[str, dict] = {}
    for name, lines in present:
        files[name] = {"present": True, "lines": list(lines)}
    for name in missing:
        files[name] = {"present": False, "lines": []}
    return files


def load_state() -> dict | None:
    if not STATE_PATH.is_file():
        return None
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def save_state(state: dict) -> None:
    STATE_PATH.write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def folder_key(folder: Path) -> str:
    return str(folder.resolve())


def diff_snapshots(
    old: dict[str, dict], new: dict[str, dict]
) -> list[str]:
    """Return short human lines describing each change."""
    changes: list[str] = []
    names = list(dict.fromkeys([*old.keys(), *new.keys()]))
    for name in names:
        was = old.get(name)
        now = new.get(name)
        if was is None and now is not None:
            if now.get("present"):
                changes.append(f"{name}: newly present")
            else:
                changes.append(f"{name}: newly missing")
            continue
        if now is None and was is not None:
            # Expected list shrank; treat as gone from the check set.
            continue
        assert was is not None and now is not None
        was_present = bool(was.get("present"))
        now_present = bool(now.get("present"))
        if was_present and not now_present:
            changes.append(f"{name}: newly missing")
        elif not was_present and now_present:
            changes.append(f"{name}: newly present")
        elif was_present and now_present and list(was.get("lines") or []) != list(
            now.get("lines") or []
        ):
            changes.append(f"{name}: wake-up lines differ")
    return changes


def run(folder: Path, expected: list[str]) -> int:
    snapshot = build_snapshot(folder, expected)
    key = folder_key(folder)
    state = load_state()

    if state is None or key not in state.get("folders", {}):
        print("first look: nothing to compare yet")
        if state is None or not isinstance(state.get("folders"), dict):
            state = {"folders": {}}
        state["folders"][key] = {"files": snapshot}
        save_state(state)
        return 0

    old = state["folders"][key].get("files") or {}
    if not isinstance(old, dict):
        old = {}
    changes = diff_snapshots(old, snapshot)
    state["folders"][key] = {"files": snapshot}
    save_state(state)

    if not changes:
        print("nothing changed")
        return 0

    print("changed:")
    for line in changes:
        print(f"  {line}")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare a continuity folder to the last look and "
        "print only what changed (presence or wake-up lines)."
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
    return run(args.folder, expected)


if __name__ == "__main__":
    sys.exit(main())
