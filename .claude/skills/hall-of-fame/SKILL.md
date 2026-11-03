---
id: 7b1c0e52-3d4a-4f6e-9a28-5e0d1c9b7a43
name: hall-of-fame
description: 'Gives a student''s game a Hall of Fame — a table of the best scores of
  everyone who plays it from the shared link — by setting up the student''s own server
  and database on xhostd, then wiring the game to them (ask for the player''s name at
  game over, send the score, show the top 10). Use when the student wants a score
  table, a leaderboard, a Hall of Fame or "to compete with friends", or asks what a
  server or a database is. NOT for real-time multiplayer.'
allowed-tools:
- Read
- Write
- Edit
- Bash
- Glob
- Grep
---

# Hall of Fame

The student's game gets **its own server and its own database** on xhostd. One link
shows the game and keeps its table. Teach it as you build it: the game (a page in the
browser) *sends* a score to the server, the server *stores* it in the database, and
every player's browser *asks* for the top 10. Say each of the three in one plain
sentence at the moment you build it.

## The order

1. **Wire the game** to the table (see "Wire the game") and test it locally with
   `web-tester`, including the case where the server is unreachable.
2. **Upload the code to the repo** when the student is done (see "Upload the code") —
   **without running it yet.**
3. **Run it** (see "Run it"): deploy, then test the live link — play a round, check the
   score shows in the table, ask the student to open the link on another device.

## The class token

The teacher posts `XHOSTD_TOKEN=...` as a message in a Flowpad conversation. Everyone
in the class uses the same one.

- **Never print, quote or echo the token** — not in the chat, not in a file you show,
  not in a command line, not in a commit. Only `scripts/xhostd.py` touches it; it
  stores it in `.secrets/xhostd_token`, which git ignores.
- First time only: `flow conversation list`, find the conversation with the teacher,
  then `uv run --no-project python <this-skill>/scripts/xhostd.py save-token <conversation-id>`.
  It prints only "token saved". If it says there is no such message, ask the student
  to tell the teacher.
- Never run `GET` on an app's `env` — it can show secrets.

## Upload the code (step 7 — save it, do not run it yet)

The student's code is saved in a **repo** (git) on xhostd, with its **history of versions**.
You do it for them: **do not send the student to the "Link to cloud" button or to the
project page** for this, as an earlier version of this lesson did.

**When to do it:** when you think the student has finished and has an app ready to upload,
ask: "Is your game ready, or is there anything else you want to change before I upload it?"
If they want more changes, make them. If not, upload.

All calls go through `scripts/xhostd.py`. Read each answer for the ids you need; do not guess
them. Keep the ids and the app's public address in `.secrets/hof_app.json` (git-ignored), so
a later update finds them.

1. **First time only — create the app.** Name: `hof-<student's first name in English letters,
   lowercase>` (e.g. `hof-dana`; add a digit if xhostd says the name is taken). Then
   `xhostd.py api POST /apps '{"name":"<name>","template":"app","branch":"master"}'`, and keep
   the app id, the channel id and the git url from the answer. Then
   `xhostd.py new-admin-secret <app-id>` once (it stays in `.secrets/`, never printed).
2. **Keep the code in the project, upload from a copy.** The student's source stays in the
   project: the game in `games/<game>/`, the server in `server/` (copy this skill's
   `assets/server.py`, `install.sh`, `launch.sh` there). Rebuild the git-ignored staging
   folder `.deploy/<name>/` each time: `server/*` at its top, the game's files in `public/`,
   then `git init` (first time). Never edit the staging copy.
3. **Commit and push — do not deploy.** Commit with a short message that says what this
   version is ("First version", "Added sound", …), then
   `xhostd.py push .deploy/<name> <git url>`.
4. **Tell the student**, in their language and in plain words: their code is now saved in a
   **repo in the cloud, with a history of versions**, so it is kept safe. You may call it a
   **repo** — that word is worth knowing — but never mention GitHub or Langware, and don't
   promise a link to the files: the student has none. They can open the code on another
   computer later (see "Open the code on another computer"); that needs the class token.
