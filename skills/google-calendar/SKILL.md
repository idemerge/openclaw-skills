---
name: google-calendar
description: Manage Google Calendar via Google Calendar API. Activate when the user asks to create, update, delete, or query Google events, or to share/manage calendar permissions. Supports natural language quick-add, full CRUD, and calendar sharing. See references/config.md for configuration.
---

# Google Calendar Skill

Manage Google Calendar via Google Calendar API v3 (CRUD + sharing).

## Setup

The script requires a Python virtual environment and Google OAuth credentials. Both are configured interactively through chat.

### Step 1: Install dependencies (run once)

When the skill is first used and the venv is missing, the script will print setup commands. Execute them:

```bash
python3 -m venv ~/.openclaw/skills/google-calendar/.venv
~/.openclaw/skills/google-calendar/.venv/bin/pip install google-api-python-client google-auth-oauthlib python-dateutil
```

### Step 2: Configure Google OAuth credentials

The script reads credentials from `~/.openclaw/workspace/.credentials/google-calendar.json`.

**When credentials are missing**, do NOT ask the user to edit files manually. Instead, collect the values in chat and write the file automatically:

1. Tell the user they need a Google OAuth credential. Briefly explain how to obtain one (see references/config.md).
2. Ask the user to provide these values in chat: `client_id`, `client_secret`, `refresh_token`
3. Once all three values are provided, write the credentials file:

```bash
mkdir -p ~/.openclaw/workspace/.credentials
cat > ~/.openclaw/workspace/.credentials/google-calendar.json << 'EOF'
{
  "client_id": "<client_id>",
  "client_secret": "<client_secret>",
  "refresh_token": "<refresh_token>",
  "token_uri": "https://oauth2.googleapis.com/token"
}
EOF
```

4. Verify by running `gcal.py list today`.

**Do not** instruct the user to manually create or edit the credentials file. Collect the values in chat and write the file for them.

## Tool Script

`scripts/gcal.py` — Auto-detects and uses the venv Python. Credentials at `~/.openclaw/workspace/.credentials/google-calendar.json`.

---

## 📌 Default Behavior Rules

> **Default timezone: `Asia/Dubai` (GST, UTC+4) — always.**
>
> - All event times are treated as Dubai time unless the user explicitly specifies a different timezone.
> - The `TIMEZONE` constant in `gcal.py` is set to `"Asia/Dubai"` — do not override it unless the user asks.
> - Display and discuss all times in GST. Never assume UTC or any other timezone.

> **Always call `session_status` before computing any date or time.**
>
> - Never guess or assume today's date — it may be wrong.
> - When the user says "today", "tomorrow", "next Monday", etc., **first call `session_status`** to get the current UTC time, then convert to GST (UTC+4) to determine the correct date.
> - This is mandatory for any relative date/time reference (today, tomorrow, next week, etc.).
> - Only use absolute dates the user explicitly provides (e.g. "2026-04-10") without calling `session_status`.

> **No default attendees when creating events.**
>
> - Do NOT add any attendees unless the user explicitly specifies them.
> - Do NOT run `share-list` or auto-add shared calendar users as attendees.
> - If the user wants attendees, they will say so.

> **Event titles and all text content must match the language of the user's message. Do not translate.**
>
> - User writes in Chinese → use Chinese for title/body
> - User writes in English → use English for title/body

---

## Commands

### List events
```bash
python3 ~/.openclaw/skills/google-calendar/scripts/gcal.py list [today|tomorrow|week|next-week|month]
```

### Get event details
```bash
python3 ~/.openclaw/skills/google-calendar/scripts/gcal.py get <event_id>
```

### Create event
```bash
python3 ~/.openclaw/skills/google-calendar/scripts/gcal.py create \
  "Title" "2026-03-30T14:00:00" ["2026-03-30T15:00:00"] ["Description"] \
  [--attendees a@x.com b@x.com ...]
```

> ⚠️ **`--attendees` format**: Multiple emails must be passed as **separate space-separated arguments**, not quoted together.
> - ✅ Correct: `--attendees a@x.com b@x.com c@x.com`
> - ❌ Wrong: `--attendees "a@x.com,b@x.com,c@x.com"`

### Quick add (natural language)
```bash
python3 ~/.openclaw/skills/google-calendar/scripts/gcal.py quick "Meeting tomorrow at 3pm"
```

### Update event
```bash
python3 ~/.openclaw/skills/google-calendar/scripts/gcal.py update <event_id> <field> <value>
# field: summary | description | start | end | location
```

### Delete event
```bash
python3 ~/.openclaw/skills/google-calendar/scripts/gcal.py delete <event_id>
```

### View sharing permissions
```bash
python3 ~/.openclaw/skills/google-calendar/scripts/gcal.py share-list
```

### Share calendar with user
```bash
python3 ~/.openclaw/skills/google-calendar/scripts/gcal.py share <email> [reader|writer|owner|freeBusyReader]
```

---

## Workflow

1. **Determining dates**: If the request involves relative dates (today, tomorrow, next week, etc.), call `session_status` first to get the real current date in GST — never guess.
2. **Creating events**: Do NOT add attendees unless the user explicitly asks.
3. Times in ISO8601 (`YYYY-MM-DDTHH:MM:SS`), default timezone `Asia/Dubai` (GST, UTC+4)
4. When event ID needed, use `list` first to get full ID, then operate
5. On auth error or missing credentials, collect `client_id`, `client_secret`, `refresh_token` from the user in chat and write the credentials file for them (see Setup section)

## Configuration

See `references/config.md`.
