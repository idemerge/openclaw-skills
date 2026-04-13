# Google Calendar API Configuration

## Credentials File

Location: `~/.openclaw/workspace/.credentials/google-calendar.json`

| Field | Description |
|-------|-------------|
| client_id | OAuth 2.0 Client ID |
| client_secret | Client Secret |
| refresh_token | Long-lived refresh token |
| token_uri | `https://oauth2.googleapis.com/token` |

## How to Obtain Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → **APIs & Services** → **Credentials**
2. Create a project (or select an existing one)
3. Click **Create Credentials** → **OAuth 2.0 Client ID** → Application type: **Desktop app**
4. Note down the `client_id` and `client_secret`
5. Go to **Library** → search **Google Calendar API** → **Enable**
6. Obtain a `refresh_token` using the OAuth 2.0 Playground:
   - Visit https://developers.google.com/oauthplayground
   - Click the gear icon → check "Use your own OAuth credentials" → enter `client_id` and `client_secret`
   - Select scope `https://www.googleapis.com/auth/calendar` → Authorize APIs
   - Click "Exchange authorization code for tokens" → copy the `refresh_token`
7. Save the credentials file:

```bash
mkdir -p ~/.openclaw/workspace/.credentials
cat > ~/.openclaw/workspace/.credentials/google-calendar.json << 'EOF'
{
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET",
  "refresh_token": "YOUR_REFRESH_TOKEN",
  "token_uri": "https://oauth2.googleapis.com/token"
}
EOF
```

## OAuth Scope

```
https://www.googleapis.com/auth/calendar
```

Full read/write access to calendar (events + ACL sharing).

## Token Notes

- `refresh_token` is long-lived (unless manually revoked or unused for 6+ months)
- `token` (access_token) is auto-refreshed; the script writes it back to the credentials file on each run
- To re-authorize, regenerate credentials in Google Cloud Console

## Key API Endpoints

- Event management: `GET/POST/PUT/DELETE /calendars/primary/events`
- Calendar sharing: `POST /calendars/primary/acl`
- Quick add: `POST /calendars/primary/events/quickAdd`
