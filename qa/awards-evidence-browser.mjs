import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const BASE = process.env.IDENTITY_BASE_URL || 'http://127.0.0.1:4173';
const OUT = process.env.IDENTITY_ARTIFACT_DIR || 'artifacts/identity-public';
const route = '/premios.html';
const viewports = [
  { name: '320x900', width: 320, height: 900 },
  { name: '390x900', width: 390, height: 900 },
  { name: '768x1000', width: 768, height: 1000 },
  { name: '1440x900', width: 1440, height: 900 },
];

const failures = [];
const metrics = [];
const check = (value, message) => { if (!value) failures.push(message); };

await fs.mkdir(OUT, { recursive: true });
const browser = await chromium.launch({ headless: true });

async function contextFor(width, height, extra = {}) {
  return browser.newContext({ viewport: { width, height }, reducedMotion: 'reduce', ...extra });
}

async function openChecked(context) {
  const page = await context.newPage();
  const errors = [];
  const brokenLocal = [];
  page.on('pageerror', (error) => errors.push(`pageerror: ${error.message}`));
  page.on('console', (message) => { if (message.type() === 'error') errors.push(`console: ${message.text()}`); });
  page.on('response', (response) => {
    const url = new URL(response.url());
    if (url.origin === new URL(BASE).origin && response.status() >= 400) brokenLocal.push(`${response.status()} ${url.pathname}`);
  });
  const response = await page.goto(BASE + route, { waitUntil: 'load' });
  check(response && response.ok(), `${route}: HTTP ${response?.status() ?? 'no response'}`);
  await page.waitForTimeout(200);
  return { page, errors, brokenLocal };
}

for (const viewport of viewports) {
  const context = await contextFor(viewport.width, viewport.height);
  const { page, errors, brokenLocal } = await openChecked(context);
  const state = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    h1: document.querySelectorAll('h1').length,
    recognitions: document.querySelectorAll('[data-award-record]').length,
    mainText: document.querySelector('main')?.innerText.trim().length || 0,
  }));
  check(state.scrollWidth <= state.clientWidth + 1, `${route} @ ${viewport.name}: horizontal overflow ${state.scrollWidth}/${state.clientWidth}`);
  check(state.h1 === 1, `${route} @ ${viewport.name}: expected one H1, got ${state.h1}`);
  check(state.recognitions === 2, `${route} @ ${viewport.name}: expected two recognition records, got ${state.recognitions}`);
  check(state.mainText > 1000, `${route} @ ${viewport.name}: content unexpectedly short`);
  check(errors.length === 0, `${route} @ ${viewport.name}: ${errors.join(' | ')}`);
  check(brokenLocal.length === 0, `${route} @ ${viewport.name}: broken local assets ${[...new Set(brokenLocal)].join(', ')}`);
  metrics.push({ viewport: viewport.name, overflow: state.scrollWidth - state.clientWidth });
  await context.close();
}

// External evidence links are secure, explicit and keyboard reachable. No request
// to the external origin is made here: CI must not depend on third-party uptime.
{
  const context = await contextFor(390, 900);
  const { page } = await openChecked(context);
  const links = await page.locator('[data-award-source]').evaluateAll((nodes) => nodes.map((node) => ({
    href: node.getAttribute('href') || '',
    target: node.getAttribute('target') || '',
    rel: node.getAttribute('rel') || '',
  })));
  check(links.length >= 3, `awards sources: expected at least 3 evidence links, got ${links.length}`);
  for (const link of links) {
    const rel = new Set(link.rel.split(/\s+/).filter(Boolean));
    check(link.href.startsWith('https://'), `awards source is not HTTPS: ${link.href}`);
    check(link.target === '_blank', `awards source does not open explicitly in a new tab: ${link.href}`);
    check(rel.has('noopener') && rel.has('noreferrer'), `awards source lacks safe rel: ${link.href}`);
  }

  let reachedSource = false;
  for (let i = 0; i < 40; i += 1) {
    await page.keyboard.press('Tab');
    reachedSource = await page.evaluate(() => document.activeElement?.hasAttribute('data-award-source') || false);
    if (reachedSource) break;
  }
  check(reachedSource, 'keyboard: no award source link reached by Tab');
  if (reachedSource) {
    const focusState = await page.evaluate(() => {
      const style = getComputedStyle(document.activeElement);
      return { outlineStyle: style.outlineStyle, outlineWidth: style.outlineWidth };
    });
    check(focusState.outlineStyle !== 'none' && focusState.outlineWidth !== '0px', `focus-visible: source link lacks visible outline (${focusState.outlineStyle} ${focusState.outlineWidth})`);
  }
  await context.close();
}

