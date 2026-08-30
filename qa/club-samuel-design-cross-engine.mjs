import assert from 'node:assert/strict';
import { chromium, firefox, webkit } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const engines = { chromium, firefox, webkit };
const BLUE = 'rgb(29, 79, 150)';
const GOLD = 'rgb(184, 134, 11)';
const PALE = 'rgb(238, 250, 255)';

for (const [name, launcher] of Object.entries(engines)) {
  const browser = await launcher.launch({ headless: true });
  try {
    const context = await browser.newContext({ viewport: { width: 1280, height: 850 }, reducedMotion: 'reduce' });
    await context.addInitScript(() => {
      try { localStorage.setItem('nl-popup-ts', String(Date.now())); } catch {}
    });
    const page = await context.newPage();

    let response = await page.goto(`${ORIGIN}/clubes-de-lectura/samuel-entre-mundos/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
    assert.equal(response?.ok(), true, `${name}: Club Samuel no carga`);
    await page.evaluate(() => document.fonts?.ready);

    assert.equal(await page.locator('html').getAttribute('data-editorial-context'), 'samuel', `${name}: contexto Samuel incorrecto`);
    assert.equal(await page.locator('main').getAttribute('data-family'), 'lore', `${name}: familia Club incorrecta`);
    assert.equal(await page.locator('html').evaluate(el => getComputedStyle(el).getPropertyValue('--club-blue').trim()), '#1d4f96', `${name}: scope Club no aplicado`);
    assert.equal(await page.locator('.tool-hero h1').evaluate(el => getComputedStyle(el).color), BLUE, `${name}: H1 Club no azul`);
    assert.equal(await page.locator('.tool-hero>.eyebrow').evaluate(el => getComputedStyle(el).color), GOLD, `${name}: apertura Club no dorada`);
    assert.equal(await page.locator('.section-context [aria-current="page"]').evaluate(el => getComputedStyle(el).backgroundColor), PALE, `${name}: contexto activo no pálido`);

    const quickCols = (await page.locator('#guia-rapida>.id-cards').evaluate(el => getComputedStyle(el).gridTemplateColumns)).split(' ').filter(Boolean).length;
    assert.equal(quickCols, 3, `${name}: briefing desktop no tiene tres columnas`);
    const factCols = (await page.locator('#ficha>.fact-list').evaluate(el => getComputedStyle(el).gridTemplateColumns)).split(' ').filter(Boolean).length;
    assert.equal(factCols, 2, `${name}: ficha desktop no tiene dos columnas`);
    assert.equal(await page.locator('#guia details').count(), 10, `${name}: preguntas Club no son 10`);

    const first = page.locator('#guia details').first();
    await first.locator('summary').click();
    assert.equal(await first.getAttribute('open'), '', `${name}: details no abre`);
    const open = await first.evaluate(el => ({ bg: getComputedStyle(el).backgroundImage, shadow: getComputedStyle(el).boxShadow }));
    assert.match(open.bg, /linear-gradient/, `${name}: pregunta abierta sin fondo`);
    assert.match(open.shadow, /rgb\(29, 79, 150\)/, `${name}: pregunta abierta sin rail azul`);

    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(100);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    assert.ok(overflow <= 1, `${name}: overflow móvil ${overflow}px`);
    const mobileQuick = (await page.locator('#guia-rapida>.id-cards').evaluate(el => getComputedStyle(el).gridTemplateColumns)).split(' ').filter(Boolean).length;
    const mobileFacts = (await page.locator('#ficha>.fact-list').evaluate(el => getComputedStyle(el).gridTemplateColumns)).split(' ').filter(Boolean).length;
    assert.equal(mobileQuick, 1, `${name}: briefing móvil no apila`);
    assert.equal(mobileFacts, 1, `${name}: ficha móvil no apila`);

    response = await page.goto(`${ORIGIN}/clubes-de-lectura/samuel-entre-mundos/guia-imprimible/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
    assert.equal(response?.ok(), true, `${name}: guía imprimible no carga`);
    assert.equal(await page.locator('html').evaluate(el => getComputedStyle(el).getPropertyValue('--club-blue').trim()), '', `${name}: scope visual Club se filtra a guía imprimible`);
    assert.equal((await page.locator('html').getAttribute('class')) || '', '', `${name}: guía imprimible adquiere clase v1 inesperada`);

    await context.close();
    console.log(`ok [${name}] Club Samuel design`);
  } finally {
    await browser.close();
  }
}

console.log('club-samuel-design-cross-engine: PASS');
