import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const OUT = process.env.QA_OUT || 'artifacts/sitewide-reflow';
fs.mkdirSync(OUT, { recursive: true });

const BLUE = 'rgb(29, 79, 150)';
const HEADER_BLUE = 'rgb(10, 77, 159)';
const GOLD = 'rgb(184, 134, 11)';
const PALE = 'rgb(238, 250, 255)';
const TRANSPARENT = 'rgba(0, 0, 0, 0)';
const STATE_SETTLE_MS = 260;

const viewports = [
  ['desktop-1440', 1440, 1000],
  ['desktop-1280', 1280, 800],
  ['tablet-1024', 1024, 768],
  ['guide-901', 901, 800],
  ['guide-900', 900, 800],
  ['tablet-768', 768, 1024],
  ['facts-761', 761, 900],
  ['facts-760', 760, 900],
  ['debate-641', 641, 900],
  ['debate-640', 640, 900],
  ['mobile-390', 390, 844],
  ['mobile-360', 360, 800],
];

async function css(locator, pseudo = null) {
  return locator.evaluate((el, p) => {
    const s = getComputedStyle(el, p || null);
    return {
      color: s.color,
      backgroundColor: s.backgroundColor,
      backgroundImage: s.backgroundImage,
      borderTopColor: s.borderTopColor,
      borderTopWidth: s.borderTopWidth,
      borderRightColor: s.borderRightColor,
      borderRightWidth: s.borderRightWidth,
      borderBottomColor: s.borderBottomColor,
      borderBottomWidth: s.borderBottomWidth,
      borderLeftColor: s.borderLeftColor,
      borderLeftWidth: s.borderLeftWidth,
      boxShadow: s.boxShadow,
      content: s.content,
      display: s.display,
      fontFamily: s.fontFamily,
      fontSize: s.fontSize,
      gridTemplateColumns: s.gridTemplateColumns,
      minHeight: s.minHeight,
      position: s.position,
    };
  }, pseudo);
}

const browser = await chromium.launch({ headless: true });
const failures = [];

