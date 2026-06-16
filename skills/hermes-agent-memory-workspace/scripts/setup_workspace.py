#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from common import context_path, default_state, state_path, vault_root, write_json


ENZYME_BLOCK_BEGIN = "# BEGIN hermes-agent-memory-workspace"
ENZYME_BLOCK_END = "# END hermes-agent-memory-workspace"
DEFAULT_CRON_NAME = "Hermes agent memory heartbeat"
DEFAULT_CRON_SCHEDULE = "0 2 * * *"
DEFAULT_OPENAI_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENAI_MODEL = "google/gemini-3.1-flash-lite"
OFFICIAL_ENZYME_INSTALL = "curl -fsSL https://enzyme.garden/install.sh | bash"


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


def managed_enzyme_block(vault: Path) -> str:
    return f"{ENZYME_BLOCK_BEGIN}\n{enzyme_example(vault).rstrip()}\n{ENZYME_BLOCK_END}\n"


def install_enzyme_config(vault: Path, config_path: Path) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    existing = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    block = managed_enzyme_block(vault)
    if ENZYME_BLOCK_BEGIN in existing and ENZYME_BLOCK_END in existing:
        before, rest = existing.split(ENZYME_BLOCK_BEGIN, 1)
        _, after = rest.split(ENZYME_BLOCK_END, 1)
        updated = before.rstrip() + "\n\n" + block + after.lstrip()
    else:
        updated = existing.rstrip() + ("\n\n" if existing.strip() else "") + block
    config_path.write_text(updated.rstrip() + "\n", encoding="utf-8")


def write_enzyme_env(root: Path, api_key_env: str) -> Path:
    env_path = root / "memory" / "enzyme-env.sh"
    env_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Source this before running Enzyme manually for the Hermes memory vault.",
        "# This file stores variable references only; it does not store API secrets.",
    ]
    if api_key_env == "OPENAI_API_KEY":
        lines.append('export OPENAI_API_KEY="${OPENAI_API_KEY:?OPENAI_API_KEY must be set before running Enzyme}"')
    else:
        lines.append(f'export OPENAI_API_KEY="${{{api_key_env}:?{api_key_env} must be set before running Enzyme}}"')
    lines.extend(
        [
            f'export OPENAI_BASE_URL="{DEFAULT_OPENAI_BASE_URL}"',
            f'export OPENAI_MODEL="{DEFAULT_OPENAI_MODEL}"',
            "",
        ]
    )
    env_path.write_text("\n".join(lines), encoding="utf-8")
    return env_path


def install_enzyme_cli(enzyme_bin: str) -> dict:
    resolved = shutil.which(enzyme_bin) if enzyme_bin == "enzyme" else shutil.which(enzyme_bin) or enzyme_bin
    if resolved and Path(resolved).exists():
        return {"installed": False, "reason": "already-present", "enzymeBin": resolved}
    result = subprocess.run(["bash", "-lc", OFFICIAL_ENZYME_INSTALL], text=True)
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    resolved = shutil.which("enzyme") or str(Path.home() / ".local" / "bin" / "enzyme")
    return {"installed": True, "enzymeBin": resolved}


def enzyme_env(api_key_env: str) -> dict:
    key = os.environ.get(api_key_env)
    if not key:
        raise SystemExit(
            {
                "ok": False,
                "missingEnv": [api_key_env],
                "detail": f"Set {api_key_env}; it will be passed to Enzyme as OPENAI_API_KEY without printing or storing the value.",
            }
        )
    env = os.environ.copy()
    env["OPENAI_API_KEY"] = key
    env["OPENAI_BASE_URL"] = DEFAULT_OPENAI_BASE_URL
    env["OPENAI_MODEL"] = DEFAULT_OPENAI_MODEL
    return env


def run_enzyme(vault: Path, action: str, enzyme_bin: str, api_key_env: str) -> dict:
    if action == "none":
        return {"action": "none"}
    resolved = shutil.which(enzyme_bin) if enzyme_bin == "enzyme" else shutil.which(enzyme_bin) or enzyme_bin
    if not resolved or not Path(resolved).exists():
        raise SystemExit({"ok": False, "missingExecutable": enzyme_bin, "install": OFFICIAL_ENZYME_INSTALL})
    cmd = [resolved, action, "--vault", str(vault)]
    result = subprocess.run(cmd, text=True, env=enzyme_env(api_key_env))
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    return {
        "action": action,
        "vault": str(vault),
        "enzymeBin": resolved,
        "providerEnv": {
            "apiKey": api_key_env,
            "baseUrl": "OPENAI_BASE_URL",
            "model": "OPENAI_MODEL",
        },
    }


