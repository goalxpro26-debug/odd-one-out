// Real-click test for Odd One Out. Usage: node test.js <url> <outdir>
const { chromium } = require('playwright-core');
const fs = require('fs');
const [url, outdir] = process.argv.slice(2);
fs.mkdirSync(outdir, { recursive: true });
const results = [];
function check(name, ok, detail) { results.push({ name, ok: !!ok, detail: detail || '' }); console.log((ok ? 'PASS' : 'FAIL') + '  ' + name + (detail ? '  — ' + detail : '')); }

(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/meta-chromium/chrome', args: ['--no-sandbox', '--disable-dev-shm-usage', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--allow-file-access-from-files', '--hatch-webgl-allowed-domains-file=/home/hatch/workspace/tools/pw-shot/webgl-policy.txt', '--hatch-webgl-allowed-domains-sha256=dc8a0e5eec744f6590a4c1889139c00568ffedc3eced6d0a1a5127e35f9ccd16'] });
  const page = await browser.newPage({ viewport: { width: 480, height: 860 } });
  const errors = [];
  page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push('CONSOLE: ' + m.text().slice(0, 200)); });
  const state = () => page.evaluate(() => window.__oddGame ? window.__oddGame() : null);
  const clickCanvasAt = async (pt) => {
    const box = await page.locator('#game').boundingBox();
    await page.mouse.click(box.x + pt.x / 480 * box.width, box.y + pt.y / 640 * box.height);
  };

  await page.goto(url, { waitUntil: 'load' });
  await page.waitForTimeout(800);
  let s = await state();
  check('loads, hook present, menu screen', s && s.screen === 'menu', JSON.stringify(s));
  await page.screenshot({ path: outdir + '/01-menu.png' });

  // Start game
  await page.click('#btn-start');
  await page.waitForTimeout(400);
  s = await state();
  check('start -> playing, level 1, 3 lives, 9 figures', s && s.screen === 'playing' && s.level === 1 && s.lives === 3 && s.figures === 9, JSON.stringify(s));
  await page.screenshot({ path: outdir + '/02-level1.png' });

  // Wrong tap penalises
  const livesBefore = s.lives;
  await clickCanvasAt(s.wrongCenter);
  await page.waitForTimeout(300);
  s = await state();
  check('wrong tap: lives 3->2, wrongTaps 1, level stays 1', s.lives === livesBefore - 1 && s.wrongTaps === 1 && s.level === 1, JSON.stringify(s));

  // Correct tap advances
  s = await state();
  await clickCanvasAt(s.oddCenter);
  await page.waitForTimeout(400);
  s = await state();
  check('correct tap: score > 0, correctTaps 1, clear screen', s.score > 0 && s.correctTaps === 1 && s.screen === 'clear', JSON.stringify(s));
  await page.waitForTimeout(1300);
  s = await state();
  check('after clear delay -> level 2 playing, 9 figures (3x3)', s.screen === 'playing' && s.level === 2 && s.figures === 9, JSON.stringify(s));

  // Pause / resume
  await page.click('#btn-pause');
  await page.waitForTimeout(200);
  s = await state();
  check('pause button -> paused', s.screen === 'paused', JSON.stringify(s));
  await page.click('#btn-resume');
  await page.waitForTimeout(200);
  s = await state();
  check('resume -> playing', s.screen === 'playing', JSON.stringify(s));

  // Mute toggle
  await page.click('#btn-mute');
  s = await state();
  check('mute toggles on', s.muted === true, JSON.stringify(s));
  await page.click('#btn-mute');

  // Play through to win: tap odd on every level, waiting out clear screens
  let won = false, guard = 0;
  while (guard++ < 120) {
    s = await state();
    if (!s) break;
    if (s.screen === 'win') { won = true; break; }
    if (s.screen === 'over') break;
    if (s.screen === 'playing') {
      if (s.level === 10) await page.screenshot({ path: outdir + '/03-level10.png' });
      if (s.level === 20) await page.screenshot({ path: outdir + '/04-level20.png' });
      await clickCanvasAt(s.oddCenter);
    }
    await page.waitForTimeout(250);
  }
  s = await state();
  check('full playthrough reaches WIN after 20 levels', won && s.screen === 'win' && s.level === 20 && s.correctTaps >= 20, JSON.stringify(s));
  await page.screenshot({ path: outdir + '/05-win.png' });

  // Game over path: fresh game, 3 wrong taps
  await page.click('#btn-again-win');
  await page.waitForTimeout(400);
  s = await state();
  check('play again resets to level 1, score 0, 3 lives', s.screen === 'playing' && s.level === 1 && s.score === 0 && s.lives === 3, JSON.stringify(s));
  for (let i = 0; i < 3; i++) {
    s = await state();
    await clickCanvasAt(s.wrongCenter);
    await page.waitForTimeout(300);
  }
  s = await state();
  check('3 wrong taps -> game over screen, lives 0', s.screen === 'over' && s.lives === 0, JSON.stringify(s));
  await page.screenshot({ path: outdir + '/06-gameover.png' });

  // Retry from game over
  await page.click('#btn-again-over');
  await page.waitForTimeout(400);
  s = await state();
  check('retry from game over -> playing level 1', s.screen === 'playing' && s.level === 1, JSON.stringify(s));

  check('no page/console errors', errors.length === 0, errors.slice(0, 3).join(' | '));
  const failed = results.filter(r => !r.ok).length;
  console.log(`\n${results.length - failed}/${results.length} checks passed`);
  await browser.close();
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error('TEST CRASH', e); process.exit(2); });
