# Google Calendar Credential Setup Guide

Read this file when the user needs to set up Google Calendar credentials for the first time, or when the script reports `[SETUP NEEDED]`.

## Overview

The skill needs three values from the user:

| Value | What it is |
|-------|------------|
| `client_id` | OAuth 2.0 Client ID from Google Cloud Console |
| `client_secret` | OAuth 2.0 Client Secret from Google Cloud Console |
| `refresh_token` | Long-lived token obtained via OAuth Playground |

Once the user provides all three, write them to `~/.openclaw/workspace/.credentials/google-calendar.json`.

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
cat > ~/.openclaw/workspace/.credentials/google-calendar.json << 'EOF'
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
python3 ~/.openclaw/skills/google-calendar/scripts/gcal.py list today
```

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
