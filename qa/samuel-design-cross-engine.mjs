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
    const page = await browser.newPage({ viewport: { width: 1280, height: 850 } });
    let response = await page.goto(`${ORIGIN}/libros/samuel-entre-mundos/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
    assert.equal(response?.ok(), true, `${name}: Samuel no carga`);
    await page.evaluate(() => document.fonts?.ready);

    assert.equal(await page.locator('html').getAttribute('data-editorial-context'), 'samuel', `${name}: contexto Samuel incorrecto`);
    assert.equal(await page.locator('main').getAttribute('data-family'), 'book-samuel', `${name}: familia Samuel incorrecta`);
    const token = await page.locator('body').evaluate(el => getComputedStyle(el).getPropertyValue('--sam-blue').trim());
    assert.equal(token, '#1d4f96', `${name}: capa visual Samuel no aplicada`);

    const h1 = await page.locator('#samuel-title').evaluate(el => getComputedStyle(el).color);
    assert.equal(h1, BLUE, `${name}: H1 fuera del azul`);
    const opening = await page.locator('.samuel-threshold__copy>.eyebrow').evaluate(el => ({ family: getComputedStyle(el).fontFamily, color: getComputedStyle(el).color }));
    assert.match(opening.family.toLowerCase(), /yellowtail/, `${name}: apertura sin Yellowtail`);
    assert.equal(opening.color, GOLD, `${name}: apertura fuera del dorado`);

    const cover = page.locator('.samuel-object');
    const brackets = await cover.evaluate(el => ({
      before: getComputedStyle(el, '::before').backgroundImage,
      after: getComputedStyle(el, '::after').backgroundImage,
    }));
    assert.match(brackets.before, /corner-bracket-blue-gold\.svg/, `${name}: falta bracket superior`);
    assert.match(brackets.after, /corner-bracket-blue-gold\.svg/, `${name}: falta bracket inferior`);

    const rail = await page.locator('.samuel-threshold').evaluate(el => ({
      width: getComputedStyle(el, '::before').width,
      color: getComputedStyle(el, '::before').backgroundColor,
    }));
    assert.equal(rail.width, '2.5px', `${name}: rail hero no es 2.5px`);
    assert.equal(rail.color, BLUE, `${name}: rail hero no es azul`);

    const firstHead = page.locator('.samuel-section__head').first();
    const head = await firstHead.evaluate(el => ({
      h2: getComputedStyle(el.querySelector('h2')).color,
      eyebrow: getComputedStyle(el.querySelector('.eyebrow')).color,
      family: getComputedStyle(el.querySelector('.eyebrow')).fontFamily,
    }));
    assert.equal(head.h2, BLUE, `${name}: H2 de registro no azul`);
    assert.equal(head.eyebrow, GOLD, `${name}: apertura de registro no dorada`);
    assert.match(head.family.toLowerCase(), /yellowtail/, `${name}: apertura de registro sin Yellowtail`);

    const quiz = await page.locator('#samuel-quiz-app').evaluate(el => ({
      bg: getComputedStyle(el).backgroundColor,
      top: getComputedStyle(el).borderTopColor,
      bottom: getComputedStyle(el).borderBottomColor,
    }));
    assert.equal(quiz.bg, PALE, `${name}: quiz sin azul pálido`);
    assert.equal(quiz.top, BLUE, `${name}: quiz sin borde azul`);
    assert.equal(quiz.bottom, GOLD, `${name}: quiz sin dorado`);

    const trigger = page.locator('.samuel-actions [data-buy-modal]').first();
    await trigger.click();
    const dialog = page.locator('#buy-dialog');
    await dialog.waitFor({ state: 'visible', timeout: 4000 });
    await page.waitForFunction(() => getComputedStyle(document.querySelector('#buy-dialog')).borderTopColor === 'rgb(29, 79, 150)');
    const modal = await dialog.evaluate(el => ({
      bg: getComputedStyle(el).backgroundColor,
      top: getComputedStyle(el).borderTopColor,
      bottom: getComputedStyle(el).borderBottomColor,
    }));
    assert.equal(modal.bg, 'rgb(255, 255, 255)', `${name}: modal conserva material legacy`);
    assert.equal(modal.top, BLUE, `${name}: modal sin azul`);
    assert.equal(modal.bottom, GOLD, `${name}: modal sin dorado`);
    await dialog.locator('.buy-dialog-close').click();

    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(100);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    assert.ok(overflow <= 1, `${name}: overflow móvil ${overflow}px`);
    const mobileRail = await page.locator('.samuel-threshold').evaluate(el => getComputedStyle(el, '::before').width);
    assert.equal(mobileRail, '2.5px', `${name}: rail móvil no es 2.5px`);

    console.log(`ok [${name}] Samuel design`);
  } finally {
    await browser.close();
  }
}

console.log('samuel-design-cross-engine: PASS');

// Superficies de la misma familia editorial. Cada una mantiene su contrato en
// un módulo propio y se ejecuta desde el smoke ya conectado al workflow.
await import('./samuel-fragmento-design-cross-engine.mjs');
await import('./noveris-design-cross-engine.mjs');
await import('./club-samuel-design-cross-engine.mjs');
