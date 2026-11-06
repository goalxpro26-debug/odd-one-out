# Odd One Out — GameDistribution staged build (NOT submitted)

**Status: STAGED ONLY. No dashboard entry, no upload, no submission.**
Original game untouched (`../index.html` md5 `14897666eb2abc812f0b96b8f6f45f73`).

## Files in this folder

| File | What it is |
|---|---|
| `index.html` (31,762 B) | Staged GD build — single file, game + GD SDK + bridge |
| `odd-one-out-gamedistribution-STAGED.zip` (10,097 B) | ZIP of `index.html` only (1 entry, testzip clean) — **do NOT upload as final** |
| `odd-one-out-512x512.jpg` | 512×512 |
| `odd-one-out-512x384.jpg` | 512×384 |
| `odd-one-out-200x120.jpg` | 200×120 |
| `odd-one-out-1280x720.jpg` | 1280×720 |
| `odd-one-out-1280x550.jpg` | 1280×550 |

All 5 thumbnails are JPG, derived from the game's own test shots (cover = menu + Level 1 + Level 20 panels; landscape sizes are cover scaled to target height and centre-cropped, full height kept so the title band survives; 200×120 is fit + letterboxed). Sizes PIL-verified.

## What was integrated

- **GameDistribution SDK**, following `~/workspace/babylonjs/projects/aether-weaver/index.gd.html` + `src/gamedistribution.ts`:
  - `window["GD_OPTIONS"] = { gameId, onEvent }` before the SDK script `https://html5.api.gamedistribution.com/main.min.js`, which precedes the game script. Events fired before the bridge runs are queued in `window.__gdEventQueue` and drained on init.
  - Pause/resume on `SDK_GAME_PAUSE` / `SDK_GAME_START`, guarded: resume can never force a menu / level-clear / win screen into 'playing'. Pause also mutes (mandatory during ads); the pre-ad mute state is restored exactly on resume.
  - Pre-roll: `gdsdk.showAd()` exactly once, on first user-initiated Play click — this IS the start signal (GD has no `gameStart()` call). Never on load.
  - Mid-roll: one `showAd()` at win and at Level 5 / 10 / 15 clear breaks. **No ad on a loss.** One ad at a time (in-flight guard, promise `.then()` clear + 60 s safety valve).
  - Verification surface: `window.__gamedistribution` (live `available`, `preRollShown`, `midRollCalls`, `pausedByGD`, `mutedByGD`, `lastAdError`, `simulatePause`, `simulateResume`).
- **Game hook surface (inert without a bridge):** `window.__oddPortalHooks` (`onLevelStart` / `onWin` / `onLevelClear`) + `window.__oddPortal` (guarded `pause()` / `resume()` / `setMuted()`).
- **Canvas id is `game`** (verified — 1 occurrence, 0 `gameCanvas` references).
- **Placeholder gameId: `[YOUR GD GAME ID HERE]`** (present 2×: comment + definition). After the portal entry exists, replace it with the real **32-char hex gameId from the GD Upload tab** and REBUILD (re-run `stage-portals.py` after editing the placeholder in the script, or substitute + re-zip + re-verify). Do NOT invent a gameId. Do NOT upload the `-STAGED` ZIP as a final build.
- **Isolation verified:** no GamePix or GM SDK strings in this build (`integration.gamepix.com` 0, `api.gamemonetize.com` 0, `SDK_OPTIONS` 0, `GamePixConfig` 0).

## Test evidence (headless Chromium, real mouse clicks — `../test-portal.js`)

**16/16 checks passed** (Nov 6, 2026), SDK absent offline: loads/menu, bridge present with `available=false`, pre-roll NOT shown before Play, Play → playing Level 1 / 3 lives / 9 figures, pre-roll hook fired once on first Play (ad skipped silently), wrong tap 3→2 lives, correct tap → score + clear → Level 2, simulated SDK pause → paused + muted, simulated resume → playing + mute restored off, levels 2–5 cleared → Level 6 with `midRollCalls=1` (exactly once, Level 5 clear), manual pause/resume + mute still work, **no page/console errors** (1 SDK script-load failure only: `net::ERR_TUNNEL_CONNECTION_FAILED` — expected offline).

