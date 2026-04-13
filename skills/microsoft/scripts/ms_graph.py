#!/usr/bin/env python3
"""
ms_graph.py - Microsoft 365 Management Tool (Calendar + OneDrive + Mail)

Usage:
  ms_graph.py calendar create   --subject "Meeting" --start "2026-03-30T10:00:00" --end "2026-03-30T11:00:00" [options]
  ms_graph.py calendar list     [--days 7]
  ms_graph.py calendar get      --event-id <id>
  ms_graph.py calendar update   --event-id <id> [--subject ...] [--start ...] [--end ...] [options]
  ms_graph.py calendar delete   --event-id <id>
  ms_graph.py calendar calendars
  ms_graph.py calendar share-list   [--calendar-id <id>]
  ms_graph.py calendar share-add    --email <email> [--role read] [--calendar-id <id>]
  ms_graph.py calendar share-update --permission-id <id> --role <role> [--calendar-id <id>]
  ms_graph.py calendar share-remove --permission-id <id> [--calendar-id <id>]

  ms_graph.py onedrive list   [--path "/"] [--top 20]
  ms_graph.py onedrive info    --item-id <id>
  ms_graph.py onedrive download --item-id <id> [--output /path/to/save]
  ms_graph.py onedrive upload   --local-file /path/to/file --remote-path "/folder/file.ext"
  ms_graph.py onedrive mkdir    --name "New Folder" [--parent-id <id>]
  ms_graph.py onedrive delete   --item-id <id>
  ms_graph.py onedrive search   --query "keyword"

  ms_graph.py mail list     [--top 10] [--folder inbox]
  ms_graph.py mail get      --message-id <id>
  ms_graph.py mail send     --to "a@x.com" --subject "Sub" --body "Text" [--cc ...] [--bcc ...]
  ms_graph.py mail reply    --message-id <id> --body "Reply text"
  ms_graph.py mail delete   --message-id <id>
  ms_graph.py mail folders

  ms_graph.py check-cred
  ms_graph.py show-config

Credentials: ~/.openclaw/workspace/.credentials/ms-graph.json
Config:      ~/.openclaw/workspace/.credentials/ms-graph-config.json
Token cache: ~/.ms-graph-token
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.parse
import re

TOKEN_FILE = os.path.expanduser("~/.ms-graph-token")
CREDENTIALS_FILE = os.path.expanduser("~/.openclaw/workspace/.credentials/ms-graph.json")
CONFIG_FILE = os.path.expanduser("~/.openclaw/workspace/.credentials/ms-graph-config.json")
GRAPH_API = "https://graph.microsoft.com/v1.0/me"


def load_timezone():
    """Load timezone from config file. Falls back to Asia/Dubai."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                cfg = json.load(f)
            if cfg.get("timezone"):
                return cfg["timezone"]
        except Exception:
            pass
    return "Asia/Dubai"


DEFAULT_TIMEZONE = load_timezone()


def load_credentials():
    """Load credentials from file."""
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"[SETUP NEEDED] Microsoft Graph credentials not found.", file=sys.stderr)
        print(f"\nPlease provide the following values:\n"
              f"  1. client_id\n"
              f"  2. client_secret\n"
              f"  3. refresh_token\n"
              f"\nShare them in chat and I will save them to:\n"
              f"  {CREDENTIALS_FILE}", file=sys.stderr)
        sys.exit(1)
    with open(CREDENTIALS_FILE) as f:
        return json.load(f)


# ── Token helpers ──────────────────────────────────────────────────────────────

def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            return json.load(f)
    cred = load_credentials()
    return {"refresh_token": cred["refresh_token"], "access_token": None, "expires_at": 0}


def save_tokens(data):
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f, indent=2)
    os.chmod(TOKEN_FILE, 0o600)


