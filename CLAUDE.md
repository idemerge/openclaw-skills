# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A collection of [OpenClaw](https://github.com/idemerge/openclaw-skills) skills following the [AgentSkills](https://agentskills.io) spec. Each skill is a self-contained directory that teaches the OpenClaw agent how to perform a specific domain task.

## Skill Anatomy

```
skills/<skill-name>/
├── SKILL.md          # Required — YAML frontmatter (name, description) + markdown instructions
├── scripts/          # Optional — executable code for deterministic reliability
├── references/       # Optional — documentation loaded into context as needed
└── assets/           # Optional — files used in output (templates, icons, etc.)
```

Key design rules:
- **SKILL.md frontmatter `description` is the primary trigger** — it determines when the agent activates the skill. Put all "when to use" info here, not in the body.
- **Body < 500 lines** — move detailed reference material into `references/` files and link from SKILL.md.
- **Progressive disclosure** — metadata always loaded (~100 words), body loaded on trigger (<5k words), references loaded as needed.
- **Scripts auto-re-exec under venv** — if a `.venv/bin/python3` exists relative to the skill dir, scripts re-exec themselves under it automatically (shebang can't use `~`).

## Packaging

After modifying any skill, rebuild its tar.gz archive:

```bash
rm -f skills-tars/<skill-name>.tar.gz
tar czf skills-tars/<skill-name>.tar.gz \
  --exclude='__pycache__' --exclude='*.pyc' --exclude='*.pyo' \
  --exclude='.venv' --exclude='*.swp' --exclude='*.swo' \
  -C skills <skill-name>
```

Verify: `tar tzf skills-tars/<skill-name>.tar.gz`

## Credential Handling Pattern

Skills that require external API credentials should:
1. **Never** ask the user to manually edit files
2. Collect credential values in chat and write the file programmatically
3. Provide a `check-cred` script command to verify credential status
4. Include setup/update/delete flows in `references/config.md`
5. When credentials are missing, print `[SETUP NEEDED]` with a brief explanation pointing the agent to the reference doc

## Timezone Pattern

Skills that deal with dates/times should:
1. Read timezone from a config file (e.g. `google-config.json`), not hardcode it
2. During initial setup, ask the user for their timezone — provide a default (e.g. `Asia/Dubai`)
3. Provide a `show-config` script command to display current timezone
4. Support changing timezone without re-entering credentials

## Language

- Always respond in Chinese-simplified
- Code, scripts, and documents must be written in English
