# Microsoft 365 Configuration Guide

Read this file when the user needs to log in, log out, check status, or update the timezone.

## Overview

This skill uses **Device Code Flow** — no Azure app registration or client secret required.

| Item | Location |
|------|----------|
| Token cache | `~/.openclaw/ms365_token_cache.json` |
| Config | `~/.openclaw/workspace/.credentials/ms-graph-config.json` |

### Account type & tenant

The tenant endpoint depends on the Microsoft account type (per [Microsoft docs](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-device-code)):

| Account type | `tenant_id` value |
|--------------|-------------------|
| Personal (Outlook.com / Hotmail) | `consumers` (default) |
| Enterprise (Microsoft 365 / work) | `organizations` |

**You MUST ask the user which account type they use before starting the login flow.** Do not default silently — using the wrong tenant causes `response_type` errors on the localhost redirect. Ask explicitly:

> "Which Microsoft account type are you using?
> 1. Personal account (Outlook.com / Hotmail / live.com) → tenant_id = consumers
> 2. Work or school account (organization-assigned) → tenant_id = organizations"

The `tenant_id` must be written to the config file **before** running `device-code`, because the script reads it at startup. If the config file does not exist yet, create it with the user's answer and a default timezone. If it already exists, preserve the timezone and update only `tenant_id`.

> **Why not `common`?** The `/common` tenant is documented to support both account types, but in practice personal accounts may encounter a `response_type` error when redirected to `localhost` after sign-in. Using `/consumers` for personal accounts avoids this issue.

---

## Login

Login uses two commands: `device-code` (get code) and `login-poll` (wait for completion). The agent is never blocked.

**1. Get device code:**
```bash
python3 {baseDir}/scripts/ms_graph.py device-code
```
Output: JSON with `verification_uri`, `user_code`, `device_code`.

**2. Show the user:**
- URL: value of `verification_uri`
- Code: value of `user_code`

Steps for the user:
1. Open the URL in any browser
2. Enter the code
3. Sign in with their Microsoft account (personal Outlook.com or enterprise Microsoft 365)
4. Accept the permissions on the consent screen
5. Microsoft may ask for a verification code (SMS/email/authenticator) — this is normal
6. After approval, the browser may show a "localhost" error page — this is normal, just close it

**3. When user confirms login is done:**
```bash
python3 {baseDir}/scripts/ms_graph.py login-poll --device-code <device_code>
```
Output:
- `LOGIN_SUCCESS | Name | email@example.com` — proceed to timezone check
- `LOGIN_TIMEOUT` — device code expired, start over
- `LOGIN_FAILED: ...` — check error message

Token is cached locally and auto-refreshed. Typically valid for 90 days without re-login.

> **After successful login, tell the user:** Token is cached locally and auto-refreshes for ~90 days. You do not need to log in again unless you see `NOT_LOGGED_IN`.

For interactive terminal use (not via agent), use `python3 {baseDir}/scripts/ms_graph.py login` which combines both steps.

---

## Check Status

```bash
python3 {baseDir}/scripts/ms_graph.py status
```

Output:
- `LOGGED_IN | Name | email@example.com` — authenticated and ready
- `NOT_LOGGED_IN` — need to run login

---

## Logout

```bash
python3 {baseDir}/scripts/ms_graph.py logout
```

Deletes the local token cache file. Does not revoke tokens server-side.

---

## Timezone Setup (Required after every login)

After every successful login, **always** check the existing timezone config first:

```bash
cat ~/.openclaw/workspace/.credentials/ms-graph-config.json 2>/dev/null
```

- **Config missing** → ask the user to choose a timezone. Do NOT set one silently.
- **Config exists** → show the current value and ask to confirm:
  > "Your timezone is currently `Asia/Dubai`. Keep it or change?"

Available timezones to suggest:

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

Once the user confirms, write the config file:

```bash
mkdir -p ~/.openclaw/workspace/.credentials
cat > ~/.openclaw/workspace/.credentials/ms-graph-config.json << 'EOF'
{
  "timezone": "<user_confirmed_timezone>",
  "tenant_id": "<consumers_or_organizations>"
}
EOF
```

> **Important**: `tenant_id` must be set correctly before running `device-code` or `login`. If the user later changes their account type, update this field and re-login.

---

## Show Config

```bash
python3 {baseDir}/scripts/ms_graph.py show-config
```

Displays current timezone setting and login status.

---

## Delete Token Cache

```bash
rm -f ~/.openclaw/ms365_token_cache.json
```

This removes the login token only. Timezone config is preserved so the user does not need to re-select it on next login.

## Delete All Data (token + timezone)

```bash
rm -f ~/.openclaw/ms365_token_cache.json
rm -f ~/.openclaw/workspace/.credentials/ms-graph-config.json
```

Use this only when the user wants a complete reset.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `NOT_LOGGED_IN` | Run `ms_graph.py login` |
| `[ERROR] Token refresh failed` | Run `ms_graph.py login` again |
| Login code expired (15 min limit) | Run `ms_graph.py login` again to get a new code |
| 403 Forbidden on API calls | The Microsoft account may lack a license for that service (e.g. no Exchange/OneDrive plan) |
| `interaction_required` error | Conditional Access policy (MFA) requires re-login. Run `ms_graph.py login` |
| Consent screen blocked by admin | Enterprise tenant admin has disabled user consent. Ask IT admin to grant consent for the app |
| Browser shows `response_type` error on localhost after sign-in | Wrong `tenant_id` in config. Personal accounts must use `consumers`, enterprise must use `organizations`. Update `ms-graph-config.json` and re-login. |

### Enterprise tenant: admin consent required

Some organizations disable user consent for third-party apps. In this case the user will see an error during login saying admin approval is required.

The IT admin can grant consent for the entire tenant by visiting:

```
https://login.microsoftonline.com/<tenant-id>/adminconsent?client_id=14d82eec-204b-4c2f-b7e8-296a70dab67e
```

Replace `<tenant-id>` with the organization's tenant ID (found in Azure Portal → Azure Active Directory → Overview).

After admin consent, users in the tenant can log in without seeing the consent prompt.