def refresh_access_token(refresh_token: str) -> dict:
    cred = load_credentials()
    token_url = cred.get("token_url", "https://login.microsoftonline.com/consumers/oauth2/v2.0/token")
    data = urllib.parse.urlencode({
        "client_id": cred["client_id"],
        "client_secret": cred.get("client_secret", ""),
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": "offline_access Calendars.ReadWrite Files.ReadWrite.All Mail.ReadWrite Mail.Send User.Read",
    }).encode()
    req = urllib.request.Request(token_url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[ERROR] Failed to refresh token: {e.code} {body}", file=sys.stderr)
        sys.exit(1)


def get_access_token() -> str:
    tokens = load_tokens()
    now = time.time()
    if tokens.get("access_token") and tokens.get("expires_at", 0) > now + 60:
        return tokens["access_token"]
    print("[INFO] Refreshing access token...", file=sys.stderr)
    result = refresh_access_token(tokens["refresh_token"])
    tokens["access_token"] = result["access_token"]
    tokens["expires_at"] = now + result.get("expires_in", 3600)
    if "refresh_token" in result:
        tokens["refresh_token"] = result["refresh_token"]
    save_tokens(tokens)
    return tokens["access_token"]


# ── API helper ─────────────────────────────────────────────────────────────────

def api_request(method: str, path: str, body: dict = None, prefer: str = None) -> dict:
    token = get_access_token()
    url = GRAPH_API + path
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    if prefer:
        req.add_header("Prefer", prefer)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read()
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        body_err = e.read().decode()
        print(f"[ERROR] API request failed: {e.code}\n{body_err}", file=sys.stderr)
        sys.exit(1)


# ── Print helpers ──────────────────────────────────────────────────────────────

def strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", text)).strip()


def print_event(ev: dict):
    print(f"  Title     : {ev.get('subject', '(no title)')}")
    print(f"  Start     : {ev.get('start', {}).get('dateTime', '')} ({ev.get('start', {}).get('timeZone', '')})")
    print(f"  End       : {ev.get('end', {}).get('dateTime', '')}")
    loc = ev.get("location", {}).get("displayName", "")
    if loc:
        print(f"  Location  : {loc}")
    body_content = ev.get("body", {}).get("content", "").strip()
    if body_content:
        plain = strip_html(body_content)
        if plain:
            print(f"  Body      : {plain[:200]}")
    attendees = ev.get("attendees", [])
    if attendees:
        emails = [a.get("emailAddress", {}).get("address", "") for a in attendees]
        print(f"  Attendees : {', '.join(emails)}")
    if ev.get("isOnlineMeeting"):
        join_url = ev.get("onlineMeeting", {}).get("joinUrl", "")
        print(f"  Online    : {join_url or 'Yes'}")
    print(f"  Web link  : {ev.get('webLink', 'N/A')}")
    print(f"  ID        : {ev.get('id', '')}")


def build_attendees(emails: list) -> list:
    normalized = []
    for e in emails:
        for addr in e.split(","):
            addr = addr.strip()
            if addr:
                normalized.append(addr)
    return [{"emailAddress": {"address": addr}, "type": "required", "status": {"response": "notResponded"}} for addr in normalized]


# ── Calendar commands ──────────────────────────────────────────────────────────

ROLE_LABEL = {
    "freeBusyRead": "Free/busy only",
    "limitedRead": "Free/busy + title + location",
    "read": "Read-only",
    "write": "Read/write",
    "delegateWithoutPrivateEventAccess": "Delegate (non-private)",
    "delegateWithPrivateEventAccess": "Delegate (all)",
}


def get_calendar_id(args_calendar_id: str) -> str:
    if args_calendar_id:
        return args_calendar_id
    result = api_request("GET", "/calendars?$select=id,name,isDefaultCalendar")
    for cal in result.get("value", []):
        if cal.get("isDefaultCalendar"):
            return cal["id"]
    cals = result.get("value", [])
    if cals:
        return cals[0]["id"]
    print("[ERROR] No calendars found", file=sys.stderr)
    sys.exit(1)


def cmd_cal_create(args):
    event = {
        "subject": args.subject,
        "start": {"dateTime": args.start, "timeZone": args.timezone},
        "end":   {"dateTime": args.end,   "timeZone": args.timezone},
        "responseRequested": True,
    }
    if args.body:
        event["body"] = {"contentType": "text", "content": args.body}
    if args.location:
        event["location"] = {"displayName": args.location}
    if args.attendees:
        event["attendees"] = build_attendees(args.attendees)
    if args.online:
        event["isOnlineMeeting"] = True
        event["onlineMeetingProvider"] = "teamsForBusiness"

    result = api_request("POST", "/events", event)
    print("[OK] Event created")
    print_event(result)


def cmd_cal_list(args):
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    end_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() + args.days * 86400))
    path = (
        f"/calendarView?startDateTime={now_iso}Z&endDateTime={end_iso}Z"
        f"&$orderby=start/dateTime&$top=50"
        f"&$select=id,subject,start,end,location,isOnlineMeeting"
    )
    result = api_request("GET", path)
    events = result.get("value", [])
    if not events:
        print(f"No events in the next {args.days} day(s).")
        return
    print(f"Events in the next {args.days} day(s) ({len(events)} total):\n")
    for ev in events:
        start = ev.get("start", {}).get("dateTime", "")[:16]
        end   = ev.get("end",   {}).get("dateTime", "")[11:16]
        subject = ev.get("subject", "(no title)")
        online = " [Online]" if ev.get("isOnlineMeeting") else ""
        loc = ev.get("location", {}).get("displayName", "")
        loc_str = f"  @{loc}" if loc else ""
        print(f"  {start} ~ {end}  {subject}{online}{loc_str}")
        print(f"    id: {ev.get('id', '')}")


