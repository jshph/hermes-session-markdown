#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

from common import memory_dir, now_iso, read_json, safe_read, state_path, today, vault_root, wikilink_date, write_json


PERSON_RE = re.compile(r"\[\[([A-Z][^]\n]{1,80})\]\]")
EDGEOS_BASE = "https://api.edgeos.world/api/v1"
EDGE_ESMERALDA_POPUP_ID = "43746fd0-bce2-472b-93e4-a438177b2dff"
EDGE_ESMERALDA_EVENT_BASE_URL = "https://edgecity.simplefi.tech/portal/edge-esmeralda-2026/events"
PACIFIC_TZ = "America/Los_Angeles"


def recent_session_text(session_root: Path, limit: int = 5) -> str:
    files = sorted(session_root.rglob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
    return "\n\n".join(safe_read(path)[:3000] for path in files)


def pacific_day_bounds(day: str) -> tuple[str, str]:
    # EdgeOS expects UTC instants. For this deployment we only need Pacific dates.
    # Avoid third-party deps; noon UTC offset is enough for PDT/PST day bounds here.
    y, m, d = [int(part) for part in day.split("-")]
    start_local = dt.datetime(y, m, d, 0, 0)
    # Determine offset from Intl-equivalent zone by asking the system zoneinfo.
    try:
        from zoneinfo import ZoneInfo

        tz = ZoneInfo(PACIFIC_TZ)
        start = start_local.replace(tzinfo=tz).astimezone(dt.timezone.utc)
        end = (start_local + dt.timedelta(days=1)).replace(tzinfo=tz).astimezone(dt.timezone.utc)
    except Exception:
        start = dt.datetime(y, m, d, 7, 0, tzinfo=dt.timezone.utc)
        end = start + dt.timedelta(days=1)
    return (
        start.isoformat(timespec="seconds").replace("+00:00", "Z"),
        end.isoformat(timespec="seconds").replace("+00:00", "Z"),
    )


def format_pacific(iso_value: str) -> str:
    try:
        from zoneinfo import ZoneInfo

        parsed = dt.datetime.fromisoformat(iso_value.replace("Z", "+00:00"))
        local = parsed.astimezone(ZoneInfo(PACIFIC_TZ))
        return local.strftime("%-I:%M %p %Z")
    except Exception:
        return iso_value


def edgeos_get_events(day: str, rsvped_only: bool) -> tuple[list[dict], str]:
    token = os.environ.get("EDGEOS_API_KEY", "").strip()
    if not token:
        return [], "unavailable:no-edgeos-api-key"
    popup_id = os.environ.get("EDGEOS_POPUP_ID", EDGE_ESMERALDA_POPUP_ID).strip()
    start_iso, end_iso = pacific_day_bounds(day)
    params = {
        "popup_id": popup_id,
        "event_status": "published",
        "start_after": start_iso,
        "start_before": end_iso,
        "limit": "100",
    }
    if rsvped_only:
        params["rsvped_only"] = "true"
    url = f"{EDGEOS_BASE}/events/portal/events?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
        results = data.get("results", [])
        return results if isinstance(results, list) else [], "edgeos"
    except Exception as exc:
        return [], f"unavailable:{type(exc).__name__}"


def event_line(event: dict, reason: str) -> str:
    title = str(event.get("title") or "Untitled event")
    event_id = event.get("id")
    url = f"{EDGE_ESMERALDA_EVENT_BASE_URL}/{event_id}" if event_id else ""
    start = str(event.get("start_time") or "")
    venue = event.get("venue_title") or event.get("custom_location_name") or ""
    parts = [format_pacific(start), f"[{title}]({url})" if url else title]
    if venue:
        parts.append(f"at {venue}")
    return f"- {' - '.join(part for part in parts if part)} ({reason})"


def edgeos_calendar_context(day: str) -> tuple[str, dict]:
    events, event_source = edgeos_get_events(day, False)
    rsvps, rsvp_source = edgeos_get_events(day, True)
    highlighted = [event for event in events if event.get("highlighted") is True][:6]
    if not highlighted:
        highlighted = sorted(events, key=lambda event: str(event.get("start_time") or ""))[:6]
    lines = ["## EdgeOS calendar"]
    if rsvps:
        lines.append("\n### RSVPs")
        lines.extend(event_line(event, "RSVP") for event in sorted(rsvps, key=lambda event: str(event.get("start_time") or ""))[:6])
    if highlighted:
        lines.append("\n### Highlighted / selected events")
        lines.extend(event_line(event, "calendar") for event in sorted(highlighted, key=lambda event: str(event.get("start_time") or ""))[:6])
    if not rsvps and not highlighted:
        lines.append("\n- No live EdgeOS events available from this run.")
    return "\n".join(lines), {
        "calendarSource": event_source,
        "rsvpSource": rsvp_source,
        "eventCount": len(events),
        "rsvpCount": len(rsvps),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--date", default=today())
    parser.add_argument("--calendar", default="memory/calendar-context.md")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    vault = vault_root(root)
    session_text = recent_session_text(vault / "hermes" / "sessions")
    local_calendar_text = safe_read(root / args.calendar)
    edgeos_text, edgeos_meta = edgeos_calendar_context(args.date)
    calendar_text = "\n\n".join(part for part in [local_calendar_text.strip(), edgeos_text.strip()] if part)
    people = sorted(set(PERSON_RE.findall(session_text + "\n" + calendar_text)))[:20]
    out = memory_dir(root) / "hermes-workspace-preprocessed" / "irl" / f"{args.date}.md"

    people_lines = "\n".join(f'- [[{name}]] came up in recent Hermes/calendar context. Treat as context, not a confirmed want.' for name in people)
    if not people_lines:
        people_lines = "- No grounded people/opportunity signal found in configured sources."

    people_frontmatter = "\n".join(f'  - "[[{name}]]"' for name in people) if people else "people: []"
    people_block = f"people:\n{people_frontmatter}" if people else people_frontmatter

    note = f"""---
created: "{wikilink_date(args.date)}"
source: telegram-calendar-preprocessed
{people_block}
---

# IRL context for agent distillation - {wikilink_date(args.date)}

This is bounded source context for the heartbeat agent. Do not copy it wholesale into the vault.

## Calendar / events

{calendar_text.strip()[:1200] if calendar_text.strip() else "- No configured calendar/event context for this period."}

Calendar diagnostics: `{json.dumps(edgeos_meta, sort_keys=True)}`

## People / opportunities

{people_lines}

## Recent session excerpt

{session_text.strip()[:1800] if session_text.strip() else "- No recent rendered Hermes session Markdown found."}

## Uncertainty

- Preserve uncertainty plainly: attended, maybe attended, RSVP'd, mentioned, proposed, or unclear.

## Distillation target

- Write `agent-memory-vault/irl/{args.date}.md`.
- Capture people, events, opportunities, and uncertainty from Telegram/calendar context.
- Create person/event subnotes only when an entity recurs enough to deserve one.
"""

    if args.dry_run:
        print({"out": str(out), "people": people, "edgeos": edgeos_meta, "chars": len(note)})
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(note.rstrip() + "\n", encoding="utf-8")
    state = read_json(state_path(root))
    state.setdefault("irlPreprocess", []).append({"at": now_iso(), "date": args.date, "path": str(out), "people": people, "edgeos": edgeos_meta})
    write_json(state_path(root), state)
    print({"wrote": str(out), "people": people})


if __name__ == "__main__":
    main()
