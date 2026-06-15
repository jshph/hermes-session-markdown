# hermes-session-markdown

Hermes skills for rendering Hermes/Codex/Pi JSON or JSONL session logs into Markdown and setting up a small Hermes agent memory workspace.

## Install with Hermes

Install the transcript renderer directly:

```bash
hermes skills inspect jshph/hermes-session-markdown/skills/hermes-session-markdown
hermes skills install jshph/hermes-session-markdown/skills/hermes-session-markdown
```

Install the agent memory workspace setup/runtime skill directly:

```bash
hermes skills inspect jshph/hermes-session-markdown/skills/hermes-agent-memory-workspace
hermes skills install jshph/hermes-session-markdown/skills/hermes-agent-memory-workspace
```

Or add the repo as a tap and install by skill name:

```bash
hermes skills tap add jshph/hermes-session-markdown
hermes skills install jshph/hermes-session-markdown/hermes-session-markdown
hermes skills install jshph/hermes-session-markdown/hermes-agent-memory-workspace
```

Installable skills live under `skills/`.