def cmd_cal_get(args):
    result = api_request("GET", f"/events/{args.event_id}")
    print("[Event Details]")
    print_event(result)


def cmd_cal_update(args):
    patch = {}
    if args.subject:
        patch["subject"] = args.subject
    if args.start or args.end or args.timezone:
        current = api_request("GET", f"/events/{args.event_id}")
        tz = args.timezone or current.get("start", {}).get("timeZone", DEFAULT_TIMEZONE)
        patch["start"] = {"dateTime": args.start or current["start"]["dateTime"][:19], "timeZone": tz}
        patch["end"]   = {"dateTime": args.end   or current["end"]["dateTime"][:19],   "timeZone": tz}
    if args.body is not None:
        patch["body"] = {"contentType": "text", "content": args.body}
    if args.location is not None:
        patch["location"] = {"displayName": args.location}
    if args.attendees is not None:
        patch["attendees"] = build_attendees(args.attendees)
    if args.online:
        patch["isOnlineMeeting"] = True
        patch["onlineMeetingProvider"] = "teamsForBusiness"

    if not patch:
        print("[INFO] No fields specified, nothing to update.")
        return

    result = api_request("PATCH", f"/events/{args.event_id}", patch)
    print("[OK] Event updated")
    print_event(result)


def cmd_cal_delete(args):
    api_request("DELETE", f"/events/{args.event_id}")
    print(f"[OK] Event deleted: {args.event_id}")


def cmd_cal_calendars(args):
    result = api_request("GET", "/calendars?$select=id,name,isDefaultCalendar,color")
    cals = result.get("value", [])
    if not cals:
        print("No calendars found.")
        return
    print(f"{len(cals)} calendar(s) found:\n")
    for cal in cals:
        default = " *" if cal.get("isDefaultCalendar") else ""
        print(f"  {cal.get('name', '(unnamed)')}{default}")
        print(f"    id: {cal.get('id', '')}")


def cmd_cal_share_list(args):
    cal_id = get_calendar_id(getattr(args, "calendar_id", None))
    result = api_request("GET", f"/calendars/{cal_id}/calendarPermissions")
    perms = result.get("value", [])
    if not perms:
        print("No sharing permissions on this calendar.")
        return
    print(f"{len(perms)} sharing permission(s):\n")
    for p in perms:
        email = p.get("emailAddress", {})
        role = p.get("role", "")
        role_str = ROLE_LABEL.get(role, role)
        inside = "Internal" if p.get("isInsideOrganization") else "External"
        print(f"  {email.get('address', '(everyone)')}  [{role_str}]  {inside}")
        print(f"    permission-id: {p.get('id', '')}")
        allowed = p.get("allowedRoles", [])
        if allowed:
            print(f"    upgradeable to: {', '.join(allowed)}")


