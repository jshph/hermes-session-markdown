#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import context_path, default_state, state_path, vault_root, write_json


def enzyme_example(vault: Path) -> str:
    return f'''[vaults."{vault}"]
entities = [
  {{ "folder:hermes/sessions" = {{ profile = "resonance_trace" }} }},
  {{ "folder:forum" = {{ profile = "resonance_trace" }} }},
  {{ "folder:irl" = {{ profile = "relational" }} }},
  {{ "folder:irl/people" = {{ profile = "relational" }} }},
  {{ "folder:irl/events" = {{ profile = "relational" }} }}
]
excluded_folders = [".enzyme", ".git", ".obsidian", "templates"]
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Target Hermes workspace root")
    parser.add_argument("--check", action="store_true", help="Validate expected files/folders exist")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    vault = vault_root(root)
    folders = [
        vault / "hermes" / "sessions",
        vault / "forum",
        vault / "irl",
        vault / "irl" / "people",
        vault / "irl" / "events",
        root / "memory",
        root / "memory" / "hermes-workspace-staged",
    ]
    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)

    if not state_path(root).exists():
        write_json(state_path(root), default_state())
    if not context_path(root).exists():
        write_json(context_path(root), {"created": None, "forum": {}, "irl": {}, "petri": {}})

    (vault / "enzyme-config.example.toml").write_text(enzyme_example(vault), encoding="utf-8")

    missing = [str(folder) for folder in folders if not folder.exists()]
    if args.check and missing:
        raise SystemExit({"ok": False, "missing": missing})
    print({"ok": True, "vault": str(vault), "enzymeExample": str(vault / "enzyme-config.example.toml")})


if __name__ == "__main__":
    main()
