---
name: microsoft-365
description: Manage Microsoft 365 via Microsoft Graph API — no Azure registration required. Activate when the user asks about Outlook calendar events, Teams meetings, OneDrive files, or Outlook email. Also activate when the user wants to create a Teams meeting or schedule something on Teams calendar. Also activate when the user wants to connect or log in to Microsoft 365, or change the timezone. Supports calendar CRUD + sharing with Teams online meetings, OneDrive file operations, and Outlook mail. See references/config.md for login and credential management.
homepage: https://github.com/idemerge/openclaw-skills
metadata:
  clawdbot:
    emoji: "🟦"
    requires:
      env: []
    files:
      - "scripts/*"
      - "references/*"
---

# Microsoft 365 Skill (v2)

Unified access to Microsoft 365 services via Microsoft Graph API — Calendar, OneDrive, and Outlook Mail.

Uses **Device Code Flow** with a public Client ID — no Azure app registration or client secret required.

## Setup

### Step 1: Login

The login command blocks while waiting for the user to complete browser login.
Follow these steps exactly so the user sees the device code in chat:

**Step 1a — Start login in background:**
```bash
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py login &
```

**Step 1b — Wait for device code file (retry up to 10s):**
```bash
for i in $(seq 1 10); do
  [ -f ~/.openclaw/ms365_device_code.json ] && break
  sleep 1
done
cat ~/.openclaw/ms365_device_code.json
```

**Step 1c — Read the JSON and show the user in chat:**
```
verification_uri: https://microsoft.com/devicelogin
user_code: ABCD-1234
```
Tell the user:
1. Open `verification_uri` in their browser
2. Enter the code `user_code`
3. Sign in with their Microsoft account and accept the permissions

**Step 1d — Wait for login to complete:**
```bash
wait
```

**Step 1e — Verify:**
```bash
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py status
```

The browser shows a permissions consent screen for **Microsoft Graph Command Line Tools** (a Microsoft first-party app). Token is cached at `~/.openclaw/ms365_token_cache.json` and auto-refreshed. Login is typically valid for 90 days.

### Step 2: Check Timezone (after every login)

After every successful login, **always** check the timezone config:

```bash
cat ~/.openclaw/workspace/.credentials/ms-graph-config.json 2>/dev/null
```

**If config does not exist** — ask the user to choose a timezone. Do NOT set one silently.

**If config already exists** — show the current value and ask the user to confirm:
> "Your timezone is currently set to `Asia/Shanghai`. Keep it or change?"

Only proceed if the user confirms. If they want to change, let them pick from:

| Timezone | Region |
|----------|--------|
| `Asia/Shanghai` | China, Hong Kong, Taiwan |
| `Asia/Dubai` | UAE, Gulf |
| `Asia/Tokyo` | Japan |
| `Asia/Singapore` | Singapore, Malaysia |
| `Europe/London` | UK |
| `America/New_York` | US East |
| `America/Los_Angeles` | US West |
| `UTC` | UTC |

Once confirmed, write the config:

```bash
mkdir -p ~/.openclaw/workspace/.credentials
cat > ~/.openclaw/workspace/.credentials/ms-graph-config.json << 'EOF'
{
  "timezone": "<user_confirmed_timezone>"
}
EOF
```

**Do not skip the timezone step** — it is required for correct calendar event times.

### Step 3: Verify

```bash
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py status
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py calendar list
```

### Update / Delete / Logout

See `references/config.md`.

---

## Tool Script

`scripts/ms_graph.py` — Requires `msal` (auto-installed on first run). Token cache at `~/.openclaw/ms365_token_cache.json`.

---

## Default Behavior Rules

> **Timezone is per-user config, default `Asia/Dubai` on first setup.**
>
> - Read timezone from `ms-graph-config.json`. If not configured, fall back to `Asia/Dubai`.
> - Display and discuss all times in the configured timezone.

> **Always call `session_status` before computing any date or time.**
>
> - Never guess or assume today's date.
> - When the user says "today", "tomorrow", "next Monday", etc., **first call `session_status`** to get the current UTC time.

> **No default attendees when creating events.**
>
> - Do NOT add any attendees unless the user explicitly specifies them.

