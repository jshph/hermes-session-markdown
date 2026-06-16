# hermes-agent-memory-workspace

Hermes skill for setting up a small agent memory workspace with session Markdown, forum observations, IRL notes, Enzyme profile mapping, and stage-only Petri/nudge evaluation.

## Install with Hermes

Install the workspace setup/runtime skill directly:

```bash
hermes skills inspect jshph/hermes-session-markdown/skills/hermes-agent-memory-workspace
hermes skills install jshph/hermes-session-markdown/skills/hermes-agent-memory-workspace
```

Or add the repo as a tap and install by skill name:

```bash
hermes skills tap add jshph/hermes-session-markdown
hermes skills install jshph/hermes-session-markdown/hermes-agent-memory-workspace
```

The session renderer is an internal script used by the workspace skill, not a separate installable skill.
