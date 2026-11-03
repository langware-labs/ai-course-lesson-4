"""The only way the agent touches xhostd — so the class token never appears in the chat.

    xhostd.py save-token <conversation-id>   read XHOSTD_TOKEN=... from a Flowpad message, store it
    xhostd.py api METHOD /path [json-body]   call https://api.xhostd.com/path, print the answer
    xhostd.py put-secret <app-id> NAME       set an app secret; the value comes on stdin
    xhostd.py push <folder> <git-url>        git push <folder> to xhostd (token as a header)
    xhostd.py clone <git-url> <folder>       git clone an app's repo into a NEW folder (token as a header)
    xhostd.py new-admin-secret <app-id>      make this app's ADMIN_TOKEN (kept in .secrets/, set on the app)
    xhostd.py delete-scores <url> <game> <name>   remove a test row from the live table
    xhostd.py show-scores <url> [game]       print every row of this app's scores table

The token lives in .secrets/xhostd_token (git-ignored, mode 600). It is never printed.
Stdlib only.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import subprocess
import sys
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.xhostd.com"
# parents: scripts/ hall-of-fame/ skills/ .claude/ <project root>
TOKEN_FILE = Path(__file__).resolve().parents[4] / ".secrets" / "xhostd_token"
ADMIN_FILE = TOKEN_FILE.with_name("hof_admin_token")


def token() -> str:
    if not TOKEN_FILE.is_file():
        sys.exit("no token saved yet - run save-token first")
    return TOKEN_FILE.read_text().strip()


def save_token(conversation: str) -> None:
    text = subprocess.run(["flow", "conversation", "show", conversation],
                          capture_output=True, text=True, check=True).stdout
    found = re.findall(r"XHOSTD_TOKEN=(\S+)", text)
    if not found:
        sys.exit("no message with XHOSTD_TOKEN=... in that conversation")
    TOKEN_FILE.parent.mkdir(exist_ok=True)
    fd = os.open(TOKEN_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(found[-1])
    print(f"token saved ({len(found[-1])} characters, not shown)")


def call(method: str, path: str, body: bytes | None, content_type: str) -> None:
    req = urllib.request.Request(API + path, data=body, method=method)
    req.add_header("Authorization", f"Bearer {token()}")
    if body is not None:
        req.add_header("Content-Type", content_type)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            print(resp.status, resp.read().decode())
    except urllib.error.HTTPError as e:
        print(e.code, e.read().decode())
        sys.exit(1)


def new_admin_secret(app_id: str) -> None:
    value = secrets.token_urlsafe(32)
    ADMIN_FILE.parent.mkdir(exist_ok=True)
    fd = os.open(ADMIN_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(value)
    call("PUT", f"/apps/{app_id}/env/ADMIN_TOKEN?kind=secret", value.encode(), "application/octet-stream")


def delete_scores(url: str, game: str, name: str) -> None:
    if not ADMIN_FILE.is_file():
        sys.exit("no admin secret yet - run new-admin-secret first")
    query = urllib.parse.urlencode({"game": game, "name": name})
    req = urllib.request.Request(f"{url.rstrip('/')}/api/scores?{query}", method="DELETE")
    req.add_header("Authorization", f"Bearer {ADMIN_FILE.read_text().strip()}")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            print(resp.status, resp.read().decode())
    except urllib.error.HTTPError as e:
        print(e.code, e.read().decode())
        sys.exit(1)


def show_scores(url: str, game: str = "") -> None:
    if not ADMIN_FILE.is_file():
        sys.exit("no admin secret yet - run new-admin-secret first")
    query = urllib.parse.urlencode({"game": game}) if game else ""
    req = urllib.request.Request(f"{url.rstrip('/')}/api/scores/all" + (f"?{query}" if query else ""))
    req.add_header("Authorization", f"Bearer {ADMIN_FILE.read_text().strip()}")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            rows = json.loads(resp.read())["rows"]
    except urllib.error.HTTPError as e:
        print(e.code, e.read().decode())
        sys.exit(1)
    print(f"{len(rows)} rows" + (f" for {game}" if game else ""))
    for r in rows:
        print(f'{r["created_at"][:19]}  {r["game"]:<20} {r["name"]:<20} {r["score"]}')


def main() -> None:
    args = sys.argv[1:]
    if args[:1] == ["save-token"] and len(args) == 2:
        save_token(args[1])
    elif args[:1] == ["api"] and len(args) in (3, 4):
        body = args[3].encode() if len(args) == 4 else None
        call(args[1].upper(), args[2], body, "application/json")
    elif args[:1] == ["put-secret"] and len(args) == 3:
        call("PUT", f"/apps/{args[1]}/env/{args[2]}?kind=secret", sys.stdin.buffer.read(),
             "application/octet-stream")
    elif args[:1] == ["clone"] and len(args) == 3:
        env = {**os.environ, "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "http.extraHeader",
               "GIT_CONFIG_VALUE_0": f"Authorization: Bearer {token()}"}
        subprocess.run(["git", "clone", args[1], args[2]], env=env, check=True)
    elif args[:1] == ["push"] and len(args) == 3:
        env = {**os.environ, "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "http.extraHeader",
               "GIT_CONFIG_VALUE_0": f"Authorization: Bearer {token()}"}
        subprocess.run(["git", "-C", args[1], "push", args[2], "HEAD:master"], env=env, check=True)
    elif args[:1] == ["new-admin-secret"] and len(args) == 2:
        new_admin_secret(args[1])
    elif args[:1] == ["delete-scores"] and len(args) == 4:
        delete_scores(*args[1:])
    elif args[:1] == ["show-scores"] and len(args) in (2, 3):
        show_scores(*args[1:])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
