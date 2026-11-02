"""The only way the agent touches xhostd — so the class token never appears in the chat.

    xhostd.py save-token <conversation-id>   read XHOSTD_TOKEN=... from a Flowpad message, store it
    xhostd.py api METHOD /path [json-body]   call https://api.xhostd.com/path, print the answer
    xhostd.py put-secret <app-id> NAME       set an app secret; the value comes on stdin
    xhostd.py push <folder> <git-url>        git push <folder> to xhostd (token as a header)

The token lives in .secrets/xhostd_token (git-ignored, mode 600). It is never printed.
Stdlib only.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.xhostd.com"
TOKEN_FILE = Path(__file__).resolve().parents[3] / ".secrets" / "xhostd_token"


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
    elif args[:1] == ["push"] and len(args) == 3:
        env = {**os.environ, "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "http.extraHeader",
               "GIT_CONFIG_VALUE_0": f"Authorization: Bearer {token()}"}
        subprocess.run(["git", "-C", args[1], "push", args[2], "HEAD:master"], env=env, check=True)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
