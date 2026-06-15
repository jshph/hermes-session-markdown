# Markdown format and Enzyme handoff

Use this reference when deciding where rendered sessions live, what frontmatter to emit, and how to describe the folder to Enzyme.

## Folder layout

Prefer a raw transcript root separate from later distillations:

```txt
memory/
  session-markdown/
    .render-state.json
    index.md
    2026-06-15/
      2026-06-15--telegram--abc123.md
      2026-06-15--cron--def456.md
  distillations/          # optional later layer, not v0 raw dumps
```

## Frontmatter

Every rendered session Markdown file should begin with YAML frontmatter:

```yaml
---
created: "[[2026-06-15]]"
rendered_at: "2026-06-15T12:34:56Z"
session_id: "session_or_file_id"
source_kind: "hermes-jsonl"
source_file: "sessions/example.jsonl"
message_count: 42
privacy: "private-local"
derived_observations: false
---
```

Required field for Enzyme/date-aware vault tooling:

```yaml
created: "[[YYYY-MM-DD]]"
```

Use the session start date when available; otherwise use the first message timestamp; otherwise use the file mtime.

## Transcript body

Use stable headings and message anchors:

```md
# Hermes Session session_abc123

- Created: [[2026-06-15]]
- Source: `sessions/session_abc123.jsonl`
- Messages: 42

## Messages

### m0001 · user · 2026-06-15T09:00:01Z

Message text.

### m0002 · assistant · 2026-06-15T09:00:03Z

Assistant text.

#### Tool calls

```json
[
  {"name": "example", "arguments": {}}
]
```

### m0003 · tool · 2026-06-15T09:00:04Z

> Tool output collapsed: 18342 chars, sha256: ...
```

Avoid sections titled “Observations,” “User preferences,” “Wants,” or “Intents” in raw transcript files.

## Enzyme handoff config

If Enzyme needs configuration, generate a workspace-local file such as `memory/session-markdown/enzyme.session-markdown.yaml`:

```yaml
vault:
  roots:
    - path: "memory/session-markdown"
      kind: "raw_session_transcripts"
frontmatter:
  created_field: "created"
  created_format: "wikilink-date"
  created_regex: '^\\[\\[\\d{4}-\\d{2}-\\d{2}\\]\\]$'
content:
  message_heading_regex: '^### m\\d{4} · (user|assistant|tool|system|session_meta) · '
  derived_observations: false
privacy:
  raw_transcripts: true
  local_only: true
  default_redactions: true
```

Enzyme should analyze structure and recurrence from the vault; it should not require the session renderer to infer user preferences.