def cmd_cal_share_add(args):
    cal_id = get_calendar_id(getattr(args, "calendar_id", None))
    body = {
        "emailAddress": {
            "address": args.email,
            "name": args.name or args.email.split("@")[0],
        },
        "isInsideOrganization": False,
        "role": args.role,
    }
    result = api_request("POST", f"/calendars/{cal_id}/calendarPermissions", body)
    role_str = ROLE_LABEL.get(args.role, args.role)
    print(f"[OK] Calendar shared with {args.email} (permission: {role_str})")
    print(f"  permission-id: {result.get('id', '')}")
    print("  Note: The recipient must accept the email invitation to access the calendar.")


def cmd_cal_share_update(args):
    cal_id = get_calendar_id(getattr(args, "calendar_id", None))
    result = api_request(
        "PATCH",
        f"/calendars/{cal_id}/calendarPermissions/{args.permission_id}",
        {"role": args.role},
    )
    role_str = ROLE_LABEL.get(args.role, args.role)
    print(f"[OK] Permission updated to: {role_str}")


def cmd_cal_share_remove(args):
    cal_id = get_calendar_id(getattr(args, "calendar_id", None))
    api_request("DELETE", f"/calendars/{cal_id}/calendarPermissions/{args.permission_id}")
    print(f"[OK] Sharing permission removed: {args.permission_id}")


# ── OneDrive commands ──────────────────────────────────────────────────────────

def cmd_od_list(args):
    path = args.path.strip("/")
    if path:
        api_path = f"/drive/root:/{urllib.parse.quote(path)}:/children?$top={args.top}&$select=id,name,size,lastModifiedDateTime,folder,file"
    else:
        api_path = f"/drive/root/children?$top={args.top}&$select=id,name,size,lastModifiedDateTime,folder,file"
    result = api_request("GET", api_path)
    items = result.get("value", [])
    if not items:
        print(f"No items found in '{args.path}'.")
        return
    print(f"Items in '{args.path}' ({len(items)} total):\n")
    for item in items:
        name = item.get("name", "(unnamed)")
        if "folder" in item:
            print(f"  [DIR]  {name}")
        else:
            size = item.get("size", 0)
            size_str = f"{size / 1024:.1f}KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f}MB"
            print(f"  [FILE] {name}  ({size_str})")
        print(f"    id: {item.get('id', '')}")


def cmd_od_info(args):
    result = api_request("GET", f"/drive/items/{args.item_id}?$select=id,name,size,createdDateTime,lastModifiedDateTime,folder,file,webUrl,parentReference")
    name = result.get("name", "(unnamed)")
    print(f"  Name       : {name}")
    print(f"  ID         : {result.get('id', '')}")
    print(f"  Type       : {'Folder' if 'folder' in result else 'File'}")
    size = result.get("size", 0)
    print(f"  Size       : {size} bytes")
    print(f"  Created    : {result.get('createdDateTime', 'N/A')}")
    print(f"  Modified   : {result.get('lastModifiedDateTime', 'N/A')}")
    print(f"  Web URL    : {result.get('webUrl', 'N/A')}")
    parent = result.get("parentReference", {})
    if parent:
        print(f"  Parent     : {parent.get('name', 'N/A')} (id: {parent.get('id', 'N/A')})")


def cmd_od_download(args):
    result = api_request("GET", f"/drive/items/{args.item_id}?$select=name,@microsoft.graph.downloadUrl")
    dl_url = result.get("@microsoft.graph.downloadUrl")
    if not dl_url:
        print("[ERROR] No download URL found for this item.", file=sys.stderr)
        sys.exit(1)
    filename = result.get("name", "download")
    output = args.output or filename
    print(f"[INFO] Downloading '{filename}'...")
    req = urllib.request.Request(dl_url)
    token = get_access_token()
    req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        with open(output, "wb") as f:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                f.write(chunk)
    print(f"[OK] Downloaded to: {output}")


