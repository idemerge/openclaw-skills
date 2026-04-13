---
name: microsoft
description: Manage Microsoft 365 via Microsoft Graph API. Activate when the user asks about Outlook calendar events, Teams meetings, OneDrive files, or Outlook email. Also activate when the user wants to create a Teams meeting or schedule something on Teams calendar. Also activate when the user wants to set up, update, or delete Microsoft Graph credentials, or change the timezone. Supports calendar CRUD + sharing with Teams online meetings, OneDrive file operations, and Outlook mail. See references/config.md for credential management.
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

# Microsoft 365 Skill

Unified access to Microsoft 365 services via Microsoft Graph API — Calendar, OneDrive, and Outlook Mail.

## Setup

The script requires Microsoft Graph credentials and a timezone setting. All are configured interactively through chat.

### Step 1: Configure Microsoft Graph credentials

The script reads credentials from `~/.openclaw/workspace/.credentials/ms-graph.json`.

**When credentials are missing**, do NOT ask the user to edit files manually. Instead:

1. Read `references/config.md` for the full step-by-step guide
2. Walk the user through the setup in chat, one step at a time — **do not skip any step**
3. After each step, wait for the user to complete it before proceeding
4. Collect `client_id`, `client_secret`, `refresh_token` from the user in chat
5. Write the credentials file automatically:

```bash
mkdir -p ~/.openclaw/workspace/.credentials
cat > ~/.openclaw/workspace/.credentials/ms-graph.json << 'EOF'
{
  "client_id": "<client_id>",
  "client_secret": "<client_secret>",
  "refresh_token": "<refresh_token>",
  "token_url": "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
}
EOF
```

6. **Immediately after** credentials are saved, ask the user for their timezone. Default: `Asia/Dubai`. Write the config file:

```bash
cat > ~/.openclaw/workspace/.credentials/ms-graph-config.json << 'EOF'
{
  "timezone": "<timezone>"
}
EOF
```

7. Verify by running `ms_graph.py check-cred` and `ms_graph.py calendar list`

**Do not** instruct the user to manually create or edit the credentials file.
**Do not** skip the timezone step — it is required for correct calendar event times.

### Update / Delete credentials

Same pattern as credential setup. See `references/config.md` for full guide.

## Tool Script

`scripts/ms_graph.py` — Pure Python standard library, no external dependencies. Credentials at `~/.openclaw/workspace/.credentials/ms-graph.json`. Token cache at `~/.ms-graph-token`.

---

## 📌 Default Behavior Rules

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
python3 ~/.openclaw/skills/microsoft/scripts/ms_graph.py calendar create \
  --subject "Title" --start "2026-03-30T10:00:00" --end "2026-03-30T11:00:00" \
  [--timezone "Asia/Dubai"] [--body "Description"] [--location "Location"] \
  [--attendees a@x.com b@x.com] [--online]
```

### List events
```bash
python3 ~/.openclaw/skills/microsoft/scripts/ms_graph.py calendar list [--days 7]
```

### Get event details
```bash
python3 ~/.openclaw/skills/microsoft/scripts/ms_graph.py calendar get --event-id <id>
```

### Update event
```bash
python3 ~/.openclaw/skills/microsoft/scripts/ms_graph.py calendar update \
  --event-id <id> [--subject ...] [--start ...] [--end ...] [--body ...] \
  [--location ...] [--attendees ...] [--online]
