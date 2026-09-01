import assert from 'node:assert/strict';
import { chromium, firefox, webkit } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const BLUE = 'rgb(29, 79, 150)';
const GOLD = 'rgb(184, 134, 11)';
const engines = { chromium, firefox, webkit };

for (const [engineName, launcher] of Object.entries(engines)) {
  const browser = await launcher.launch({ headless: true });
  try {
    for (const [mode, width, height] of [['desktop', 1280, 850], ['mobile', 390, 844]]) {
      const context = await browser.newContext({ viewport: { width, height }, reducedMotion: 'reduce' });
      const page = await context.newPage();
      try {
        const response = await page.goto(`${ORIGIN}/universo/noveris/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
        assert.equal(response?.ok(), true, `${engineName}/${mode}: Noveris no carga`);
        await page.evaluate(() => document.fonts?.ready);

        assert.equal(await page.locator('main').getAttribute('data-family'), 'lore', `${engineName}/${mode}: familia lore incorrecta`);
        assert.equal(await page.locator('html').evaluate(el => getComputedStyle(el).getPropertyValue('--nov-blue').trim()), '#1d4f96', `${engineName}/${mode}: capa Noveris no aplicada`);
        assert.equal(await page.locator('.tool-hero h1').evaluate(el => getComputedStyle(el).color), BLUE, `${engineName}/${mode}: H1 no azul`);

        const opening = await page.locator('.tool-hero>.eyebrow').evaluate(el => {
          const s = getComputedStyle(el);
          return { color: s.color, family: s.fontFamily };
        });
        assert.equal(opening.color, GOLD, `${engineName}/${mode}: apertura no dorada`);
        assert.match(opening.family.toLowerCase(), /yellowtail/, `${engineName}/${mode}: apertura sin Yellowtail`);

        const mapRail = await page.locator('#respuesta .lore-figure').first().evaluate(el => {
          const s = getComputedStyle(el);
          return { image: s.backgroundImage, size: s.backgroundSize };
        });
        assert.match(mapRail.image, /linear-gradient/, `${engineName}/${mode}: mapa sin rail`);
        assert.match(mapRail.size, /2\.5px\s+100%/, `${engineName}/${mode}: mapa sin rail 2.5px`);

        const bentoCols = await page.locator('.lore-bento-grid').evaluate(el => getComputedStyle(el).gridTemplateColumns.split(' ').filter(Boolean).length);
        if (width > 900) assert.ok(bentoCols >= 2, `${engineName}/${mode}: focos desktop no dobles`);
        else assert.equal(bentoCols, 1, `${engineName}/${mode}: focos móviles no apilan`);

        const table = page.locator('.lore-table');
        if (width <= 760) {
          assert.equal(await table.evaluate(el => getComputedStyle(el).display), 'block', `${engineName}/${mode}: canalizadores no pasan a registro móvil`);
          assert.equal(await table.locator('tbody tr').first().evaluate(el => getComputedStyle(el).display), 'grid', `${engineName}/${mode}: fila de canalizador no grid`);
        }

        assert.equal(await page.locator('#glosario .id-card').count(), 14, `${engineName}/${mode}: glosario visible no tiene 14 términos`);
        assert.equal(await page.locator('#glosario .id-card h3').first().evaluate(el => getComputedStyle(el).color), BLUE, `${engineName}/${mode}: término no azul`);

        const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
        assert.ok(overflow <= 1, `${engineName}/${mode}: overflow ${overflow}px`);

        if (width <= 1300) {
          const launcherNode = page.locator('.assistant-widget__launcher');
          await launcherNode.waitFor({ state: 'attached', timeout: 2500 }).catch(() => {});
          if (await launcherNode.count()) assert.equal(await launcherNode.evaluate(el => getComputedStyle(el).display), 'none', `${engineName}/${mode}: launcher invade archivo`);
        }
        assert.notEqual(await page.locator('.header-search').evaluate(el => getComputedStyle(el).display), 'none', `${engineName}/${mode}: Asistente header no disponible`);

        console.log(`ok [${engineName}] Noveris ${mode}`);
      } finally {
        await context.close();
      }
    }

    // noveris.css is shared with the Samuel reading-club page. Prove that the
    // archive V2 :has() guard does not leak its --nov-* tokens into that family.
    for (const [mode, width, height] of [['club-desktop', 1280, 850], ['club-mobile', 390, 844]]) {
      const context = await browser.newContext({ viewport: { width, height }, reducedMotion: 'reduce' });
      const page = await context.newPage();
      try {
        const response = await page.goto(`${ORIGIN}/clubes-de-lectura/samuel-entre-mundos/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
        assert.equal(response?.ok(), true, `${engineName}/${mode}: Club Samuel no carga`);
        assert.equal(await page.locator('main').getAttribute('data-family'), 'lore', `${engineName}/${mode}: familia lore del Club cambió`);
        const leakedToken = await page.locator('html').evaluate(el => getComputedStyle(el).getPropertyValue('--nov-blue').trim());
        assert.equal(leakedToken, '', `${engineName}/${mode}: la capa Noveris se filtró al Club`);
        assert.equal(await page.locator('link[href="/assets/noveris.css"]').count(), 1, `${engineName}/${mode}: el contrato de aislamiento ya no prueba una hoja compartida`);
        const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
        assert.ok(overflow <= 1, `${engineName}/${mode}: overflow del Club tras cargar noveris.css (${overflow}px)`);
        console.log(`ok [${engineName}] Noveris scope isolation ${mode}`);
      } finally {
        await context.close();
      }
    }
  } finally {
    await browser.close();
  }
}

console.log('noveris-design-cross-engine: PASS');
