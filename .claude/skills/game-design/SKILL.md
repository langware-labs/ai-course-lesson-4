---
id: 4c2dace2-f011-4b06-b008-e21505dd956d
name: game-design
description: How to make a browser game that is fun, feels good and runs smoothly
  on a phone (portrait, touch) or a computer (keyboard and mouse), as static HTML/CSS/JS
  with no libraries. Covers the game loop, scaling the canvas, controls
  for touch and keyboard, the screens every game needs, "juice" (feedback that makes
  actions feel good), difficulty, saving the high score, and recipes for a first-person
  shooter, a fight simulator, a farm sim, a board game and Tetris. Use together with
  `html-builder` (which owns the files, the look and the share button) whenever the
  thing being built is a game.
allowed-tools:
- Read
- Write
- Edit
- Bash
- Glob
- Grep
---

# Game design

`html-builder` owns the folder, the look and the share button. This skill owns
what makes it a **game**: it must be playable in the first version, fun in the
first ten seconds, and smooth on a cheap phone.

## Build order — playable first

1. **The core action, ugly is fine for five minutes:** the thing the player does
   over and over (move and shoot, drop and rotate, plant and harvest). Get it
   working and feeling right before anything else.
2. **A goal and a fail state:** score, a timer, lives, a win condition.
3. **The screens:** start → playing → paused → game over (see below).
4. **Look and juice:** palette and characters from `frontend-design`, then
   feedback for every action.
5. **Difficulty curve and the high score.**

Each step ends playable. Never show the student a version that doesn't start.

## Files

`games/<name>/index.html`, `style.css`, `game.js` (split into more classic
`<script defer>` files — `input.js`, `levels.js`, loaded in order — once `game.js`
passes ~400 lines; no ES modules, see `html-builder`), `share.js`. No
libraries: Canvas 2D and the DOM cover every game here, and nothing has to be
downloaded.

## The loop

Real-time games run on `requestAnimationFrame` with a **fixed-step update**, so
the game runs at the same speed on a 60 Hz phone and a 144 Hz monitor:

```js
const STEP = 1000 / 60;
let last = performance.now(), acc = 0;
function frame(now) {
  acc += Math.min(now - last, 250); // a hidden tab must not fast-forward the world
  last = now;
  while (acc >= STEP) { update(STEP / 1000); acc -= STEP; }
  render();
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
```

- Speeds are per second (`x += speed * dt`), never per frame.
- **Pause on `visibilitychange`** (tab hidden, phone locked) and show the pause screen.
- Expose `window.advanceTime = (ms) => { …run update() ms/STEP times; render(); }`
  so a test can step the game deterministically, and keep the whole game state in
  one `state` object.
- Turn-based games (board games, a farm with slow ticks) don't need a loop: update
  on each move or on `setInterval`, and redraw.

## Canvas that fits and stays sharp

```js
function fit() {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const { width, height } = canvas.getBoundingClientRect();
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  ctx.setTransform(dpr * width / WORLD_W, 0, 0, dpr * height / WORLD_H, 0, 0);
}
addEventListener('resize', fit);
```

Draw in a fixed **world size** (e.g. 360×640 for a portrait phone game, 960×540 for
a computer game) and let CSS size the canvas to the screen with `aspect-ratio`,
letterboxing the rest. Collision and movement then never depend on the screen.

## Controls

Read input into one `input` object (`input.left`, `input.fire`, `input.aim`) and
let `update()` read only that — the keyboard, touch buttons and a joystick all
write to the same object.

**Phone (portrait):**
- On-screen controls in the bottom third, where thumbs are: at least 64px, with a
  pressed state. A **virtual joystick** for movement (bottom-left), action buttons
  bottom-right. Use Pointer Events (`pointerdown/move/up` with `setPointerCapture`)
  so several fingers work at once.
- Swipe and tap where they fit better (Tetris, a board game, a farm).
- `touch-action: none` on the play area, and call `preventDefault()` in the
  handlers, so the page doesn't scroll or zoom while playing.
- A short vibration on a hit (`navigator.vibrate?.(30)`), optional.

**Computer:**
- Arrows and WASD for movement, Space for the main action, Esc / P for pause, M
  for mute. Show the keys on the start screen.
- `event.code` (physical key), not `event.key`, so a Hebrew keyboard layout works.
- First-person aiming uses Pointer Lock (`canvas.requestPointerLock()` on click).

## The screens every game needs

- **Start:** the game's name big, one line on how to play, the controls, a big
  "Play" button, and the best score so far.
- **Playing:** a HUD with score / lives / level, kept clear of the share pill's
  corner; a pause button on phones.
- **Paused:** resume, restart, mute.
- **Game over / win:** the score, "New record!" when it is one, and a big "Play
  again". This is where the player is proudest — make it look like a reward.

## Juice — make every action feel good

Small feedback is the difference between "it works" and "it's fun":

- Hits: a short flash, a burst of particles (stars, bolts, sparks), a tiny screen
  shake (3–6px for 150ms), a pop sound.
- Score: the number bumps up in size, a floating "+10" rises from where it happened.
- Movement: ease in and out instead of snapping; a little squash on landing.
- Sounds made with the Web Audio API (an oscillator with a quick envelope) need no
  sound files; start the `AudioContext` on the first tap, and offer mute.