// 200% text zoom must reflow without horizontal scrolling.
{
  const context = await contextFor(390, 900);
  const { page } = await openChecked(context);
  await page.addStyleTag({ content: 'html{font-size:200% !important}' });
  await page.waitForTimeout(100);
  const state = await page.evaluate(() => ({
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    recognitionText: document.querySelector('#reconocimientos')?.innerText.length || 0,
  }));
  check(state.overflow <= 1, `200% text zoom: horizontal overflow ${state.overflow}`);
  check(state.recognitionText > 500, '200% text zoom: recognition content lost');
  await context.close();
}

// WCAG 1.4.12 text-spacing fixture. Keep offender geometry in the failure so a
// future regression identifies the responsible node instead of inviting CSS guesses.
{
  const context = await contextFor(390, 900);
  const { page } = await openChecked(context);
  await page.addStyleTag({ content: '*{line-height:1.5 !important;letter-spacing:.12em !important;word-spacing:.16em !important} p{margin-bottom:2em !important}' });
  const state = await page.evaluate(() => {
    const viewportWidth = document.documentElement.clientWidth;
    const offenders = [...document.body.querySelectorAll('*')]
      .map((el) => {
        const rect = el.getBoundingClientRect();
        const style = getComputedStyle(el);
        return {
          tag: el.tagName.toLowerCase(),
          id: el.id || '',
          className: typeof el.className === 'string' ? el.className : '',
          text: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 80),
          left: Math.round(rect.left * 10) / 10,
          right: Math.round(rect.right * 10) / 10,
          width: Math.round(rect.width * 10) / 10,
          scrollWidth: el.scrollWidth,
          clientWidth: el.clientWidth,
          display: style.display,
          overflowX: style.overflowX,
        };
      })
      .filter((item) => item.display !== 'none' && (item.right > viewportWidth + 1 || item.left < -1 || item.scrollWidth > item.clientWidth + 1))
      .sort((a, b) => Math.max(b.right - viewportWidth, b.scrollWidth - b.clientWidth) - Math.max(a.right - viewportWidth, a.scrollWidth - a.clientWidth))
      .slice(0, 12);
    return {
      overflow: document.documentElement.scrollWidth - viewportWidth,
      offenders,
    };
  });
  const detail = state.offenders.length ? `; offenders=${JSON.stringify(state.offenders)}` : '';
  check(state.overflow <= 1, `text spacing: horizontal overflow ${state.overflow}${detail}`);
  await context.close();
}

// No-JS: public evidence remains readable and does not overflow.
{
  const context = await browser.newContext({ viewport: { width: 390, height: 900 }, javaScriptEnabled: false });
  const page = await context.newPage();
  const response = await page.goto(BASE + route, { waitUntil: 'load' });
  check(response && response.ok(), 'no-JS: premios.html HTTP failure');
  const state = await page.evaluate(() => ({
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    recognition: document.querySelector('#reconocimientos')?.innerText.length || 0,
    trajectory: document.querySelector('#colaboraciones')?.innerText.length || 0,
    reception: document.querySelector('#recepcion')?.innerText.length || 0,
  }));
  check(state.overflow <= 1, `no-JS: horizontal overflow ${state.overflow}`);
  check(state.recognition > 500 && state.trajectory > 300 && state.reception > 100, 'no-JS: public award/trajectory/reception content unavailable');
  await context.close();
}

async function capture(width, height, suffix) {
  const context = await contextFor(width, height);
  const { page } = await openChecked(context);
  await page.locator('#reconocimientos').screenshot({ path: path.join(OUT, `premios-reconocimientos-${suffix}.png`) });

  // Produce a focused documentary capture without page-coordinate clipping:
  // hide unrelated regions only in this Playwright page, then screenshot the
  // resulting full page. Published HTML/CSS is untouched.
  await page.addStyleTag({ content: `
    body > .skip-link,
    body > .site-header,
    body > .explore-dialog,
    main > :not(#colaboraciones):not(#recepcion),
    body > .site-footer { display:none !important; }
    html, body { min-height:0 !important; }
  ` });
  await page.screenshot({ path: path.join(OUT, `premios-trayectoria-recepcion-${suffix}.png`), fullPage: true });
  await context.close();
}

await capture(1440, 900, '1440');
await capture(390, 900, '390');

await fs.writeFile(path.join(OUT, 'awards-browser-metrics.json'), JSON.stringify({ metrics, failures }, null, 2));
await browser.close();

if (failures.length) {
  console.error('\nAwards evidence browser QA failed:');
  for (const message of failures) console.error(`- ${message}`);
  process.exit(1);
}
console.log(`Awards evidence browser QA PASS (${viewports.length} required viewports + keyboard/zoom/text-spacing/no-JS).`);