5. Before pushing, make sure no secret is inside a project file (the class token and the
   passwords must not be): check with `grep -r` for the token's first 6 characters *without
   printing the match*, and fix the file if it is there.

**Later changes:** when the student changes the game after the first upload, rebuild the
staging copy, commit with a message for the new version, push, and say: "I created a new
version of your code in the cloud (the repo) — you now have a history of versions." Then run
it again if the game is already running (see "Run it").

## Open the code on another computer

If the student asks to get their game's code on another computer, or the project is gone:
this works from the repo, and it needs the **class token** (the teacher posts it as
`XHOSTD_TOKEN=...` in a Flowpad conversation; save it with `xhostd.py save-token`, never print it).

1. Find the app by its name `hof-<first name>`: `xhostd.py api GET /apps`, then
   `xhostd.py api GET /apps/<app-id>` for its git url. Only the student's own app: never open
   another student's.
2. `xhostd.py clone <git url> .deploy/<name>` — the whole history of versions comes with it.
3. Copy the pieces back to where the project keeps them: `public/*` into `games/<game>/`, and
   `server.py`, `install.sh`, `launch.sh` into `server/`.
4. The app's admin secret did not travel (it lives on the first computer): if the student wants
   to see their scores or clean test rows, run `xhostd.py new-admin-secret <app-id>` again and
   run it (deploy) once so the app picks it up.

The running game itself needs none of this: it is already published, so its link opens on any
computer.

## Run it (step 8)

Only after the code is uploaded (or updated):

1. `xhostd.py api POST /apps/<app-id>/channels/<channel-id>/deploy '{"ref":"master"}'`. Wait
   until the deploy is done (read the answer; check `GET` on the channel again).
2. **The link:** the public address of the app, from the answers. Give it to the student.
   The Share button needs nothing written down: a page served from its own public address
   shares that address (`share.js`), so there is no second upload.
3. Test the live link, as in "The order".

The student must understand why this is a *different* kind of publishing from the
`html-builder` publish script: that one only stores files; this one runs a program.

## Wire the game

In `game.js`, using relative URLs (`/api/scores`, so the same code works anywhere):

```js
async function sendScore(name, score) {
  try {
    await fetch('/api/scores', {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({game: GAME, name, score})});
  } catch { /* offline: the game still works */ }
}
async function topScores() {
  try { return (await (await fetch('/api/scores?game=' + GAME)).json()).scores; }
  catch { return null; }   // null = "the table can't be reached"
}
```

`GAME` is the game's folder name (lowercase letters, digits, dashes). At game over:
ask the player's name (remember it in `localStorage`), call `sendScore`, then show
`topScores()` as a table with the player's own row highlighted; if it returns `null`,
say the table is unavailable and keep the game playable. Test with `web-tester`, then
open the page, play a round, and check that the score shows in the table.

## Showing the student their database

When the student asks to see their database, their scores, or "what the server saved":
run `xhostd.py show-scores <app-address> [game]` and show the rows as a small table
(time, game, name, score). Explain in two sentences: this is the `scores` table in
*their* Postgres database; the server adds a row each time a game sends a score, and
the Hall of Fame is the ten highest rows. Read-only: never change or delete the
student's rows without being asked. This uses the app's own admin secret, so it can only
see this student's app — never use the class token to read a database or another
student's app.

## Test rows — clean up after yourself

When you test the table, use a clearly fake player name, `__test__`. The moment the
test is done (pass or fail), delete it from the live table:
`xhostd.py delete-scores <app-address> <game> __test__`, then read the table again
and make sure no `__test__` row is left. A test row must never stay in the student's Hall
of Fame. If the delete fails, tell the student plainly and tell the teacher.

## Rules

- The student's name and score are the only data. No passwords, accounts or emails.
- Anyone with the link can send a fake score. Say so once, honestly — it is a good
  question for the student to think about — and don't try to prevent it here.
- Do not touch another student's app. Only create and change the one named after this student.
