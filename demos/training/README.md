# Training sessions

Dual-mode HTML session pages for live AI training. Same house style as the demos one
directory up: self-contained single files, no build step, system fonts, real captured
evidence only.

**Hub:** `index.html` — the one link participants bookmark
(`https://augmentgrowth.github.io/skill-factory/demos/training/`). Every new session
gets a card there.

## Dual mode

Each session page renders two ways from the same content:

- **Guide mode** (default) — a scrolling walkthrough with copy-paste prompt blocks.
  This is the leave-behind: drop the link in Slack after the session.
- **Present mode** (`▶ present` button, or `?mode=present`) — one step card per
  full-viewport slide for remote screen share. Arrow keys / space / PageUp/PageDown
  navigate; Esc returns to guide mode; a step counter sits bottom-right.

If anything fails live (keyboard, clipboard), guide mode scrolls and text selects with
zero JavaScript — present and copy are enhancements, not dependencies.

## Authoring a new session

1. Copy `session-template.html` to `YYYY-MM-DD-<topic>.html` in this directory.
   The template's HTML comments mark every fill-in slot.
2. 4–8 step cards for a 30-minute session. Minute labels on the cards must sum to the
   session length; mark participant work time with the "You do — N min" badge.
3. Every prompt is real, copy-pasteable text in a `pre.prompt` block — never a
   description of a prompt. Include the read-only boundary and a stop rule whenever a
   step touches real data.
4. Each step gets an "expected result" panel and 1–3 facilitator notes (talking point,
   trip-up, transition cue) in the collapsed `details.fac` block — the page should be
   verbally presentable from the notes alone.
5. Evidence panels (`.compare`) show real captured runs only, with a provenance line in
   the footer pointing at the artifacts. Baselines are captured before the skill exists.
6. Add a card to `index.html`.

The canonical lesson content lives as markdown in the vault
(`02_Areas/AI_TRAINING_PROGRAM/`, per that area's markdown-canonical rule); these pages
are delivery artifacts and should link back to nothing that requires vault access.

## House rules

- No external fonts, CDNs, or trackers. One inline `<style>`, one `<script>`.
- No emojis in body copy (UI glyphs on buttons are fine).
- No client-confidential content — these pages are public. Scrubbed samples only.
- Keep the design tokens in sync with `demos/*.html` if the palette ever changes.