def cron_prompt() -> str:
    return "\n".join(
        [
            "Use the injected Hermes agent memory heartbeat context.",
            "Write or update `agent-memory-vault/forum/YYYY-MM-DD.md` and `agent-memory-vault/irl/YYYY-MM-DD.md`.",
            "Keep the notes concise, grounded, and uncertainty-aware.",
            "Do not copy `memory/hermes-workspace-context.json` wholesale into the vault.",
            "After writing the notes, run `python3 skills/hermes-agent-memory-workspace/scripts/workspace_loop.py --prepare`.",
            "Return `[SILENT]` unless a local operator-facing summary is genuinely needed.",
        ]
    )


def cron_exists(name: str, hermes_bin: str) -> bool:
    result = subprocess.run([hermes_bin, "cron", "list", "--all"], text=True, capture_output=True)
    if result.returncode != 0:
        return False
    return f"Name:      {name}" in result.stdout


def install_cron(root: Path, schedule: str, name: str, hermes_bin: str) -> dict:
    if cron_exists(name, hermes_bin):
        return {"installed": False, "reason": "already-exists", "name": name, "schedule": schedule}
    script = root / "skills" / "hermes-agent-memory-workspace" / "scripts" / "cron_prepare.py"
    if not script.exists():
        # Development checkout fallback.
        script = Path(__file__).resolve().with_name("cron_prepare.py")
    args = [
        hermes_bin,
        "cron",
        "create",
        schedule,
        cron_prompt(),
        "--name",
        name,
        "--skill",
        "hermes-agent-memory-workspace",
        "--script",
        str(script),
        "--workdir",
        str(root),
    ]
    result = subprocess.run(args, text=True, capture_output=True)
    if result.returncode != 0:
        if result.stdout.strip():
            print(result.stdout.strip(), file=sys.stderr)
        if result.stderr.strip():
            print(result.stderr.strip(), file=sys.stderr)
        raise SystemExit(result.returncode)
    return {"installed": True, "name": name, "schedule": schedule}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Target Hermes workspace root")
    parser.add_argument("--check", action="store_true", help="Validate expected files/folders exist")
    parser.add_argument("--install-enzyme-config", action="store_true", help="Write/update managed vault mapping in ~/.enzyme/config.toml")
    parser.add_argument("--enzyme-config", default=str(Path.home() / ".enzyme" / "config.toml"), help="Enzyme config path")
    parser.add_argument("--install-enzyme-cli", action="store_true", help="Install the Enzyme CLI with the official installer if missing")
    parser.add_argument("--write-enzyme-env", action="store_true", help="Write memory/enzyme-env.sh with OpenRouter-compatible Enzyme environment exports")
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY", help="Existing environment variable that contains the OpenAI-compatible API key")
    parser.add_argument("--enzyme-bin", default=shutil.which("enzyme") or "enzyme", help="Enzyme executable")
    parser.add_argument(
        "--run-enzyme",
        choices=["none", "init", "refresh", "status"],
        default="none",
        help="Run an Enzyme command against agent-memory-vault after setup",
    )
    parser.add_argument("--install-cron", action="store_true", help="Install the default 2am Hermes heartbeat cron")
    parser.add_argument("--cron-schedule", default=DEFAULT_CRON_SCHEDULE, help="Hermes heartbeat cron schedule")
    parser.add_argument("--cron-name", default=DEFAULT_CRON_NAME, help="Hermes heartbeat cron name")
    parser.add_argument("--hermes-bin", default=shutil.which("hermes") or "hermes", help="Hermes executable")
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
    enzyme_config = Path(args.enzyme_config).expanduser().resolve()
    if args.install_enzyme_config:
        install_enzyme_config(vault, enzyme_config)
    enzyme_cli_result = None
    if args.install_enzyme_cli:
        enzyme_cli_result = install_enzyme_cli(args.enzyme_bin)
        if enzyme_cli_result.get("enzymeBin"):
            args.enzyme_bin = enzyme_cli_result["enzymeBin"]
    enzyme_env_path = None
    if args.write_enzyme_env:
        enzyme_env_path = write_enzyme_env(root, args.api_key_env)
    enzyme_run_result = run_enzyme(vault, args.run_enzyme, args.enzyme_bin, args.api_key_env)
    cron_result = None
    if args.install_cron:
        cron_result = install_cron(root, args.cron_schedule, args.cron_name, args.hermes_bin)

    missing = [str(folder) for folder in folders if not folder.exists()]
    if args.check and missing:
        raise SystemExit({"ok": False, "missing": missing})
    print({
        "ok": True,
        "vault": str(vault),
        "enzymeExample": str(vault / "enzyme-config.example.toml"),
        "enzymeConfigInstalled": bool(args.install_enzyme_config),
        "enzymeConfig": str(enzyme_config) if args.install_enzyme_config else None,
        "enzymeCli": enzyme_cli_result,
        "enzymeEnv": str(enzyme_env_path) if enzyme_env_path else None,
        "enzymeRun": enzyme_run_result,
        "cron": cron_result,
    })


if __name__ == "__main__":
    main()