- Honour `prefers-reduced-motion`: no shake, fewer particles.

## Difficulty

- The first 20 seconds are easy — the player learns by playing, not by reading.
- Then ramp smoothly: speed or enemy count grows a little every level or every N
  points; a breather after each jump.
- Save the best score in `localStorage` (`<game-name>.best`), and show it on the
  start and game-over screens — "beat my record" is what friends get the link for.

## Performance on a cheap phone

- Reuse objects (pools for bullets and particles) instead of creating new ones every
  frame; cap particles (~200).
- Draw static backgrounds once to an offscreen canvas and copy it each frame.
- No `shadowBlur` in the loop; no DOM reads/writes inside the loop except the HUD,
  and update the HUD only when its value changes.

## Recipes

Content rules always apply: action targets robots, aliens, monsters or objects —
never people — with no blood and no real weapons (see the agent's content rules).

### First-person shooter
- **3D without libraries: a raycaster** (the Wolfenstein technique) on Canvas 2D.
  A grid map (`1` = wall), the player has `x, y, angle`; for each screen column
  cast a ray with DDA, draw a vertical wall slice whose height is
  `screenH / distance` (correct fisheye by multiplying by `cos(rayAngle - angle)`),
  shade by distance and side. Enemies are billboard sprites sorted far-to-near,
  hidden behind walls using a per-column depth buffer.
- Theme: a laser-tag arena against robots, a space station with aliens, a paintball
  maze, a snowball fight against snowmen.
- Computer: WASD to move, mouse (Pointer Lock) to look, click to fire.
  Phone (portrait): the 3D view in the top ~60%, a joystick bottom-left to move,
  drag on the right half to turn, a big fire button bottom-right.
- Aim with a crosshair at the centre; a hit is the sprite under the centre column
  within range. Ammo or a cooldown, health pickups, a wave counter.

### Fight simulator
- Side view, two fighters (robots, mechs, cartoon animals, sumo pushers), each with
  health, a state machine (`idle → walk → attack → hit → block → ko`), and attacks
  with a wind-up, an active window and a recovery — that timing is what makes it
  feel like fighting.
- Hitboxes are rectangles active only during an attack's active frames; a hit
  knocks back, flashes the defender and gives a short "hit-stop" freeze (60–100ms).
- Health bars at the top, a round timer, best of three rounds, a "special" meter
  that fills as you land hits.
- Modes: vs the computer (a simple AI that approaches, attacks in range at random
  intervals, blocks sometimes, gets sharper each round) and two players on the same
  keyboard (WASD+F/G vs arrows+K/L). On a phone: vs computer only, joystick + attack
  / block / special buttons.
- A KO is a robot falling apart into bolts or a fighter pushed out of the ring —
  never a hurt person.

### Farm sim
- A tile grid (CSS grid or canvas); each tile has a state
  (`empty → plowed → seeded → growing → ready`) and a timestamp. Crops grow by
  elapsed time, so growth continues while the game is closed: compute it from
  `Date.now()` on load.
- Loop of play: plant → water → wait → harvest → sell → buy better seeds, animals,
  more land, decorations. Coins and a small shop. Short grow times (20s–2min) so it
  stays lively in class.
- Save the whole farm in `localStorage` on every change, and load it on start — the
  farm is still there tomorrow.
- Phone: tap a tile to act, a tool bar at the bottom. Computer: click, number keys
  for tools.

### Board game
- DOM + CSS grid, not canvas: a board of `<button>` cells is accessible and easy to
  animate. Ideas: Connect Four, checkers, Reversi, snakes and ladders, memory cards,
  tic-tac-toe on a big board.
- Keep the rules as pure functions over a `state` (`legalMoves(state)`,
  `applyMove(state, move)`, `winner(state)`) — that's what makes the computer
  opponent easy.
- Two players on the same device (pass the phone), and vs the computer: easy =
  random legal move, medium = win if you can / block if you must, hard = minimax a
  few moves deep.
- Show whose turn it is clearly, animate pieces moving, highlight legal moves and
  the winning line. Dice are fine; no betting.

### Tetris
- A 10×20 grid, the seven pieces (I, O, T, S, Z, J, L) in their usual colours, a
  "7-bag" randomizer (shuffle all seven, deal them out, repeat) so droughts don't
  happen.
- Rotation with simple wall kicks (try the move, then one cell left, right, up);
  a ghost piece showing where it lands; hard drop; a next-piece preview; hold.
- Gravity speeds up every 10 lines (level); score 100/300/500/800 × level for
  1/2/3/4 lines; a short flash on cleared rows.
- A little "lock delay" (~500ms) after a piece touches down, so the player can
  slide it — this alone makes it feel professional.
- Computer: ← → move, ↑ rotate, ↓ soft drop, Space hard drop, C hold.
  Phone: tap = rotate, swipe left/right = move, swipe down = hard drop, plus
  on-screen buttons for players who prefer them.

## Before showing it

Play it yourself through `window.advanceTime` and a few simulated inputs, then run
`web-tester` at the right screen size. Check: it starts, the controls do what they
say, the score counts, game over shows and "Play again" really restarts, the high
score survives a reload, nothing is covered by the share pill.
