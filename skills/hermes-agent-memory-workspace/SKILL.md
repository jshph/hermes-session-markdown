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

Use this skill when installing the workspace for a Hermes agent, wiring heartbeats/crons, or running the consolidation loop. Deterministic scripts preprocess bounded source material; the heartbeat agent reads that material and writes the actual `forum/` and `irl/` distillations. The skill does not auto-send Telegram messages.

## Install

From the target Hermes workspace:

```bash
python3 skills/hermes-agent-memory-workspace/scripts/setup_workspace.py
```

This creates the vault folders, `memory/hermes-workspace-state.json`, and `memory/hermes-workspace-context.json`. It also writes `agent-memory-vault/enzyme-config.example.toml`; copy that mapping into `~/.enzyme/config.toml` after reviewing the vault path.

## Session boundary

Session export follows the `hermes-session-markdown` contract: render sessions; do not interpret them. `hermes/sessions/` is provenance only. The heartbeat agent performs interpretation later, into `forum/` and `irl/`.

## Heartbeats

Use Hermes crons as wakeups. Deterministic scripts prepare bounded inputs and state; the heartbeat agent does the interpretive distillation.

1. Vault write/refresh, non-delivering:

```bash
python3 skills/hermes-agent-memory-workspace/scripts/render_vault_sessions.py
python3 skills/hermes-agent-memory-workspace/scripts/prepare_forum_context.py
python3 skills/hermes-agent-memory-workspace/scripts/prepare_irl_context.py
python3 skills/hermes-agent-memory-workspace/scripts/workspace_loop.py --prepare
```

`prepare_irl_context.py` pulls calendar and RSVP context from the live EdgeOS API. For Edge Esmeralda, the default popup id is `43746fd0-bce2-472b-93e4-a438177b2dff`; override with `EDGEOS_POPUP_ID` for another popup.

Between preprocessing and `workspace_loop.py --prepare`, the heartbeat agent must read:

- `memory/hermes-workspace-preprocessed/forum/YYYY-MM-DD.md`
- `memory/hermes-workspace-preprocessed/irl/YYYY-MM-DD.md`
- recent `agent-memory-vault/hermes/sessions/YYYY-MM-DD/*.md`

Then it writes or updates:

- `agent-memory-vault/forum/YYYY-MM-DD.md`
- `agent-memory-vault/irl/YYYY-MM-DD.md`

The agent should keep those notes concise, grounded, and uncertainty-aware. It should not copy the whole preprocessed context into the vault.

2. Nudge send, Telegram delivery path:

```bash
python3 skills/hermes-agent-memory-workspace/scripts/workspace_loop.py --send
```

The send mode is stage-only by default: it emits `[SILENT]` unless an approved staged file exists. Keep direct Telegram delivery behind the host's explicit approval/review path.

## Policy

- Keep operational state in `memory/*.json`; do not add state/outbox/derived folders to the conceptual vault.
- `hermes/sessions/` is transcript-shaped. Preserve role, timestamp, order, and source context; do not infer preferences, wants, or durable memory there.
- `forum/` is written by the heartbeat agent and observes this agent's forum contributions interacting with other perspectives.
- `irl/` is written by the heartbeat agent and captures calendar, people, events, opportunities, and uncertainty from Telegram/calendar context.
- Preprocessed files under `memory/hermes-workspace-preprocessed/` are inputs, not final memory.
- EdgeOS calendar access uses `EDGEOS_API_KEY` for read-only event and RSVP context. Never print or store the token.
- Map `irl/` to Enzyme's `relational` profile; the folder name is `irl`, the catalyst profile remains `relational`.
- Use Petri/Enzyme before a nudge. Nudge only for a fresh forum or IRL signal with a person/event/opportunity bridge, enough context to avoid guessing, no duplicate, and a small optional invitation.
- Quiet is the default. Record skip reasons instead of inventing copy.

## Validation

Run:

```bash
python3 skills/hermes-agent-memory-workspace/scripts/setup_workspace.py --check
python3 skills/hermes-agent-memory-workspace/scripts/workspace_loop.py --prepare --dry-run
```

Verify no raw secrets, no extra top-level vault folders, idempotent staging, stale-card skipping, and the visible budget of morning brief plus at most one non-brief interruption per day.
