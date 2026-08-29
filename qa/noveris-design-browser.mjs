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
const WHITE = 'rgb(255, 255, 255)';
const TRANSPARENT = 'rgba(0, 0, 0, 0)';
const MAP_FRAME = 'rgba(29, 79, 150, 0.5)';

const viewports = [
  ['desktop-1440', 1440, 1000],
  ['desktop-1280', 1280, 800],
  ['tablet-1024', 1024, 768],
  ['bento-901', 901, 800],
  ['bento-900', 900, 800],
  ['tablet-768', 768, 1024],
  ['table-761', 761, 900],
  ['table-760', 760, 900],
  ['glossary-641', 641, 900],
  ['glossary-640', 640, 900],
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
      backgroundSize: s.backgroundSize,
      borderTopColor: s.borderTopColor,
      borderTopWidth: s.borderTopWidth,
      borderRightColor: s.borderRightColor,
      borderRightWidth: s.borderRightWidth,
      borderBottomColor: s.borderBottomColor,
      borderBottomWidth: s.borderBottomWidth,
      borderLeftColor: s.borderLeftColor,
      borderLeftWidth: s.borderLeftWidth,
      boxShadow: s.boxShadow,
      display: s.display,
      fontFamily: s.fontFamily,
      fontSize: s.fontSize,
      gridTemplateColumns: s.gridTemplateColumns,
      minWidth: s.minWidth,
      overflowX: s.overflowX,
      position: s.position,
      width: s.width,
    };
  }, pseudo);
}

async function rect(locator) {
  const r = await locator.boundingBox();
  assert.ok(r, `elemento sin caja: ${await locator.evaluate(el => el.id || el.className || el.tagName)}`);
  return { ...r, right: r.x + r.width, bottom: r.y + r.height };
}

async function loadDocumentaryImages(page) {
  const images = page.locator('main img');
  const count = await images.count();
  for (let i = 0; i < count; i += 1) {
    const img = images.nth(i);
    await img.scrollIntoViewIfNeeded();
    await img.evaluate(async el => {
      el.loading = 'eager';
      if (!el.complete) {
        await new Promise((resolve, reject) => {
          el.addEventListener('load', resolve, { once: true });
          el.addEventListener('error', reject, { once: true });
        }).catch(() => {});
      }
      if (typeof el.decode === 'function') await el.decode().catch(() => {});
    });
  }
  await page.evaluate(() => scrollTo(0, 0));
}

const browser = await chromium.launch({ headless: true });
const failures = [];

