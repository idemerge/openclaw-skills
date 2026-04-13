# Google Calendar Credential Management Guide

Read this file when the user needs to set up, update, or delete Google Calendar credentials or timezone, or when the script reports `[SETUP NEEDED]`.

## Overview

The skill needs three credential values and one timezone setting:

| Value | What it is | File |
|-------|------------|------|
| `client_id` | OAuth 2.0 Client ID from Google Cloud Console | `google.json` |
| `client_secret` | OAuth 2.0 Client Secret from Google Cloud Console | `google.json` |
| `refresh_token` | Long-lived token obtained via OAuth Playground | `google.json` |
| `timezone` | IANA timezone name (default: `Asia/Dubai`) | `google-config.json` |

Both files are stored in `~/.openclaw/workspace/.credentials/`.

## Step-by-Step Guide for the User

Walk the user through these steps in chat. Wait for the user to complete each step before moving to the next.

### Step 1: Create a Google Cloud Project

1. Open [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with the Google account whose calendar you want to manage
3. Click the project dropdown at the top → click **New Project**
4. Enter a project name (e.g. "OpenClaw Calendar") → click **Create**
5. Make sure the new project is selected (click the dropdown again and select it)

### Step 2: Enable the Google Calendar API

1. Go to [API Library](https://console.cloud.google.com/apis/library) (or navigate via menu → APIs & Services → Library)
2. Search for **"Google Calendar API"**
3. Click on it → click **Enable**

### Step 3: Create OAuth 2.0 Credentials

1. Go to [Credentials](https://console.cloud.google.com/apis/credentials) (or navigate via menu → APIs & Services → Credentials)
2. Click **Create Credentials** → **OAuth 2.0 Client ID**
3. If prompted to configure the consent screen:
   - Click **Configure Consent Screen**
   - Choose **External** → click **Create**
   - Fill in the required fields (App name, User support email, Developer contact email)
   - Click **Save and Continue** through each section (Scopes → add no extra scopes → Save → Test users → add your own email → Save)
   - Click **Back to Dashboard**
4. Now create the OAuth Client ID:
   - Application type: **Desktop app**
   - Name: anything (e.g. "OpenClaw Calendar Client")
   - Click **Create**
5. A dialog will show your **Client ID** and **Client Secret** — ask the user to copy both and share them in chat

### Step 4: Get the Refresh Token

1. Open the [OAuth 2.0 Playground](https://developers.google.com/oauthplayground)
2. Click the **gear icon** (OAuth 2.0 configuration) in the top right
3. Check **"Use your own OAuth credentials"**
4. Paste the `client_id` and `client_secret` from Step 3 → click **Close**
5. In the left panel, find and expand **Calendar API v3**
6. Check the scope **`https://www.googleapis.com/auth/calendar`**
7. Click **Authorize APIs**
8. Sign in with the same Google account and grant permission
9. You'll be redirected back to the Playground — click **Exchange authorization code for tokens**
10. The response will contain a **refresh_token** — ask the user to copy it and share it in chat

### Step 5: Save the Credentials

Once the user provides all three values in chat, write the credentials file:

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

Then verify:

```bash
python3 ~/.openclaw/skills/google/scripts/gcal.py list today
```

### Step 6: Set Timezone

Ask the user what timezone they want. If they don't specify, default to `Asia/Dubai`.

Write the config file:

```bash
mkdir -p ~/.openclaw/workspace/.credentials
cat > ~/.openclaw/workspace/.credentials/google-config.json << 'EOF'
{
  "timezone": "<timezone>"
}
EOF
```

Common timezone values:

| City/Region | Timezone |
|-------------|----------|
| Dubai / UAE | `Asia/Dubai` |
| Shanghai / Beijing | `Asia/Shanghai` |
| Tokyo | `Asia/Tokyo` |
| Singapore | `Asia/Singapore` |
| London | `Europe/London` |
| New York | `America/New_York` |
| Los Angeles | `America/Los_Angeles` |
| UTC | `UTC` |

Full list: [IANA Time Zone Database](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

Verify:

```bash
python3 ~/.openclaw/skills/google/scripts/gcal.py show-config
```

## Update Credentials

When the user wants to switch to a different Google account or an existing refresh_token has expired:

1. Check current status: `python3 ~/.openclaw/skills/google/scripts/gcal.py check-cred`
2. Ask the user which fields to update:
   - **Switch account**: need new `client_id`, `client_secret`, `refresh_token` (all three)
   - **Token expired**: only need a new `refresh_token`
3. If only updating `refresh_token`, follow Step 4 above (OAuth Playground) to get a new one
4. If switching accounts, follow Steps 1-4 above from the beginning
5. Write the updated credentials file (same command as Step 5 above)
6. Verify: `python3 ~/.openclaw/skills/google/scripts/gcal.py check-cred`

## Delete Credentials

When the user wants to revoke Google Calendar access:

1. Confirm with the user — this will remove all stored Google Calendar credentials
2. Delete the credentials file:

```bash
rm ~/.openclaw/workspace/.credentials/google.json
```

3. Verify: `python3 ~/.openclaw/skills/google/scripts/gcal.py check-cred`
   Should show `[MISSING] Credentials file not found`
4. Optionally, also revoke access in [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials → OAuth 2.0 Client IDs → delete the client, or in [Google Account Permissions](https://myaccount.google.com/permissions) → remove the app

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `access_denied` during OAuth | Make sure your email is added as a test user on the consent screen (Step 3) |
| `invalid_grant` on refresh_token | The refresh_token may have expired or been revoked — generate a new one (Step 4) |
| 403 Forbidden on Calendar API | Make sure the Google Calendar API is enabled (Step 2) |
| refresh_token is blank in Playground | The app may be in "Production" mode — switch consent screen back to "Testing", or use a different project |

## Token Notes

- `refresh_token` is long-lived unless manually revoked or unused for 6+ months
- `token` (access_token) is auto-refreshed by the script on each run
- The script writes the refreshed access_token back to the credentials file automatically
