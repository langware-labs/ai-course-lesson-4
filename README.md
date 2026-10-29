# ai-course-lesson-4 — a game with a Hall of Fame

Lesson 4 of the AI course. Open it in Flowpad with **Open from git** and you get
**Game Builder**, a vibe agent that builds a game with you — for a phone (portrait,
touch) or a computer (keyboard and mouse) — as plain HTML/CSS/JS that opens on any
device, with a Hall of Fame: the best scores of everyone who played, kept in a
database behind a server. Every game has a "copy link" button in a
corner: paste the link in WhatsApp and send it to friends and family.

Pick a starter on the screen — first-person shooter, fight simulator, farm sim,
board game, Tetris — or invent your own.

- `agentic-assets/agent/game-builder/` — the agent (its rules, language, starters)
- `.claude/skills/html-builder/` — builds static pages, with the share button (`assets/share.js`)
- `.claude/skills/game-design/` — how to make the game fun, smooth and playable on a phone
- `games/<name>/` — where the games you build are saved
