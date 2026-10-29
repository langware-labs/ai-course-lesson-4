---
id: 8d3fa8e2-45b2-4f15-ad15-133afbb79bd5
name: html-builder
description: 'Builds a static web page or browser app — HTML, CSS and JavaScript files
  a browser opens directly, with no build step or install — that
  looks designed and carries a share button in a corner (WhatsApp, email, copy link,
  download), and publishes it to a free public link with no sign-up. Use for any page made from plain files: a game, a quiz,
  a poster, a small site, a tool, an interactive toy. Covers the folder layout, modern
  CSS and JavaScript without a framework, phone (portrait) versus computer layouts,
  the share button and publishing, saving with localStorage or a server and database, the accessibility floor and how to verify
  the result. Aesthetic direction comes from `frontend-design`, which this skill loads
  first. NOT for anything that needs accounts or a build step.'
allowed-tools:
- Read
- Write
- Edit
- Bash
- Glob
- Grep
---

# HTML Builder

Static does not mean plain. A page with no build step can look as considered as
one built with a toolchain: the browser already ships what used to need Sass, a
bundler and a component library. This skill is the craft — how to build it. The
taste — palette, type, the one signature element — belongs to `frontend-design`.

## First: load `frontend-design`

Before writing any markup, load the `frontend-design` skill and settle the look:
palette, typefaces, layout concept and one signature element. Building first and
styling after produces a page whose structure fights its design.

## The contract

What you write is what ships — the folder IS the page.

- **No sign-in, no build.** Plain files any browser opens, so the page works for
  anyone who gets the link. Data that belongs to one player and must survive a
  reload (their own best score, a saved list) goes in `localStorage`, under one key
  named after the page, read with a safe default when it is missing or broken.
- **A server and a database are allowed** for data that everyone who opens the link
  shares — a Hall of Fame of the best scores. The page talks to the server over
  `fetch`, and keeps working when the server can't be reached: it says the table is
  unavailable and the game stays playable. A secret (a database password, a key)
  lives on the server only, never in a page file.
- **One folder per page:** `index.html`, `style.css`, `script.js` (a game may name
  it `game.js`), `share.js`, and images or sounds as their own files. Every path
  relative, so the folder works wherever it is copied or served from.
- **No CDN links.** Anything you would download goes into the folder, so the page
  still works on a weak connection. Prefer drawing with CSS, SVG or `<canvas>`, and
  emoji, over image files you don't have; never hot-link someone else's image.
- **Fonts:** the system font stack, or a font file vendored into the folder.

## Every page gets the share button

The page is made to be shared, so every page carries a small **Share** pill in a
corner. It opens a menu: **send on WhatsApp**, **send by email**, **copy link**
and **download** (one self-contained `.html` file that opens with nothing beside it).

1. Copy `assets/share.js` from this skill's folder into the page's folder, as is.
2. Add one line to the end of `<head>`:
   ```html
   <script src="share.js" defer></script>
   ```
3. Pick the corner with `data-corner` — `top-left` (default), `bottom-left`,
   `bottom-right`. **Not `top-right`:** Flowpad floats its own Share pill there.
   Choose the corner that covers nothing important: if the page has a score in the
   top-left or controls along the bottom, move the pill to a free corner.
4. The text follows `<html lang>` (Hebrew, Arabic, English).

The link it shares is the page's **published** address, read from
`share-link.json` beside the page. Until the page is published, the menu says so and
offers only the download. Don't restyle or rewrite the button per page — if it needs
to change, it changes in `assets/share.js`.

## Publishing — a public link with no sign-up

Run the publish script from this skill's folder on the page's folder:

```bash
uv run --no-project python <this-skill>/scripts/publish.py <page-folder>
```

(`python3` works too where it is a real Python; on Windows prefer `uv run`.) It
prints one JSON line: `{"ok": true, "url": "..."}` or `{"ok": false, "error": "..."}`.

- The page goes to the **Flowpad Pages** server and is served at
  `https://<server>/<page-name>-<tag>/`. No account, password or email — nothing for
  the user to do, and no hosting credential on this computer.
- The first publish of a page claims it for this computer (a secret kept in
  `~/.config/flowpad-pages/`). Publishing it again replaces it and **keeps the same
  link**; nobody else can change it.
