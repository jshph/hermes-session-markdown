#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

from common import memory_dir, now_iso, read_json, safe_read, state_path, today, vault_root, wikilink_date, write_json


PERSON_RE = re.compile(r"\[\[([A-Z][^]\n]{1,80})\]\]")


def recent_session_text(session_root: Path, limit: int = 5) -> str:
    files = sorted(session_root.rglob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
    return "\n\n".join(safe_read(path)[:3000] for path in files)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--date", default=today())
    parser.add_argument("--calendar", default="memory/calendar-context.md")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    vault = vault_root(root)
    session_text = recent_session_text(vault / "hermes" / "sessions")
    calendar_text = safe_read(root / args.calendar)
    people = sorted(set(PERSON_RE.findall(session_text + "\n" + calendar_text)))[:20]
    out = memory_dir(root) / "hermes-workspace-preprocessed" / "irl" / f"{args.date}.md"

    people_lines = "\n".join(f'- [[{name}]] came up in recent Hermes/calendar context. Treat as context, not a confirmed want.' for name in people)
    if not people_lines:
        people_lines = "- No grounded people/opportunity signal found in configured sources."

    people_frontmatter = "\n".join(f'  - "[[{name}]]"' for name in people) if people else "people: []"
    people_block = f"people:\n{people_frontmatter}" if people else people_frontmatter

    note = f"""---
created: "{wikilink_date(args.date)}"
source: telegram-calendar-preprocessed
{people_block}
---

# IRL context for agent distillation - {wikilink_date(args.date)}

This is bounded source context for the heartbeat agent. Do not copy it wholesale into the vault.

## Calendar / events

{calendar_text.strip()[:1200] if calendar_text.strip() else "- No configured calendar/event context for this period."}

## People / opportunities

{people_lines}

## Recent session excerpt

{session_text.strip()[:1800] if session_text.strip() else "- No recent rendered Hermes session Markdown found."}

## Uncertainty

- Preserve uncertainty plainly: attended, maybe attended, RSVP'd, mentioned, proposed, or unclear.

## Distillation target

- Write `agent-memory-vault/irl/{args.date}.md`.
- Capture people, events, opportunities, and uncertainty from Telegram/calendar context.
- Create person/event subnotes only when an entity recurs enough to deserve one.
"""

    if args.dry_run:
        print({"out": str(out), "people": people, "chars": len(note)})
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(note.rstrip() + "\n", encoding="utf-8")
    state = read_json(state_path(root))
    state.setdefault("irlPreprocess", []).append({"at": now_iso(), "date": args.date, "path": str(out), "people": people})
    write_json(state_path(root), state)
    print({"wrote": str(out), "people": people})


if __name__ == "__main__":
    main()
