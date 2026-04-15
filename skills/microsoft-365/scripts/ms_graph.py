#!/usr/bin/env python3
"""
ms_graph.py - Microsoft 365 Management Tool (Calendar + OneDrive + Mail)
Uses Device Code Flow with pure Python stdlib — no external dependencies required.

Usage:
  ms_graph.py device-code    # Get device code (JSON output, for agent use)
  ms_graph.py login-poll     # Poll for login completion (for agent use)
  ms_graph.py login          # Interactive login (for direct terminal use)
  ms_graph.py logout         # Clear token cache
  ms_graph.py status         # Check login status
  ms_graph.py show-config    # Show timezone and login status

  ms_graph.py calendar create   --subject "Meeting" --start "2026-03-30T10:00:00" --end "2026-03-30T11:00:00" [options]
  ms_graph.py calendar list     [--days 7] [--top 50]
  ms_graph.py calendar get      --event-id <id>
  ms_graph.py calendar update   --event-id <id> [--subject ...] [--start ...] [--end ...] [options]
  ms_graph.py calendar delete   --event-id <id>
  ms_graph.py calendar calendars
  ms_graph.py calendar share-list   [--calendar-id <id>]
  ms_graph.py calendar share-add    --email <email> [--role read] [--calendar-id <id>]
  ms_graph.py calendar share-update --permission-id <id> --role <role> [--calendar-id <id>]
  ms_graph.py calendar share-remove --permission-id <id> [--calendar-id <id>]

  ms_graph.py onedrive list     [--path "/"] [--top 20]
  ms_graph.py onedrive info     --item-id <id>
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

Token cache: ~/.openclaw/ms365_token_cache.json
Config:      ~/.openclaw/workspace/.credentials/ms-graph-config.json
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# ── Constants ──────────────────────────────────────────────────────────────────

# Microsoft Graph Command Line Tools (public client, no secret required)
CLIENT_ID  = "14d82eec-204b-4c2f-b7e8-296a70dab67e"

def _tenant_id():
    """Return tenant ID: 'consumers' for personal accounts, 'organizations' for enterprise.
    Reads from config file; defaults to 'consumers' for personal Outlook.com accounts."""
    cfg_path = os.path.expanduser("~/.openclaw/workspace/.credentials/ms-graph-config.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path) as f:
                cfg = json.load(f)
            tid = cfg.get("tenant_id", "").strip()
            if tid in ("consumers", "organizations", "common"):
                return tid
        except Exception:
            pass
    return "consumers"

TENANT_ID  = _tenant_id()
AUTHORITY  = f"https://login.microsoftonline.com/{TENANT_ID}"
GRAPH_API  = "https://graph.microsoft.com/v1.0/me"

SCOPES = [
    "User.Read",
    "Mail.ReadWrite",
    "Mail.Send",
    "Calendars.ReadWrite",
    "Files.ReadWrite.All",
]

TOKEN_CACHE_PATH  = Path.home() / ".openclaw" / "ms365_token_cache.json"
CONFIG_FILE      = os.path.expanduser("~/.openclaw/workspace/.credentials/ms-graph-config.json")


# ── OAuth helpers (pure stdlib) ───────────────────────────────────────────────

TOKEN_ENDPOINT = f"{AUTHORITY}/oauth2/v2.0/token"
DEVICE_CODE_ENDPOINT = f"{AUTHORITY}/oauth2/v2.0/devicecode"
SCOPE_STRING = " ".join(SCOPES) + " offline_access"


def _oauth_post(url: str, params: dict) -> dict:
    """POST form-encoded data, return JSON response (or error JSON on HTTP 4xx)."""
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())


def _load_cache() -> dict | None:
    """Load token cache from disk, return dict or None."""
    if not TOKEN_CACHE_PATH.exists():
        return None
    try:
        data = json.loads(TOKEN_CACHE_PATH.read_text())
        if "refresh_token" in data:
            return data
    except Exception:
        pass
    TOKEN_CACHE_PATH.unlink(missing_ok=True)
    return None


def _save_cache(data: dict):
    """Write token cache to disk with restricted permissions."""
    TOKEN_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_CACHE_PATH.write_text(json.dumps(data, indent=2))
    if os.name != "nt":
        TOKEN_CACHE_PATH.chmod(0o600)


def _refresh_token(cache: dict) -> dict | None:
    """Use refresh_token to get a new access_token. Returns updated cache or None."""
    result = _oauth_post(TOKEN_ENDPOINT, {
        "client_id": CLIENT_ID,
        "grant_type": "refresh_token",
        "refresh_token": cache["refresh_token"],
        "scope": SCOPE_STRING,
    })
    if "access_token" not in result:
        return None
    cache["access_token"] = result["access_token"]
    cache["refresh_token"] = result.get("refresh_token", cache["refresh_token"])
    cache["expires_at"] = int(time.time()) + result.get("expires_in", 3600)
    _save_cache(cache)
    return cache


def get_access_token(force_refresh: bool = False) -> str:
    """Return a valid access token, auto-refreshing from cache. Exits if not logged in."""
    cache = _load_cache()
    if not cache:
        print("[SETUP NEEDED] Not logged in. Run: ms_graph.py login", file=sys.stderr)
        sys.exit(1)
    # Return cached token if still valid and no forced refresh
    if not force_refresh and cache.get("expires_at", 0) > time.time() + 60:
        return cache["access_token"]
    # Refresh
    updated = _refresh_token(cache)
    if updated:
        return updated["access_token"]
    print("[ERROR] Token refresh failed. Run: ms_graph.py login", file=sys.stderr)
    sys.exit(1)


# ── Auth commands ──────────────────────────────────────────────────────────────

def cmd_device_code(args):
    """Request a device code and output JSON. Returns immediately — no polling."""
    flow = _oauth_post(DEVICE_CODE_ENDPOINT, {
        "client_id": CLIENT_ID,
        "scope": SCOPE_STRING,
    })
    if "user_code" not in flow:
        print(f"[ERROR] Could not start device flow: {flow.get('error_description', flow.get('error'))}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps({
        "verification_uri": flow["verification_uri"],
        "user_code": flow["user_code"],
        "device_code": flow["device_code"],
        "expires_in": flow.get("expires_in", 900),
        "interval": flow.get("interval", 10),
    }))


def cmd_login_poll(args):
    """Poll for token after user confirms browser login is done. Blocks up to 60 seconds."""
    interval = args.interval or 5
    poll_timeout = 60  # 1 minute — user already confirmed login
    expires_at = time.time() + poll_timeout

    while time.time() < expires_at:
        time.sleep(interval)
        result = _oauth_post(TOKEN_ENDPOINT, {
            "client_id": CLIENT_ID,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": args.device_code,
        })
        error = result.get("error")
        if error == "authorization_pending":
            continue
        if error == "slow_down":
            interval += 5
            continue
        if error:
            print(f"LOGIN_FAILED: {result.get('error_description', error)}")
            sys.exit(1)
        # Success — save token cache
        cache = {
            "access_token": result["access_token"],
            "refresh_token": result.get("refresh_token", ""),
            "expires_at": int(time.time()) + result.get("expires_in", 3600),
        }
        try:
            user = _get_user_profile(result["access_token"])
            cache["account"] = {
                "name": user.get("displayName", ""),
                "username": user.get("mail") or user.get("userPrincipalName", ""),
            }
        except Exception:
            cache["account"] = {"name": "", "username": ""}
        _save_cache(cache)
        name = cache["account"].get("name", "")
        email = cache["account"].get("username", "")
        print(f"LOGIN_SUCCESS | {name} | {email}")
        return
    print("LOGIN_TIMEOUT")
    sys.exit(1)


def cmd_login(args):
    """Interactive login — get device code, print instructions, poll. For direct terminal use."""
    flow = _oauth_post(DEVICE_CODE_ENDPOINT, {
        "client_id": CLIENT_ID,
        "scope": SCOPE_STRING,
    })
    if "user_code" not in flow:
        print(f"[ERROR] Could not start device flow: {flow.get('error_description', flow.get('error'))}", file=sys.stderr)
        sys.exit(1)

    print("\n" + "=" * 52)
    print("  Microsoft 365 Login")
    print("=" * 52)
    print(f"  1. Open browser: {flow['verification_uri']}")
    print(f"  2. Enter code:   {flow['user_code']}")
    print(f"  3. Sign in and approve permissions")
    print("=" * 52)
    print("  Note: Microsoft may ask for a verification code")
    print("  (SMS/email/authenticator). This is normal and")
    print("  only required for this login session.")
    print("  After approval, the browser may show a localhost")
    print("  error page — this is expected. Just close it.")
    print("  Waiting for login...\n")

    interval = flow.get("interval", 10)
    poll_timeout = 180
    expires_at = time.time() + poll_timeout
    device_code = flow["device_code"]

    while time.time() < expires_at:
        time.sleep(interval)
        result = _oauth_post(TOKEN_ENDPOINT, {
            "client_id": CLIENT_ID,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": device_code,
        })
        error = result.get("error")
        if error == "authorization_pending":
            continue
        if error == "slow_down":
            interval += 5
            continue
        if error:
            print(f"[ERROR] Login failed: {result.get('error_description', error)}", file=sys.stderr)
            sys.exit(1)
        # Success
        cache = {
            "access_token": result["access_token"],
            "refresh_token": result.get("refresh_token", ""),
            "expires_at": int(time.time()) + result.get("expires_in", 3600),
        }
        try:
            user = _get_user_profile(result["access_token"])
            cache["account"] = {
                "name": user.get("displayName", ""),
                "username": user.get("mail") or user.get("userPrincipalName", ""),
            }
            print(f"[OK] Logged in: {cache['account']['name']} ({cache['account']['username']})")
        except Exception:
            cache["account"] = {"name": "", "username": ""}
            print("[OK] Login successful.")
        _save_cache(cache)
        print("[INFO] Token is cached locally and auto-refreshes for ~90 days. No need to run login again unless you see NOT_LOGGED_IN.")
        return

    print("[ERROR] Login timed out (3 minutes). Please try again.", file=sys.stderr)
    sys.exit(1)


def cmd_logout(args):
    if TOKEN_CACHE_PATH.exists():
        TOKEN_CACHE_PATH.unlink()
        print("[OK] Logged out. Token cache cleared.")
    else:
        print("[INFO] Not currently logged in.")


def cmd_status(args):
    cache = _load_cache()
    if not cache:
        print("NOT_LOGGED_IN")
        return
    # Try refreshing to verify token is still valid
    updated = _refresh_token(cache)
    if updated:
        account = updated.get("account", {})
        name = account.get("name", "")
        email = account.get("username", "")
        if name or email:
            print(f"LOGGED_IN | {name} | {email}")
        else:
            print("LOGGED_IN")
    else:
        print("NOT_LOGGED_IN")


def _get_user_profile(access_token: str) -> dict:
    req = urllib.request.Request(
        "https://graph.microsoft.com/v1.0/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


# ── Config helpers ─────────────────────────────────────────────────────────────

def load_timezone() -> str:
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


# ── API helper ─────────────────────────────────────────────────────────────────

def api_request(method: str, path: str, body: dict = None, prefer: str = None) -> dict:
    url  = GRAPH_API + path
    data = json.dumps(body).encode() if body else None

    def _do_request(token: str) -> dict:
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Content-Type", "application/json")
        if prefer:
            req.add_header("Prefer", prefer)
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read()
            return json.loads(content) if content else {}

    try:
        return _do_request(get_access_token())
    except urllib.error.HTTPError as e:
        if e.code == 401:
            try:
                return _do_request(get_access_token(force_refresh=True))
            except urllib.error.HTTPError as e2:
                body_err = e2.read().decode()
                print(f"[ERROR] API request failed: {e2.code}\n{body_err}", file=sys.stderr)
                sys.exit(1)
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
        f"&$orderby=start/dateTime&$top={args.top}"
        f"&$select=id,subject,start,end,location,isOnlineMeeting"
    )
    result = api_request("GET", path, prefer=f'outlook.timezone="{DEFAULT_TIMEZONE}"')
    events = result.get("value", [])
    if not events:
        print(f"No events in the next {args.days} day(s).")
        return
    print(f"Events in the next {args.days} day(s) ({len(events)} total):\n")
    for ev in events:
        start   = ev.get("start", {}).get("dateTime", "")[:16]
        end     = ev.get("end",   {}).get("dateTime", "")[11:16]
        subject = ev.get("subject", "(no title)")
        online  = " [Online]" if ev.get("isOnlineMeeting") else ""
        loc     = ev.get("location", {}).get("displayName", "")
        loc_str = f"  @{loc}" if loc else ""
        print(f"  {start} ~ {end}  {subject}{online}{loc_str}")
        print(f"    id: {ev.get('id', '')}")


def cmd_cal_get(args):
    result = api_request("GET", f"/events/{args.event_id}", prefer=f'outlook.timezone="{DEFAULT_TIMEZONE}"')
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
        email    = p.get("emailAddress", {})
        role     = p.get("role", "")
        role_str = ROLE_LABEL.get(role, role)
        inside   = "Internal" if p.get("isInsideOrganization") else "External"
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
        "role": args.role,
    }
    result   = api_request("POST", f"/calendars/{cal_id}/calendarPermissions", body)
    role_str = ROLE_LABEL.get(args.role, args.role)
    print(f"[OK] Calendar shared with {args.email} (permission: {role_str})")
    print(f"  permission-id: {result.get('id', '')}")
    print("  Note: The recipient must accept the email invitation to access the calendar.")


def cmd_cal_share_update(args):
    cal_id = get_calendar_id(getattr(args, "calendar_id", None))
    api_request(
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
    items  = result.get("value", [])
    if not items:
        print(f"No items found in '{args.path}'.")
        return
    print(f"Items in '{args.path}' ({len(items)} total):\n")
    for item in items:
        name = item.get("name", "(unnamed)")
        if "folder" in item:
            print(f"  [DIR]  {name}")
        else:
            size     = item.get("size", 0)
            size_str = f"{size / 1024:.1f}KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f}MB"
            print(f"  [FILE] {name}  ({size_str})")
        print(f"    id: {item.get('id', '')}")


def cmd_od_info(args):
    result = api_request("GET", f"/drive/items/{args.item_id}?$select=id,name,size,createdDateTime,lastModifiedDateTime,folder,file,webUrl,parentReference")
    print(f"  Name       : {result.get('name', '(unnamed)')}")
    print(f"  ID         : {result.get('id', '')}")
    print(f"  Type       : {'Folder' if 'folder' in result else 'File'}")
    print(f"  Size       : {result.get('size', 0)} bytes")
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
    output   = args.output or filename
    print(f"[INFO] Downloading '{filename}'...")
    # @microsoft.graph.downloadUrl is pre-signed — no Authorization header needed
    req = urllib.request.Request(dl_url)
    with urllib.request.urlopen(req, timeout=30) as resp:
        with open(output, "wb") as f:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                f.write(chunk)
    print(f"[OK] Downloaded to: {output}")


def cmd_od_upload(args):
    local_path  = args.local_file
    if not os.path.exists(local_path):
        print(f"[ERROR] Local file not found: {local_path}", file=sys.stderr)
        sys.exit(1)
    file_size = os.path.getsize(local_path)
    if file_size > 4 * 1024 * 1024:
        size_mb = file_size / (1024 * 1024)
        print(f"[ERROR] File too large ({size_mb:.1f}MB). Upload supports files up to 4MB. Large file upload is not yet supported.", file=sys.stderr)
        sys.exit(1)
    filename = os.path.basename(local_path)
    # If user gave a directory path (ending with /), append the local filename
    if args.remote_path.endswith("/"):
        remote_path = args.remote_path.strip("/") + "/" + filename
    else:
        remote_path = args.remote_path.strip("/")
    api_path = f"/drive/root:/{urllib.parse.quote(remote_path)}:/content"
    with open(local_path, "rb") as f:
        file_data = f.read()
    url = GRAPH_API + api_path

    def _do_upload(token: str) -> dict:
        req = urllib.request.Request(url, data=file_data, method="PUT")
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Content-Type", "application/octet-stream")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())

    try:
        result = _do_upload(get_access_token())
    except urllib.error.HTTPError as e:
        if e.code == 401:
            try:
                result = _do_upload(get_access_token(force_refresh=True))
            except urllib.error.HTTPError as e2:
                body_err = e2.read().decode()
                print(f"[ERROR] Upload failed: {e2.code}\n{body_err}", file=sys.stderr)
                sys.exit(1)
        else:
            body_err = e.read().decode()
            print(f"[ERROR] Upload failed: {e.code}\n{body_err}", file=sys.stderr)
            sys.exit(1)
    print(f"[OK] File uploaded: {result.get('name', filename)}")
    print(f"  ID      : {result.get('id', '')}")
    print(f"  Web URL : {result.get('webUrl', 'N/A')}")


def cmd_od_mkdir(args):
    api_path = f"/drive/items/{args.parent_id}/children" if args.parent_id else "/drive/root/children"
    body     = {"name": args.name, "folder": {}, "@microsoft.graph.conflictBehavior": "rename"}
    result   = api_request("POST", api_path, body)
    print(f"[OK] Folder created: {args.name}")
    print(f"  ID      : {result.get('id', '')}")
    print(f"  Web URL : {result.get('webUrl', 'N/A')}")


def cmd_od_delete(args):
    api_request("DELETE", f"/drive/items/{args.item_id}")
    print(f"[OK] Item deleted: {args.item_id}")


def cmd_od_search(args):
    api_path = f"/drive/root/search(q='{urllib.parse.quote(args.query)}')?$top=20&$select=id,name,size,folder,file,webUrl"
    result   = api_request("GET", api_path)
    items    = result.get("value", [])
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
    sender     = msg.get("from", {}).get("emailAddress", {})
    sender_str = f"{sender.get('name', '')} <{sender.get('address', '')}>"
    subject    = msg.get("subject", "(no subject)")
    received   = msg.get("receivedDateTime", "N/A")
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
    body    = msg.get("body", {})
    content = body.get("content", "").strip()
    if content:
        plain = strip_html(content)
        if plain:
            print(f"  Body      : {plain[:300]}")


def cmd_mail_list(args):
    folder   = args.folder or "inbox"
    api_path = f"/mailFolders/{folder}/messages?$top={args.top}&$select=id,subject,from,receivedDateTime,toRecipients"
    result   = api_request("GET", api_path)
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
    api_request("POST", f"/messages/{args.message_id}/reply", {"comment": args.body})
    print(f"[OK] Reply sent for message: {args.message_id}")


def cmd_mail_delete(args):
    api_request("DELETE", f"/messages/{args.message_id}")
    print(f"[OK] Message deleted: {args.message_id}")


def cmd_mail_folders(args):
    result  = api_request("GET", "/mailFolders?$top=50&$select=id,displayName,totalItemCount,unreadItemCount")
    folders = result.get("value", [])
    if not folders:
        print("No mail folders found.")
        return
    print(f"Mail folders ({len(folders)} total):\n")
    for folder in folders:
        name   = folder.get("displayName", "(unnamed)")
        total  = folder.get("totalItemCount", 0)
        unread = folder.get("unreadItemCount", 0)
        print(f"  {name}  ({unread} unread / {total} total)")
        print(f"    id: {folder.get('id', '')}")


# ── Config commands ────────────────────────────────────────────────────────────

def cmd_show_config(args):
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        tz = cfg.get("timezone", "(not set)")
        tid = cfg.get("tenant_id", "consumers (default)")
    else:
        tz = "Asia/Dubai (default — config file not found)"
        tid = "consumers (default)"
    print(f"Timezone   : {tz}")
    print(f"Tenant     : {tid}")
    print(f"Config     : {CONFIG_FILE}")
    print(f"Token cache: {TOKEN_CACHE_PATH}")
    cache = _load_cache()
    if cache:
        username = cache.get("account", {}).get("username", "unknown")
        print(f"Login      : LOGGED_IN ({username})")
    else:
        print("Login      : NOT_LOGGED_IN — run: ms_graph.py login")


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Microsoft 365 (Calendar + OneDrive + Mail) — Device Code Flow")
    sub    = parser.add_subparsers(dest="group")

    # ── Auth ──
    sub.add_parser("login",       help="Interactive login (terminal use)")
    sub.add_parser("device-code", help="Get device code for login (outputs JSON)")
    p_lp = sub.add_parser("login-poll", help="Poll for login completion after browser auth")
    p_lp.add_argument("--device-code", required=True)
    p_lp.add_argument("--interval", type=int, default=10)
    sub.add_parser("logout",      help="Clear token cache")
    sub.add_parser("status",      help="Check login status")
    sub.add_parser("show-config", help="Show timezone and login status")

    # ── Calendar ──
    cal     = sub.add_parser("calendar", help="Calendar operations")
    cal_sub = cal.add_subparsers(dest="command")

    p_c = cal_sub.add_parser("create")
    p_c.add_argument("--subject",   required=True)
    p_c.add_argument("--start",     required=True)
    p_c.add_argument("--end",       required=True)
    p_c.add_argument("--timezone",  default=DEFAULT_TIMEZONE)
    p_c.add_argument("--body")
    p_c.add_argument("--location")
    p_c.add_argument("--attendees", nargs="*")
    p_c.add_argument("--online",    action="store_true")

    p_l = cal_sub.add_parser("list")
    p_l.add_argument("--days", type=int, default=7)
    p_l.add_argument("--top",  type=int, default=50)

    p_g = cal_sub.add_parser("get")
    p_g.add_argument("--event-id", required=True)

    p_u = cal_sub.add_parser("update")
    p_u.add_argument("--event-id",  required=True)
    p_u.add_argument("--subject")
    p_u.add_argument("--start")
    p_u.add_argument("--end")
    p_u.add_argument("--timezone")
    p_u.add_argument("--body")
    p_u.add_argument("--location")
    p_u.add_argument("--attendees", nargs="*")
    p_u.add_argument("--online",    action="store_true")

    p_d = cal_sub.add_parser("delete")
    p_d.add_argument("--event-id", required=True)

    cal_sub.add_parser("calendars")

    p_sl = cal_sub.add_parser("share-list")
    p_sl.add_argument("--calendar-id")

    p_sa = cal_sub.add_parser("share-add")
    p_sa.add_argument("--email",       required=True)
    p_sa.add_argument("--name")
    p_sa.add_argument("--role",        default="read",
                      choices=["freeBusyRead", "limitedRead", "read", "write",
                               "delegateWithoutPrivateEventAccess", "delegateWithPrivateEventAccess"])
    p_sa.add_argument("--calendar-id")

    p_su = cal_sub.add_parser("share-update")
    p_su.add_argument("--permission-id", required=True)
    p_su.add_argument("--role",          required=True,
                      choices=["freeBusyRead", "limitedRead", "read", "write",
                               "delegateWithoutPrivateEventAccess", "delegateWithPrivateEventAccess"])
    p_su.add_argument("--calendar-id")

    p_sr = cal_sub.add_parser("share-remove")
    p_sr.add_argument("--permission-id", required=True)
    p_sr.add_argument("--calendar-id")

    # ── OneDrive ──
    od     = sub.add_parser("onedrive", help="OneDrive file operations")
    od_sub = od.add_subparsers(dest="command")

    p_odl = od_sub.add_parser("list")
    p_odl.add_argument("--path", default="/")
    p_odl.add_argument("--top",  type=int, default=20)

    p_odi = od_sub.add_parser("info")
    p_odi.add_argument("--item-id", required=True)

    p_odd = od_sub.add_parser("download")
    p_odd.add_argument("--item-id", required=True)
    p_odd.add_argument("--output")

    p_odu = od_sub.add_parser("upload")
    p_odu.add_argument("--local-file",   required=True)
    p_odu.add_argument("--remote-path",  required=True)

    p_odm = od_sub.add_parser("mkdir")
    p_odm.add_argument("--name",      required=True)
    p_odm.add_argument("--parent-id")

    p_odx = od_sub.add_parser("delete")
    p_odx.add_argument("--item-id", required=True)

    p_ods = od_sub.add_parser("search")
    p_ods.add_argument("--query", required=True)

    # ── Mail ──
    mail     = sub.add_parser("mail", help="Outlook mail operations")
    mail_sub = mail.add_subparsers(dest="command")

    p_ml = mail_sub.add_parser("list")
    p_ml.add_argument("--top",    type=int, default=10)
    p_ml.add_argument("--folder", default="inbox")

    p_mg = mail_sub.add_parser("get")
    p_mg.add_argument("--message-id", required=True)

    p_ms = mail_sub.add_parser("send")
    p_ms.add_argument("--to",      required=True)
    p_ms.add_argument("--subject", required=True)
    p_ms.add_argument("--body",    required=True)
    p_ms.add_argument("--cc")
    p_ms.add_argument("--bcc")

    p_mr = mail_sub.add_parser("reply")
    p_mr.add_argument("--message-id", required=True)
    p_mr.add_argument("--body",       required=True)

    p_md = mail_sub.add_parser("delete")
    p_md.add_argument("--message-id", required=True)

    mail_sub.add_parser("folders")

    # ── Route ──
    args = parser.parse_args()

    if args.group == "login":
        cmd_login(args)
    elif args.group == "device-code":
        cmd_device_code(args)
    elif args.group == "login-poll":
        cmd_login_poll(args)
    elif args.group == "logout":
        cmd_logout(args)
    elif args.group == "status":
        cmd_status(args)
    elif args.group == "show-config":
        cmd_show_config(args)

    elif args.group == "calendar":
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
            "list":     cmd_od_list,
            "info":     cmd_od_info,
            "download": cmd_od_download,
            "upload":   cmd_od_upload,
            "mkdir":    cmd_od_mkdir,
            "delete":   cmd_od_delete,
            "search":   cmd_od_search,
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

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
