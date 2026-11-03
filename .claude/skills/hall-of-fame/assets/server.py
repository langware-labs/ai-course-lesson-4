"""A game's server: serves the game from ./public and keeps its Hall of Fame in Postgres.

    GET  /api/scores?game=<name>   -> {"ok": true, "scores": [{"name", "score"}, ...]}  top 10
    POST /api/scores {"game", "name", "score"} -> {"ok": true}
    GET    /api/scores/all[?game=<name>]  -> {"ok": true, "rows": [...]}  every row, newest first
    DELETE /api/scores?game=<name>&name=<player>  -> {"ok": true, "deleted": n}
        both need `Authorization: Bearer $ADMIN_TOKEN` — the builder's way to look at the whole
        table and to remove a test row
"""

import hmac
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from psycopg_pool import ConnectionPool

PUBLIC = Path(__file__).parent / "public"
GAME_RE = re.compile(r"^[a-z0-9-]{1,40}$")
TYPES = {".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript",
         ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png",
         ".jpg": "image/jpeg", ".mp3": "audio/mpeg", ".wav": "audio/wav", ".ogg": "audio/ogg"}

pool = ConnectionPool(os.environ.get("DATABASE_URL_DIRECT") or os.environ["DATABASE_URL"],
                      min_size=1, max_size=3, kwargs={"prepare_threshold": None}, open=True)
with pool.connection() as conn:
    conn.execute("""CREATE TABLE IF NOT EXISTS scores (
        id serial PRIMARY KEY, game text NOT NULL, name text NOT NULL,
        score integer NOT NULL, created_at timestamptz NOT NULL DEFAULT now())""")


class Handler(BaseHTTPRequestHandler):
    def send(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        # the game page may be opened from another address (e.g. inside Flowpad)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status, payload):
        self.send(status, json.dumps(payload).encode(), "application/json")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def is_admin(self):
        admin = os.environ.get("ADMIN_TOKEN", "")
        sent = self.headers.get("Authorization", "").removeprefix("Bearer ")
        return bool(admin) and hmac.compare_digest(sent, admin)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/api/scores/all":
            if not self.is_admin():
                return self.send_json(403, {"ok": False, "error": "not allowed"})
            game = parse_qs(url.query).get("game", [""])[0]
            if game and not GAME_RE.match(game):
                return self.send_json(400, {"ok": False, "error": "bad game name"})
            with pool.connection() as conn:
                found = conn.execute("SELECT game, name, score, created_at FROM scores "
                                     "WHERE (%s = '' OR game = %s) ORDER BY created_at DESC LIMIT 500",
                                     (game, game)).fetchall()
            rows = [{"game": g, "name": n, "score": s, "created_at": c.isoformat()} for g, n, s, c in found]
            return self.send_json(200, {"ok": True, "rows": rows})
        if url.path == "/api/scores":
            game = parse_qs(url.query).get("game", [""])[0]
            if not GAME_RE.match(game):
                return self.send_json(400, {"ok": False, "error": "bad game name"})
            with pool.connection() as conn:
                rows = conn.execute("SELECT name, score FROM scores WHERE game = %s "
                                    "ORDER BY score DESC, created_at LIMIT 10", (game,)).fetchall()
            return self.send_json(200, {"ok": True, "scores": [{"name": n, "score": s} for n, s in rows]})
        rel = unquote(url.path).lstrip("/") or "index.html"
        target = (PUBLIC / rel / "index.html") if (PUBLIC / rel).is_dir() else (PUBLIC / rel)
        target = target.resolve()
        if PUBLIC.resolve() not in target.parents or not target.is_file():
            return self.send(404, b"not found", "text/plain")
        self.send(200, target.read_bytes(), TYPES.get(target.suffix, "application/octet-stream"))

    def do_DELETE(self):
        url = urlparse(self.path)
        if url.path != "/api/scores" or not self.is_admin():
            return self.send_json(403, {"ok": False, "error": "not allowed"})
        query = parse_qs(url.query)
        game, name = query.get("game", [""])[0], query.get("name", [""])[0]
        if not GAME_RE.match(game) or not name:
            return self.send_json(400, {"ok": False, "error": "send game and name"})
        with pool.connection() as conn:
            deleted = conn.execute("DELETE FROM scores WHERE game = %s AND name = %s", (game, name)).rowcount
        self.send_json(200, {"ok": True, "deleted": deleted})

    def do_POST(self):
        if urlparse(self.path).path != "/api/scores":
            return self.send_json(404, {"ok": False, "error": "not found"})
        try:
            data = json.loads(self.rfile.read(min(int(self.headers.get("Content-Length", 0)), 2000)))
            game, name, score = data["game"], str(data["name"]).strip()[:20], int(data["score"])
        except (ValueError, KeyError, TypeError):
            return self.send_json(400, {"ok": False, "error": "send game, name and score"})
        if not GAME_RE.match(str(game)) or not name or not 0 <= score <= 10**9:
            return self.send_json(400, {"ok": False, "error": "bad game, name or score"})
        with pool.connection() as conn:
            conn.execute("INSERT INTO scores (game, name, score) VALUES (%s, %s, %s)", (game, name, score))
        self.send_json(200, {"ok": True})


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("XHOSTD_HTTP_PORT") or os.environ.get("PORT") or 8080)), Handler).serve_forever()
