---
name: hermes-session-markdown
description: Render Hermes/Codex/Pi JSON or JSONL session logs into raw or near-raw user-inspectable Markdown files with WikiLink date frontmatter. Use when Codex needs to set up session-log Markdown exports, heartbeat/cron exports, or Enzyme-ready transcript folders without summarizing or inferring user preferences.
---

# Hermes Session Markdown

Render sessions; do not interpret them.

The output is a debuggable transcript layer. Keep summaries, observations, wants, and Index promotion out of these files.

## Run

```bash
python3 scripts/render_hermes_sessions.py \
  --input "${HERMES_HOME:-$HOME/.hermes}/sessions" \
  --output ./memory/session-markdown \
  --state ./memory/session-markdown/.render-state.json \
  --mode new
```

The renderer writes:

- `memory/session-markdown/YYYY-MM-DD/*.md`
- `memory/session-markdown/index.md`
- `memory/session-markdown/enzyme.session-markdown.yaml`

Each transcript file includes:

```yaml
created: "[[YYYY-MM-DD]]"
derived_observations: false
```

## Rules

- Preserve role, timestamp, order, source file, session id, and tool-call boundaries.
- Redact obvious secrets by default.
- Collapse huge tool outputs by default; keep hashes/pointers.
- Keep derived notes elsewhere, e.g. `memory/distillations/`.
- Do not write Index intents or premises.

## References

- `references/heartbeat-rollout.md` for installing as a Hermes heartbeat/cron.
- `references/markdown-format.md` for the transcript and Enzyme config shape.