def cmd_od_upload(args):
    local_path = args.local_file
    remote_path = args.remote_path.strip("/")
    if not os.path.exists(local_path):
        print(f"[ERROR] Local file not found: {local_path}", file=sys.stderr)
        sys.exit(1)
    file_size = os.path.getsize(local_path)
    if file_size > 4 * 1024 * 1024:
        print(f"[ERROR] File too large ({file_size} bytes). Simple upload supports files up to 4MB.", file=sys.stderr)
        print("For larger files, use the resumable upload session API.", file=sys.stderr)
        sys.exit(1)
    filename = os.path.basename(local_path)
    # If remote_path ends with "/", append filename
    if remote_path.endswith("/"):
        remote_path = remote_path + filename
    api_path = f"/drive/root:/{urllib.parse.quote(remote_path)}:/content"
    with open(local_path, "rb") as f:
        file_data = f.read()
    token = get_access_token()
    url = GRAPH_API + api_path
    req = urllib.request.Request(url, data=file_data, method="PUT")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/octet-stream")
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
        print(f"[OK] File uploaded: {result.get('name', filename)}")
        print(f"  ID      : {result.get('id', '')}")
        print(f"  Web URL : {result.get('webUrl', 'N/A')}")
    except urllib.error.HTTPError as e:
        body_err = e.read().decode()
        print(f"[ERROR] Upload failed: {e.code}\n{body_err}", file=sys.stderr)
        sys.exit(1)


def cmd_od_mkdir(args):
    parent_id = args.parent_id
    if parent_id:
        api_path = f"/drive/items/{parent_id}/children"
    else:
        api_path = "/drive/root/children"
    body = {
        "name": args.name,
        "folder": {},
        "@microsoft.graph.conflictBehavior": "rename",
    }
    result = api_request("POST", api_path, body)
    print(f"[OK] Folder created: {args.name}")
    print(f"  ID      : {result.get('id', '')}")
    print(f"  Web URL : {result.get('webUrl', 'N/A')}")


def cmd_od_delete(args):
    api_request("DELETE", f"/drive/items/{args.item_id}")
    print(f"[OK] Item deleted: {args.item_id}")


def cmd_od_search(args):
    api_path = f"/drive/root/search(q='{urllib.parse.quote(args.query)}')?$top=20&$select=id,name,size,folder,file,webUrl"
    result = api_request("GET", api_path)
    items = result.get("value", [])
    if not items:
        print(f"No results for '{args.query}'.")
        return
    print(f"Search results for '{args.query}' ({len(items)} total):\n")
    for item in items:
        name = item.get("name", "(unnamed)")
        kind = "[DIR]" if "folder" in item else "[FILE]"
        print(f"  {kind}  {name}")
        print(f"    id: {item.get('id', '')}  url: {item.get('webUrl', 'N/A')}")


# ── Mail commands ──────────────────────────────────────────────────────────────

def print_message(msg: dict, brief: bool = False):
    sender = msg.get("from", {}).get("emailAddress", {})
    sender_str = f"{sender.get('name', '')} <{sender.get('address', '')}>"
    subject = msg.get("subject", "(no subject)")
    received = msg.get("receivedDateTime", "N/A")
    if brief:
        print(f"  {received[:16]}  {sender_str[:30]:30s}  {subject[:50]}")
        print(f"    id: {msg.get('id', '')}")
        return
    print(f"  Subject   : {subject}")
    print(f"  From      : {sender_str}")
    to_addrs = [r.get("emailAddress", {}).get("address", "") for r in msg.get("toRecipients", [])]
    if to_addrs:
        print(f"  To        : {', '.join(to_addrs)}")
    cc_addrs = [r.get("emailAddress", {}).get("address", "") for r in msg.get("ccRecipients", [])]
    if cc_addrs:
        print(f"  Cc        : {', '.join(cc_addrs)}")
    print(f"  Received  : {received}")
    print(f"  ID        : {msg.get('id', '')}")
    body = msg.get("body", {})
    content = body.get("content", "").strip()
    if content:
        plain = strip_html(content)
        if plain:
            print(f"  Body      : {plain[:300]}")


