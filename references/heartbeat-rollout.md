# Heartbeat rollout

Use this reference when installing the renderer for test users or a Hermes agent workspace.

## Rollout shape

V0 heartbeat responsibility:

```txt
new Hermes sessions -> deterministic Markdown transcript files
```

Not included in v0:

- summarizing the user
- extracting wants/open loops
- creating Index intents/premises
- sending messages or accepting opportunities

## Manual test first

From the target workspace:

```bash
mkdir -p memory/session-markdown
python3 /path/to/hermes-session-markdown/scripts/render_hermes_sessions.py \
  --input "${HERMES_HOME:-$HOME/.hermes}/sessions" \
  --output ./memory/session-markdown \
  --state ./memory/session-markdown/.render-state.json \
  --mode new
```

Inspect one output file before scheduling.

## Suggested heartbeat

Install one Hermes cron/heartbeat after manual validation:

- Name: `Hermes — session markdown export`
- Cadence: hourly for active test users, nightly for conservative rollout.
- Command/action: run the renderer with `--mode new`.
- Output root: workspace-local `memory/session-markdown/`.

Pseudo prompt for an agent-managed heartbeat:

```txt
Render new Hermes session JSON/JSONL files into workspace-local Markdown transcripts.
Use the hermes-session-markdown renderer. Do not summarize, infer preferences, or write Index intents.
Verify generated files have created: "[[YYYY-MM-DD]]" frontmatter and no obvious secrets.
```

## Safety defaults

- Use `--mode new` with a state file to avoid rewriting everything each run.
- Keep raw JSON/JSONL in Hermes-owned storage; Markdown copies are for inspectability.
- Keep output local to the user/agent workspace.
- Redact secrets by default.
- Collapse large tool outputs unless a test user explicitly asks for full near-raw logs.
- Log counts and paths, not transcript contents.

## Test-user checklist

Ask the receiving agent to report:

1. Hermes home detected.
2. Number of sessions scanned and Markdown files written.
3. Output folder path.
4. One frontmatter sample with `created: "[[YYYY-MM-DD]]"`.
5. Whether any files were skipped/redacted/collapsed.
6. Whether Enzyme config was created or where Enzyme should point.
