#!/usr/bin/env python3
"""Stage portal builds for Odd One Out: Spot the Difference.

Reads the ORIGINAL index.html (never modifies it), applies the minimal
inert portal hook surface to the game script, injects the portal SDK
config/script ahead of the game script, appends the portal bridge after
the game script, and zips each staged build.

Canvas id is `game` (480x640 internal) — verified in the original; the
GameMonetize canvas-id lesson (template hardcoding `gameCanvas`) does
NOT apply here, and no `gameCanvas` string is introduced anywhere.

Placeholders (fill after the portal entry exists; never invent an ID):
  GamePix:        no gameId in the build (GamePix v3 SDK has no gameId
                  in the page; the entry is created on the dashboard and
                  the ZIP is uploaded to it)
  GameDistribution: [YOUR GD GAME ID HERE]  (32-char hex from GD Upload tab)
  GameMonetize:   [YOUR GM GAME ID HERE]    (32-char token from GM panel)

Usage: python3 stage-portals.py   (run from this portals/ directory)
"""
import hashlib
import pathlib
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "index.html"
OUT = pathlib.Path(__file__).resolve().parent

ORIG_MD5 = "14897666eb2abc812f0b96b8f6f45f73"  # recorded before staging


def md5(p: pathlib.Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def must_replace(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        print(f"FATAL: hook not found: {label}")
        sys.exit(1)
    if text.count(old) != 1:
        print(f"FATAL: hook not unique ({text.count(old)}x): {label}")
        sys.exit(1)
    return text.replace(old, new)


# ---------------------------------------------------------------- game edits
# These are the ONLY edits to the game itself, identical in all 3 builds.
# They are inert without a bridge: __oddPortalHooks stay null, the game
# behaves exactly as the original.
HOOK_HELPER = """let lastTs = 0, clearTimer = null;

// ---------- portal hook surface (inert without a portal bridge) ----------
// The trailing portal script assigns these; with no bridge they stay null
// and the game behaves exactly as the original. Hooks fire only from user
// gestures (Play click) or natural breaks (level clear / win), never on load.
window.__oddPortalHooks = { onLevelStart: null, onWin: null, onLevelClear: null };
function portalHook(name) {
  try {
    const h = window.__oddPortalHooks && window.__oddPortalHooks[name];
    if (typeof h === 'function') h();
  } catch (e) { /* never let a portal hook break the game */ }
}"""

PORTAL_SURFACE = """
// ---------- portal pause/mute surface (guarded, portal-neutral) ----------
// pauseForPortal: pauses ONLY from 'playing', else no-op (returns false).
// resumeForPortal: resumes ONLY from a bridge pause, else no-op.
// setMutedDirect: sets the mute flag + button WITHOUT touching any saved
// setting (there is none in this game) — used ONLY as the mandatory
// mute-during-ad fallback when the game is not in 'playing' (e.g. the
// level-clear / win screen at a mid-roll), where the guarded pause above
// is a correct no-op. The bridge records the pre-ad mute state and
// restores exactly that state on resume.
function pauseForPortal() { if (state.screen !== 'playing') return false; pauseGame(); return true; }
function resumeForPortal() { if (state.screen !== 'paused') return false; resumeGame(); return true; }
function setMutedDirect(m) {
  state.muted = !!m;
  const b = document.getElementById('btn-mute');
  if (b) b.textContent = state.muted ? '\\u{1F507}' : '\\u{1F50A}';
}
window.__oddPortal = {
  pause: pauseForPortal, resume: resumeForPortal, setMuted: setMutedDirect,
  get muted() { return state.muted; }, get screen() { return state.screen; },
};
"""


def apply_game_edits(html: str) -> str:
    html = must_replace(html,
        "let lastTs = 0, clearTimer = null;",
        HOOK_HELPER, "hook helper anchor")
    # Pre-roll hook: startGame() runs only from a user click (Play / Play
    # again / Retry). The bridge's once-guard makes it fire on the first
    # start only, inside the user-gesture call stack.
    html = must_replace(html,
        "  state.screen = 'playing';\n  hideAllOverlays();\n  buildLevel(1);",
        "  state.screen = 'playing';\n  hideAllOverlays();\n  portalHook('onLevelStart');\n  buildLevel(1);",
        "startGame hook")
    # Mid-roll hook: level-clear break, levels 5/10/15 only (not every
    # level — a 20-level game would otherwise show an ad every ~30s).
    # Win is handled separately in winGame() below.
    html = must_replace(html,
        "  if (state.level >= 20) { winGame(); return; }\n  state.screen = 'clear';",
        "  if (state.level >= 20) { winGame(); return; }\n  if (state.level === 5 || state.level === 10 || state.level === 15) portalHook('onLevelClear');\n  state.screen = 'clear';",
        "level-clear hook")
    # Win hook.
    html = must_replace(html,
        "  hideAllOverlays(); show('ov-win');\n  sfx.win(); stopMusic(); render();",
        "  hideAllOverlays(); show('ov-win');\n  portalHook('onWin');\n  sfx.win(); stopMusic(); render();",
        "win hook")
    html = must_replace(html,
        "// ---------- test hook (state only, no gameplay shortcuts beyond read access) ----------",
        PORTAL_SURFACE + "\n// ---------- test hook (state only, no gameplay shortcuts beyond read access) ----------",
        "portal surface anchor")
    return html


# ---------------------------------------------------------------- bridges
# Shared pause/mute logic, written per portal because the SDK call and
# event source differ. All three follow the proven Babylon templates:
# guarded pause first, direct-mute fallback so an ad is NEVER audible,
# who-paused flag so resume can never force a menu/clear/win game into
# 'playing', in-flight guard (one ad at a time), failed ad never blocks play.

def bridge_common(portal: str, sdk_check: str, show_ad: str, clear_note: str) -> str:
    return f"""
<script>
"use strict";
/* {portal} bridge for Odd One Out — {portal} variant ONLY.
   Game surface: window.__oddPortal (pause/resume/setMuted, guarded).
   Every SDK call is defensive: with the SDK absent the game plays
   normally and ad calls are skipped silently. {clear_note} */
(function () {{
  const portal = window.__oddPortal;
  if (!portal) return;
  let bridgePaused = false, bridgeMuted = false, wasMutedBeforeAd = false;
  let preRollShown = false, adInFlight = false, midRollCalls = 0, lastAdError = null;
  let adTimer = undefined;
  const clearAdInFlight = () => {{ adInFlight = false; if (adTimer !== undefined) {{ clearTimeout(adTimer); adTimer = undefined; }} }};
  const onPause = () => {{
    try {{
      if (portal.pause()) bridgePaused = true;
      else if (!bridgeMuted) {{ wasMutedBeforeAd = portal.muted; portal.setMuted(true); bridgeMuted = true; }}
      if (bridgePaused && !bridgeMuted) {{ wasMutedBeforeAd = portal.muted; portal.setMuted(true); bridgeMuted = true; }}
    }} catch (e) {{ /* never let a portal event break the game */ }}
  }};
  const onResume = () => {{
    try {{
      clearAdInFlight();
      if (bridgePaused) {{ if (!portal.resume()) {{ /* left pause by another route */ }} bridgePaused = false; }}
      if (bridgeMuted) {{ portal.setMuted(wasMutedBeforeAd); bridgeMuted = false; }}
    }} catch (e) {{ bridgePaused = false; bridgeMuted = false; }}
  }};
  {sdk_check}
  // __oddPortalBridge is assigned HERE, before the queue-drain in show_ad
  // aliases it under the portal's own global name. The notify methods
  // are lazy wrappers (the const arrow functions are defined in show_ad
  // below, so a direct reference here would hit the temporal dead zone).
  window.__oddPortalBridge = {{
    get available() {{ return sdkPresent(); }},
    get preRollShown() {{ return preRollShown; }},
    get midRollCalls() {{ return midRollCalls; }},
    get pausedByPortal() {{ return bridgePaused; }},
    get mutedByPortal() {{ return bridgeMuted; }},
    get lastAdError() {{ return lastAdError; }},
    simulatePause: onPause, simulateResume: onResume,
    notifyLevelStart: (...a) => notifyLevelStart(...a),
    notifyWin: (...a) => notifyWin(...a),
    notifyLevelClear: (...a) => notifyLevelClear(...a),
  }};
  {show_ad}
  window.__oddPortalHooks.onLevelStart = notifyLevelStart;
  window.__oddPortalHooks.onWin = notifyWin;
  window.__oddPortalHooks.onLevelClear = notifyLevelClear;
}})();
</script>
"""


GAMEPIX_BRIDGE = """
<script>
"use strict";
/* GamePix SDK v3 bridge for Odd One Out — GamePix variant ONLY.
   Game surface: window.__oddPortal (pause/resume/setMuted, guarded).
   Every GamePix call is defensive: with window.GamePix absent (SDK failed
   to load, or the game runs outside a GamePix Player) the game plays
   normally and lifecycle/ad calls resolve immediately / are skipped.
   Lifecycle: loading(0) at init -> loading(100) + loaded() -> gameStart()
   on first user-initiated Play (notifyLevelStart). Mid-roll: happyMoment
   + one interstitial at win and at level 5/10/15 clear breaks. No ad on
   a loss, never on load. Pause/resume via GamePix events, guarded so a
   resume can never force a menu/clear/win game into 'playing'. */
(function () {
  const portal = window.__oddPortal;
  if (!portal) return;
  const gp = () => (window.GamePix ? window.GamePix : null);
  let bridgePaused = false, bridgeMuted = false, wasMutedBeforeAd = false;
  let handlersRegistered = false, loadedDone = false, gameStarted = false;
  let preRollShown = false, interstitialInFlight = false, interstitialCalls = 0;
  let midRollCalls = 0, lastInterstitial = null;
  const onPause = () => {
    try {
      if (portal.pause()) bridgePaused = true;
      else if (!bridgeMuted) { wasMutedBeforeAd = portal.muted; portal.setMuted(true); bridgeMuted = true; }
      if (bridgePaused && !bridgeMuted) { wasMutedBeforeAd = portal.muted; portal.setMuted(true); bridgeMuted = true; }
    } catch (e) { /* never let a Player event break the game */ }
  };
  const onResume = () => {
    try {
      if (bridgePaused) { portal.resume(); bridgePaused = false; }
      if (bridgeMuted) { portal.setMuted(wasMutedBeforeAd); bridgeMuted = false; }
    } catch (e) { bridgePaused = false; bridgeMuted = false; }
  };
  const sdk = gp();
  if (sdk && sdk.events) {
    try { sdk.events.on('pause', onPause); sdk.events.on('resume', onResume); handlersRegistered = true; }
    catch (e) { handlersRegistered = false; }
  }
  const loading = (pct) => { try { const s = gp(); if (s && s.lifecycle) s.lifecycle.loading(pct); } catch (e) {} };
  let readyPromise = null;
  const ready = () => {
    if (readyPromise) return readyPromise;
    readyPromise = (async () => {
      loading(100);
      const s = gp();
      if (s && s.lifecycle) {
        try { await Promise.race([Promise.resolve(s.lifecycle.loaded()), new Promise((r) => setTimeout(() => r(null), 3000))]); }
        catch (e) { /* fall through: game must never hang on lifecycle */ }
      }
      loadedDone = true;
    })();
    return readyPromise;
  };
  const notifyLevelStart = () => {
    if (gameStarted) return;
    preRollShown = true;
    void ready().then(() => {
      if (gameStarted) return;
      gameStarted = true;
      try { const s = gp(); if (s && s.lifecycle) s.lifecycle.gameStart(); } catch (e) {}
    });
  };
  const notifyWin = async () => { await showInterstitial('level_complete'); };
  const notifyLevelClear = async () => { await showInterstitial('level_complete'); };
  async function showInterstitial(moment) {
    midRollCalls++;
    try { const s = gp(); if (s && s.happyMoment) s.happyMoment(moment); } catch (e) {}
    const s = gp();
    if (!loadedDone || interstitialInFlight || !s || !s.ads) return;
    interstitialInFlight = true; interstitialCalls++;
    try {
      lastInterstitial = await Promise.race([
        Promise.resolve(s.ads.interstitial()),
        new Promise((r) => setTimeout(() => r({ success: false, message: 'interstitial timed out (local guard)' }), 30000)),
      ]);
    } catch (e) { lastInterstitial = { success: false, message: 'interstitial threw (caught)' }; }
    finally { interstitialInFlight = false; }
  }
  window.__gamepix = {
    get available() { return gp() !== null; },
    get handlersRegistered() { return handlersRegistered; },
    get loaded() { return loadedDone; },
    get gameStarted() { return gameStarted; },
    get pausedByGamePix() { return bridgePaused; },
    get interstitialCalls() { return interstitialCalls; },
    get lastInterstitial() { return lastInterstitial; },
    get preRollShown() { return preRollShown; },
    get midRollCalls() { return midRollCalls; },
    simulatePause: onPause, simulateResume: onResume,
  };
  window.__oddPortalHooks.onLevelStart = notifyLevelStart;
  window.__oddPortalHooks.onWin = notifyWin;
  window.__oddPortalHooks.onLevelClear = notifyLevelClear;
  window.__oddPortalBridge = window.__gamepix;
  loading(0);
})();
</script>
"""

GD_SDK_CHECK = """
  const gdSdk = () => {
    const w = window;
    const s = w.gdsdk;
    return (s && typeof s.showAd === 'function') ? s : null;
  };
  const sdkPresent = () => gdSdk() !== null;"""

GD_SHOW_AD = """
  const showAd = () => {
    const live = gdSdk();
    if (!live || adInFlight) return;
    adInFlight = true;
    try {
      const p = Promise.resolve(live.showAd());
      p.then(() => { adInFlight = false; }, (err) => { lastAdError = String(err); adInFlight = false; });
      setTimeout(() => { adInFlight = false; }, 60000); // safety valve
    } catch (err) { lastAdError = String(err); clearAdInFlight(); }
  };
  const notifyLevelStart = () => {
    if (preRollShown) return;
    preRollShown = true;
    // PRE-ROLL, first user-initiated Play only; this IS the start signal
    // (GD has no gameStart() lifecycle call). Never on load.
    showAd();
  };
  const notifyWin = () => { midRollCalls++; showAd(); };
  const notifyLevelClear = () => { midRollCalls++; showAd(); };
  // Drain events fired before this bridge ran (GD_OPTIONS.onEvent queues).
  const handleEvent = (ev) => {
    try {
      if (!ev || typeof ev.name !== 'string') return;
      if (ev.name === 'SDK_GAME_PAUSE') onPause();
      else if (ev.name === 'SDK_GAME_START') onResume();
    } catch (e) {}
  };
  try {
    const queued = window.__gdEventQueue || [];
    window.__gdEventQueue = [];
    for (const ev of queued) handleEvent(ev);
    window.__gdEventHandler = handleEvent;
    window.__gamedistribution = window.__oddPortalBridge;
  } catch (e) {}"""

GM_SDK_CHECK = """
  const gmSdk = () => {
    const w = window;
    const s = w.sdk;
    return (s && typeof s.showBanner === 'function') ? s : null;
  };
  const sdkPresent = () => gmSdk() !== null;"""

GM_SHOW_AD = """
  const showBanner = () => {
    const live = gmSdk();
    if (!live || adInFlight) return;
    adInFlight = true;
    try {
      // Fire-and-forget: showBanner() has NO documented return value —
      // do NOT await it or depend on a promise. The flag clears on
      // SDK_GAME_START (see onResume) or the 60s safety valve.
      live.showBanner();
      adTimer = setTimeout(() => { clearAdInFlight(); }, 60000);
    } catch (err) { lastAdError = String(err); clearAdInFlight(); }
  };
  const notifyLevelStart = () => {
    if (preRollShown) return;
    preRollShown = true;
    // PRE-ROLL, first user-initiated Play only; this IS the start signal
    // (GM has no gameStart() lifecycle call). Never on load, never before
    // a user gesture.
    showBanner();
  };
  const notifyWin = () => { midRollCalls++; showBanner(); };
  const notifyLevelClear = () => { midRollCalls++; showBanner(); };
  // Drain events fired before this bridge ran (SDK_OPTIONS.onEvent queues).
  // NOTE (GM difference vs GD): the official GM loader injects sdk.js
  // ASYNC, so `sdk` may not exist when this bridge runs; availability is
  // re-checked live on every ad call (sdkPresent above), never snapshotted.
  const handleEvent = (ev) => {
    try {
      if (!ev || typeof ev.name !== 'string') return;
      if (ev.name === 'SDK_GAME_PAUSE') onPause();
      else if (ev.name === 'SDK_GAME_START') onResume();
      else if (ev.name === 'SDK_READY') { /* late-loading sdk now visible via live getter */ }
    } catch (e) {}
  };
  try {
    const queued = window.__gmEventQueue || [];
    window.__gmEventQueue = [];
    for (const ev of queued) handleEvent(ev);
    window.__gmEventHandler = handleEvent;
    window.__gamemonetize = window.__oddPortalBridge;
  } catch (e) {}"""


def gd_bridge() -> str:
    b = bridge_common("GameDistribution", GD_SDK_CHECK, GD_SHOW_AD,
                      "GD: gdsdk.showAd() returns a Promise; the in-flight flag clears in .then() plus a 60s safety valve.")
    # bridge_common defines __oddPortalBridge before the queue-drain block
    # runs; the drain block then aliases __gamedistribution to it. Fix the
    # alias order: __oddPortalBridge is assigned inside the IIFE before the
    # drain code, so the alias works as written.
    return b


def gm_bridge() -> str:
    return bridge_common("GameMonetize", GM_SDK_CHECK, GM_SHOW_AD,
                         "GM: sdk.showBanner() has no documented return value; the in-flight flag clears on SDK_GAME_START plus a 60s safety valve.")


# ---------------------------------------------------------------- head blocks
GAMEPIX_HEAD = """<!-- GamePix SDK v3, manual lifecycle: config MUST precede the SDK script,
     and the SDK script MUST precede the game script. This file is the
     GamePix entry only; the plain index.html and the other portal entries
     have no GamePix script tag at all. GamePix v3 has NO gameId in the
     page — the dashboard entry is created first and this ZIP is uploaded
     to it. Canvas id is `game` (this game's own canvas). -->
<script>window.GamePixConfig = { lifecycle: 'manual' };</script>
<script src="https://integration.gamepix.com/sdk/v3/gamepix.sdk.js"></script>
"""

GD_HEAD = """<!-- GameDistribution SDK: GD_OPTIONS MUST precede the SDK script, and the
     SDK script MUST precede the game script. This file is the GD entry
     only; the plain index.html and the other portal entries have no GD
     script tag at all.
     STAGED BUILD — gameId is a PLACEHOLDER. After the portal entry exists,
     replace "[YOUR GD GAME ID HERE]" with the real 32-char hex gameId from
     the GD Upload tab and REBUILD; do not upload this staged ZIP as final.
     Canvas id is `game` (this game's own canvas). -->
<script>
  window["GD_OPTIONS"] = {
    gameId: "[YOUR GD GAME ID HERE]",
    onEvent: function (event) {
      var h = window.__gdEventHandler;
      if (typeof h === "function") h(event);
      else (window.__gdEventQueue = window.__gdEventQueue || []).push(event);
    }
  };
</script>
<script src="https://html5.api.gamedistribution.com/main.min.js"></script>
"""

GM_HEAD = """<!-- GameMonetize SDK: SDK_OPTIONS MUST precede the SDK loader, and the
     SDK loader MUST precede the game script. This file is the GM entry
     only; the plain index.html and the other portal entries have no GM
     script tag at all.
     STAGED BUILD — gameId is a PLACEHOLDER. After the portal entry exists,
     replace "[YOUR GM GAME ID HERE]" with the real 32-char gameId from the
     GM control panel (NOT the numeric id in the edit URL) and REBUILD;
     do not upload this staged ZIP as a final build.
     NOTE (GD difference): the official GM loader injects sdk.js ASYNC, so
     the `sdk` global may not exist when the bridge runs. The bridge
     re-checks for it live on every ad call — never snapshot availability.
     Canvas id is `game` (this game's own canvas). -->
<script>
  window.SDK_OPTIONS = {
    gameId: "[YOUR GM GAME ID HERE]",
    onEvent: function (event) {
      var h = window.__gmEventHandler;
      if (typeof h === "function") h(event);
      else (window.__gmEventQueue = window.__gmEventQueue || []).push(event);
    }
  };
</script>
<script>
  // Official GameMonetize SDK loader (github.com/MonetizeGame/GameMonetize.com-SDK).
  (function (a, b, c) {
    var d = a.getElementsByTagName(b)[0];
    a.getElementById(c) || (a = a.createElement(b), a.id = c, a.src = "https://api.gamemonetize.com/sdk.js", d.parentNode.insertBefore(a, d))
  })(document, "script", "gamemonetize-sdk");
</script>
"""

PORTALS = {
    "gamepix": (GAMEPIX_HEAD, GAMEPIX_BRIDGE, "odd-one-out-gamepix-STAGED.zip"),
    "gamedistribution": (GD_HEAD, gd_bridge(), "odd-one-out-gamedistribution-STAGED.zip"),
    "gamemonetize": (GM_HEAD, gm_bridge(), "odd-one-out-gamemonetize-STAGED.zip"),
}


def main() -> None:
    if md5(SRC) != ORIG_MD5:
        print(f"FATAL: original index.html changed! md5={md5(SRC)} expected {ORIG_MD5}")
        sys.exit(1)
    base = SRC.read_text(encoding="utf-8")
    if "gameCanvas" in base:
        print("FATAL: original contains 'gameCanvas' — canvas-id assumption wrong")
        sys.exit(1)
    gamed = apply_game_edits(base)
    assert "portalHook('onLevelStart')" in gamed
    assert "portalHook('onWin')" in gamed
    assert "portalHook('onLevelClear')" in gamed
    assert "__oddPortal" in gamed
    for name, (head, bridge, zipname) in PORTALS.items():
        outdir = OUT / name
        outdir.mkdir(parents=True, exist_ok=True)
        html = must_replace(gamed, '<script>\n"use strict";', head + '<script>\n"use strict";',
                            f"{name} head injection")
        # Append bridge just before </body>.
        html = must_replace(html, "</body>\n</html>", bridge + "\n</body>\n</html>",
                            f"{name} bridge injection")
        # Isolation: this portal's build must contain NO other portal's SDK.
        others = {"gamepix": ["gamedistribution", "gamemonetize", "GD_OPTIONS", "SDK_OPTIONS", "api.gamemonetize.com"],
                  "gamedistribution": ["gamepix", "gamemonetize", "GamePixConfig", "SDK_OPTIONS", "api.gamemonetize.com"],
                  "gamemonetize": ["gamepix", "gamedistribution", "GamePixConfig", "GD_OPTIONS", "gamedistribution.com"]}
        for bad in others[name]:
            if bad.lower() in html.lower():
                print(f"FATAL: {name} build contains other-portal string: {bad}")
                sys.exit(1)
        target = outdir / "index.html"
        target.write_text(html, encoding="utf-8")
        zippath = outdir / zipname
        with zipfile.ZipFile(zippath, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(target, arcname="index.html")
        with zipfile.ZipFile(zippath) as z:
            assert z.testzip() is None
            assert z.namelist() == ["index.html"]
        print(f"{name}: index.html {target.stat().st_size} B, {zipname} {zippath.stat().st_size} B, 1 entry, testzip clean")
    print(f"original untouched: md5 {md5(SRC)} == {ORIG_MD5}")


if __name__ == "__main__":
    main()
