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

> **Account type matters**: Personal accounts (Outlook.com/Hotmail) use `tenant_id=consumers`, enterprise accounts use `tenant_id=organizations`. This is stored in `ms-graph-config.json`. Default is `consumers`. See `references/config.md` for details.

> **Script path**: Commands below use `{baseDir}/scripts/ms_graph.py` where `{baseDir}` is resolved to the skill's installation directory at runtime.

## Setup

### Step 0: Determine Account Type (REQUIRED before login)

**You MUST ask the user which Microsoft account type they use before running `device-code`.** Do not skip this step or default silently.

Ask:
> "Which Microsoft account type are you using?
> 1. Personal account (Outlook.com / Hotmail / live.com) → tenant_id = consumers
> 2. Work or school account (organization-assigned) → tenant_id = organizations"

Then write the config file (or update it) **before** proceeding to login:

```bash
mkdir -p ~/.openclaw/workspace/.credentials
# If config file already exists, read it first and only update tenant_id
cat > ~/.openclaw/workspace/.credentials/ms-graph-config.json << 'EOF'
{
  "timezone": "<existing_or_default_timezone>",
  "tenant_id": "<consumers_or_organizations>"
}
EOF
```

> **Why this matters**: Using the wrong tenant_id causes `response_type` errors on the localhost redirect after sign-in. The `device-code` command reads tenant_id from this config file at startup — if it's wrong, the entire login flow fails.

### Step 1: Login

**Step 1a — Get device code:**
```bash
python3 {baseDir}/scripts/ms_graph.py device-code
```
Output: JSON with `verification_uri`, `user_code`, `device_code`.

**Step 1b — Show the user in chat:**

Tell the user:
1. Open `verification_uri` in their browser
2. Enter the code `user_code`
3. Sign in with their Microsoft account and accept the permissions
4. Microsoft may ask for a verification code (SMS/email/authenticator) — this is normal
5. After approval, the browser may show a "localhost" error page — this is normal, just close it
6. **When done, let me know** so I can verify the login
7. If you see "Need admin approval" in the browser, let me know — your organization may need IT admin to authorize this app first

**Step 1c — When the user confirms login is done:**
```bash
python3 {baseDir}/scripts/ms_graph.py login-poll --device-code <device_code from step 1a>
```
- `LOGIN_SUCCESS | name | email` → login succeeded, proceed to timezone check
- `LOGIN_TIMEOUT` → device code expired, offer to start over from step 1a
- `LOGIN_FAILED: ...` → check the error. If admin consent issue, tell the user:
  > Your organization requires admin approval. Ask your IT admin to visit:
  > `https://login.microsoftonline.com/<tenant-id>/adminconsent?client_id=14d82eec-204b-4c2f-b7e8-296a70dab67e`
  > Or use a personal Microsoft account (Outlook.com / Hotmail) instead.

See `references/config.md` → **Troubleshooting** for details.

> **After successful login, tell the user:** Token is cached locally and auto-refreshes for ~90 days. You do not need to log in again unless you see `NOT_LOGGED_IN`. Microsoft may require a verification code during login — this is normal and only happens once per login session.

The browser shows a permissions consent screen for **Microsoft Graph Command Line Tools** (a Microsoft first-party app). Token is cached at `~/.openclaw/ms365_token_cache.json`.

### Step 2: Check Timezone (after every login)

After every successful login, **always** check and confirm the timezone with the user.
See `references/config.md` → **Timezone Setup** for the full procedure.

**Do not skip the timezone step** — it is required for correct calendar event times.

### Step 3: Verify

```bash
python3 {baseDir}/scripts/ms_graph.py calendar list
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
python3 {baseDir}/scripts/ms_graph.py calendar create \
  --subject "Title" --start "2026-03-30T10:00:00" --end "2026-03-30T11:00:00"
python3 {baseDir}/scripts/ms_graph.py calendar list [--days 7] [--top 50]
python3 {baseDir}/scripts/ms_graph.py calendar update --event-id <id> [--subject ...]
python3 {baseDir}/scripts/ms_graph.py calendar delete --event-id <id>
```

See `references/calendar.md` for full options including `--timezone`, `--location`, `--attendees`, `--online`, and calendar sharing commands.

---

## OneDrive

Quick reference (full details in `references/onedrive.md`):

```bash
python3 {baseDir}/scripts/ms_graph.py onedrive list [--path "/"]
python3 {baseDir}/scripts/ms_graph.py onedrive download --item-id <id>
python3 {baseDir}/scripts/ms_graph.py onedrive upload --local-file /path/file --remote-path "/folder/file"
python3 {baseDir}/scripts/ms_graph.py onedrive search --query "keyword"
```

See `references/onedrive.md` for full options including `info`, `mkdir`, `delete`.

---

## Outlook Mail

Quick reference (full details in `references/mail.md`):

```bash
python3 {baseDir}/scripts/ms_graph.py mail list [--top 10]
python3 {baseDir}/scripts/ms_graph.py mail get --message-id <id>
python3 {baseDir}/scripts/ms_graph.py mail send --to "a@b.com" --subject "Subj" --body "Body"
python3 {baseDir}/scripts/ms_graph.py mail reply --message-id <id> --body "Reply"
```

See `references/mail.md` for full options including `delete`, `folders`.

---

## Config & Status

```bash
python3 {baseDir}/scripts/ms_graph.py status
python3 {baseDir}/scripts/ms_graph.py show-config
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
| `https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/devicecode` | POST | client_id, scope | Obtain device code |
| `https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token` | POST | client_id, device_code, grant_type | Poll for access token |
| `https://graph.microsoft.com/v1.0/me/...` | GET/POST/PATCH/DELETE | access_token, event/mail/file data | Calendar, OneDrive, Mail operations |

## Security & Privacy

- **No client secret**: Uses a public Microsoft first-party Client ID — no secrets stored anywhere.
- **Token cache** is stored locally at `~/.openclaw/ms365_token_cache.json` with restricted permissions (0600). Never sent anywhere except Microsoft's token endpoint for refresh.
- **Calendar, mail, and file data** is sent to/from Microsoft Graph API only. No third-party services involved.
- **No telemetry** — the script does not phone home or report usage.
- **Consent screen**: Microsoft shows a standard OAuth consent screen in your browser listing the requested permissions. You control what you approve.
