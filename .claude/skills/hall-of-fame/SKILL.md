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
2. **Save the working version** in the cloud repo (see "Upload the code").
3. **Set up the server and database and deploy** (see "Set it up").
4. **Test the live link** — play a round, check the score shows in the table, ask the
   student to open the link on another device.

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

## Set it up (once per student)

All calls go through `scripts/xhostd.py`. Read each answer for the ids you need; do
not guess them.

1. **Name:** `hof-<student's first name in English letters, lowercase>` (e.g.
   `hof-dana`). If xhostd says the name is taken, add a digit.
2. **Create the app:** `xhostd.py api POST /apps '{"name":"<name>","template":"app","branch":"master"}'`.
   Keep the app id and the channel id from the answer.
3. **Keep the code in the project, deploy from a copy.** The student's source stays in
   the project: the game in `games/<game>/`, the server in `server/` (copy this skill's
   `assets/server.py`, `install.sh`, `launch.sh` there). To deploy, rebuild the git-ignored
   staging folder `.deploy/<name>/` each time: `server/*` at its top, the game's files
   in `public/`, then `git init` (first time). Never edit the staging copy.
4. **Push and deploy:** commit, then `xhostd.py push .deploy/<name> <git url from the answer in step 2>`,
   then `xhostd.py api POST /apps/<app-id>/channels/<channel-id>/deploy '{"ref":"master"}'`.
   Wait until the deploy is done (read the answer; check `GET` on the channel again).
5. **The link:** the public address of the app, from the answers. Give it to the student.
   The Share button needs nothing written down: a page served from its own public
   address shares that address (`share.js`), so there is no second upload.

The student must understand why this is a *different* kind of publishing from the
`html-builder` publish script: that one only stores files; this one runs a program.

## Upload the code to the project's cloud repository

The student's code also goes to the project's cloud storage. For the student this is
a Flowpad feature, nothing more: **Flowpad keeps a saved copy of their project online,
with its history of changes** (the idea of git), so it is not lost if the computer
breaks and can be opened on another machine or shared with friends. Explain exactly
that, in plain words. You may call it a **repo** — that word is worth knowing — but **never mention GitHub or Langware, and don't promise a link to the
files**: the student has none. In Flowpad this is the
**Link to cloud** button on the project's home page; it uploads every file in the
project (it respects `.gitignore`, so `.secrets/` and `.deploy/` stay out).

- Once the game and server work, tell the student in one sentence what it does ("Flowpad
  will keep a saved copy of your project online, with its history"), then walk them to the
  button, in the student's language, step by step:
  1. In the thin bar at the bottom of the screen, under the chat, the project's name
     appears: **ai-course-lesson-4**. Click it. That opens the project's page.
     (Never say "footer" — the student doesn't know the word.)
  2. On that page, click the **"קשרו לענן"** button (**Link to cloud** in English). If a
     sign-in window opens, they sign in to their Flowpad account and the button
     continues by itself.
  3. Click **Back** to return to this chat, and tell me it's done.
  Wait for them to say it's done. You cannot press the button for them.
- The button uploads the files the first time. After later changes, ask the student
  to press it again or share the project; if it does nothing, say the code was not
  re-uploaded and tell the teacher.
- Before asking, make sure no secret is inside a project file (the token and database
  passwords must not be): check with `grep -r` for the token's first 6 characters
  *without printing the match*, and fix the file if it is there.

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

## Rules

- The student's name and score are the only data. No passwords, accounts or emails.
- Anyone with the link can send a fake score. Say so once, honestly — it is a good
  question for the student to think about — and don't try to prevent it here.
- Do not touch another student's app. Only create and change the one named after this student.
