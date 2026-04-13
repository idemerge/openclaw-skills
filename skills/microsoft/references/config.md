# Microsoft Graph API Configuration

Read this file when the user needs to set up, update, or delete Microsoft Graph credentials or timezone.

## Overview

The skill needs three credential values and one timezone setting:

| Value | What it is | File |
|-------|------------|------|
| `client_id` | Application (client) ID from Microsoft Entra ID | `ms-graph.json` |
| `client_secret` | Client secret from the app registration | `ms-graph.json` |
| `refresh_token` | Long-lived token obtained via OAuth flow | `ms-graph.json` |
| `timezone` | IANA timezone name (default: `Asia/Dubai`) | `ms-graph-config.json` |

Both files are stored in `~/.openclaw/workspace/.credentials/`.

## Step-by-Step Guide for the User

Walk the user through these steps in chat. Wait for the user to complete each step before moving to the next.

### Step 1: Register an App in Microsoft Entra ID

1. Go to [Microsoft Entra admin center](https://entra.microsoft.com/) or [Azure Portal](https://portal.azure.com/)
2. Navigate to **App registrations** → **New registration**
3. Fill in:
   - **Name**: anything (e.g. "OpenClaw Calendar")
   - **Supported account types**: choose based on your account:
     - Personal Microsoft accounts only (Outlook.com) → use tenant `consumers`
     - Any organizational directory and personal accounts → use tenant `common`
   - **Redirect URI**: select **Public client/native**, set to `https://login.microsoftonline.com/common/oauth2/nativeclient`
4. Click **Register**
5. Note the **Application (client) ID** — this is your `client_id`

### Step 2: Create a Client Secret

1. In your app registration, go to **Certificates & secrets** → **New client secret**
2. Add a description and expiry → click **Add**
3. Copy the **Value** immediately — it will be hidden later. This is your `client_secret`

### Step 3: Configure API Permissions

1. Go to **API permissions** → **Add a permission** → **Microsoft Graph** → **Delegated permissions**
2. Add **all** of the following permissions:
   - `Calendars.ReadWrite` — read and write calendar events
   - `Files.ReadWrite.All` — read and write OneDrive files
   - `Mail.ReadWrite` — read and write Outlook mail
   - `Mail.Send` — send emails
   - `User.Read` — read user profile
   - `offline_access` — maintain access via refresh token
3. Click **Grant admin consent** (if you have admin rights)

> **Important**: Add all permissions at once before proceeding to Step 4. If you add more permissions later, you must re-authorize to get a new refresh_token that includes the new scopes.

### Step 4: Get the Refresh Token

1. Open the following URL in a browser (replace `{client_id}` with your actual client ID):

```
https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize?client_id={client_id}&response_type=code&redirect_uri=https%3A%2F%2Flogin.microsoftonline.com%2Fcommon%2Foauth2%2Fnativeclient&response_mode=query&scope=offline_access%20Calendars.ReadWrite%20Files.ReadWrite.All%20Mail.ReadWrite%20Mail.Send%20User.Read&state=12345
```

2. Sign in with your Microsoft account and grant consent
3. After redirect, copy the `code` parameter from the URL
4. Exchange the code for tokens using this command (replace placeholders):

```bash
curl -X POST https://login.microsoftonline.com/consumers/oauth2/v2.0/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id={client_id}&client_secret={client_secret}&scope=offline_access Calendars.ReadWrite Files.ReadWrite.All Mail.ReadWrite Mail.Send User.Read&code={authorization_code}&redirect_uri=https://login.microsoftonline.com/common/oauth2/nativeclient&grant_type=authorization_code"
```

5. The response JSON contains a `refresh_token` — copy it

### Step 5: Save the Credentials

Once the user provides all three values in chat, write the credentials file:

```bash
mkdir -p ~/.openclaw/workspace/.credentials
cat > ~/.openclaw/workspace/.credentials/ms-graph.json << 'EOF'
{
  "client_id": "<client_id>",
  "client_secret": "<client_secret>",
  "refresh_token": "<refresh_token>",
  "token_url": "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
}
```

### Step 6: Set Timezone

Ask the user for their timezone. Default: `Asia/Dubai`.

```bash
cat > ~/.openclaw/workspace/.credentials/ms-graph-config.json << 'EOF'
{
  "timezone": "<timezone>"
}
EOF
```

Common timezone values: `Asia/Dubai`, `Asia/Shanghai`, `America/New_York`, `Europe/London`, `UTC`.

## Update Credentials

1. Ask which fields to update
2. Collect new values in chat
3. Overwrite the credentials file (same command as Step 5)
4. Verify with `ms_graph.py calendar list`

## Delete Credentials

```bash
rm ~/.openclaw/workspace/.credentials/ms-graph.json
rm ~/.openclaw/workspace/.credentials/ms-graph-config.json
rm ~/.ms-graph-token
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `invalid_grant` on refresh_token | Token expired (~90 days). Generate a new one (Step 4) |
| `invalid_client` | Check client_id and client_secret are correct |
| 403 Forbidden | Check API permissions are added and consented |
| `interaction_required` | Re-authorize in browser (Step 4) |

## Token Notes

- `refresh_token` is valid for ~90 days and rotates on each refresh
- `access_token` expires in ~1 hour, auto-refreshed by the script
- The script writes refreshed tokens to `~/.ms-graph-token`
