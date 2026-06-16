---
name: hermes-agent-memory-workspace
description: Install and operate a small Hermes agent memory vault with Hermes session Markdown, forum observations, IRL notes, Enzyme profile mapping, and stage-only Petri/nudge evaluation.
---

# Hermes Agent Memory Workspace

Set up and run a small local Markdown vault for a Hermes agent:

```text
agent-memory-vault/
  hermes/sessions/YYYY-MM-DD/*.md
  forum/YYYY-MM-DD.md
  irl/YYYY-MM-DD.md
  irl/people/*.md
  irl/events/*.md
```

Use this skill when installing the workspace for a Hermes agent, wiring the default heartbeat cron, or running the consolidation loop. Deterministic scripts prepare bounded source context; the cron's LLM agent reads that context and writes the actual `forum/` and `irl/` distillations. The skill does not auto-send Telegram messages.

## Full Install

First make sure this skill is installed as a Hermes skill named `hermes-agent-memory-workspace`. The cron is created with `--skill hermes-agent-memory-workspace`; if Hermes cannot load that skill name, the scheduled run will fail even if the scripts exist on disk.

Then run setup from the target Hermes workspace root, usually `/opt/data` on an AgentVillage machine. If running from another directory, pass `--root /opt/data`.

```bash
python3 skills/hermes-agent-memory-workspace/scripts/setup_workspace.py \
  --install-enzyme-config \
  --install-cron
```

This creates the vault folders, `memory/hermes-workspace-state.json`, `memory/hermes-workspace-context.json`, writes `agent-memory-vault/enzyme-config.example.toml`, installs the managed Enzyme profile mapping into `~/.enzyme/config.toml`, and creates one Hermes cron:

- name: `Hermes agent memory heartbeat`
- schedule: `0 2 * * *`
- skill: `hermes-agent-memory-workspace`
- script: `skills/hermes-agent-memory-workspace/scripts/cron_prepare.py`
- delivery: none

For a non-mutating install check, omit both install flags:

```bash
python3 skills/hermes-agent-memory-workspace/scripts/setup_workspace.py --check
```

## Session boundary

Session export follows a strict renderer contract: render sessions; do not interpret them. `hermes/sessions/` is provenance only. The heartbeat agent performs interpretation later, into `forum/` and `irl/`.

## Cron Behavior

The installed cron is intentionally LLM-driven. `cron_prepare.py` is not the distiller. It runs before the agent, renders sessions, prepares IRL/forum JSON context, and prints that context into the cron prompt. Hermes then starts a fresh agent session with this skill loaded.

On each 2am run:

1. `cron_prepare.py` renders `agent-memory-vault/hermes/sessions/YYYY-MM-DD/*.md`.
2. `cron_prepare.py` updates `memory/hermes-workspace-context.json` with bounded IRL/forum source context.
3. The heartbeat agent reads the injected context plus recent rendered sessions.
4. The heartbeat agent writes or updates:
   - `agent-memory-vault/forum/YYYY-MM-DD.md`
   - `agent-memory-vault/irl/YYYY-MM-DD.md`
5. The heartbeat agent runs:

   ```bash
   python3 skills/hermes-agent-memory-workspace/scripts/workspace_loop.py --prepare
   ```

The notes should stay concise, grounded, and uncertainty-aware. `memory/hermes-workspace-context.json` is runtime scratch, not memory; do not copy it wholesale into the vault. There is no default Telegram delivery cron or morning watchdog.

`prepare_irl_context.py` pulls calendar and RSVP context from the live EdgeOS API. For Edge Esmeralda, the default popup id is `43746fd0-bce2-472b-93e4-a438177b2dff`; override with `EDGEOS_POPUP_ID` for another popup. `EDGEOS_API_KEY` must be present for live calendar context.

## Policy

- Keep operational state in `memory/*.json`; do not add state/outbox/derived folders to the conceptual vault.
- `hermes/sessions/` is transcript-shaped. Preserve role, timestamp, order, and source context; do not infer preferences, wants, or durable memory there.
- `forum/` is written by the heartbeat agent and observes this agent's forum contributions interacting with other perspectives.
- `irl/` is written by the heartbeat agent and captures calendar, people, events, opportunities, and uncertainty from Telegram/calendar context.
- `memory/hermes-workspace-context.json` and `memory/hermes-workspace-state.json` are operational scratch/state, not conceptual vault folders.
- EdgeOS calendar access uses `EDGEOS_API_KEY` for read-only event and RSVP context. Never print or store the token.
- Map `irl/` to Enzyme's `relational` profile; the folder name is `irl`, the catalyst profile remains `relational`.
- Enzyme profile assignment belongs in `~/.enzyme/config.toml`, not in session renderer sidecar files.
- Use Petri/Enzyme before a nudge. Nudge only for a fresh forum or IRL signal with a person/event/opportunity bridge, enough context to avoid guessing, no duplicate, and a small optional invitation.
- Quiet is the default. Record skip reasons instead of inventing copy.

## Validation

Run:

```bash
python3 skills/hermes-agent-memory-workspace/scripts/setup_workspace.py --check
python3 skills/hermes-agent-memory-workspace/scripts/cron_prepare.py
python3 skills/hermes-agent-memory-workspace/scripts/workspace_loop.py --prepare --dry-run
hermes cron list --all
hermes cron status
```

Verify:

- the cron list contains `Hermes agent memory heartbeat`;
- the cron has no delivery target;
- the script points at `cron_prepare.py`;
- no raw secrets appear in stdout or vault notes;
- no extra top-level vault folders are created;
- staging is idempotent and records skip reasons;
- the visible budget remains morning brief plus at most one non-brief interruption per day.

To run the cron immediately, get its id from `hermes cron list --all`, queue it, then tick the scheduler:

```bash
hermes cron run <job-id>
hermes cron tick
```
