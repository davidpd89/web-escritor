import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { chromium } from 'playwright';

const ROOT = process.cwd();
const PAGE_PATH = 'las-manecillas-del-recuerdo/fragmentos/index.html';
const JS_PATH = 'assets/v1-fragments.js';
const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const OUT = process.env.QA_OUT || 'qa-artifacts';
const BASE_SHA = process.env.BASE_SHA || process.env.PR_BASE_SHA;

assert(BASE_SHA, 'BASE_SHA/PR_BASE_SHA es obligatorio para verificar preservación literaria');
fs.mkdirSync(path.join(ROOT, OUT), { recursive: true });

const currentHtml = fs.readFileSync(path.join(ROOT, PAGE_PATH), 'utf8');
const baseHtml = execFileSync('git', ['show', `${BASE_SHA}:${PAGE_PATH}`], { encoding: 'utf8' });
const navJs = fs.readFileSync(path.join(ROOT, JS_PATH), 'utf8');

const sha = value => crypto.createHash('sha256').update(value).digest('hex');
const excerptPattern = /<div class="excerpt-field" data-nosnippet>([\s\S]*?)\n\s*<\/div>/g;
const excerpts = html => [...html.matchAll(excerptPattern)].map(match => match[1]);
const beforeExcerpts = excerpts(baseHtml);
const afterExcerpts = excerpts(currentHtml);

assert.equal(beforeExcerpts.length, 3, 'base: deben existir exactamente 3 .excerpt-field');
assert.equal(afterExcerpts.length, 3, 'after: deben existir exactamente 3 .excerpt-field');
assert.deepEqual(afterExcerpts, beforeExcerpts, 'el contenido literario de .excerpt-field cambió');

const excerptHashes = beforeExcerpts.map(sha);
assert.deepEqual(excerptHashes, afterExcerpts.map(sha), 'los hashes literarios before/after no coinciden');

const fragmentIds = [...currentHtml.matchAll(/<section class="book-section excerpt-section" id="(fragmento-[123])"/g)].map(m => m[1]);
assert.deepEqual(fragmentIds, ['fragmento-1', 'fragmento-2', 'fragmento-3'], 'los tres IDs canónicos deben conservarse y ser únicos');

const indexBlock = currentHtml.match(/<nav class="fragment-index"[\s\S]*?<\/nav>/)?.[0] || '';
const indexHrefs = [...indexBlock.matchAll(/href="(#[^"]+)"/g)].map(m => m[1]);
assert.deepEqual(indexHrefs, ['#fragmento-1', '#fragmento-2', '#fragmento-3'], 'el índice debe enlazar exactamente a los tres fragmentos');
for (const id of fragmentIds) assert(currentHtml.includes(`id="${id}"`), `target inexistente: #${id}`);