```

### Delete event
```bash
python3 ~/.openclaw/skills/microsoft/scripts/ms_graph.py calendar delete --event-id <id>
```

### List calendars
```bash
python3 ~/.openclaw/skills/microsoft/scripts/ms_graph.py calendar calendars
```

### Calendar sharing
```bash
python3 ~/.openclaw/skills/microsoft/scripts/ms_graph.py calendar share-list [--calendar-id <id>]
python3 ~/.openclaw/skills/microsoft/scripts/ms_graph.py calendar share-add --email <email> [--role read] [--calendar-id <id>]
python3 ~/.openclaw/skills/microsoft/scripts/ms_graph.py calendar share-update --permission-id <id> --role <role> [--calendar-id <id>]
python3 ~/.openclaw/skills/microsoft/scripts/ms_graph.py calendar share-remove --permission-id <id> [--calendar-id <id>]
```

---

## OneDrive

### List files
```bash
python3 ~/.openclaw/skills/microsoft/scripts/ms_graph.py onedrive list [--path "/"] [--top 20]
```

### Get file/folder info
```bash
python3 ~/.openclaw/skills/microsoft/scripts/ms_graph.py onedrive info --item-id <id>
```

### Download file
```bash
python3 ~/.openclaw/skills/microsoft/scripts/ms_graph.py onedrive download --item-id <id> [--output /path/to/save]
```

### Upload file
```bash
python3 ~/.openclaw/skills/microsoft/scripts/ms_graph.py onedrive upload --local-file /path/to/file --remote-path "/folder/filename.ext"
```

### Create folder
```bash
python3 ~/.openclaw/skills/microsoft/scripts/ms_graph.py onedrive mkdir --name "New Folder" [--parent-id <id>]
```

### Delete file/folder
```bash
python3 ~/.openclaw/skills/microsoft/scripts/ms_graph.py onedrive delete --item-id <id>
```

### Search files
```bash
python3 ~/.openclaw/skills/microsoft/scripts/ms_graph.py onedrive search --query "keyword"
```

---

## Outlook Mail

### List emails
```bash
python3 ~/.openclaw/skills/microsoft/scripts/ms_graph.py mail list [--top 10] [--folder inbox]
```

### Get email details
```bash
python3 ~/.openclaw/skills/microsoft/scripts/ms_graph.py mail get --message-id <id>
```

### Send email
```bash
python3 ~/.openclaw/skills/microsoft/scripts/ms_graph.py mail send \
  --to "recipient@example.com" --subject "Subject" --body "Message body" \
  [--cc a@x.com] [--bcc b@x.com]
```

### Reply to email
```bash
python3 ~/.openclaw/skills/microsoft/scripts/ms_graph.py mail reply \
  --message-id <id> --body "Reply text"
```

### Delete email
```bash
python3 ~/.openclaw/skills/microsoft/scripts/ms_graph.py mail delete --message-id <id>
```

### List mail folders
```bash
python3 ~/.openclaw/skills/microsoft/scripts/ms_graph.py mail folders
```

---

## Config & Status

### Check credentials
```bash
python3 ~/.openclaw/skills/microsoft/scripts/ms_graph.py check-cred
```

### Show current config
```bash
python3 ~/.openclaw/skills/microsoft/scripts/ms_graph.py show-config
```

---

## Workflow

1. **Determining dates**: If the request involves relative dates, call `session_status` first — never guess.
2. **Creating events**: Do NOT add attendees unless the user explicitly asks.
3. Times in ISO8601 (`YYYY-MM-DDTHH:MM:SS`), timezone from config (default `Asia/Dubai`)
4. On auth error or missing credentials, collect values in chat and write the file (see Setup)
5. If token expires, the script auto-refreshes. If refresh fails, re-authorize (see references/config.md)

## Configuration

See `references/config.md`.

---

## External Endpoints

| Endpoint | Method | Data Sent | Purpose |
|----------|--------|-----------|---------|
| `https://login.microsoftonline.com/consumers/oauth2/v2.0/token` | POST | client_id, client_secret, refresh_token, grant_type, scope | Obtain/refresh OAuth access token |
| `https://graph.microsoft.com/v1.0/me/...` | GET/POST/PATCH/DELETE | access_token, event/mail/file data | Calendar, OneDrive, Mail operations |
| `https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize` | GET (browser) | client_id, scope, redirect_uri | User authorization (one-time setup) |

## Security & Privacy

- **Credentials** (client_id, client_secret, refresh_token) are stored locally in `~/.openclaw/workspace/.credentials/ms-graph.json`. Never sent anywhere except Microsoft's OAuth token endpoint.
- **Access token** is cached in `~/.ms-graph-token` with restricted permissions (0600) and auto-refreshed. Not logged or transmitted outside Microsoft Graph API calls.
- **Calendar, mail, and file data** is sent to/from Microsoft Graph API only. No third-party services are involved.
- **No telemetry** — the script does not phone home or report usage.
- **No hardcoded secrets** — all credentials are read from the local config file at runtime.

## Trust Statement

By using this skill, your Microsoft 365 data (calendar, email, files) is exchanged with Microsoft Graph API using your own OAuth credentials. Only install this skill if you trust Microsoft's cloud services. Credential values never leave your machine except to authenticate with Microsoft directly.