## Listing copy (pre-trimmed to the GD 500-char caps, counted)

- **Description (420 chars, cap 500):** "Odd One Out: Spot the Difference is a quick observation puzzle. A crowd of near-identical blobs fills the screen — one is different. Tap the odd one out before the timer runs out. 20 levels: the crowd grows from 3x3 to 7x6, the clock shrinks, and the differences get subtler — colour, hat, eyes, mouth, accessories, size, ears, facing. Three lives, combo bonuses for correct taps in a row, and a fresh board every level."
- **Instructions (405 chars, cap 500):** "Look at the crowd — every blob looks the same except one. Tap the odd one out to score and advance. A wrong tap costs a life, and so does letting the timer run out. The hint names what kind of difference to look for: colour, hat, eyes, mouth, accessory, size, ears, or facing. Correct taps in a row build a combo for bonus points. Clear all 20 levels to win. Pause with the pause button or P, mute with M."
- **Category:** Puzzle. **Tags** (GD fixed vocabulary, as used for the puzzle games): logic, thinking, singleplayer.
- **Targeting** (same as the 32 GD games): Male+Female, all five age ranges, No Blood + Child Friendly + HTTPS Ready ticked. Content note: no blood, no gore, no sexual content; no verified IARC/Play rating exists for this game — the settings reflect its content, not a verified rating.

## What still needs the portal (NOT done here)

1. Create the GD entry (this joins the back of the existing GD queue — 2 In Review + 30 ready drafts already pending, and GD allows **2 submissions per week**).
2. Copy the 32-char hex gameId from the Upload tab; substitute for `[YOUR GD GAME ID HERE]`; rebuild; re-verify (gameId present, placeholder absent, testzip clean).
3. Upload the final ZIP + all 5 thumbnails, fill description/instructions/category/tags/targeting.
4. Watch the pre-roll ad completely in the portal iframe → "I'm done checking" → SDK: Yes → Request Activation (do NOT click it while the weekly limit is active — stop at the ready state and report).
5. Live verification in the portal before calling it done.

## FINAL build (Nov 6, 2026 — gameId substituted, ready to upload)

- **Final ZIP:** `odd-one-out-gamedistribution.zip` — **10,065 bytes, 1 entry (`index.html` at root), testzip clean**. Final source kept at `final/index.html` (31,663 chars). The staged files (`index.html` + `odd-one-out-gamedistribution-STAGED.zip`, placeholder still present 2×) are untouched as the pre-substitution record.
- **gameId:** `ef1dfa0c75a84d788b4a0e63c31d49d9` (from the portal Upload tab, entry 80460 — the numeric entry id is NOT in the build file). Present **1×** in the code (`GD_OPTIONS.gameId`); the staged build's second occurrence was in a comment, which was cleaned up, so 1× is correct. Placeholder `[YOUR GD GAME ID HERE]`: 0 occurrences. No `80460` in the file.
- **Verification (final build):** canvas id `game` (1×, `gameCanvas` 0×); isolation clean — GamePix, GameMonetize, GamePixConfig, SDK_OPTIONS, api.gamemonetize.com all 0×; GD_OPTIONS present; ZIP content byte-identical to `final/index.html`.
- **Headless real-click test (test-portal.js, final build): 16/16 passed** — loads/menu, bridge available=false offline, pre-roll not shown before Play, start → Level 1 / 3 lives / 9 figures, pre-roll hook once, wrong tap 3→2 lives, correct tap → score 250 → Level 2, simulated SDK pause → paused + muted, resume → playing + mute restored, levels 2–5 cleared → Level 6 with midRollCalls exactly 1, manual pause/resume + mute work, no page/console errors. One expected SDK script-load failure only (SDK host unreachable from `file://` offline; loads normally in the portal iframe). Screenshot: `../test-results/gamedistribution-final/portal-level6.png`.
- **Original game unchanged:** `../../index.html` md5 `14897666eb2abc812f0b96b8f6f45f73` (matches the recorded original).
- **Not submitted** — no portal work done; upload this final ZIP to the GD entry, then watch the pre-roll fully / "I'm done checking" / SDK: Yes / Request Activation per the portal steps in the main portals README.
