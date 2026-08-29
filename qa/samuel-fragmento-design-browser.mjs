import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const OUT = process.env.QA_OUT || 'artifacts/sitewide-reflow';
fs.mkdirSync(OUT, { recursive: true });

const BLUE = 'rgb(29, 79, 150)';
const DEEP = 'rgb(13, 44, 87)';
const GOLD = 'rgb(184, 134, 11)';
const PALE = 'rgb(238, 250, 255)';
const INK = 'rgb(5, 5, 5)';

const viewports = [
  ['desktop-1440', 1440, 1000],
  ['desktop-1280', 1280, 800],
  ['tablet-1024', 1024, 768],
  ['seam-901', 901, 800],
  ['seam-900', 900, 800],
  ['tablet-768', 768, 1024],
  ['seam-620', 620, 900],
  ['mobile-390', 390, 844],
  ['mobile-360', 360, 800],
];

async function computed(locator, pseudo = null) {
  return locator.evaluate((el, pseudoArg) => {
    const cs = getComputedStyle(el, pseudoArg || null);
    return {
      color: cs.color,
      backgroundColor: cs.backgroundColor,
      backgroundImage: cs.backgroundImage,
      backgroundSize: cs.backgroundSize,
      borderTopColor: cs.borderTopColor,
      borderTopWidth: cs.borderTopWidth,
      borderBottomColor: cs.borderBottomColor,
      borderBottomWidth: cs.borderBottomWidth,
      borderLeftWidth: cs.borderLeftWidth,
      boxShadow: cs.boxShadow,
      display: cs.display,
      fontFamily: cs.fontFamily,
      fontSize: cs.fontSize,
      position: cs.position,
      transform: cs.transform,
      width: cs.width,
      height: cs.height,
      maxWidth: cs.maxWidth,
      paddingLeft: cs.paddingLeft,
      gridTemplateColumns: cs.gridTemplateColumns,
    };
  }, pseudo);
}

async function box(locator) {
  const value = await locator.boundingBox();
  assert.ok(value, `sin caja para ${await locator.evaluate(el => el.className || el.id || el.tagName)}`);
  return { ...value, right: value.x + value.width, bottom: value.y + value.height };
}

const browser = await chromium.launch({ headless: true });
const failures = [];

