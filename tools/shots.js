// Screenshots of the map in headless Chromium, and a few checks of the page.
//   python3 -m http.server 8765 --directory docs &
//   node tools/shots.js [http://localhost:8765/] [tools/screens]
// Needs Playwright (npm i playwright; or NODE_PATH=/opt/node22/lib/node_modules) and a Chromium.
const path = require('path'), fs = require('fs');
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright');
const URL = process.argv[2] || 'http://localhost:8765/';
const OUT = process.argv[3] || path.join(__dirname, 'screens');
const CHROME = process.env.CHROME || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ executablePath: fs.existsSync(CHROME) ? CHROME : undefined, args: ['--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 1360, height: 900 } });
  const errors = [];
  page.on('pageerror', e => errors.push('pageerror ' + e.message));
  page.on('console', m => { if (m.type() === 'error' && !/fonts\.g/.test(m.text())) errors.push('console ' + m.text()); });
  page.on('requestfailed', r => { if (!/fonts\.g/.test(r.url())) errors.push('requestfailed ' + r.url()); });
  const t0 = Date.now();
  await page.goto(URL + '?v=' + Date.now(), { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.__hegel && window.__hegel.day(), null, { timeout: 30000 });
  console.log('ready after', Date.now() - t0, 'ms');
  console.log('MISSING', JSON.stringify(await page.evaluate(() => window.__hegel.MISSING)));
  const canvas = page.locator('#map');
  const shot = async (name, wait = 1800) => { await page.waitForTimeout(wait); await canvas.screenshot({ path: path.join(OUT, name + '.png') }); console.log('saved', name); };
  await page.evaluate(() => { window.__hegel.setZoom(2); });
  const at = async (name, minute, centre) => {
    await page.evaluate(([m, c]) => { const H = window.__hegel; H.setTown(false); H.setMinute(m); if (c) H.center(c[0], c[1]); }, [minute, centre]);
    await shot(name);
  };
  await at('home', 6 * 60 + 10);
  await at('lodhi', 7 * 60 + 40);
  await at('gandhi', 11 * 60 + 30);
  await at('khan', 13 * 60);
  await at('gym', 17 * 60 + 30, [41, 56]);       // he is inside the club then: look at the club house and the courts
  await page.evaluate(() => window.__hegel.setMinute(12 * 60));
  await page.click('.menu [data-tab=places]');
  await page.click('[data-show=safdarjung]');
  await shot('safdarjung');
  await page.click('#btnFind');
  await page.evaluate(() => { window.__hegel.setMinute(7 * 60 + 5); window.__hegel.setTown(true); });
  await shot('town', 600);
  console.log('errors', JSON.stringify(errors));
  await browser.close();
})();
