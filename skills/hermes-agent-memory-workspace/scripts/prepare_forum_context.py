#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import context_path, now_iso, read_json, safe_read, state_path, today, write_json


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
    body = source_text.strip()
    context = read_json(context_path(root), {"forum": {}, "irl": {}, "petri": {}})
    context["forum"] = {
        "date": args.date,
        "sourcePath": str(source) if source else None,
        "sourceExcerpt": body[:1200] if body else "",
        "targetPath": f"agent-memory-vault/forum/{args.date}.md",
        "instructions": [
            "Focus on how this agent's forum contributions interacted with other perspectives.",
            "Include themes, tensions, reframes, and any grounded social affordance.",
            "Do not preserve the whole forum raw.",
        ],
        "updatedAt": now_iso(),
    }

    if args.dry_run:
        print({"context": str(context_path(root)), "source": str(source) if source else None, "chars": len(body[:1200])})
        return
    write_json(context_path(root), context)
    state = read_json(state_path(root))
    state.setdefault("forumPreprocess", []).append({"at": now_iso(), "date": args.date, "context": str(context_path(root)), "source": str(source) if source else None})
    write_json(state_path(root), state)
    print({"updated": str(context_path(root)), "source": str(source) if source else None})



if __name__ == "__main__":
    main()
