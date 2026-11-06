# Odd One Out — GamePix staged build (NOT submitted)

**Status: STAGED ONLY. No dashboard entry, no upload, no submission.**
Original game untouched (`../index.html` md5 `14897666eb2abc812f0b96b8f6f45f73`).

## Files in this folder

| File | What it is |
|---|---|
| `index.html` (31,920 B) | Staged GamePix build — single file, game + SDK v3 + bridge |
| `odd-one-out-gamepix-STAGED.zip` (9,980 B) | ZIP of `index.html` only (1 entry, testzip clean) — **do NOT upload as final; it is staged, see below** |
| `odd-one-out-icon-512x512.jpg` (512×512) | Icon — centre square crop of the Level 1 test shot |
| `odd-one-out-cover-1360x850.jpg` (1360×850) | Cover — menu + Level 1 + Level 20 panels, title band intact (visually inspected) |

## What was integrated

- **GamePix SDK v3, manual lifecycle**, following `~/workspace/babylonjs/projects/aether-weaver/index.gamepix.html` + `src/gamepix.ts`:
  - `window.GamePixConfig = { lifecycle: 'manual' }` before the SDK script; SDK script `https://integration.gamepix.com/sdk/v3/gamepix.sdk.js` before the game script.
  - Lifecycle: `loading(0)` at init → `loading(100)` + `loaded()` (3 s timeout guard) → `gameStart()` on first user-initiated Play click.
  - Pause/resume via `GamePix.events.on('pause'/'resume')`, guarded: resume can never force a menu / level-clear / win screen into 'playing'. Pause also mutes (mandatory during ads); the pre-ad mute state is restored exactly on resume.
  - Mid-roll: `happyMoment('level_complete')` + one `interstitial()` at win and at Level 5 / 10 / 15 clear breaks. **No ad on a loss, never on load.** One interstitial at a time (in-flight guard, 30 s timeout).
  - Verification surface: `window.__gamepix` (`available`, `handlersRegistered`, `loaded`, `gameStarted`, `pausedByGamePix`, `interstitialCalls`, `simulatePause`, `simulateResume`).
- **Game hook surface (inert without a bridge):** `window.__oddPortalHooks` (`onLevelStart` / `onWin` / `onLevelClear`) + `window.__oddPortal` (guarded `pause()` / `resume()` / `setMuted()`). The game itself is unchanged apart from these hook call sites.
- **Canvas id is `game`** (this game's own canvas, verified — 1 occurrence, 0 `gameCanvas` references). The GameMonetize canvas-id lesson does not apply here.
- **No gameId placeholder for GamePix** — SDK v3 has no gameId in the page. The dashboard entry is created first and this ZIP is uploaded to it. (GD and GM builds do have placeholders; this one does not, by design.)
- **Isolation verified:** no GD or GM SDK strings in this build (`gamedistribution.com` 0, `api.gamemonetize.com` 0, `GD_OPTIONS` 0, `SDK_OPTIONS` 0).

## Test evidence (headless Chromium, real mouse clicks — `../test-portal.js`)

**17/17 checks passed** (Nov 6, 2026), SDK absent offline:
loads/menu, bridge present with `available=false`, pre-roll NOT shown before Play, Play → playing Level 1 / 3 lives / 9 figures, pre-roll hook fired once on first Play (ad skipped silently), GamePix lifecycle reached `gameStarted=true` + `loaded=true`, wrong tap 3→2 lives, correct tap → score + clear screen → Level 2, simulated SDK pause → paused + muted, simulated resume → playing + mute restored off, levels 2–5 cleared → Level 6 with `midRollCalls=1` (exactly once, Level 5 clear), manual pause/resume + mute still work, **no page/console errors** (1 SDK script-load failure only: `net::ERR_TUNNEL_CONNECTION_FAILED` — expected offline; the SDK host is unreachable from `file://` here and loads normally in the portal iframe).

## Listing copy (for the dashboard entry — verify field caps live)

- **Description** (420 chars; GamePix cap not recorded for the 32 games — check the field live, do not assume): "Odd One Out: Spot the Difference is a quick observation puzzle. A crowd of near-identical blobs fills the screen — one is different. Tap the odd one out before the timer runs out. 20 levels: the crowd grows from 3x3 to 7x6, the clock shrinks, and the differences get subtler — colour, hat, eyes, mouth, accessories, size, ears, facing. Three lives, combo bonuses for correct taps in a row, and a fresh board every level."
- **Category:** Puzzle (confirm the portal's category list live).
- **Tags:** confirm the portal's tag vocabulary live; suggested from the GD/GM vocabularies used for the puzzle games: Brain, Logic, Puzzle, Relaxation.
- **Thumbnails:** icon 512×512 + cover 1360×850 above (GamePix rejected a 1024×500 cover for Aether — 1360×850 is the required cover size).

## What still needs the portal (NOT done here)

1. Create the GamePix dashboard entry for Odd One Out.
2. Upload `odd-one-out-gamepix-STAGED.zip` (the staged ZIP is uploadable as-is — GamePix has no gameId to substitute; rename to a final name only if the portal workflow requires it, and re-verify after any rename).
3. Upload icon + cover, fill description/category/tags, submit for review.
4. Live verification in the portal (game renders + plays, ad behaviour) before calling it done — the offline tests above prove the game + bridge, not the portal's SDK.