try {
  for (const [name, width, height] of viewports) {
    const context = await browser.newContext({ viewport: { width, height }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    try {
      const response = await page.goto(`${ORIGIN}/universo/noveris/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
      assert.ok(response?.ok(), `${name}: Noveris no carga`);
      await page.evaluate(() => document.fonts?.ready);
      await loadDocumentaryImages(page);

      assert.equal(await page.locator('html').getAttribute('data-editorial-context'), 'samuel', `${name}: contexto Samuel perdido`);
      assert.equal(await page.locator('main').getAttribute('data-family'), 'lore', `${name}: familia lore perdida`);
      assert.equal(await page.locator('link[rel="canonical"]').getAttribute('href'), 'https://davidportodiaz.com/universo/noveris/', `${name}: canonical alterado`);
      assert.equal(await page.locator('h1').count(), 1, `${name}: H1 no único`);
      assert.equal(await page.locator('.section-context [aria-current="page"]').getAttribute('href'), '/universo/noveris/', `${name}: contexto no marca Noveris`);

      const token = await page.locator('html').evaluate(el => getComputedStyle(el).getPropertyValue('--nov-blue').trim());
      assert.equal(token, '#1d4f96', `${name}: capa visual Noveris no aplicada`);

      const currentContext = await css(page.locator('.section-context [aria-current="page"]'));
      assert.equal(currentContext.color, BLUE, `${name}: navegación contextual activa no azul`);
      assert.equal(currentContext.backgroundColor, PALE, `${name}: navegación contextual activa no usa azul pálido`);
      assert.match(currentContext.boxShadow, /rgb\(184, 134, 11\)/, `${name}: navegación contextual activa pierde subrayado dorado`);
      assert.equal((await css(page.locator('.section-context__title'))).color, BLUE, `${name}: título contextual no azul`);

      if (name === 'desktop-1440' || name === 'mobile-390') {
        const headerSearch = page.locator('.header-search');
        await headerSearch.hover();
        const headerHover = await css(headerSearch);
        assert.equal(headerHover.color, HEADER_BLUE, `${name}: hover Asistente no usa azul especial de header`);
        assert.equal(headerHover.backgroundColor, PALE, `${name}: hover Asistente no usa superficie pálida`);
        await page.mouse.move(Math.max(1, width - 2), Math.max(1, height - 2));

        const exploreTrigger = page.locator('.explore-trigger');
        await exploreTrigger.click();
        const dialog = page.locator('#explore-dialog');
        await dialog.waitFor({ state: 'visible', timeout: 3000 });
        assert.equal((await css(dialog)).borderRightColor, BLUE, `${name}: Explorar no tiene borde azul`);
        assert.equal((await css(dialog.locator('.explore-dialog__head'))).borderBottomColor, GOLD, `${name}: cabecera Explorar no cierra en dorado`);
        assert.equal((await css(dialog.locator('.explore-dialog__head h2'))).color, BLUE, `${name}: título Explorar no azul`);
        const toggle = dialog.locator('.explore-row__toggle').first();
        assert.equal((await css(toggle)).color, BLUE, `${name}: toggle Explorar en reposo no azul`);
        await toggle.hover();
        const toggleHover = await css(toggle);
        assert.equal(toggleHover.color, WHITE, `${name}: toggle Explorar hover no blanco`);
        assert.equal(toggleHover.backgroundColor, BLUE, `${name}: toggle Explorar hover no azul`);
        await dialog.locator('[data-explore-close]').click();
        await dialog.waitFor({ state: 'hidden', timeout: 3000 });
      }

      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert.ok(overflow <= 1, `${name}: overflow horizontal ${overflow}px`);

      const opening = await css(page.locator('.tool-hero > .eyebrow'));
      assert.equal(opening.color, GOLD, `${name}: apertura hero no dorada`);
      assert.match(opening.fontFamily.toLowerCase(), /yellowtail/, `${name}: apertura hero sin Yellowtail`);
      assert.ok(parseFloat(opening.fontSize) >= 23, `${name}: apertura dorada demasiado pequeña`);
      assert.match(opening.backgroundImage, /highlight-8-blue-rect\.png/, `${name}: apertura sin highlight azul`);

      const heroTitle = await css(page.locator('.tool-hero h1'));
      assert.equal(heroTitle.color, BLUE, `${name}: H1 no azul`);
      const hero = await css(page.locator('.tool-hero'));
      assert.match(hero.backgroundImage, /linear-gradient/, `${name}: hero sin cierre azul\/dorado`);

      const heroPrimary = await css(page.locator('.tool-hero .primary-action'));
      assert.equal(heroPrimary.color, BLUE, `${name}: acción hero no azul`);
      assert.match(heroPrimary.fontFamily.toLowerCase(), /yellowtail/, `${name}: acción hero sin Yellowtail`);
      assert.equal(heroPrimary.backgroundColor, TRANSPARENT, `${name}: acción hero conserva botón negro`);

      const sectionOpening = await css(page.locator('#respuesta > .eyebrow'));
      assert.equal(sectionOpening.color, GOLD, `${name}: apertura de sección no dorada`);
      assert.match(sectionOpening.fontFamily.toLowerCase(), /yellowtail/, `${name}: apertura de sección sin Yellowtail`);
      assert.equal((await css(page.locator('#respuesta > h2'))).color, BLUE, `${name}: H2 de sección no azul`);

      const mapFigure = page.locator('#respuesta .lore-figure').first();
      const mapFrame = await css(mapFigure);
      assert.match(mapFrame.backgroundImage, /linear-gradient/, `${name}: mapa sin rail`);
      assert.match(mapFrame.backgroundSize, /2\.5px\s+100%/, `${name}: rail de mapa no es 2.5px`);
      const mapImg = await css(mapFigure.locator('img'));
      assert.equal(mapImg.borderTopColor, MAP_FRAME, `${name}: mapa no conserva el marco azul documental al 50%`);
      const mapBox = await rect(mapFigure.locator('img'));
      assert.ok(mapBox.width > Math.min(260, width * .55), `${name}: mapa pierde presencia visual (${mapBox.width}px)`);

      const bento = page.locator('.lore-bento-grid');
      const bentoCss = await css(bento);
      assert.equal(bentoCss.borderTopColor, BLUE, `${name}: registro de focos sin regla azul`);
      assert.equal(bentoCss.borderBottomColor, GOLD, `${name}: registro de focos sin cierre dorado`);
      const bentoCols = bentoCss.gridTemplateColumns.split(' ').filter(Boolean).length;
      if (width > 900) assert.ok(bentoCols >= 2, `${name}: focos desktop no conservan composición documental doble`);
      else assert.equal(bentoCols, 1, `${name}: focos no se apilan <=900`);
      const largeCard = page.locator('.lore-bento-card--large');
      assert.equal((await css(largeCard)).borderTopWidth, '0px', `${name}: foco principal vuelve a card boxed`);
      assert.equal((await css(largeCard.locator('h3'))).color, BLUE, `${name}: foco principal H3 no azul`);

      const tableWrap = page.locator('.lore-table-wrap');
      const table = page.locator('.lore-table');
      const tableCss = await css(table);
      const tableWrapBox = await rect(tableWrap);
      const tableBox = await rect(table);
      assert.ok(tableBox.width <= tableWrapBox.width + 1, `${name}: tabla excede contenedor (${tableBox.width} > ${tableWrapBox.width})`);
      assert.equal((await css(tableWrap)).borderTopColor, BLUE, `${name}: registro de canalizadores sin azul`);
      assert.equal((await css(tableWrap)).borderBottomColor, GOLD, `${name}: registro de canalizadores sin oro`);
      if (width > 760) {
        assert.equal(tableCss.display, 'table', `${name}: tabla desktop dejó semántica visual de tabla`);
      } else {
        assert.equal(tableCss.display, 'block', `${name}: tabla no se convierte a registro móvil`);
        assert.equal((await css(table.locator('tbody tr').first())).display, 'grid', `${name}: fila móvil de canalizadores no es grid`);
        const label = await table.locator('tbody tr').first().locator('td').nth(1).evaluate(el => getComputedStyle(el, '::before').content);
        assert.match(label, /Usuario o contexto/, `${name}: registro móvil pierde etiqueta de contexto`);
      }
      const tableImage = await rect(table.locator('.lore-table-img').first());
      assert.ok(tableImage.width >= 60, `${name}: imagen de canalizador demasiado pequeña`);

      const zones = page.locator('#mapa .id-cards');
      const zoneCols = (await css(zones)).gridTemplateColumns.split(' ').filter(Boolean).length;
      if (width > 760) assert.ok(zoneCols >= 2, `${name}: zonas desktop no usan registro doble`);
      else assert.equal(zoneCols, 1, `${name}: zonas no apilan <=760`);
      const firstZone = page.locator('#mapa .id-card').first();
      assert.equal((await css(firstZone)).borderTopWidth, '0px', `${name}: zona vuelve a card boxed`);
      assert.equal((await css(firstZone.locator('h3'))).color, BLUE, `${name}: zona H3 no azul`);

      const glossaryRows = page.locator('#glosario .id-card');
      assert.equal(await glossaryRows.count(), 14, `${name}: glosario visible ya no contiene 14 términos`);
      const glossaryCols = (await css(glossaryRows.first())).gridTemplateColumns.split(' ').filter(Boolean).length;
      if (width > 640) assert.ok(glossaryCols >= 2, `${name}: glosario pierde ledger >640`);
      else assert.equal(glossaryCols, 1, `${name}: glosario no apila <=640`);
      assert.equal((await css(glossaryRows.first().locator('h3'))).color, BLUE, `${name}: término de glosario no azul`);

      const faq = page.locator('.identity-faq');
      assert.equal((await css(faq)).borderTopColor, BLUE, `${name}: FAQ sin regla azul`);
      assert.equal((await css(faq)).borderBottomColor, GOLD, `${name}: FAQ sin cierre dorado`);
      const faqFirst = faq.locator('details').first();
      assert.equal((await css(faqFirst.locator('summary'))).color, BLUE, `${name}: summary FAQ no azul`);
      await faqFirst.locator('summary').click();
      assert.equal(await faqFirst.getAttribute('open'), '', `${name}: FAQ no abre`);

      const footerBefore = await css(page.locator('.site-footer'), '::before');
      assert.match(footerBefore.backgroundImage, /linear-gradient/, `${name}: footer sin doble regla`);
      assert.equal((await css(page.locator('.back-to-top'))).borderTopColor, BLUE, `${name}: volver arriba no azul`);

      const launcher = page.locator('.assistant-widget__launcher');
      if (width <= 1300 && await launcher.count()) {
        assert.equal((await css(launcher)).display, 'none', `${name}: launcher invade archivo <=1300`);
      }
      assert.notEqual((await css(page.locator('.header-search'))).display, 'none', `${name}: Asistente del header no disponible`);

      await page.evaluate(() => scrollTo(0, 0));
      await page.screenshot({ path: path.join(OUT, `noveris-${name}.png`), fullPage: true });
    } catch (error) {
      failures.push(`${name}: ${error.stack || error}`);
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}

const report = {
  route: '/universo/noveris/',
  viewports: viewports.map(([name, width, height]) => ({ name, width, height })),
  failures,
};
fs.writeFileSync(path.join(OUT, 'noveris-design-report.json'), JSON.stringify(report, null, 2));

if (failures.length) {
  console.error(failures.join('\n\n'));
  process.exitCode = 1;
} else {
  console.log(`noveris-design-browser: PASS (${viewports.length} viewports)`);
}