try {
  for (const [name, width, height] of viewports) {
    const context = await browser.newContext({ viewport: { width, height }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    try {
      const response = await page.goto(`${ORIGIN}/fragmento/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
      assert.ok(response?.ok(), `${name}: /fragmento/ no carga`);
      await page.evaluate(() => document.fonts?.ready);

      const figureImg = page.locator('.visual-figure--fragment img');
      await figureImg.waitFor({ state: 'visible', timeout: 10000 });
      await figureImg.evaluate(async img => {
        if (!img.complete) await new Promise((resolve, reject) => {
          img.addEventListener('load', resolve, { once: true });
          img.addEventListener('error', reject, { once: true });
        });
        if (typeof img.decode === 'function') await img.decode().catch(() => {});
      });

      assert.equal(await page.locator('html').getAttribute('data-editorial-context'), 'samuel', `${name}: contexto Samuel perdido`);
      assert.equal(await page.locator('link[rel="canonical"]').getAttribute('href'), 'https://davidportodiaz.com/fragmento/', `${name}: canonical alterado`);
      assert.equal(await page.locator('.fragment-reading[data-nosnippet]').count(), 1, `${name}: data-nosnippet perdido`);

      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      assert.ok(overflow <= 1, `${name}: overflow horizontal ${overflow}px`);

      const opening = await computed(page.locator('.article-header .eyebrow'));
      assert.match(opening.fontFamily.toLowerCase(), /yellowtail/, `${name}: apertura sin Yellowtail`);
      assert.equal(opening.color, GOLD, `${name}: apertura no dorada`);
      assert.ok(parseFloat(opening.fontSize) >= 24, `${name}: dorado de apertura no es texto grande`);
      assert.match(opening.backgroundImage, /highlight-8-blue-rect\.png/, `${name}: apertura sin highlight azul`);

      const h1 = await computed(page.locator('#article-title'));
      assert.equal(h1.color, BLUE, `${name}: H1 fuera del azul`);

      const header = await computed(page.locator('.article-header'));
      assert.match(header.backgroundImage, /linear-gradient/, `${name}: hero sin cierre azul\/dorado`);

      const meta = await computed(page.locator('.article-meta'));
      assert.match(meta.backgroundImage, /linear-gradient/, `${name}: metadata sin rail`);
      if (width > 900) assert.match(meta.backgroundSize, /2\.5px\s+100%/, `${name}: metadata desktop sin rail 2.5px`);
      else assert.match(meta.backgroundSize, /100%\s+1\.5px/, `${name}: metadata apilada sin regla horizontal`);

      const prose = page.locator('.article-prose');
      const proseCss = await computed(prose);
      assert.match(proseCss.backgroundImage, /linear-gradient/, `${name}: lectura sin rail`);
      assert.match(proseCss.backgroundSize, /2\.5px\s+100%/, `${name}: rail de lectura no es 2.5px`);
      const proseBox = await box(prose);
      assert.ok(proseBox.width <= Math.min(width - 16, 850), `${name}: medida de lectura demasiado ancha (${proseBox.width}px)`);

      const figureFrame = await computed(page.locator('.visual-figure--fragment'), '::before');
      assert.equal(figureFrame.borderTopColor, BLUE, `${name}: figura sin marco azul`);
      assert.match(figureFrame.boxShadow, /184, 134, 11/, `${name}: figura sin acento dorado`);

      const chapterTitle = await computed(page.locator('.fragment-text h2'));
      assert.equal(chapterTitle.color, BLUE, `${name}: título interno de capítulo no azul`);
      assert.equal(chapterTitle.borderBottomColor, BLUE, `${name}: título interno sin regla azul`);

      const divider = await computed(page.locator('.fragment-divider').first());
      assert.match(divider.backgroundImage, /linear-gradient/, `${name}: divider literario sin doble regla`);

      const finalCta = page.locator('.fragment-cta-box');
      const finalCtaCss = await computed(finalCta);
      assert.equal(finalCtaCss.backgroundColor, PALE, `${name}: CTA final no usa azul pálido`);
      assert.match(finalCtaCss.backgroundImage, /linear-gradient/, `${name}: CTA final sin reglas de marca`);
      const finalOpening = await computed(finalCta.locator(':scope > .eyebrow'));
      assert.equal(finalOpening.color, GOLD, `${name}: CTA final sin apertura dorada`);
      assert.match(finalOpening.fontFamily.toLowerCase(), /yellowtail/, `${name}: CTA final sin Yellowtail`);
      const finalPrimary = await computed(finalCta.locator('.primary-action'));
      assert.equal(finalPrimary.color, BLUE, `${name}: acción Amazon final no azul`);
      assert.match(finalPrimary.fontFamily.toLowerCase(), /yellowtail/, `${name}: acción Amazon final sin Yellowtail`);
      assert.equal(finalPrimary.backgroundColor, 'rgba(0, 0, 0, 0)', `${name}: CTA final volvió a botón negro`);

      const articleEnd = await computed(page.locator('.article-end'));
      assert.match(articleEnd.backgroundImage, /linear-gradient/, `${name}: continuidad sin reglas azul\/dorado`);
      const newsletter = await computed(page.locator('.editorial-newsletter'));
      assert.match(newsletter.backgroundImage, /linear-gradient/, `${name}: newsletter sin reglas azul\/dorado`);
      assert.equal((await computed(page.locator('.editorial-newsletter h2'))).color, BLUE, `${name}: newsletter H2 no azul`);

      const progress = await computed(page.locator('.reading-progress'));
      assert.match(progress.backgroundImage, /linear-gradient/, `${name}: progreso sin gradiente azul\/dorado`);
      assert.equal(progress.height, '2.5px', `${name}: progreso no conserva 2.5px`);

      // El sticky real se activa al 65% del documento; se prueba el comportamiento,
      // no solo la clase visual. El cierre debe persistir en sessionStorage.
      await page.evaluate(() => {
        const total = document.body.scrollHeight - innerHeight;
        scrollTo(0, total * .70);
      });
      await page.waitForFunction(() => document.querySelector('#sticky-cta')?.classList.contains('visible'), null, { timeout: 3000 });
      const sticky = page.locator('#sticky-cta');
      const stickyCss = await computed(sticky);
      assert.equal(stickyCss.position, 'fixed', `${name}: sticky dejó de ser persistente`);
      assert.notEqual(stickyCss.backgroundColor, 'rgb(23, 22, 20)', `${name}: sticky conserva inverso negro legacy`);
      assert.match(stickyCss.backgroundImage, /linear-gradient/, `${name}: sticky sin reglas azul\/dorado`);
      const stickyPrimary = await computed(sticky.locator('.primary-action'));
      assert.equal(stickyPrimary.color, BLUE, `${name}: acción sticky no azul`);
      assert.match(stickyPrimary.fontFamily.toLowerCase(), /yellowtail/, `${name}: acción sticky sin Yellowtail`);
      const stickyBox = await box(sticky);
      const maxStickyHeight = width <= 620 ? 76 : 88;
      assert.ok(stickyBox.height <= maxStickyHeight, `${name}: sticky demasiado alto (${stickyBox.height}px > ${maxStickyHeight}px)`);

      if (width === 1280 || width === 390) {
        await page.screenshot({ path: path.join(OUT, `samuel-fragmento-sticky-${name}.png`), fullPage: false });
      }

      await sticky.locator('#sticky-cta-close').click();
      assert.equal(await sticky.evaluate(el => el.classList.contains('visible')), false, `${name}: cerrar sticky no lo oculta`);
      assert.equal(await page.evaluate(() => sessionStorage.getItem('sticky-cta-dismissed')), '1', `${name}: dismiss sticky no persiste`);

      // El widget es asíncrono. Si ya ha cargado, <=1300 debe ocultar solo el
      // launcher flotante; el botón Asistente del header permanece visible.
      await page.waitForTimeout(80);
      const headerAssistant = page.locator('.header-search');
      assert.notEqual((await computed(headerAssistant)).display, 'none', `${name}: Asistente desapareció del header`);
      const launcher = page.locator('.assistant-widget__launcher');
      if (await launcher.count()) {
        const launcherCss = await computed(launcher);
        if (width <= 1300) assert.equal(launcherCss.display, 'none', `${name}: launcher flotante invade lectura <=1300`);
      }

      await page.evaluate(() => scrollTo(0, 0));
      await page.screenshot({ path: path.join(OUT, `samuel-fragmento-${name}.png`), fullPage: true });
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
  route: '/fragmento/',
  viewports: viewports.map(([name, width, height]) => ({ name, width, height })),
  failures,
};
fs.writeFileSync(path.join(OUT, 'samuel-fragmento-design-report.json'), JSON.stringify(report, null, 2));

if (failures.length) {
  console.error(failures.join('\n\n'));
  process.exitCode = 1;
} else {
  console.log(`samuel-fragmento-design-browser: PASS (${viewports.length} viewports)`);
}
