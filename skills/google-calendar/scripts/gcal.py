#!/usr/bin/env python3
"""
gcal.py - Google Calendar Management Tool (CRUD + Sharing)

Usage:
  gcal.py list [today|tomorrow|week|next-week|month]
  gcal.py get <event_id>
  gcal.py create <summary> <start_iso> [end_iso] [description] [--attendees a@x.com b@x.com ...]
  gcal.py update <event_id> <field> <value>   # field: summary|description|start|end|location
  gcal.py delete <event_id>
  gcal.py quick <natural language text>
  gcal.py share <email> [reader|writer|owner|freeBusyReader]
  gcal.py share-list

Credentials file: ~/.openclaw/workspace/.credentials/google-calendar.json
"""

import sys
import os
import json
import re
from datetime import datetime, timedelta, timezone, tzinfo
from pathlib import Path

# Re-exec under the venv Python if available (shebang can't use ~)
_SKILL_DIR = Path(__file__).resolve().parent.parent
_VENV_PYTHON = _SKILL_DIR / ".venv/bin/python3"
if _VENV_PYTHON.exists() and sys.executable != str(_VENV_PYTHON):
    os.execv(str(_VENV_PYTHON), [str(_VENV_PYTHON)] + sys.argv)

try:
    from dateutil import parser as date_parser
    from dateutil.relativedelta import relativedelta
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ImportError as e:
    VENV = Path.home() / ".openclaw/skills/google-calendar/.venv"
    print(f"[ERROR] Missing dependency: {e}")
    if not VENV.exists():
        print(f"Run the following to set up the virtual environment:\n"
              f"  python3 -m venv {VENV}\n"
              f"  {VENV}/bin/pip install google-api-python-client google-auth-oauthlib python-dateutil")
    else:
        print(f"Run: {VENV}/bin/pip install google-api-python-client google-auth-oauthlib python-dateutil")
    sys.exit(1)

CREDENTIALS_FILE = Path.home() / ".openclaw/workspace/.credentials/google-calendar.json"
SCOPES = ["https://www.googleapis.com/auth/calendar"]
TIMEZONE = "Asia/Dubai"  # GST UTC+4 — default timezone for all operations
TZ_OFFSET = "+04:00"     # UTC offset string for Asia/Dubai
GST = timezone(timedelta(hours=4))  # Asia/Dubai fixed offset for naive datetime localisation


# ── Auth ───────────────────────────────────────────────────────────────────────

def get_service():
    if not CREDENTIALS_FILE.exists():
        print(f"[ERROR] Credentials file not found: {CREDENTIALS_FILE}", file=sys.stderr)
        print(f"\nTo set up Google Calendar credentials:\n"
              f"1. Go to https://console.cloud.google.com/ → APIs & Services → Credentials\n"
              f"2. Create an OAuth 2.0 Client ID (type: Desktop app)\n"
              f"3. Enable the Google Calendar API for your project\n"
              f"4. Obtain a refresh_token with scope https://www.googleapis.com/auth/calendar\n"
              f"5. Save the JSON file to {CREDENTIALS_FILE} with fields:\n"
              f"   client_id, client_secret, refresh_token, token_uri\n"
              f"\nExample:\n"
              f'  mkdir -p {CREDENTIALS_FILE.parent}\n'
              f'  cat > {CREDENTIALS_FILE} << \'EOF\'\n'
              f'  {{\n'
              f'    "client_id": "YOUR_CLIENT_ID",\n'
              f'    "client_secret": "YOUR_CLIENT_SECRET",\n'
              f'    "refresh_token": "YOUR_REFRESH_TOKEN",\n'
              f'    "token_uri": "https://oauth2.googleapis.com/token"\n'
              f'  }}\n'
              f'  EOF', file=sys.stderr)
        sys.exit(1)

    with open(CREDENTIALS_FILE) as f:
        cred_data = json.load(f)

    creds = Credentials(
        token=cred_data.get("token"),
        refresh_token=cred_data["refresh_token"],
        token_uri=cred_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=cred_data["client_id"],
        client_secret=cred_data["client_secret"],
        scopes=SCOPES,
    )

    if not creds.valid:
        creds.refresh(Request())
        cred_data["token"] = creds.token
        with open(CREDENTIALS_FILE, "w") as f:
            json.dump(cred_data, f, indent=2)

    return build("calendar", "v3", credentials=creds)


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_time_range(period: str):
    # Use current time in Asia/Dubai (GST, UTC+4) so day boundaries are correct
    now = datetime.now(tz=GST)
    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1) - timedelta(seconds=1)
    elif period == "tomorrow":
        start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1) - timedelta(seconds=1)
    elif period == "week":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7) - timedelta(seconds=1)
    elif period == "next-week":
        start = (now + timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7) - timedelta(seconds=1)
    elif period == "month":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + relativedelta(months=1) - timedelta(seconds=1)
    else:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1) - timedelta(seconds=1)
    return start, end