> **Content must match the language of the user's message. Do not translate.**

---

## Calendar

### Create event
```bash
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py calendar create \
  --subject "Title" --start "2026-03-30T10:00:00" --end "2026-03-30T11:00:00" \
  [--timezone "Asia/Dubai"] [--body "Description"] [--location "Location"] \
  [--attendees a@x.com b@x.com] [--online]
```

### List events
```bash
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py calendar list [--days 7]
```

### Get event details
```bash
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py calendar get --event-id <id>
```

### Update event
```bash
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py calendar update \
  --event-id <id> [--subject ...] [--start ...] [--end ...] [--body ...] \
  [--location ...] [--attendees ...] [--online]
```

### Delete event
```bash
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py calendar delete --event-id <id>
```

### List calendars
```bash
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py calendar calendars
```

### Calendar sharing
```bash
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py calendar share-list [--calendar-id <id>]
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py calendar share-add --email <email> [--role read] [--calendar-id <id>]
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py calendar share-update --permission-id <id> --role <role> [--calendar-id <id>]
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py calendar share-remove --permission-id <id> [--calendar-id <id>]
```

---

## OneDrive

### List files
```bash
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py onedrive list [--path "/"] [--top 20]
```

### Get file/folder info
```bash
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py onedrive info --item-id <id>
```

### Download file
```bash
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py onedrive download --item-id <id> [--output /path/to/save]
```

### Upload file
```bash
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py onedrive upload --local-file /path/to/file --remote-path "/folder/filename.ext"
```

### Create folder
```bash
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py onedrive mkdir --name "New Folder" [--parent-id <id>]
```

### Delete file/folder
```bash
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py onedrive delete --item-id <id>
```

### Search files
```bash
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py onedrive search --query "keyword"
```

---

## Outlook Mail

### List emails
```bash
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py mail list [--top 10] [--folder inbox]
```

### Get email details
```bash
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py mail get --message-id <id>
```

### Send email
```bash
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py mail send \
  --to "recipient@example.com" --subject "Subject" --body "Message body" \
  [--cc a@x.com] [--bcc b@x.com]
```

### Reply to email
```bash
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py mail reply \
  --message-id <id> --body "Reply text"
```

### Delete email
```bash
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py mail delete --message-id <id>
```

### List mail folders
```bash
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py mail folders
```

---

## Config & Status

### Check login status
```bash
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py status
```

### Show current config
```bash
python3 ~/.openclaw/skills/microsoft-365/scripts/ms_graph.py show-config
```

---

## Workflow

1. **Determining dates**: If the request involves relative dates, call `session_status` first — never guess.
2. **Creating events**: Do NOT add attendees unless the user explicitly asks.
3. Times in ISO8601 (`YYYY-MM-DDTHH:MM:SS`), timezone from config (default `Asia/Dubai`).
4. On auth error or NOT_LOGGED_IN, instruct user to run `ms_graph.py login`.
5. Token auto-refreshes silently. If refresh fails, re-run login.

## Configuration

See `references/config.md`.

---

## External Endpoints

| Endpoint | Method | Data Sent | Purpose |
|----------|--------|-----------|---------|
| `https://login.microsoftonline.com/common/oauth2/v2.0/devicecode` | POST | client_id, scope | Obtain device code |
| `https://login.microsoftonline.com/common/oauth2/v2.0/token` | POST | client_id, device_code, grant_type | Poll for access token |
| `https://graph.microsoft.com/v1.0/me/...` | GET/POST/PATCH/DELETE | access_token, event/mail/file data | Calendar, OneDrive, Mail operations |

## Security & Privacy

- **No client secret**: Uses a public Microsoft first-party Client ID — no secrets stored anywhere.
- **Token cache** is stored locally at `~/.openclaw/ms365_token_cache.json` with restricted permissions (0600). Never sent anywhere except Microsoft's token endpoint for refresh.
- **Calendar, mail, and file data** is sent to/from Microsoft Graph API only. No third-party services involved.
- **No telemetry** — the script does not phone home or report usage.
- **Consent screen**: Microsoft shows a standard OAuth consent screen in your browser listing the requested permissions. You control what you approve.
