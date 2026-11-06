// Per-portal real-click test for Odd One Out staged builds.
// Usage: NODE_PATH=~/workspace/tools/pw-shot/node_modules node test-portal.js <portal> <file-url> <outdir>
// portal: gamepix | gamedistribution | gamemonetize
// SDK is absent offline (no network to the SDK hosts): the bridge must
// report available=false, ad calls must be skipped silently, and the game
// must still play. SDK script-load failures are recorded separately and do
// NOT count as game errors (the SDK hosts are unreachable from file://
// in this environment; in the portal iframe they load normally).
const { chromium } = require('playwright-core');
const fs = require('fs');
const [portal, url, outdir] = process.argv.slice(2);
const SURFACE = { gamepix: '__gamepix', gamedistribution: '__gamedistribution', gamemonetize: '__gamemonetize' }[portal];
if (!SURFACE) { console.error('unknown portal', portal); process.exit(2); }
fs.mkdirSync(outdir, { recursive: true });
const results = [];
function check(name, ok, detail) { results.push({ name, ok: !!ok, detail: detail || '' }); console.log((ok ? 'PASS' : 'FAIL') + '  ' + name + (detail ? '  — ' + detail : '')); }

(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/meta-chromium/chrome', args: ['--no-sandbox', '--disable-dev-shm-usage', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--allow-file-access-from-files', '--hatch-webgl-allowed-domains-file=/home/hatch/workspace/tools/pw-shot/webgl-policy.txt', '--hatch-webgl-allowed-domains-sha256=dc8a0e5eec744f6590a4c1889139c00568ffedc3eced6d0a1a5127e35f9ccd16'] });
  const page = await browser.newPage({ viewport: { width: 480, height: 860 } });
  const errors = [], sdkLoadErrors = [];
  const SDK_HOSTS = ['gamepix.com', 'gamedistribution.com', 'gamemonetize.com'];
  page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));
  page.on('console', m => {
    if (m.type() !== 'error') return;
    const t = m.text();
    if (SDK_HOSTS.some(h => t.includes(h)) || /Failed to load resource/i.test(t)) sdkLoadErrors.push('SDK-LOAD: ' + t.slice(0, 160));
    else errors.push('CONSOLE: ' + t.slice(0, 200));
  });
  const state = () => page.evaluate(() => window.__oddGame ? window.__oddGame() : null);
  const bridge = () => page.evaluate((s) => {
    const b = window[s];
    if (!b) return null;
    return { available: b.available, preRollShown: b.preRollShown, midRollCalls: b.midRollCalls, pausedByPortal: b.pausedByPortal ?? b.pausedByGamePix, mutedByPortal: b.mutedByPortal ?? b.mutedByGamePix, handlersRegistered: b.handlersRegistered, gameStarted: b.gameStarted, loaded: b.loaded };
  }, SURFACE);
  const clickCanvasAt = async (pt) => {
    const box = await page.locator('#game').boundingBox();
    await page.mouse.click(box.x + pt.x / 480 * box.width, box.y + pt.y / 640 * box.height);
  };
  const clickOdd = async () => { const s = await state(); await clickCanvasAt(s.oddCenter); };

  await page.goto(url, { waitUntil: 'load' });
  await page.waitForTimeout(1500); // let SDK script loads fail / settle
  let s = await state();
  check('loads, menu screen, canvas id is game', s && s.screen === 'menu' && (await page.locator('#game').count()) === 1 && (await page.locator('#gameCanvas').count()) === 0, JSON.stringify(s));
  let b = await bridge();
  check('portal bridge surface present, SDK absent offline (available=false)', b && b.available === false, JSON.stringify(b));
  check('pre-roll not shown before Play', b && b.preRollShown === false, JSON.stringify(b));

  // Start (user gesture) -> pre-roll hook fires, ad skipped silently.
  await page.click('#btn-start');
  await page.waitForTimeout(600);
  s = await state(); b = await bridge();
  check('start -> playing, level 1, 3 lives, 9 figures', s && s.screen === 'playing' && s.level === 1 && s.lives === 3 && s.figures === 9, JSON.stringify(s));
  check('pre-roll hook fired once on first Play (ad skipped, SDK absent)', b && b.preRollShown === true, JSON.stringify(b));
  if (portal === 'gamepix') check('GamePix lifecycle: gameStart reached', b && b.gameStarted === true && b.loaded === true, JSON.stringify(b));

  // Wrong tap penalises, correct tap advances.
  await clickCanvasAt(s.wrongCenter);
  await page.waitForTimeout(300);
  s = await state();
  check('wrong tap: lives 3->2, wrongTaps 1, level stays 1', s.lives === 2 && s.wrongTaps === 1 && s.level === 1, JSON.stringify(s));
  await clickCanvasAt(s.oddCenter);
  await page.waitForTimeout(400);
  s = await state();
  check('correct tap: score > 0, correctTaps 1, clear screen', s.score > 0 && s.correctTaps === 1 && s.screen === 'clear', JSON.stringify(s));
  await page.waitForTimeout(1300);
  s = await state();
  check('after clear delay -> level 2 playing', s.screen === 'playing' && s.level === 2, JSON.stringify(s));

  // Bridge pause/mute while playing, then resume restores.
  await page.evaluate((surf) => { window[surf].simulatePause(); }, SURFACE);
  await page.waitForTimeout(200);
  s = await state(); b = await bridge();
  check('simulate SDK pause -> paused + muted', s.screen === 'paused' && s.muted === true, JSON.stringify({ screen: s.screen, muted: s.muted, b }));
  await page.evaluate((surf) => { window[surf].simulateResume(); }, SURFACE);
  await page.waitForTimeout(200);
  s = await state();
  check('simulate SDK resume -> playing + mute restored off', s.screen === 'playing' && s.muted === false, JSON.stringify(s));

  // Play through to level 5 clear -> mid-roll hook fires exactly once.
  for (let lv = 2; lv <= 5; lv++) {
    let guard = 0;
    while (guard++ < 40) {
      s = await state();
      if (!s) break;
      if (s.screen === 'playing' && s.level === lv) { await clickOdd(); break; }
      if (s.screen === 'playing' && s.level > lv) break;
      await page.waitForTimeout(250);
    }
    await page.waitForTimeout(1500); // clear screen delay
  }
  s = await state(); b = await bridge();
  check('reached level 6 playing (levels 2-5 cleared)', s.screen === 'playing' && s.level === 6, JSON.stringify(s));
  check('mid-roll hook fired exactly once (level 5 clear)', b && b.midRollCalls === 1, JSON.stringify(b));

  // Manual pause/resume + mute still work.
  await page.click('#btn-pause');
  await page.waitForTimeout(200);
  s = await state();
  check('pause button -> paused', s.screen === 'paused', JSON.stringify(s));
  await page.click('#btn-resume');
  await page.waitForTimeout(200);
  s = await state();
  check('resume -> playing', s.screen === 'playing', JSON.stringify(s));
  await page.click('#btn-mute');
  s = await state();
  check('mute toggles on', s.muted === true, JSON.stringify(s));
  await page.click('#btn-mute');

  await page.screenshot({ path: outdir + '/portal-level6.png' });
  check('no page/console errors (excluding SDK script-load failures)', errors.length === 0, errors.slice(0, 3).join(' | '));
  console.log('SDK script-load failures (expected offline, not game errors): ' + sdkLoadErrors.length + (sdkLoadErrors.length ? ' — ' + sdkLoadErrors[0] : ''));
  const failed = results.filter(r => !r.ok).length;
  console.log(`\n${results.length - failed}/${results.length} checks passed (${portal})`);
  await browser.close();
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error('TEST CRASH', e); process.exit(2); });
