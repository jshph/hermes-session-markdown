#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import memory_dir, now_iso, read_json, safe_read, state_path, today, wikilink_date, write_json


def newest_markdown(source: Path) -> Path | None:
    if source.is_file():
        return source
    if not source.exists():
        return None
    files = sorted(source.rglob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--source", default="memory/forum-source", help="Forum source file or folder")
    parser.add_argument("--date", default=today())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    source = newest_markdown(root / args.source)
    source_text = safe_read(source) if source else ""
    out = memory_dir(root) / "hermes-workspace-preprocessed" / "forum" / f"{args.date}.md"
    body = source_text.strip()
    if body:
        note = f"""---
created: "{wikilink_date(args.date)}"
source: forum-preprocessed
---

# Forum context for agent distillation - {wikilink_date(args.date)}

This is bounded source context for the heartbeat agent. Do not copy it wholesale into the vault.

## Source excerpt

{body[:1200]}

## Distillation target

- Write `agent-memory-vault/forum/{args.date}.md`.
- Focus on how this agent's forum contributions interacted with other perspectives.
- Include themes, tensions, reframes, and any grounded social affordance.
- Do not preserve the whole forum raw.
"""
    else:
        note = f"""---
created: "{wikilink_date(args.date)}"
source: forum-preprocessed
---

# Forum context for agent distillation - {wikilink_date(args.date)}

No configured forum source produced grounded source context for this period.
"""

    if args.dry_run:
        print({"out": str(out), "source": str(source) if source else None, "chars": len(note)})
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(note.rstrip() + "\n", encoding="utf-8")
    state = read_json(state_path(root))
    state.setdefault("forumPreprocess", []).append({"at": now_iso(), "date": args.date, "path": str(out), "source": str(source) if source else None})
    write_json(state_path(root), state)
    print({"wrote": str(out), "source": str(source) if source else None})



if __name__ == "__main__":
    main()