- It writes `share-link.json` into the page folder, so the Share menu — locally and
  online — knows the address.
- Publishing puts the page on the public internet. Publish only when the user asks
  or agrees, and never publish personal details (real names, phone numbers,
  addresses, photos of people).
- After changing a page that was already published, publish it again so the shared
  link shows the new version.
- `{"ok": false}` — tell the user in one plain sentence that publishing didn't work
  this time, offer the **download** from the Share menu instead, and don't retry in
  a loop.

## The starting skeleton

```html
<!doctype html>
<html lang="he" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="theme-color" content="#1b1b2f">
  <title>The page's real name</title>
  <!-- What WhatsApp shows in the link preview -->
  <meta property="og:title" content="The page's real name">
  <meta property="og:description" content="One inviting sentence">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎮</text></svg>">
  <link rel="stylesheet" href="style.css">
  <script src="share.js" defer></script>
  <script src="script.js" defer></script>
</head>
<body>
  <main>…</main>
</body>
</html>
```

`lang` and `dir` follow the language of the page's text: `he`/`ar` with
`dir="rtl"`, English with `dir="ltr"`.

## Phone or computer

Ask (or know) which one the page is for, and build for it — a page that is "kind
of both" is good at neither.

- **Phone — portrait.** Design for a 390×844 screen first. Use `100dvh` (not
  `100vh`) for full-height layouts, respect `env(safe-area-inset-*)` for the notch,
  tap targets at least 48px, no hover-only behaviour, no horizontal scroll. For
  something played or used full-screen, stop accidental zoom and scrolling:
  `touch-action: none` on the play area, `user-select: none`,
  `-webkit-tap-highlight-color: transparent`. If someone opens it on a computer,
  show the portrait layout centred in a phone-shaped column, not stretched.
- **Computer — landscape.** Design for 1366×768 up to 1920×1080; keyboard and mouse
  are available, so show the keys on screen. Still don't break at a narrower
  window.

## Structure: semantic elements first

Style the element, not a class, wherever an element exists for the job:
`<main>`, `<header>`, `<nav>`, `<section>`, `<button>`, `<label>`, `<dialog>`,
`<details>`, `<ul>`, `<table>`. Classes are for variants. A `<div>` with a click
handler is a button you now have to make accessible yourself — use `<button>`.

## CSS without a preprocessor

All Baseline — none of it needs a build step:

- **Custom properties** on `:root` for every colour, radius and spacing from the
  design plan; never repeat a hex value.
- **`@layer reset, tokens, base, components;`** to keep one owner per property.
- **Nesting**, **`clamp()`** for fluid type and spacing, **container queries**,
  **`:has()`**, **`color-mix()`** for tints, **logical properties**
  (`padding-inline`, `inset-inline-start`) so the same CSS works in RTL and LTR,
  `text-wrap: balance` on headings.
- Motion with `transition` / `@keyframes` on `transform` and `opacity` only (they
  are cheap), all inside `@media (prefers-reduced-motion: no-preference)`.

## JavaScript without a framework

- Classic scripts: `<script src="…" defer>`, one or more files loaded in order,
  sharing what they need through plain globals. **No `type="module"` and no
  `import`** — the Share menu's download inlines every script into one file, and a
  module that imports a sibling file breaks there. No framework, no bundler.
- Prefer the platform: `<dialog>` for modals, `popover` for menus, `<details>`
  for disclosure, form inputs for validation, `localStorage` for saving.
- Sound only after the first tap or key press (browsers block it before that), and
  always with a mute button.
- Keep state in one object and draw the page from it; don't scatter state across
  the DOM.

## The quality floor

Build to it as you go:

- Visible keyboard focus (`:focus-visible`), never a removed outline.
- Real labels on controls — a placeholder is not a label.
- Readable contrast, text at least 16px on a phone.
- Fits its screen with no horizontal scroll.
- Every text the user sees is in the page's language.

## Verify — do not assert

You cannot tell whether a page looks right by reading its source. Run the
`web-tester` skill on it — at a portrait phone size for a phone page, a laptop size
for a computer page — and fix every console error, crash and failed request it
finds. Look at the screenshot: does it look designed, does it fit, is the share
pill in a free corner? Then open the Share menu once and confirm it opens.
