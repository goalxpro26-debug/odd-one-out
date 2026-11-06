# Odd One Out: Spot the Difference — pilot game

Original spot-the-odd-one-out HTML5 game. Mechanics only were inspired by
the popular "scan a crowd, tap the different one" genre — no art, code,
names, characters, or assets were copied from any existing game.

## Game

- **Name:** Odd One Out: Spot the Difference
- **Format:** single self-contained `index.html` — plain HTML5 + vanilla JS + Canvas, no engine, no external assets, no network needed.
- **Play:** a crowd of near-identical procedurally-drawn blob characters fills the screen. One is different. Tap it to score and advance.
- **Levels:** 20. Grid grows 3×3 → 4×4 → 5×5 → 6×5 → 7×6; time limit shrinks 31s → 12s; differences get subtler.
- **Difference types (rotate):** colour, hat, eyes, mouth, accessory (glasses/bow/scarf), facing direction, size, ears. A per-level hint names the category.
- **Rules:** 3 lives. Wrong tap = −1 life, combo reset. Timer running out = −1 life and the same level retries with a fresh board. Correct tap = 100 + 5×seconds-left + 25×(combo−1) points. Win screen after level 20; game-over screen with retry.
- **Extras:** start menu with how-to-play, HUD (level / score / lives / timer bar), pause (button or P/Esc), mute (button or M), synthesised WebAudio sound effects + a simple original looping melody (no copyrighted music), combo toasts, touch + mouse input, portrait-friendly, works on desktop too.
- **Test hook:** `window.__oddGame()` returns screen/level/score/lives/odd & wrong figure centres — state only, used by the automated test.

## How to run

Open `index.html` directly in a browser, or serve the folder:

```bash
cd ~/workspace/playables-inspired/odd-one-out
python3 -m http.server 8931
# open http://127.0.0.1:8931/index.html
```

## Test results — 13/13 passed (real mouse clicks, headless Chromium)

Run with: `NODE_PATH=~/workspace/tools/pw-shot/node_modules node test.js file:///.../index.html ./test-shots`
(Test script: `test.js`; screenshots: `test-shots/`.)

| Check | Result |
|---|---|
| Loads, menu screen, no errors | PASS |
| Start → playing, level 1, 3 lives, 9 figures | PASS |
| Wrong tap → lives 3→2, wrongTaps 1, level stays 1 | PASS |
| Correct tap → score 250, correctTaps 1, level-clear screen | PASS |
| After clear delay → level 2 playing, 9 figures (3×3) | PASS |
| Pause button → paused; Resume → playing | PASS |
| Mute toggles on | PASS |
| Full playthrough (real clicks on the odd figure each level) → WIN after 20 levels, score 8890, 20 correct, 1 miss, best combo ×20 | PASS |
| Play again → resets to level 1, score 0, 3 lives | PASS |
| 3 wrong taps → game over, lives 0 | PASS |
| Retry from game over → playing level 1 | PASS |
| No page/console errors | PASS |

Notes from testing:
- First run was 12/13: the one failure was a wrong expectation in my own test (it expected 16 figures on level 2; level 2 is 3×3 = 9 by design). Fixed the test, re-ran clean: 13/13.
- Headless Chrome on this VM needs the existing `--hatch-webgl-allowed-domains-file` launch flag (see `test.js`); localhost navigation is blocked by Chrome's local-network checks, so the test uses a `file://` URL. The game itself needs no network.
- Screenshots visually verified: level 1 board (odd blob clearly a different colour), level 20 board (dense 7×6 grid), win screen (final score 8890, best combo ×20).

## Status

**Portal status (Nov 6, 2026): IN REVIEW on GamePix** (Game Id PUP7TS) and **ready draft on GameDistribution** (entry 80460, GameId ef1dfa0c75a84d788b4a0e63c31d49d9, Request Activation not clicked — weekly limit). Not submitted to GameMonetize (account banned Nov 6; see GameMonetize restoration work).
