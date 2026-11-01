import { chromium, firefox, webkit, devices } from 'playwright';
// Mail chooser (footer «@ Escríbeme» + header envelope) on desktop, touch and keyboard.
// Usage: QA_ORIGIN=http://127.0.0.1:4173 node qa/mail-chooser-browser.mjs
const BASE = (process.argv[2] || process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/?$/, '/');
let fails = 0;
const ok = (cond, msg) => { console.log(`${cond ? 'PASS' : 'FAIL'} ${msg}`); if (!cond) fails++; };
const inViewport = (b, vw, vh) => b && b.x >= 0 && b.y >= 0 && b.x + b.width <= vw + 0.5 && b.y + b.height <= vh + 0.5;

async function page(browser, opts, path = '') {
  const ctx = await browser.newContext(opts);
  const p = await ctx.newPage();
  const errors = [];
  p.on('pageerror', e => errors.push(e.message));
  await p.goto(BASE + path, { waitUntil: 'load' });
  return { ctx, p, errors };
}

async function desktop(browserType, name, perms) {
  const b = await browserType.launch();
  const { ctx, p, errors } = await page(b, { viewport: { width: 1440, height: 900 }, permissions: perms });
  const tag = `[${name}${perms.length ? ' +perm' : ''}]`;
  // Footer «@ Escríbeme»
  await p.locator('.site-footer [data-email-reveal]').scrollIntoViewIfNeeded();
  await p.locator('.site-footer [data-email-reveal]').click();
  const panel = p.locator('.mail-chooser');
  ok(await panel.count() === 1, `${tag} footer opens chooser on first click`);
  const email = (await p.locator('.mail-chooser__address').textContent()).trim();
  ok(/^[^@\s]+@[^@\s]+\.[a-z]+$/.test(email), `${tag} chooser shows address`);
  ok(await p.evaluate(() => document.activeElement?.textContent) === 'Abrir en Gmail', `${tag} focus moves to first option`);
  const gmail = await p.locator('.mail-chooser a', { hasText: 'Gmail' }).getAttribute('href');
  ok(gmail.includes('view=cm') && gmail.includes(encodeURIComponent(email)), `${tag} Gmail compose href`);
  const outlook = await p.locator('.mail-chooser a', { hasText: 'Outlook' }).getAttribute('href');
  ok(outlook.includes('deeplink/compose') && outlook.includes(encodeURIComponent(email)), `${tag} Outlook compose href`);
  ok(inViewport(await panel.boundingBox(), 1440, 900), `${tag} footer panel inside viewport`);
  // Copy: first click must work
  const copy = p.locator('.mail-chooser button');
  await copy.click();
  await p.waitForTimeout(150);
  ok(await copy.textContent() === 'Dirección copiada ✓', `${tag} copy works on FIRST click (${await copy.textContent()})`);
  ok(await p.locator('.mail-chooser__status').textContent() === 'Dirección copiada al portapapeles', `${tag} live status announced`);
  if (perms.length && name === 'chromium') {
    ok(await p.evaluate(() => navigator.clipboard.readText()) === email, `${tag} clipboard contains the address`);
  }
  ok(await p.evaluate(() => getSelection().toString()) === '', `${tag} no stray selection after copy`);
  await copy.click();
  ok(await copy.textContent() === 'Dirección copiada ✓' && await panel.count() === 1, `${tag} repeated copy keeps working`);
  // Escape closes and restores focus to the opener
  await p.keyboard.press('Escape');
  ok(await panel.count() === 0, `${tag} Escape closes`);
  ok(await p.evaluate(() => document.activeElement?.matches('.site-footer a[href^="mailto:"]')), `${tag} focus back on footer link`);

  // Header envelope
  await p.evaluate(() => scrollTo(0, 0));
  const hc = p.locator('.header-contact').first();
  ok(await hc.isVisible(), `${tag} header envelope visible`);
  await hc.click();
  ok(await panel.count() === 1, `${tag} envelope opens chooser (no navigation)`);
  ok(!p.url().includes('prensa'), `${tag} stayed on page`);
  const hcLink = p.locator('a.header-contact[href^="mailto:"]');
  ok(await hcLink.count() === 1 && await hcLink.locator('svg').count() >= 1, `${tag} envelope keeps icon and class after reveal`);
  ok((await hcLink.textContent()).trim() === '', `${tag} envelope shows no address text`);
  const hb = await panel.boundingBox();
  ok(inViewport(hb, 1440, 900) && hb.y < 200, `${tag} envelope panel below header, inside viewport`);
  await hcLink.click();
  ok(await panel.count() === 0, `${tag} second click on envelope closes (toggle)`);
  await hcLink.click();
  ok(await panel.count() === 1, `${tag} third click reopens`);
  await p.locator('.mail-chooser button').click();
  await p.waitForTimeout(150);
  ok(await p.locator('.mail-chooser button').textContent() === 'Dirección copiada ✓', `${tag} envelope copy first click`);
  const spot = await p.evaluate(() => {
    for (let y = 10; y < 880; y += 20) for (let x = 20; x < 1420; x += 40) {
      const el = document.elementFromPoint(x, y);
      if (el && !el.closest('a,button,input,select,textarea,label,summary,.mail-chooser')) return { x, y };
    }
  });
  await p.mouse.click(spot.x, spot.y);
  ok(await panel.count() === 0, `${tag} click outside closes`);
  // Keyboard: Enter opens, Tab through, Tab out closes
  await hcLink.focus();
  await p.keyboard.press('Enter');
  ok(await panel.count() === 1, `${tag} Enter on envelope opens`);
  // Safari skips links on Tab by default, so tab until the button (max 3).
  for (let i = 0; i < 3 && await p.evaluate(() => document.activeElement?.textContent) !== 'Copiar dirección'; i++) await p.keyboard.press('Tab');
  ok(await p.evaluate(() => document.activeElement?.textContent) === 'Copiar dirección', `${tag} Tab reaches copy button`);
  await p.keyboard.press('Enter');
  await p.waitForTimeout(150);
  ok(await p.locator('.mail-chooser button').textContent() === 'Dirección copiada ✓', `${tag} keyboard copy works`);
  await p.keyboard.press('Tab');
  ok(await panel.count() === 0, `${tag} Tab out closes`);
  ok(await p.evaluate(() => document.activeElement?.matches('a.header-contact')), `${tag} Tab out returns focus to envelope`);
  await hcLink.focus();
  await p.keyboard.press('Enter');
  await p.keyboard.press('Shift+Tab');
  ok(await panel.count() === 0 && await p.evaluate(() => document.activeElement?.matches('a.header-contact')), `${tag} Shift+Tab out closes, focus on envelope`);
  // Other reveal links (press page style CTA with subject)
  ok(errors.length === 0, `${tag} no page errors ${errors.join(' | ')}`);
  await ctx.close();
  await b.close();
}

