"""Update the concise Codex project-state handoff after a sealed product phase."""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".codex" / "CURRENT_STATE.md"


def _clean(value: str, label: str) -> str:
    value = value.strip()
    if not value or "\n" in value or "\r" in value:
        raise ValueError(f"{label} must be one non-empty line")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--tests", required=True, type=int)
    parser.add_argument("--next", dest="next_phase", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--invariant", required=True)
    args = parser.parse_args()

    phase = _clean(args.phase, "phase")
    tag = _clean(args.tag, "tag")
    next_phase = _clean(args.next_phase, "next phase")
    date = _clean(args.date, "date")
    invariant = _clean(args.invariant, "invariant")
    if args.tests < 0:
        raise ValueError("tests must be non-negative")

    text = f"""# Nayeon v1 - Codex current state

> This is the concise live handoff for Codex. Git remains authoritative. Read this after the root AGENTS.md at the start of every Nayeon task.

- **Branch:** `nayeon-v1`
- **Latest completed product phase:** {phase}
- **Latest milestone tag:** `{tag}`
- **Full regression baseline:** **{args.tests:,} / {args.tests:,}**
- **Last updated:** {date}
- **Next restart point:** {next_phase}

## Latest architecture invariant

{invariant}

## Required startup behavior

Inspect current HEAD/tag/status and read the latest relevant phase review before editing. If Git disagrees with this file, report the mismatch and treat Git as authoritative.

## Close-out rule

When the next product phase is sealed, refresh this file again as part of that phase close-out before the next Codex implementation session.
"""
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