const sectionBlock = id => {
  const start = currentHtml.indexOf(`<section class="book-section excerpt-section" id="${id}"`);
  assert(start >= 0, `no existe ${id}`);
  const end = currentHtml.indexOf('</section>', start);
  assert(end >= 0, `no cierra ${id}`);
  return currentHtml.slice(start, end + '</section>'.length);
};
const pagerHrefs = id => [...sectionBlock(id).matchAll(/class="fragment-pager__link[^"]*" href="([^"]+)"/g)].map(m => m[1]);
assert.deepEqual(pagerHrefs('fragmento-1'), ['#fragmento-2']);
assert.deepEqual(pagerHrefs('fragmento-2'), ['#fragmento-1', '#fragmento-3']);
assert.deepEqual(pagerHrefs('fragmento-3'), ['#fragmento-2', '#cta-final']);
assert(currentHtml.includes('id="cta-final"'), 'falta CTA final existente');

assert(!/tabindex\s*=\s*["']?[1-9]/i.test(currentHtml), 'no se permite tabindex positivo');
assert(!/\bfetch\s*\(/.test(navJs), 'v1-fragments.js no debe hacer fetch');
assert(!/history\.(pushState|replaceState)/.test(navJs), 'no se debe implementar router/historial JS');
assert(!/aria-current/.test(indexBlock), 'el índice no debe usar aria-current');

const protectedParts = html => ({
  title: html.match(/<title>[\s\S]*?<\/title>/)?.[0],
  description: html.match(/<meta name="description"[^>]*>/)?.[0],
  canonical: html.match(/<link rel="canonical"[^>]*>/)?.[0],
  og: [...html.matchAll(/<meta property="og:[^>]+>/g)].map(m => m[0]),
  twitter: [...html.matchAll(/<meta name="twitter:[^>]+>/g)].map(m => m[0]),
  jsonld: html.match(/<script type="application\/ld\+json">[\s\S]*?<\/script>/)?.[0]
});
assert.deepEqual(protectedParts(currentHtml), protectedParts(baseHtml), 'SEO/schema protegido cambió');
assert(currentHtml.includes('<body data-reading-progress>'), 'debe conservar body[data-reading-progress]');

const pageErrors = [];
const report = { excerptHashes, viewports: {}, deepLinks: {}, noJs: {}, accessibility: {}, currentState: {}, readingProgress: {} };

function watchErrors(page, label) {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  pageErrors.push([label, errors]);
  return errors;
}

async function settle(page) {
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
}

async function assertNoOverflow(page, label) {
  const metrics = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth
  }));
  assert(metrics.scrollWidth <= metrics.clientWidth + 1, `${label}: overflow horizontal ${metrics.scrollWidth}/${metrics.clientWidth}`);
}

async function assertTargetBelowHeader(page, id, label) {
  const values = await page.evaluate(targetId => {
    const target = document.getElementById(targetId);
    const heading = target?.querySelector('h2') || target;
    const header = document.querySelector('[data-header]');
    return {
      top: heading?.getBoundingClientRect().top ?? -1,
      headerBottom: header?.getBoundingClientRect().bottom ?? 0
    };
  }, id);
  assert(values.top >= values.headerBottom - 1, `${label}: heading queda bajo header sticky (${values.top} < ${values.headerBottom})`);
}

const browser = await chromium.launch({ headless: true });
try {
  for (const viewport of [
    { width: 320, height: 900 },
    { width: 390, height: 900 },
    { width: 768, height: 1000 },
    { width: 1440, height: 900 }
  ]) {
    const context = await browser.newContext({ viewport });
    const page = await context.newPage();
    const errors = watchErrors(page, `viewport-${viewport.width}`);
    await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/fragmentos/`, { waitUntil: 'load' });
    await settle(page);
    await assertNoOverflow(page, `viewport ${viewport.width}`);
    const indexLinks = page.locator('[data-fragment-index] a');
    assert.equal(await indexLinks.count(), 3, `${viewport.width}: índice incompleto`);
    for (let i = 0; i < 3; i++) {
      const box = await indexLinks.nth(i).boundingBox();
      assert(box && box.height >= 44, `${viewport.width}: target demasiado pequeño en índice`);
    }
    assert.equal(errors.length, 0, `${viewport.width}: pageerror: ${errors.join(' | ')}`);
    report.viewports[viewport.width] = { overflow: false, indexTargets: 3 };
    await context.close();
  }

  for (const id of fragmentIds) {
    const context = await browser.newContext({ viewport: { width: 390, height: 900 } });
    const page = await context.newPage();
    const errors = watchErrors(page, `deep-${id}`);
    await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/fragmentos/#${id}`, { waitUntil: 'load' });
    await settle(page);
    assert.equal(new URL(page.url()).hash, `#${id}`);
    await assertTargetBelowHeader(page, id, `deep link ${id}`);
    assert.equal(errors.length, 0, `${id}: pageerror`);
    report.deepLinks[id] = true;
    await context.close();
  }

  {
    const context = await browser.newContext({ viewport: { width: 390, height: 900 } });
    const page = await context.newPage();
    const errors = watchErrors(page, 'history');
    await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/fragmentos/`, { waitUntil: 'load' });
    await page.locator('[data-fragment-link="fragmento-2"]').click();
    assert.equal(new URL(page.url()).hash, '#fragmento-2');
    await page.locator('[data-fragment-link="fragmento-3"]').click();
    assert.equal(new URL(page.url()).hash, '#fragmento-3');
    await page.goBack();
    assert.equal(new URL(page.url()).hash, '#fragmento-2');
    await page.goForward();
    assert.equal(new URL(page.url()).hash, '#fragmento-3');
    assert.equal(errors.length, 0, `history: pageerror ${errors.join(' | ')}`);
    report.deepLinks.backForward = true;
    await context.close();
  }

  {
    const context = await browser.newContext({ viewport: { width: 390, height: 900 }, javaScriptEnabled: false });
    const page = await context.newPage();
    await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/fragmentos/#fragmento-2`, { waitUntil: 'load' });
    await settle(page);
    assert.equal(await page.locator('.excerpt-section').count(), 3);
    for (const id of fragmentIds) assert(await page.locator(`#${id}`).isVisible(), `no-JS: ${id} no visible`);
    assert.equal(await page.locator('[data-fragment-index] a').count(), 3);
    assert.equal(await page.locator('.fragment-pager__link').count(), 5);
    assert(await page.locator('#cta-final').isVisible(), 'no-JS: CTA final no visible');
    await assertTargetBelowHeader(page, 'fragmento-2', 'no-JS deep link fragmento-2');
    await page.locator('[data-fragment-link="fragmento-3"]').click();
    assert.equal(new URL(page.url()).hash, '#fragmento-3');
    await settle(page);
    await assertTargetBelowHeader(page, 'fragmento-3', 'no-JS anchor fragmento-3');
    await assertNoOverflow(page, 'no-JS 390');
    report.noJs = { index: true, anchors: true, pager: true, fragments: 3, cta: true };
    await context.close();
  }

  {
    const context = await browser.newContext({ viewport: { width: 390, height: 900 } });
    const page = await context.newPage();
    const errors = watchErrors(page, 'a11y');
    await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/fragmentos/`, { waitUntil: 'load' });
    const first = page.locator('[data-fragment-link="fragmento-1"]');
    await first.focus();
    await page.keyboard.press('Shift+Tab');
    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(() => document.activeElement?.getAttribute('data-fragment-link')), 'fragmento-1', 'Tab/Shift+Tab no vuelve al enlace del índice');
    const focus = await first.evaluate(el => {
      const s = getComputedStyle(el);
      return { style: s.outlineStyle, width: parseFloat(s.outlineWidth) || 0 };
    });
    assert(focus.style !== 'none' && focus.width >= 2, 'focus-visible insuficiente');
    assert.equal(errors.length, 0, `a11y: pageerror ${errors.join(' | ')}`);
    report.accessibility.keyboard = true;
    report.accessibility.focusVisible = focus;

    const cdp = await context.newCDPSession(page);
    await cdp.send('Emulation.setPageScaleFactor', { pageScaleFactor: 2 });
    await settle(page);
    assert(await page.locator('[data-fragment-index]').isVisible(), 'zoom 200%: índice no visible');
    await assertNoOverflow(page, 'zoom 200%');
    report.accessibility.zoom200 = true;
    await cdp.send('Emulation.setPageScaleFactor', { pageScaleFactor: 1 });

    await page.addStyleTag({ content: `html *{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important} p{margin-bottom:2em!important}` });
    await settle(page);
    await assertNoOverflow(page, 'text spacing');
    report.accessibility.textSpacing = true;
    await context.close();
  }

  {
    const context = await browser.newContext({ viewport: { width: 390, height: 900 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/fragmentos/`, { waitUntil: 'load' });
    const motion = await page.locator('[data-fragment-link="fragmento-1"]').evaluate(el => {
      const s = getComputedStyle(el);
      return { animationName: s.animationName, transitionDuration: s.transitionDuration };
    });
    assert.equal(motion.animationName, 'none');
    report.accessibility.reducedMotion = motion;
    await context.close();
  }

  {
    const context = await browser.newContext({ viewport: { width: 390, height: 900 } });
    const page = await context.newPage();
    const errors = watchErrors(page, 'current-state');
    await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/fragmentos/`, { waitUntil: 'load' });
    await page.locator('#fragmento-2').scrollIntoViewIfNeeded();
    await page.waitForFunction(() => document.querySelector('[data-fragment-link="fragmento-2"]')?.dataset.current === 'true');
    assert.equal(await page.locator('[data-fragment-link][data-current="true"]').count(), 1, 'debe existir un único fragmento actual');
    assert.match(await page.locator('[data-fragment-link="fragmento-2"] [data-current-label]').textContent(), /Fragmento actual/);
    assert.equal(errors.length, 0, `current-state: pageerror ${errors.join(' | ')}`);
    report.currentState = { fragmento2: true, unique: true };
    assert(await page.locator('body').getAttribute('data-reading-progress') !== null, 'reading progress attribute desapareció');
    await page.evaluate(() => scrollTo(0, document.documentElement.scrollHeight));
    await settle(page);
    assert.equal(errors.length, 0, `reading progress: pageerror ${errors.join(' | ')}`);
    report.readingProgress = { preserved: true, compatibleWithNavigation: true };
    await context.close();
  }

  const shots = [
    { width: 1440, height: 900, target: '[data-fragment-index]', file: 'manecillas-fragments-index-1440.png' },
    { width: 390, height: 900, target: '[data-fragment-index]', file: 'manecillas-fragments-index-390.png' },
    { width: 390, height: 900, target: '#fragmento-2', file: 'manecillas-fragmento-2-390.png' },
    { width: 1440, height: 900, target: '#fragmento-2', file: 'manecillas-fragmento-2-1440.png' }
  ];
  for (const shot of shots) {
    const context = await browser.newContext({ viewport: { width: shot.width, height: shot.height } });
    const page = await context.newPage();
    await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/fragmentos/`, { waitUntil: 'load' });
    await page.locator(shot.target).scrollIntoViewIfNeeded();
    await settle(page);
    await page.screenshot({ path: path.join(ROOT, OUT, shot.file), fullPage: false });
    await context.close();
  }
} finally {
  await browser.close();
}

for (const [label, errors] of pageErrors) assert.equal(errors.length, 0, `${label}: pageerror ${errors.join(' | ')}`);
fs.writeFileSync(path.join(ROOT, OUT, 'manecillas-fragments-nav-report.json'), JSON.stringify(report, null, 2));
console.log('MANECILLAS FRAGMENTS NAV QA: PASS');
console.log('LITERARY SHA256:', excerptHashes.join(' '));
