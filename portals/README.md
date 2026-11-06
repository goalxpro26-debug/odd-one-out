# Odd One Out — portal staged builds

Preparation only. **Nothing submitted, no portal entry created, no live
browser portal work done.**

- Source: `../index.html` (single-file HTML5/Canvas game, 20 levels).
  Untouched — md5 `14897666eb2abc812f0b96b8f6f45f73` before and after staging.
- Canvas id is **`game`** (verified; 0 `gameCanvas` references anywhere).
- Builders: `stage-portals.py` (game hook surface + SDK injection + bridge
  + staged ZIP, with isolation checks), `make-thumbs.py` (thumbnails from
  the game's own test shots), `test-portal.js` (headless real-click tests).

| Portal | Folder | Staged ZIP | Tests |
|---|---|---|---|
| GamePix | `gamepix/` | `odd-one-out-gamepix-STAGED.zip` (9,980 B, 1 entry) | 17/17 |
| GameDistribution | `gamedistribution/` | `odd-one-out-gamedistribution-STAGED.zip` (10,097 B, 1 entry) | 16/16 |
| GameMonetize | `gamemonetize/` | `odd-one-out-gamemonetize-STAGED.zip` (10,525 B, 1 entry) | 16/16 |

Common integration (all three): pre-roll ad hook once on first Play click
(never on load); mid-roll hook at win + Level 5/10/15 clear breaks (never
on a loss); guarded pause + mute on the ad-pause event, exact mute-state
restore on resume; all SDK calls guarded so the game plays fully offline
with the SDK absent. Each portal's README has its SDK details, placeholder
game ID, thumbnails, listing copy (character-counted), test evidence, and
the exact portal steps still outstanding.
