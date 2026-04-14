# Microsoft 365 Configuration Guide

Read this file when the user needs to log in, log out, check status, or update the timezone.

## Overview

This skill uses **Device Code Flow** — no Azure app registration or client secret required.

| Item | Location |
|------|----------|
| Token cache | `~/.openclaw/ms365_token_cache.json` |
| Timezone config | `~/.openclaw/workspace/.credentials/ms-graph-config.json` |

---

## Login

The login command blocks waiting for the user's browser action, so the agent must
run it in background, read the device code file, and show the code to the user in chat.

**1. Start login in background:**
```bash
python3 {baseDir}/scripts/ms_graph.py login &
```

**2. Wait for device code file (up to 10s):**
```bash
for i in $(seq 1 10); do
  [ -f ~/.openclaw/ms365_device_code.json ] && break
  sleep 1
done
cat ~/.openclaw/ms365_device_code.json
```

**3. Show the user in chat** (extract from JSON):
- URL: value of `verification_uri`
- Code: value of `user_code`

**4. Wait for login to complete:**
```bash
wait
```

**5. Verify:**
```bash
python3 {baseDir}/scripts/ms_graph.py status
```

Steps for the user:
1. Open the `verification_uri` in any browser
2. Enter the `user_code`
3. Sign in with their Microsoft account (personal Outlook.com or enterprise Microsoft 365)
4. Accept the permissions on the consent screen
5. Microsoft may ask for a verification code (SMS/email/authenticator) — this is normal and only required for this login session
6. After approval, the browser may show a "localhost" error page — this is normal and can be safely closed. The login has already succeeded.

On success, `status` returns:
```
LOGGED_IN | Zhang San | zhangsan@company.com
```

Token is cached locally and auto-refreshed. Typically valid for 90 days without re-login.

> **After successful login, tell the user:** Token is cached locally and auto-refreshes for ~90 days. You do not need to log in again unless you see `NOT_LOGGED_IN`. Microsoft may require a verification code during login — this is normal and only happens once per login session.

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
  "timezone": "<user_confirmed_timezone>"
}
EOF
```

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

### Enterprise tenant: admin consent required

Some organizations disable user consent for third-party apps. In this case the user will see an error during login saying admin approval is required.

The IT admin can grant consent for the entire tenant by visiting:

```
https://login.microsoftonline.com/<tenant-id>/adminconsent?client_id=14d82eec-204b-4c2f-b7e8-296a70dab67e
```

Replace `<tenant-id>` with the organization's tenant ID (found in Azure Portal → Azure Active Directory → Overview).

After admin consent, users in the tenant can log in without seeing the consent prompt.
