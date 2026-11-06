# Odd One Out — GameMonetize staged build (NOT submitted)

**Status: STAGED ONLY. No dashboard entry, no upload, no submission.**
Original game untouched (`../index.html` md5 `14897666eb2abc812f0b96b8f6f45f73`).

## Files in this folder

| File | What it is |
|---|---|
| `index.html` (32,763 B) | Staged GM build — single file, game + GM SDK + bridge |
| `odd-one-out-gamemonetize-STAGED.zip` (10,525 B) | ZIP of `index.html` only (1 entry, testzip clean) — **do NOT upload as final** |
| `odd-one-out-512x384.jpg` | 512×384 |
| `odd-one-out-512x512.jpg` | 512×512 |
| `odd-one-out-512x340.jpg` | 512×340 (centre crop of the cover, full height kept, title band intact — visually inspected) |

All 3 thumbnails are JPG, derived from the game's own test shots. Sizes PIL-verified.

## What was integrated

- **GameMonetize SDK**, following `~/workspace/gamemonetize/CONVERSION-PLAN.md` + `templates/babylon/`:
  - `window.SDK_OPTIONS = { gameId, onEvent }` before the official async injector IIFE (`https://api.gamemonetize.com/sdk.js`, script id `gamemonetize-sdk`), which precedes the game script. Events fired before the bridge runs are queued in `window.__gmEventQueue` and drained on init.
  - **Async-loader difference (vs GD) handled:** `sdk` may not exist when the bridge runs, so availability is a **live getter re-checked on every ad call**, never snapshotted; `SDK_READY` is explicitly acknowledged.
  - **No-promise difference (vs GD) handled:** `sdk.showBanner()` has no documented return value — the in-flight flag clears on `SDK_GAME_START` plus a 60 s safety valve. No code awaits `showBanner()`.
  - Pause/resume on `SDK_GAME_PAUSE` / `SDK_GAME_START`, guarded: resume can never force a menu / level-clear / win screen into 'playing'. Pause also mutes (mandatory during ads); the pre-ad mute state is restored exactly on resume.
  - Pre-roll: `showBanner()` exactly once, on first user-initiated Play click — this IS the start signal (GM has no `gameStart()` call). **Never on load, never before a user gesture.**
  - Mid-roll: one `showBanner()` at win and at Level 5 / 10 / 15 clear breaks. **No ad on a loss.** One ad at a time (in-flight guard).
  - Verification surface: `window.__gamemonetize` (live `available`, `handlersRegistered`, `preRollShown`, `midRollCalls`, `pausedByGM`, `mutedByGM`, `lastAdError`, `simulatePause`, `simulateResume`).
- **Game hook surface (inert without a bridge):** `window.__oddPortalHooks` (`onLevelStart` / `onWin` / `onLevelClear`) + `window.__oddPortal` (guarded `pause()` / `resume()` / `setMuted()`).
- **Canvas id is `game`** (verified — 1 occurrence, 0 `gameCanvas` references). This is the canvas-id lesson from the Echoes GM build: the template hardcodes `gameCanvas`, but this game's canvas is `game`, and the staged build uses `game` consistently.
- **Placeholder gameId: `[YOUR GM GAME ID HERE]`** (present 2×: comment + definition). After the portal entry exists, replace it with the real **32-char gameId from the GM control panel (NOT the numeric id in the edit URL)** and REBUILD (re-run `stage-portals.py` after editing the placeholder in the script, or substitute + re-zip + re-verify). Do NOT invent a gameId. Do NOT upload the `-STAGED` ZIP as a final build.
- **Isolation verified:** no GamePix or GD SDK strings in this build (`integration.gamepix.com` 0, `gamedistribution.com` 0, `GD_OPTIONS` 0, `GamePixConfig` 0).

## Test evidence (headless Chromium, real mouse clicks — `../test-portal.js`)

**16/16 checks passed** (Nov 6, 2026), SDK absent offline: loads/menu, bridge present with `available=false`, pre-roll NOT shown before Play, Play → playing Level 1 / 3 lives / 9 figures, pre-roll hook fired once on first Play (ad skipped silently), wrong tap 3→2 lives, correct tap → score + clear → Level 2, simulated SDK pause → paused + muted, simulated resume → playing + mute restored off, levels 2–5 cleared → Level 6 with `midRollCalls=1` (exactly once, Level 5 clear), manual pause/resume + mute still work, **no page/console errors** (1 SDK script-load failure only: `net::ERR_TUNNEL_CONNECTION_FAILED` — expected offline).

## Listing copy (counted; GM description cap is 1,000 chars per the Aether GM report)

- **Description (670 chars, cap 1,000):** "Odd One Out: Spot the Difference is a quick observation puzzle built on one simple test: can you spot the one that is different? A crowd of near-identical blobs fills the screen and one of them is not like the others — a different colour, hat, eyes, mouth, accessory, size, ears, or facing. Tap it before the timer runs out. 20 levels grow the crowd from 3x3 to a dense 7x6 grid while the clock shrinks from 31 seconds to 12 and the differences get subtler. Three lives, combo bonuses for correct taps in a row, a hint naming the difference type each level, and a fresh board every level. Original art drawn in code, original music, no sign-up, touch and mouse controls."
- **Controls (147 chars):** "Tap the odd blob in the crowd to score. Pause with the pause button or P, mute with M. 20 levels, 3 lives, combo bonuses for correct taps in a row."
- **Category:** portal requires a minimum of 2 categories (per the Aether GM report, which used 3D + Puzzle for a 3D game). This game is 2D — pick Puzzle plus the portal's closest second category from its own list live; do NOT claim 3D.
- **Tags** (portal's own list, as used for the puzzle games): Brain, Logic, Puzzle, Relaxation.
- **Optimized for Mobile:** tick ON at Phase 2 (game is touch-first, portrait).
- **Change log for REQUEST ACTIVATION** (GM has no change-log field — Aether/Jade submitted with a single click and no field; keep this wording only as a record): "Initial GameMonetize release of Odd One Out: Spot the Difference: 20-level spot-the-odd-one-out puzzle, original art and music, and GameMonetize SDK integration with interstitial ads."

## What still needs the portal (NOT done here)

1. Create the GM entry at `/account/gameadd.php` (Game Name only on that form; the rest lives on the edit page).
2. Copy the 32-char gameId from the edit page; substitute for `[YOUR GM GAME ID HERE]`; rebuild; re-verify (GM ID present, placeholder absent, numeric entry id absent, testzip clean).
3. Upload the final ZIP + all 3 thumbnails, fill description/controls/category/tags, tick Optimized for Mobile.
4. Click **Verify Game** — record what it requires; pass = Request Activation enabled. The GM Verify quirk from Aether/Echoes: after the ad, the board in the Verify modal may stop responding to taps, but completed ad views still register.
5. Click **REQUEST ACTIVATION** (single click, no change-log field). Cap note: as of Nov 6, 2026, three GM submissions (Aether, Echoes, Jade) went through with **no cap message** — a cap is not proven absent, so report the outcome rather than assuming.
6. Live verification in the portal (game genuinely renders + plays in the Verify modal, ad watched fully) before calling it done.