async function fallbacks() {
  const b = await chromium.launch();
  for (const mode of ['execFails-clipboardOk', 'bothFail']) {
    const { ctx, p } = await page(b, { viewport: { width: 1440, height: 900 }, permissions: ['clipboard-read', 'clipboard-write'] });
    await p.evaluate((m) => {
      document.execCommand = () => false;
      if (m === 'bothFail') navigator.clipboard.writeText = () => Promise.reject(new Error('denied'));
    }, mode);
    await p.locator('.site-footer [data-email-reveal]').click();
    const email = (await p.locator('.mail-chooser__address').textContent()).trim();
    const copy = p.locator('.mail-chooser button');
    await copy.click();
    await p.waitForTimeout(150);
    if (mode === 'bothFail') {
      ok(await copy.textContent() === 'Selecciónala y cópiala', `[fallback ${mode}] tells user to copy manually`);
      ok(await p.evaluate(() => getSelection().toString().trim()) === email, `[fallback ${mode}] address left selected`);
    } else {
      ok(await copy.textContent() === 'Dirección copiada ✓', `[fallback ${mode}] async clipboard used`);
      ok(await p.evaluate(() => navigator.clipboard.readText()) === email, `[fallback ${mode}] clipboard has address`);
    }
    await p.waitForTimeout(4200);
    ok(await copy.textContent() === 'Copiar dirección', `[fallback ${mode}] label resets after 4s`);
    await ctx.close();
  }
  await b.close();
}

async function outsideSpot(p) {
  return p.evaluate(() => {
    for (let y = 10; y < innerHeight - 10; y += 20) for (let x = 10; x < innerWidth - 10; x += 20) {
      const el = document.elementFromPoint(x, y);
      if (el && !el.closest('a,button,input,select,textarea,label,summary,.mail-chooser')) return { x, y };
    }
  });
}