def fmt_dt(dt_str: str) -> str:
    """Parse an ISO datetime string and display it in GST (Asia/Dubai, UTC+4)."""
    try:
        if "T" in dt_str:
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            # Convert to Asia/Dubai (UTC+4) for display
            dt_gst = dt.astimezone(GST)
            return dt_gst.strftime("%Y-%m-%d %H:%M GST")
        return dt_str
    except Exception:
        return dt_str


def strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", text)).strip()


def print_event(ev: dict):
    print(f"  Title     : {ev.get('summary', '(no title)')}")
    start = ev.get("start", {}).get("dateTime") or ev.get("start", {}).get("date", "")
    end   = ev.get("end",   {}).get("dateTime") or ev.get("end",   {}).get("date", "")
    print(f"  Time      : {fmt_dt(start)} ~ {fmt_dt(end)}")
    loc = ev.get("location", "")
    if loc:
        print(f"  Location  : {loc}")
    desc = strip_html(ev.get("description", ""))
    if desc:
        print(f"  Body      : {desc[:200]}")
    attendees = ev.get("attendees", [])
    if attendees:
        emails = [a.get("email", "") for a in attendees]
        print(f"  Attendees : {', '.join(emails)}")
    print(f"  Link      : {ev.get('htmlLink', 'N/A')}")
    print(f"  ID        : {ev.get('id', '')}")


# ── Commands ───────────────────────────────────────────────────────────────────

def cmd_list(service, period="today"):
    start, end = get_time_range(period)
    result = service.events().list(
        calendarId="primary",
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy="startTime",
        timeZone=TIMEZONE,
    ).execute()

    events = result.get("items", [])
    period_label = {"today": "Today", "tomorrow": "Tomorrow", "week": "This week", "next-week": "Next week", "month": "This month"}
    label = period_label.get(period, period)

    if not events:
        print(f"📅 No events for {label}")
        return

    print(f"📅 {label}'s events ({len(events)} total):\n")
    for ev in events:
        start_dt = ev.get("start", {}).get("dateTime") or ev.get("start", {}).get("date", "")
        end_dt   = ev.get("end",   {}).get("dateTime") or ev.get("end",   {}).get("date", "")
        summary  = ev.get("summary", "(no title)")
        print(f"  {fmt_dt(start_dt)} ~ {fmt_dt(end_dt)}  {summary}")
        print(f"    id: {ev.get('id', '')}")
    print()


def cmd_get(service, event_id: str):
    ev = service.events().get(calendarId="primary", eventId=event_id).execute()
    print("[Event Details]")
    print_event(ev)


def build_attendees(emails):
    """Convert email list (supports comma-separated strings or list) to Google Calendar attendees format."""
    result = []
    for item in emails:
        for email in item.split(","):
            email = email.strip()
            if email:
                result.append({"email": email})
    return result


