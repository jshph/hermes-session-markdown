#!/usr/bin/env python3
"""Run the stage-only send path while suppressing silent watchdog output."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def resolve_root(script: Path, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    hermes_home = os.environ.get("HERMES_HOME", "").strip()
    if hermes_home:
        return Path(hermes_home).expanduser().resolve()
    return script.parents[3]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", help="Target Hermes workspace root. Defaults to $HERMES_HOME or the installed Hermes root.")
    args = parser.parse_args()

    script = Path(__file__).resolve()
    root = resolve_root(script, args.root)
    workspace_loop = script.parent / "workspace_loop.py"

    result = subprocess.run(
        ["python3", str(workspace_loop), "--root", str(root), "--send"],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        if result.stderr.strip():
            print(result.stderr.strip(), file=sys.stderr)
        raise SystemExit(result.returncode)

    output = result.stdout.strip()
    if output and output != "[SILENT]":
        print(output)


if __name__ == "__main__":
    main()