async function mobile(browserType, name, device, extra = {}) {
  const b = await browserType.launch();
  const { ctx, p, errors } = await page(b, { ...device, ...extra });
  const tag = `[${name}]`;
  const vw = p.viewportSize().width, vh = p.viewportSize().height;
  const panel = p.locator('.mail-chooser');
  const copy = p.locator('.mail-chooser button');
  // Header envelope
  const hc = p.locator('.header-contact').first();
  ok(await hc.isVisible(), `${tag} header envelope visible on mobile`);
  await hc.tap();
  ok(await panel.count() === 1 && !p.url().includes('prensa'), `${tag} envelope tap opens chooser`);
  ok(inViewport(await panel.boundingBox(), vw, vh), `${tag} envelope panel inside viewport`);
  await copy.tap();
  await p.waitForTimeout(200);
  let label = await copy.textContent();
  ok(label === 'Dirección copiada ✓', `${tag} envelope first tap on copy (${label})`);
  await p.locator('a.header-contact[href^="mailto:"]').tap();
  ok(await panel.count() === 0, `${tag} tapping envelope again closes`);
  // Footer
  const t = p.locator('.site-footer [data-email-reveal], .site-footer a[href^="mailto:"]').first();
  await t.scrollIntoViewIfNeeded();
  await t.tap();
  ok(await panel.count() === 1, `${tag} footer tap opens chooser`);
  ok(inViewport(await panel.boundingBox(), vw, vh), `${tag} footer panel inside viewport`);
  await copy.tap();
  await p.waitForTimeout(200);
  label = await copy.textContent();
  ok(label === 'Dirección copiada ✓', `${tag} footer first tap on copy (${label})`);
  ok(await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${tag} no horizontal overflow`);
  const spot = await outsideSpot(p);
  await p.touchscreen.tap(spot.x, spot.y);
  await p.waitForTimeout(100);
  ok(await panel.count() === 0, `${tag} tap outside closes`);
  await p.locator('.site-footer a[href^="mailto:"]').tap();
  await p.evaluate(() => scrollBy(0, -40));
  await p.waitForTimeout(100);
  ok(await panel.count() === 1, `${tag} small scroll keeps it open`);
  ok(errors.length === 0, `${tag} no page errors ${errors.join(' | ')}`);
  await ctx.close();
  await b.close();
}

async function narrow() {
  const b = await chromium.launch();
  const { ctx, p } = await page(b, { viewport: { width: 320, height: 640 }, hasTouch: true, isMobile: true });
  await p.addStyleTag({ content: 'html{font-size:200%!important}' });
  const t = p.locator('.site-footer [data-email-reveal]');
  await t.scrollIntoViewIfNeeded();
  await t.tap();
  const bb = await p.locator('.mail-chooser').boundingBox();
  ok(bb && bb.x >= 0 && bb.x + bb.width <= 320.5, `[320px 200%] panel fits horizontally (${bb && Math.round(bb.x)}..${bb && Math.round(bb.x + bb.width)})`);
  ok(await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth), '[320px 200%] no horizontal overflow');
  await ctx.close();
  await b.close();
}

async function prensa() {
  const b = await chromium.launch();
  const { ctx, p, errors } = await page(b, { viewport: { width: 1280, height: 900 } }, 'prensa.html');
  const triggers = await p.locator('main [data-email-reveal]').count();
  if (triggers) {
    await p.locator('main [data-email-reveal]').first().scrollIntoViewIfNeeded();
    await p.locator('main [data-email-reveal]').first().click();
    ok(await p.locator('.mail-chooser').count() === 1, '[prensa] in-page reveal CTA opens chooser');
  }
  const hc = p.locator('.header-contact').first();
  await p.evaluate(() => scrollTo(0, 0));
  await p.keyboard.press('Escape');
  await hc.click();
  ok(await p.locator('.mail-chooser').count() === 1, '[prensa] envelope opens chooser');
  ok(errors.length === 0, `[prensa] no page errors ${errors.join(' | ')}`);
  await ctx.close();
  await b.close();
}

const has = async (bt) => { try { const x = await bt.launch(); await x.close(); return true; } catch { return false; } };
await desktop(chromium, 'chromium', ['clipboard-read', 'clipboard-write']);
await desktop(chromium, 'chromium', []);
await fallbacks();
await mobile(chromium, 'Pixel 7', devices['Pixel 7']);
await narrow();
await prensa();
if (await has(firefox)) await desktop(firefox, 'firefox', []); else console.log('SKIP firefox not installed');
if (await has(webkit)) { await desktop(webkit, 'webkit', []); await mobile(webkit, 'iPhone 13', devices['iPhone 13']); } else console.log('SKIP webkit not installed');
console.log(fails ? `\n${fails} FAILED` : '\nALL PASSED');
process.exit(fails ? 1 : 0);