def localize_gst(dt: datetime) -> datetime:
    """If dt is naive (no tzinfo), attach the Asia/Dubai UTC+4 offset so isoformat() is correct."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=GST)
    return dt


def cmd_create(service, summary: str, start_str: str, end_str: str = None, description: str = None, attendees: list = None):
    start = localize_gst(date_parser.parse(start_str))
    end   = localize_gst(date_parser.parse(end_str)) if end_str else start + timedelta(hours=1)

    event = {
        "summary": summary,
        "start": {"dateTime": start.isoformat(), "timeZone": TIMEZONE},
        "end":   {"dateTime": end.isoformat(),   "timeZone": TIMEZONE},
    }
    if description:
        event["description"] = description
    if attendees:
        event["attendees"] = build_attendees(attendees)

    result = service.events().insert(calendarId="primary", body=event, sendUpdates="all").execute()
    print("[OK] Event created")
    print_event(result)


def cmd_update(service, event_id: str, field: str, value: str):
    ev = service.events().get(calendarId="primary", eventId=event_id).execute()

    if field == "summary":
        ev["summary"] = value
    elif field == "description":
        ev["description"] = value
    elif field in ("start", "end"):
        dt = localize_gst(date_parser.parse(value))
        ev[field] = {"dateTime": dt.isoformat(), "timeZone": TIMEZONE}
    elif field == "location":
        ev["location"] = value
    else:
        print(f"[ERROR] Unsupported field '{field}'. Available: summary, description, start, end, location")
        sys.exit(1)

    result = service.events().update(calendarId="primary", eventId=event_id, body=ev).execute()
    print("[OK] Event updated")
    print_event(result)


def cmd_delete(service, event_id: str):
    ev = service.events().get(calendarId="primary", eventId=event_id).execute()
    summary = ev.get("summary", "(no title)")
    service.events().delete(calendarId="primary", eventId=event_id).execute()
    print(f"[OK] Event deleted: {summary} ({event_id})")


def cmd_quick(service, text: str):
    result = service.events().quickAdd(calendarId="primary", text=text).execute()
    print("[OK] Event created (quick add)")
    print_event(result)


def cmd_share_list(service):
    result = service.acl().list(calendarId="primary").execute()
    items = result.get("items", [])
    if not items:
        print("📋 No sharing permissions")
        return
    role_label = {"reader": "Read-only", "writer": "Read/write", "owner": "Owner", "freeBusyReader": "Free/busy only"}
    print(f"📋 Calendar sharing permissions ({len(items)} total):\n")
    for item in items:
        scope = item.get("scope", {})
        scope_type = scope.get("type", "")
        value = scope.get("value", "")
        role = item.get("role", "")
        if scope_type == "default" or value == "default":
            continue
        print(f"  {value}  [{role_label.get(role, role)}]")
        print(f"    acl-id: {item.get('id', '')}")
    print()


def cmd_share(service, email: str, role: str = "reader"):
    valid = ["reader", "writer", "owner", "freeBusyReader"]
    if role not in valid:
        print(f"[ERROR] Invalid role '{role}'. Available: {', '.join(valid)}")
        sys.exit(1)
    rule = {"role": role, "scope": {"type": "user", "value": email}}
    service.acl().insert(calendarId="primary", body=rule, sendNotifications=True).execute()
    role_label = {"reader": "Read-only", "writer": "Read/write", "owner": "Owner", "freeBusyReader": "Free/busy only"}
    print(f"[OK] Calendar shared with {email} (permission: {role_label.get(role, role)})")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    service = get_service()

    if cmd == "list":
        period = sys.argv[2] if len(sys.argv) > 2 else "today"
        cmd_list(service, period)
    elif cmd == "get":
        if len(sys.argv) < 3:
            print("Usage: gcal.py get <event_id>"); sys.exit(1)
        cmd_get(service, sys.argv[2])
    elif cmd == "create":
        if len(sys.argv) < 4:
            print("Usage: gcal.py create <summary> <start> [end] [description] [--attendees a@x.com ...]"); sys.exit(1)
        args = sys.argv[2:]
        attendees = []
        if "--attendees" in args:
            idx = args.index("--attendees")
            attendees = args[idx + 1:]
            args = args[:idx]
        summary     = args[0]
        start_str   = args[1] if len(args) > 1 else None
        end_str     = args[2] if len(args) > 2 else None
        description = args[3] if len(args) > 3 else None
        cmd_create(service, summary, start_str, end_str, description, attendees if attendees else None)
    elif cmd == "update":
        if len(sys.argv) < 5:
            print("Usage: gcal.py update <event_id> <field> <value>"); sys.exit(1)
        cmd_update(service, sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "delete":
        if len(sys.argv) < 3:
            print("Usage: gcal.py delete <event_id>"); sys.exit(1)
        cmd_delete(service, sys.argv[2])
    elif cmd == "quick":
        if len(sys.argv) < 3:
            print("Usage: gcal.py quick <text>"); sys.exit(1)
        cmd_quick(service, " ".join(sys.argv[2:]))
    elif cmd == "share":
        if len(sys.argv) < 3:
            print("Usage: gcal.py share <email> [role]"); sys.exit(1)
        role = sys.argv[3] if len(sys.argv) > 3 else "reader"
        cmd_share(service, sys.argv[2], role)
    elif cmd == "share-list":
        cmd_share_list(service)
    else:
        print(f"[ERROR] Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