def cmd_mail_list(args):
    folder = args.folder or "inbox"
    api_path = f"/mailFolders/{folder}/messages?$top={args.top}&$select=id,subject,from,receivedDateTime,toRecipients"
    result = api_request("GET", api_path)
    messages = result.get("value", [])
    if not messages:
        print(f"No messages in '{folder}'.")
        return
    print(f"Messages in '{folder}' ({len(messages)} total):\n")
    for msg in messages:
        print_message(msg, brief=True)


def cmd_mail_get(args):
    result = api_request("GET", f"/messages/{args.message_id}?$select=id,subject,from,toRecipients,ccRecipients,receivedDateTime,body")
    print("[Message Details]")
    print_message(result)


def cmd_mail_send(args):
    to_emails = [{"emailAddress": {"address": addr.strip()}} for addr in args.to.split(",") if addr.strip()]
    msg = {
        "subject": args.subject,
        "body": {"contentType": "text", "content": args.body},
        "toRecipients": to_emails,
    }
    if args.cc:
        msg["ccRecipients"] = [{"emailAddress": {"address": addr.strip()}} for addr in args.cc.split(",") if addr.strip()]
    if args.bcc:
        msg["bccRecipients"] = [{"emailAddress": {"address": addr.strip()}} for addr in args.bcc.split(",") if addr.strip()]
    api_request("POST", "/sendMail", {"message": msg})
    print(f"[OK] Email sent to: {args.to}")


def cmd_mail_reply(args):
    reply_body = {"comment": args.body}
    api_request("POST", f"/messages/{args.message_id}/reply", reply_body)
    print(f"[OK] Reply sent for message: {args.message_id}")


def cmd_mail_delete(args):
    api_request("DELETE", f"/messages/{args.message_id}")
    print(f"[OK] Message deleted: {args.message_id}")


def cmd_mail_folders(args):
    result = api_request("GET", "/mailFolders?$top=50&$select=id,displayName,totalItemCount,unreadItemCount")
    folders = result.get("value", [])
    if not folders:
        print("No mail folders found.")
        return
    print(f"Mail folders ({len(folders)} total):\n")
    for folder in folders:
        name = folder.get("displayName", "(unnamed)")
        total = folder.get("totalItemCount", 0)
        unread = folder.get("unreadItemCount", 0)
        print(f"  {name}  ({unread} unread / {total} total)")
        print(f"    id: {folder.get('id', '')}")


# ── Config commands ────────────────────────────────────────────────────────────

def cmd_check_cred(args):
    if not os.path.exists(CREDENTIALS_FILE):
        print("[MISSING] Credentials file not found")
        print(f"  Location: {CREDENTIALS_FILE}")
        print("  Provide client_id, client_secret, refresh_token in chat to set up")
        return
    with open(CREDENTIALS_FILE) as f:
        cred = json.load(f)
    missing = [k for k in ("client_id", "client_secret", "refresh_token") if not cred.get(k)]
    if missing:
        print(f"[INVALID] Missing required fields: {', '.join(missing)}")
        print(f"  Location: {CREDENTIALS_FILE}")
        return
    try:
        get_access_token()
        print("[OK] Credentials are valid")
        print(f"  Location: {CREDENTIALS_FILE}")
        print(f"  client_id: {cred['client_id'][:20]}...")
    except SystemExit:
        pass


