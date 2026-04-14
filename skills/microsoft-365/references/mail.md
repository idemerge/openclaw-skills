# Mail — Full Command Reference

Script: `scripts/ms_graph.py` relative to the skill directory

## List emails
```bash
python3 $SKILL_DIR/scripts/ms_graph.py mail list [--top 10] [--folder inbox]
```

## Get email details
```bash
python3 $SKILL_DIR/scripts/ms_graph.py mail get --message-id <id>
```

## Send email
```bash
python3 $SKILL_DIR/scripts/ms_graph.py mail send \
  --to "recipient@example.com" \
  --subject "Subject" \
  --body "Message body" \
  [--cc a@x.com] [--bcc b@x.com]
```

## Reply to email
```bash
python3 $SKILL_DIR/scripts/ms_graph.py mail reply \
  --message-id <id> \
  --body "Reply text"
```

## Delete email
```bash
python3 $SKILL_DIR/scripts/ms_graph.py mail delete --message-id <id>
```

## List mail folders
```bash
python3 $SKILL_DIR/scripts/ms_graph.py mail folders
```

## Notes

- Default folder for `list` is `inbox`; use `--folder` to specify others (e.g. `sentitems`, `drafts`)
- `--top` limits the number of messages returned
- Always show `from`, `subject`, `receivedDateTime`, and a preview of `bodyPreview` when listing
- Get full body with `mail get --message-id <id>` before replying or summarizing
