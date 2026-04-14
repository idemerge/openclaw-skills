# Calendar — Full Command Reference

Script: `$MS_GRAPH` (set by the agent — see SKILL.md for path resolution)

## Create event
```bash
python3 $MS_GRAPH calendar create \
  --subject "Title" \
  --start "2026-03-30T10:00:00" \
  --end "2026-03-30T11:00:00" \
  [--timezone "Asia/Dubai"] \
  [--body "Description"] \
  [--location "Location"] \
  [--attendees a@x.com b@x.com] \
  [--online]
```

## List events
```bash
python3 $MS_GRAPH calendar list [--days 7] [--top 50]
```

## Get event details
```bash
python3 $MS_GRAPH calendar get --event-id <id>
```

## Update event
```bash
python3 $MS_GRAPH calendar update \
  --event-id <id> \
  [--subject ...] [--start ...] [--end ...] [--timezone ...] \
  [--body ...] [--location ...] [--attendees ...] [--online]
```

## Delete event
```bash
python3 $MS_GRAPH calendar delete --event-id <id>
```

## List calendars
```bash
python3 $MS_GRAPH calendar calendars
```

## Calendar sharing

```bash
# List sharing permissions
python3 $MS_GRAPH calendar share-list [--calendar-id <id>]

# Add sharing permission
python3 $MS_GRAPH calendar share-add \
  --email <email> [--role read] [--calendar-id <id>]
# Roles: freeBusyRead | limitedRead | read | write | delegateWithoutPrivateEventAccess | delegateWithPrivateEventAccess

# Update sharing permission
python3 $MS_GRAPH calendar share-update \
  --permission-id <id> --role <role> [--calendar-id <id>]

# Remove sharing permission
python3 $MS_GRAPH calendar share-remove \
  --permission-id <id> [--calendar-id <id>]
```

## Notes

- Times use ISO8601 format: `YYYY-MM-DDTHH:MM:SS`
- Timezone comes from `ms-graph-config.json`; pass `--timezone` to override per-event
- Do NOT add attendees unless the user explicitly asks
- Always determine the current date/time first when the request involves relative dates (today, tomorrow, next Monday)
