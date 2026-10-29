"""Publish a static page folder to a public HTTPS link — no sign-up, no password.

    python publish.py <page-folder>

The page goes to the Flowpad Pages server, which keeps it and serves it at

    https://<server>/<page-name>-<tag>/

The tag comes from an owner secret this script keeps on the computer
(~/.config/flowpad-pages/owner, override the folder with PAGES_STATE_DIR): the first
publish of a page claims it, a later publish from the same computer replaces it and
keeps its link, and nobody else can change it. No hosting credential is involved.

Before uploading it writes ``share-link.json`` ({"url": ...}) into the page folder,
which the page's Share menu reads.

Prints ONE JSON line: {"ok": true, "url": ...} or {"ok": false, "error": ...}.
Stdlib only.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import secrets
import sys
import urllib.error
import urllib.request
from pathlib import Path

SERVER = os.environ.get("PAGES_SERVER", "https://games-gadi.xhostd.app").rstrip("/")
SKIP_DIRS = {".git", "node_modules", "__pycache__"}
SKIP_FILES = {".DS_Store", "Thumbs.db"}


def owner_secret() -> str:
    folder = Path(os.environ.get("PAGES_STATE_DIR") or Path.home() / ".config" / "flowpad-pages")
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "owner"
    if not path.exists():
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            os.write(fd, secrets.token_urlsafe(32).encode())
        finally:
            os.close(fd)
    return path.read_text().strip()


def page_name(folder: Path) -> str:
    """The server's rule, mirrored, so the link is known before the upload."""
    return re.sub(r"[^a-z0-9-]+", "-", folder.name.lower()).strip("-")[:40] or "page"


def collect(page: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in sorted(page.rglob("*")):
        rel = path.relative_to(page)
        if path.is_dir() or path.name in SKIP_FILES or any(part in SKIP_DIRS for part in rel.parts):
            continue
        files[rel.as_posix()] = base64.b64encode(path.read_bytes()).decode()
    return files


def main() -> int:
    if len(sys.argv) != 2:
        print(json.dumps({"ok": False, "error": "usage: publish.py <page-folder>"}))
        return 2
    page = Path(sys.argv[1]).resolve()
    if not (page / "index.html").is_file():
        print(json.dumps({"ok": False, "error": f"{page} has no index.html"}))
        return 2
    owner = owner_secret()
    slug = f"{page_name(page)}-{hashlib.sha256(owner.encode()).hexdigest()[:6]}"
    url = f"{SERVER}/{slug}/"
    (page / "share-link.json").write_text(json.dumps({"url": url}), encoding="utf-8")

    body = json.dumps({"owner": owner, "name": page.name, "files": collect(page)}).encode()
    req = urllib.request.Request(f"{SERVER}/api/publish", data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            answer = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            answer = json.loads(e.read())
        except ValueError:
            answer = {"ok": False, "error": f"the server answered {e.code}"}
    except (urllib.error.URLError, TimeoutError) as e:
        answer = {"ok": False, "error": f"could not reach the server: {e}"}
    if answer.get("ok") and answer.get("url") != url:
        (page / "share-link.json").write_text(json.dumps({"url": answer["url"]}), encoding="utf-8")
    print(json.dumps({k: answer[k] for k in ("ok", "url", "error") if k in answer}))
    return 0 if answer.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
