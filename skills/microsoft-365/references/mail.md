# Mail — Full Command Reference

Script: `$MS_GRAPH` (set by the agent — see SKILL.md for path resolution)

## List emails
```bash
python3 $MS_GRAPH mail list [--top 10] [--folder inbox]
```

## Get email details
```bash
python3 $MS_GRAPH mail get --message-id <id>
```

## Send email
```bash
python3 $MS_GRAPH mail send \
  --to "recipient@example.com" \
  --subject "Subject" \
  --body "Message body" \
  [--cc a@x.com] [--bcc b@x.com]
```

## Reply to email
```bash
python3 $MS_GRAPH mail reply \
  --message-id <id> \
  --body "Reply text"
```

## Delete email
```bash
python3 $MS_GRAPH mail delete --message-id <id>
```

## List mail folders
```bash
python3 $MS_GRAPH mail folders
```

## Notes

- Default folder for `list` is `inbox`; use `--folder` to specify others (e.g. `sentitems`, `drafts`)
- `--top` limits the number of messages returned
- Always show `from`, `subject`, `receivedDateTime`, and a preview of `bodyPreview` when listing
- Get full body with `mail get --message-id <id>` before replying or summarizing
