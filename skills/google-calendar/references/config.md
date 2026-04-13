# Google Calendar API Configuration

## Credentials File

Location: `~/.openclaw/workspace/.credentials/google-calendar.json`

| Field | Description |
|-------|-------------|
| client_id | OAuth 2.0 Client ID |
| client_secret | Client Secret |
| refresh_token | Long-lived refresh token |
| token_uri | `https://oauth2.googleapis.com/token` |

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