try {
  for (const [name, width, height] of viewports) {
    const context = await browser.newContext({ viewport: { width, height }, reducedMotion: 'reduce' });
    await context.addInitScript(() => {
      try { localStorage.setItem('nl-popup-ts', String(Date.now())); } catch {}
    });
    const page = await context.newPage();
    try {
      const response = await page.goto(`${ORIGIN}/clubes-de-lectura/samuel-entre-mundos/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
      assert.ok(response?.ok(), `${name}: Club Samuel no carga`);
      await page.evaluate(() => document.fonts?.ready);

      assert.equal(await page.locator('html').getAttribute('data-editorial-context'), 'samuel', `${name}: contexto Samuel perdido`);
      assert.equal(await page.locator('main').getAttribute('data-family'), 'lore', `${name}: familia lore perdida`);
      assert.equal(await page.locator('link[rel="canonical"]').getAttribute('href'), 'https://davidportodiaz.com/clubes-de-lectura/samuel-entre-mundos/', `${name}: canonical alterado`);
      assert.equal(await page.locator('h1').count(), 1, `${name}: H1 no único`);
      assert.equal(await page.locator('.section-context [aria-current="page"]').getAttribute('href'), '/clubes-de-lectura/samuel-entre-mundos/', `${name}: contexto no marca Club de lectura`);

      const token = await page.locator('html').evaluate(el => getComputedStyle(el).getPropertyValue('--club-blue').trim());
      assert.equal(token, '#1d4f96', `${name}: capa visual Club no aplicada`);

      const currentContext = await css(page.locator('.section-context [aria-current="page"]'));
      assert.equal(currentContext.color, BLUE, `${name}: navegación contextual activa no azul`);
      assert.equal(currentContext.backgroundColor, PALE, `${name}: navegación contextual activa no pálida`);
      assert.match(currentContext.boxShadow, /rgb\(184, 134, 11\)/, `${name}: navegación contextual pierde cierre dorado`);

      if (name === 'desktop-1440' || name === 'mobile-390') {
        const headerSearch = page.locator('.header-search');
        await headerSearch.hover();
        await page.waitForTimeout(STATE_SETTLE_MS);
        const headerHover = await css(headerSearch);
        assert.equal(headerHover.color, HEADER_BLUE, `${name}: hover Asistente no usa azul especial de header`);
        assert.equal(headerHover.backgroundColor, PALE, `${name}: hover Asistente no usa superficie pálida`);
        await page.mouse.move(Math.max(1, width - 2), Math.max(1, height - 2));
      }

      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert.ok(overflow <= 1, `${name}: overflow horizontal ${overflow}px`);

      const heroOpening = await css(page.locator('.tool-hero > .eyebrow'));
      assert.equal(heroOpening.color, GOLD, `${name}: apertura hero no dorada`);
      assert.match(heroOpening.fontFamily.toLowerCase(), /yellowtail/, `${name}: apertura hero sin Yellowtail`);
      assert.ok(parseFloat(heroOpening.fontSize) >= 23, `${name}: apertura hero demasiado pequeña`);
      assert.match(heroOpening.backgroundImage, /highlight-8-blue-rect\.png/, `${name}: apertura hero sin highlight azul`);

      const heroTitle = await css(page.locator('.tool-hero h1'));
      assert.equal(heroTitle.color, BLUE, `${name}: H1 no azul`);
      assert.match((await css(page.locator('.tool-hero'))).backgroundImage, /linear-gradient/, `${name}: hero sin doble cierre`);

      const heroPrimary = await css(page.locator('.tool-hero .primary-action'));
      assert.equal(heroPrimary.color, BLUE, `${name}: CTA principal hero no azul`);
      assert.match(heroPrimary.fontFamily.toLowerCase(), /yellowtail/, `${name}: CTA hero sin Yellowtail`);
      assert.equal(heroPrimary.backgroundColor, TRANSPARENT, `${name}: CTA hero conserva botón negro`);
      assert.equal(heroPrimary.minHeight, '0px', `${name}: CTA hero conserva altura de botón genérico`);

      const sectionOpening = await css(page.locator('#guia-rapida > .eyebrow'));
      assert.equal(sectionOpening.color, GOLD, `${name}: apertura de sección no dorada`);
      assert.match(sectionOpening.fontFamily.toLowerCase(), /yellowtail/, `${name}: apertura de sección sin Yellowtail`);
      assert.equal((await css(page.locator('#guia-rapida > h2'))).color, BLUE, `${name}: H2 de sección no azul`);

      const quick = page.locator('#guia-rapida > .id-cards');
      const quickCols = (await css(quick)).gridTemplateColumns.split(' ').filter(Boolean).length;
      if (width > 900) assert.equal(quickCols, 3, `${name}: briefing rápido no usa tres registros`);
      else assert.equal(quickCols, 1, `${name}: briefing rápido no apila <=900`);
      const quickCard = quick.locator('.id-card').first();
      assert.equal((await css(quickCard)).borderTopWidth, '0px', `${name}: briefing vuelve a card boxed`);
      assert.equal((await css(quickCard.locator('h3'))).color, BLUE, `${name}: briefing H3 no azul`);
      assert.match((await css(quickCard, '::before')).content, /01/, `${name}: briefing pierde numeración editorial`);

      const sessionCols = (await css(page.locator('#guia-rapida .tool-two-col'))).gridTemplateColumns.split(' ').filter(Boolean).length;
      if (width > 767) assert.equal(sessionCols, 2, `${name}: plan de sesión no conserva pareja de dossiers`);
      else assert.equal(sessionCols, 1, `${name}: plan de sesión no apila <=767`);

      const facts = page.locator('#ficha > .fact-list');
      const factCols = (await css(facts)).gridTemplateColumns.split(' ').filter(Boolean).length;
      if (width > 760) assert.equal(factCols, 2, `${name}: ficha coordinador no usa ledger doble`);
      else assert.equal(factCols, 1, `${name}: ficha coordinador no apila <=760`);
      assert.equal((await css(facts.locator('li strong').first())).color, 'rgb(111, 106, 100)', `${name}: labels de ficha pierden neutral documental`);

      const faq = page.locator('#guia .identity-faq');
      assert.equal(await faq.locator('details').count(), 10, `${name}: guía ya no contiene 10 preguntas`);
      assert.equal((await css(faq)).borderTopColor, BLUE, `${name}: debate sin regla azul`);
      assert.equal((await css(faq)).borderBottomColor, GOLD, `${name}: debate sin cierre dorado`);
      const firstDetail = faq.locator('details').first();
      const firstSummary = firstDetail.locator('summary');
      assert.equal((await css(firstSummary)).color, BLUE, `${name}: pregunta no azul`);
      assert.match((await css(firstSummary, '::before')).content, /01/, `${name}: pregunta pierde índice 01`);
      await firstSummary.click();
      assert.equal(await firstDetail.getAttribute('open'), '', `${name}: primera pregunta no abre`);
      await page.waitForTimeout(STATE_SETTLE_MS);
      const openState = await css(firstDetail);
      assert.match(openState.backgroundImage, /linear-gradient/, `${name}: pregunta abierta sin superficie de lectura`);
      assert.match(openState.boxShadow, /rgb\(29, 79, 150\)/, `${name}: pregunta abierta sin rail azul`);

      const resources = page.locator('#recursos > .id-cards');
      const resourceCols = (await css(resources)).gridTemplateColumns.split(' ').filter(Boolean).length;
      if (width > 900) assert.equal(resourceCols, 3, `${name}: índice de recursos no usa tres registros`);
      else assert.equal(resourceCols, 1, `${name}: índice de recursos no apila <=900`);
      assert.equal((await css(resources.locator('h3').first())).color, BLUE, `${name}: recurso H3 no azul`);

      const finale = page.locator('#cta-final');
      const finaleCss = await css(finale);
      assert.match(finaleCss.backgroundImage, /linear-gradient/, `${name}: cierre final sin superficie editorial`);
      assert.match(finaleCss.boxShadow, /rgb\(29, 79, 150\)/, `${name}: cierre final sin rail azul`);
      assert.match(finaleCss.boxShadow, /rgb\(184, 134, 11\)/, `${name}: cierre final sin dorado`);
      assert.equal((await css(finale.locator('h2'))).color, BLUE, `${name}: H2 de cierre no azul`);

      const footerBefore = await css(page.locator('.site-footer'), '::before');
      assert.match(footerBefore.backgroundImage, /linear-gradient/, `${name}: footer sin doble regla`);
      assert.equal((await css(page.locator('.back-to-top'))).borderTopColor, BLUE, `${name}: volver arriba no azul`);

      const launcher = page.locator('.assistant-widget__launcher');
      if (width <= 1300 && await launcher.count()) assert.equal((await css(launcher)).display, 'none', `${name}: launcher invade Club <=1300`);
      assert.notEqual((await css(page.locator('.header-search'))).display, 'none', `${name}: Asistente del header no disponible`);

      await page.screenshot({ path: path.join(OUT, `club-samuel-${name}.png`), fullPage: true });
    } catch (error) {
      failures.push({ viewport: name, width, height, error: error instanceof Error ? error.message : String(error) });
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}

fs.writeFileSync(path.join(OUT, 'club-samuel-design-report.json'), `${JSON.stringify({ route: '/clubes-de-lectura/samuel-entre-mundos/', viewports, failures }, null, 2)}\n`);
assert.deepEqual(failures, [], `Club Samuel design failures:\n${JSON.stringify(failures, null, 2)}`);
console.log('club-samuel-design-browser: PASS');