def cmd_show_config(args):
    print(f"Timezone : {DEFAULT_TIMEZONE}")
    print(f"Config   : {CONFIG_FILE}")
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        print(f"  timezone: {cfg.get('timezone', '(not set)')}")
    else:
        print("  (config file not found - using default Asia/Dubai)")
    print(f"Credentials : {CREDENTIALS_FILE}")
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE) as f:
            cred = json.load(f)
        print(f"  client_id: {cred.get('client_id', 'N/A')[:20]}...")
        print(f"  tenant: {cred.get('token_url', '').split('/')[3]}")
    else:
        print("  (not configured)")


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Microsoft 365 Management (Calendar + OneDrive + Mail)")
    sub = parser.add_subparsers(dest="group")

    # ── Calendar ──
    cal = sub.add_parser("calendar", help="Calendar operations")
    cal_sub = cal.add_subparsers(dest="command")

    p_c = cal_sub.add_parser("create", help="Create a new event")
    p_c.add_argument("--subject",   required=True)
    p_c.add_argument("--start",     required=True, help="Start time ISO8601")
    p_c.add_argument("--end",       required=True, help="End time ISO8601")
    p_c.add_argument("--timezone",  default=DEFAULT_TIMEZONE)
    p_c.add_argument("--body",      help="Event description")
    p_c.add_argument("--location",  help="Location")
    p_c.add_argument("--attendees", nargs="*", help="Attendee emails")
    p_c.add_argument("--online",    action="store_true", help="Create Teams online meeting")

    p_l = cal_sub.add_parser("list", help="List upcoming events")
    p_l.add_argument("--days", type=int, default=7, help="Days to look ahead (default: 7)")

    p_g = cal_sub.add_parser("get", help="Get event details")
    p_g.add_argument("--event-id", required=True)

    p_u = cal_sub.add_parser("update", help="Update an event")
    p_u.add_argument("--event-id",  required=True)
    p_u.add_argument("--subject",   help="New title")
    p_u.add_argument("--start",     help="New start time")
    p_u.add_argument("--end",       help="New end time")
    p_u.add_argument("--timezone",  help="New timezone")
    p_u.add_argument("--body",      help="New body")
    p_u.add_argument("--location",  help="New location")
    p_u.add_argument("--attendees", nargs="*", help="New attendees list")
    p_u.add_argument("--online",    action="store_true", help="Enable Teams meeting")

    p_d = cal_sub.add_parser("delete", help="Delete an event")
    p_d.add_argument("--event-id", required=True)

    cal_sub.add_parser("calendars", help="List all calendars")

    p_sl = cal_sub.add_parser("share-list", help="View calendar sharing permissions")
    p_sl.add_argument("--calendar-id")

    p_sa = cal_sub.add_parser("share-add", help="Add a sharing permission")
    p_sa.add_argument("--email",       required=True)
    p_sa.add_argument("--name")
    p_sa.add_argument("--role",        default="read",
                      choices=["freeBusyRead", "limitedRead", "read", "write",
                               "delegateWithoutPrivateEventAccess", "delegateWithPrivateEventAccess"])
    p_sa.add_argument("--calendar-id")

    p_su = cal_sub.add_parser("share-update", help="Update a sharing permission")
    p_su.add_argument("--permission-id", required=True)
    p_su.add_argument("--role",          required=True,
                      choices=["freeBusyRead", "limitedRead", "read", "write",
                               "delegateWithoutPrivateEventAccess", "delegateWithPrivateEventAccess"])
    p_su.add_argument("--calendar-id")

    p_sr = cal_sub.add_parser("share-remove", help="Remove a sharing permission")
    p_sr.add_argument("--permission-id", required=True)
    p_sr.add_argument("--calendar-id")

    # ── OneDrive ──
    od = sub.add_parser("onedrive", help="OneDrive file operations")
    od_sub = od.add_subparsers(dest="command")

    p_odl = od_sub.add_parser("list", help="List files in a folder")
    p_odl.add_argument("--path", default="/", help="Folder path (default: /)")
    p_odl.add_argument("--top", type=int, default=20, help="Max items (default: 20)")

    p_odi = od_sub.add_parser("info", help="Get file/folder info")
    p_odi.add_argument("--item-id", required=True)

    p_odd = od_sub.add_parser("download", help="Download a file")
    p_odd.add_argument("--item-id", required=True)
    p_odd.add_argument("--output", help="Local path to save (default: original filename)")

    p_odu = od_sub.add_parser("upload", help="Upload a file (<4MB)")
    p_odu.add_argument("--local-file", required=True, help="Local file path")
    p_odu.add_argument("--remote-path", required=True, help="Remote path (e.g. /folder/file.txt)")

    p_odm = od_sub.add_parser("mkdir", help="Create a folder")
    p_odm.add_argument("--name", required=True, help="Folder name")
    p_odm.add_argument("--parent-id", help="Parent folder ID (default: root)")

    p_odx = od_sub.add_parser("delete", help="Delete a file or folder")
    p_odx.add_argument("--item-id", required=True)

    p_ods = od_sub.add_parser("search", help="Search files")
    p_ods.add_argument("--query", required=True, help="Search keyword")

    # ── Mail ──
    mail = sub.add_parser("mail", help="Outlook mail operations")
    mail_sub = mail.add_subparsers(dest="command")

    p_ml = mail_sub.add_parser("list", help="List emails")
    p_ml.add_argument("--top", type=int, default=10, help="Max messages (default: 10)")
    p_ml.add_argument("--folder", default="inbox", help="Mail folder (default: inbox)")

    p_mg = mail_sub.add_parser("get", help="Get email details")
    p_mg.add_argument("--message-id", required=True)

    p_ms = mail_sub.add_parser("send", help="Send an email")
    p_ms.add_argument("--to",      required=True, help="Recipient email(s), comma-separated")
    p_ms.add_argument("--subject", required=True)
    p_ms.add_argument("--body",    required=True)
    p_ms.add_argument("--cc",      help="Cc email(s), comma-separated")
    p_ms.add_argument("--bcc",     help="Bcc email(s), comma-separated")

    p_mr = mail_sub.add_parser("reply", help="Reply to an email")
    p_mr.add_argument("--message-id", required=True)
    p_mr.add_argument("--body",       required=True)

    p_md = mail_sub.add_parser("delete", help="Delete an email")
    p_md.add_argument("--message-id", required=True)

    mail_sub.add_parser("folders", help="List mail folders")

    # ── Config ──
    sub.add_parser("check-cred", help="Check credential status")
    sub.add_parser("show-config", help="Show current configuration")

    args = parser.parse_args()

    # Route to handler
    if args.group == "calendar":
        cal_commands = {
            "create":       cmd_cal_create,
            "list":         cmd_cal_list,
            "get":          cmd_cal_get,
            "update":       cmd_cal_update,
            "delete":       cmd_cal_delete,
            "calendars":    cmd_cal_calendars,
            "share-list":   cmd_cal_share_list,
            "share-add":    cmd_cal_share_add,
            "share-update": cmd_cal_share_update,
            "share-remove": cmd_cal_share_remove,
        }
        handler = cal_commands.get(args.command)
        if handler:
            handler(args)
        else:
            cal.print_help()

    elif args.group == "onedrive":
        od_commands = {
            "list":    cmd_od_list,
            "info":    cmd_od_info,
            "download": cmd_od_download,
            "upload":  cmd_od_upload,
            "mkdir":   cmd_od_mkdir,
            "delete":  cmd_od_delete,
            "search":  cmd_od_search,
        }
        handler = od_commands.get(args.command)
        if handler:
            handler(args)
        else:
            od.print_help()

    elif args.group == "mail":
        mail_commands = {
            "list":    cmd_mail_list,
            "get":     cmd_mail_get,
            "send":    cmd_mail_send,
            "reply":   cmd_mail_reply,
            "delete":  cmd_mail_delete,
            "folders": cmd_mail_folders,
        }
        handler = mail_commands.get(args.command)
        if handler:
            handler(args)
        else:
            mail.print_help()

    elif args.group == "check-cred":
        cmd_check_cred(args)
    elif args.group == "show-config":
        cmd_show_config(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
