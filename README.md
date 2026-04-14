# OpenClaw Skills

A collection of [OpenClaw](https://github.com/openclaw/openclaw) skills following the [AgentSkills](https://agentskills.io) spec.

## Skills

### google

Manage Google Calendar via Google Calendar API v3.

- Full CRUD for calendar events
- Natural language quick-add (`gcal.py quick "Meeting tomorrow at 3pm"`)
- Calendar sharing with permission management
- Chat-based OAuth credential setup (no manual file editing)
- Configurable timezone (default: `Asia/Dubai`)
- Python venv with auto-re-exec for dependencies

### microsoft

Manage Microsoft 365 via Microsoft Graph API — Calendar, OneDrive, and Outlook Mail.
Uses client_secret + refresh_token authentication (requires Azure app registration).

- **Calendar**: CRUD + sharing + Teams online meetings
- **OneDrive**: list, info, download, upload, mkdir, delete, search
- **Mail**: list, get, send, reply, delete, folders
- Chat-based credential setup
- Configurable timezone (default: `Asia/Dubai`)
- Pure Python stdlib — no external dependencies

### microsoft-365

Manage Microsoft 365 via Microsoft Graph API — Calendar, OneDrive, and Outlook Mail.
Uses **Device Code Flow** with a public Client ID — no Azure app registration or client secret required.

- **Calendar**: CRUD + sharing + Teams online meetings
- **OneDrive**: list, info, download, upload, mkdir, delete, search
- **Mail**: list, get, send, reply, delete, folders
- Device Code Flow login (browser-based, no manual config)
- Configurable timezone (default: `Asia/Dubai`)
- Pure Python stdlib — zero external dependencies

## Installation

### From ClawHub (recommended)

```bash
openclaw skills install google
openclaw skills install microsoft
openclaw skills install microsoft-365
```

### Manual

```bash
git clone https://github.com/idemerge/openclaw-skills.git
cp -r openclaw-skills/skills/google ~/.openclaw/skills/
cp -r openclaw-skills/skills/microsoft ~/.openclaw/skills/
cp -r openclaw-skills/skills/microsoft-365 ~/.openclaw/skills/
```

## Skill Structure

```
skills/<skill-name>/
├── SKILL.md          # Required — YAML frontmatter (name, description) + instructions
├── scripts/          # Optional — executable code
├── references/       # Optional — documentation loaded on demand
└── assets/           # Optional — templates, icons, etc.
```

## License

MIT
