# OpenClaw Skills

A collection of [OpenClaw](https://github.com/openclaw/openclaw) skills following the [AgentSkills](https://agentskills.io) spec.

## Skills

### google

Manage Google Calendar via Google Calendar API v3.

- Full CRUD for calendar events
- Natural language quick-add (`gcal.py quick "Meeting tomorrow at 3pm"`)
- Calendar sharing with permission management
- Chat-based OAuth credential setup (no manual file editing)
- Configurable timezone (default: `Asia/Shanghai`)
- Python venv with auto-re-exec for dependencies

### microsoft

Unified Microsoft 365 access via Microsoft Graph API — Calendar, OneDrive, and Outlook Mail in one skill.

- **Calendar**: CRUD + sharing + Teams online meetings
- **OneDrive**: list, info, download, upload, mkdir, delete, search
- **Mail**: list, get, send, reply, delete, folders
- Chat-based credential setup
- Configurable timezone (default: `Asia/Dubai`)
- Pure Python stdlib — no external dependencies

## Installation

### From ClawHub (recommended)

```bash
openclaw skills install google
openclaw skills install microsoft
```

### Manual

```bash
git clone https://github.com/idemerge/openclaw-skills.git
cp -r openclaw-skills/skills/google ~/.openclaw/skills/
cp -r openclaw-skills/skills/microsoft ~/.openclaw/skills/
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
