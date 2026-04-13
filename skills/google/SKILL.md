---
name: google
description: Manage Google Calendar via Google Calendar API. Activate when the user asks to create, update, delete, or query Google events, or to share/manage calendar permissions. Also activate when the user wants to set up, update, or delete Google Calendar credentials, or change the timezone. Supports natural language quick-add, full CRUD, and calendar sharing. See references/config.md for credential management.
---

# Google Calendar Skill

Manage Google Calendar via Google Calendar API v3 (CRUD + sharing).

## Setup

The script requires a Python virtual environment, Google OAuth credentials, and a timezone setting. All are configured interactively through chat.

### Step 1: Install dependencies (run once)

When the skill is first used and the venv is missing, the script will print setup commands. Execute them:

```bash
python3 -m venv ~/.openclaw/skills/google/.venv
~/.openclaw/skills/google/.venv/bin/pip install google-api-python-client google-auth-oauthlib python-dateutil
```

### Step 2: Configure Google OAuth credentials

The script reads credentials from `~/.openclaw/workspace/.credentials/google.json`.

**When credentials are missing**, do NOT ask the user to edit files manually. Instead:

1. Read `references/config.md` for the full step-by-step guide
2. Walk the user through the setup in chat, one step at a time — wait for the user to complete each step before proceeding
3. Collect `client_id`, `client_secret`, `refresh_token` from the user in chat
4. Write the credentials file automatically:

```bash
mkdir -p ~/.openclaw/workspace/.credentials
cat > ~/.openclaw/workspace/.credentials/google.json << 'EOF'
{
  "client_id": "<client_id>",
  "client_secret": "<client_secret>",
  "refresh_token": "<refresh_token>",
  "token_uri": "https://oauth2.googleapis.com/token"
}
EOF
```

5. Verify by running `gcal.py list today`

**Do not** instruct the user to manually create or edit the credentials file. Collect the values in chat and write the file for them.

### Step 3: Set timezone

After credentials are configured, ask the user for their timezone. If not specified, default to `Asia/Dubai`.

```bash
mkdir -p ~/.openclaw/workspace/.credentials
cat > ~/.openclaw/workspace/.credentials/google-config.json << 'EOF'
{
  "timezone": "<timezone>"
}
EOF
```

Common timezone values: `Asia/Dubai`, `Asia/Shanghai`, `America/New_York`, `Europe/London`, `UTC`. Full list: [IANA Time Zone Database](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

Verify with `gcal.py show-config`.

### Update credentials

When the user wants to switch to a different Google account or update an expired refresh_token:

1. Ask which fields to update: `client_id`, `client_secret`, `refresh_token`, or all three
2. Collect the new values in chat
3. Overwrite the credentials file (same command as Step 2 above)
4. Verify with `gcal.py list today`

### Delete credentials

When the user wants to remove Google Calendar access:

```bash
rm ~/.openclaw/workspace/.credentials/google.json
rm ~/.openclaw/workspace/.credentials/google-config.json
```

Confirm removal by running `gcal.py list today` — it should report `[SETUP NEEDED]`.

### Check credential status

```bash
python3 ~/.openclaw/skills/google/scripts/gcal.py check-cred
```

Shows whether the credentials file exists and whether the current token is valid.

### Show current config

```bash
python3 ~/.openclaw/skills/google/scripts/gcal.py show-config
```

Shows the current timezone and config file location.

### Change timezone

Ask the user for the new timezone, then write the config file:

```bash
cat > ~/.openclaw/workspace/.credentials/google-config.json << 'EOF'
{
  "timezone": "<new_timezone>"
}
EOF
```

Verify with `gcal.py show-config`.

## Tool Script

`scripts/gcal.py` — Auto-detects and uses the venv Python. Config at `~/.openclaw/workspace/.credentials/google-config.json`, credentials at `~/.openclaw/workspace/.credentials/google.json`.

---

## 📌 Default Behavior Rules

> **Timezone is per-user config, default `Asia/Dubai` on first setup.**
>
> - Read timezone from `google-config.json`. If not configured, fall back to system local timezone.
> - Display and discuss all times in the configured timezone.
> - If the user mentions a different timezone for a specific event, use that timezone for that event only.

> **Always call `session_status` before computing any date or time.**
>
> - Never guess or assume today's date — it may be wrong.
> - When the user says "today", "tomorrow", "next Monday", etc., **first call `session_status`** to get the current UTC time, then convert to the configured timezone to determine the correct date.
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
python3 ~/.openclaw/skills/google/scripts/gcal.py list [today|tomorrow|week|next-week|month]
```

### Get event details
```bash
python3 ~/.openclaw/skills/google/scripts/gcal.py get <event_id>
```

### Create event
```bash
python3 ~/.openclaw/skills/google/scripts/gcal.py create \
  "Title" "2026-03-30T14:00:00" ["2026-03-30T15:00:00"] ["Description"] \
  [--attendees a@x.com b@x.com ...]
```

> ⚠️ **`--attendees` format**: Multiple emails must be passed as **separate space-separated arguments**, not quoted together.
> - ✅ Correct: `--attendees a@x.com b@x.com c@x.com`
> - ❌ Wrong: `--attendees "a@x.com,b@x.com,c@x.com"`

### Quick add (natural language)
```bash
python3 ~/.openclaw/skills/google/scripts/gcal.py quick "Meeting tomorrow at 3pm"
```

### Update event
```bash
python3 ~/.openclaw/skills/google/scripts/gcal.py update <event_id> <field> <value>
# field: summary | description | start | end | location
```

### Delete event
```bash
python3 ~/.openclaw/skills/google/scripts/gcal.py delete <event_id>
```

### View sharing permissions
```bash
python3 ~/.openclaw/skills/google/scripts/gcal.py share-list
```

### Share calendar with user
```bash
python3 ~/.openclaw/skills/google/scripts/gcal.py share <email> [reader|writer|owner|freeBusyReader]
```

### Show current config
```bash
python3 ~/.openclaw/skills/google/scripts/gcal.py show-config
```

---

## Workflow

1. **Determining dates**: If the request involves relative dates (today, tomorrow, next week, etc.), call `session_status` first to get the real current date — never guess.
2. **Creating events**: Do NOT add attendees unless the user explicitly asks.
3. Times in ISO8601 (`YYYY-MM-DDTHH:MM:SS`), timezone from config (default `Asia/Dubai`)
4. When event ID needed, use `list` first to get full ID, then operate
5. On auth error or missing credentials, collect `client_id`, `client_secret`, `refresh_token` from the user in chat and write the credentials file for them (see Setup section)

## Configuration

See `references/config.md`.
