# openclaw-skills

Collection of OpenClaw skills.

## Project Structure

```
openclaw-skills/
├── skills/                  # Skill source directories
│   └── <skill-name>/
│       ├── SKILL.md
│       ├── scripts/
│       ├── references/
│       └── assets/
├── skills-tars/             # Packaged skill archives
│   └── <skill-name>.tar.gz
└── CLAUDE.md
```

## Packaging Skills

After modifying any skill under `skills/`, rebuild the corresponding tar.gz archive in `skills-tars/`:

```bash
cd /home/work/projects/openclaw-skills
rm -f skills-tars/<skill-name>.tar.gz
tar czf skills-tars/<skill-name>.tar.gz \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='*.pyo' \
  --exclude='.venv' \
  --exclude='*.swp' \
  --exclude='*.swo' \
  -C skills <skill-name>
```

Example for google-calendar:

```bash
cd /home/work/projects/openclaw-skills
rm -f skills-tars/google-calendar.tar.gz
tar czf skills-tars/google-calendar.tar.gz \
  --exclude='__pycache__' --exclude='*.pyc' --exclude='*.pyo' \
  --exclude='.venv' --exclude='*.swp' --exclude='*.swo' \
  -C skills google-calendar
```

Verify contents:

```bash
tar tzf skills-tars/<skill-name>.tar.gz
```

## Git Remote

Uses `github-idemerge` SSH host alias from `~/.ssh/config` for the idemerge account.

## Language Rules

- Always respond in Chinese-simplified
- Code, scripts, and documents must be written in English
