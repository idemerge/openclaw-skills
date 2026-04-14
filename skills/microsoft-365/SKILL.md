---
name: microsoft-365
description: Manage Microsoft 365 via Microsoft Graph API — no Azure registration required. Activate when the user asks about Outlook calendar events, Teams meetings, OneDrive files, Outlook email, or wants to connect/log in to Microsoft 365 or change the timezone. Supports calendar CRUD + sharing with Teams online meetings, OneDrive file operations, and Outlook mail. See references/config.md for login and credential management.
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

Uses **Device Code Flow** with a public Client ID — no Azure app registration or client secret required.

> **Note on paths**: Before running any command, set the script path variable once:
> ```bash
> MS_GRAPH=$(find ~/.openclaw/skills -name ms_graph.py -path "*/microsoft*/scripts/*" 2>/dev/null | head -1)
> ```
> All commands below use `$MS_GRAPH`. If the variable is empty, the skill is not installed.

## Setup

### Step 1: Login

The login command blocks while waiting for the user to complete browser login.
Follow these steps exactly so the user sees the device code in chat:

**Step 1a — Start login in background:**
```bash
python3 $MS_GRAPH login &
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
4. Microsoft may ask for a verification code (SMS/email/authenticator) — this is normal and only required for this login session
5. After approval, the browser may show a "localhost" error page — this is normal and can be safely closed. The login has already succeeded.
6. **You have about 3 minutes to complete. If you see "Need admin approval" in the browser, let me know — your organization may need IT admin to authorize this app first.**

**Step 1d — Wait for login to complete:**
```bash
wait
```

The login command times out after 3 minutes. If it times out, ask the user what happened:
- If they simply didn't complete in time → offer to try again
- If they saw "Need admin approval" in the browser → their organization requires admin consent. Tell them:
  > Your organization requires admin approval for this app. Please ask your IT admin to visit:
  > `https://login.microsoftonline.com/<tenant-id>/adminconsent?client_id=14d82eec-204b-4c2f-b7e8-296a70dab67e`
  > Replace `<tenant-id>` with your organization's tenant ID.
  > Alternatively, you can use a personal Microsoft account (Outlook.com / Hotmail) which does not require admin approval.

When showing the device code to the user, mention they have about 3 minutes to complete the browser login.

See `references/config.md` → **Troubleshooting** for details.

**Step 1e — Verify:**
```bash
python3 $MS_GRAPH status
```

The browser shows a permissions consent screen for **Microsoft Graph Command Line Tools** (a Microsoft first-party app). Token is cached at `~/.openclaw/ms365_token_cache.json` and auto-refreshed. Login is typically valid for 90 days.

> **After successful login, tell the user:** Token is cached locally and auto-refreshes for ~90 days. You do not need to log in again unless you see `NOT_LOGGED_IN`. Microsoft may require a verification code during login — this is normal and only happens once per login session.

### Step 2: Check Timezone (after every login)

After every successful login, **always** check and confirm the timezone with the user.
See `references/config.md` → **Timezone Setup** for the full procedure.

**Do not skip the timezone step** — it is required for correct calendar event times.

### Step 3: Verify

```bash
python3 $MS_GRAPH calendar list
```

### Update / Delete / Logout

See `references/config.md`.

---

## Tool Script

`scripts/ms_graph.py` — Pure Python stdlib, zero external dependencies. Token cache at `~/.openclaw/ms365_token_cache.json`.

---

## Default Behavior Rules

> **Timezone is per-user config.**
>
> - Read timezone from `ms-graph-config.json`. If not configured, fall back to `Asia/Dubai`.
> - Display and discuss all times in the configured timezone.

> **Always determine the current date/time before computing any relative date.**
>
> - Never guess or assume today's date.
> - When the user says "today", "tomorrow", "next Monday", etc., use the agent's built-in date awareness (e.g. `date` command or system clock) to get the current time before calculating.

> **No default attendees when creating events.**
>
> - Do NOT add any attendees unless the user explicitly specifies them.

> **Content must match the language of the user's message. Do not translate.**

---

## Calendar

Quick reference (full details in `references/calendar.md`):

```bash
python3 $MS_GRAPH calendar create \
  --subject "Title" --start "2026-03-30T10:00:00" --end "2026-03-30T11:00:00"
python3 $MS_GRAPH calendar list [--days 7] [--top 50]
python3 $MS_GRAPH calendar update --event-id <id> [--subject ...]
python3 $MS_GRAPH calendar delete --event-id <id>
```

See `references/calendar.md` for full options including `--timezone`, `--location`, `--attendees`, `--online`, and calendar sharing commands.

---

## OneDrive

Quick reference (full details in `references/onedrive.md`):

```bash
python3 $MS_GRAPH onedrive list [--path "/"]
python3 $MS_GRAPH onedrive download --item-id <id>
python3 $MS_GRAPH onedrive upload --local-file /path/file --remote-path "/folder/file"
python3 $MS_GRAPH onedrive search --query "keyword"
```

See `references/onedrive.md` for full options including `info`, `mkdir`, `delete`.

---

## Outlook Mail

Quick reference (full details in `references/mail.md`):

```bash
python3 $MS_GRAPH mail list [--top 10]
python3 $MS_GRAPH mail get --message-id <id>
python3 $MS_GRAPH mail send --to "a@b.com" --subject "Subj" --body "Body"
python3 $MS_GRAPH mail reply --message-id <id> --body "Reply"
```

See `references/mail.md` for full options including `delete`, `folders`.

---

## Config & Status

```bash
python3 $MS_GRAPH status
python3 $MS_GRAPH show-config
```

---

## Workflow

1. **Determining dates**: If the request involves relative dates, check the current date/time first — never guess.
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
