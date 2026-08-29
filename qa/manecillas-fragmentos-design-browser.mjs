import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const OUT = process.env.QA_OUT || 'artifacts/sitewide-reflow';
fs.mkdirSync(OUT, { recursive: true });

const BLUE = 'rgb(29, 79, 150)';
const DEEP = 'rgb(13, 44, 87)';
const HEADER_BLUE = 'rgb(10, 77, 159)';
const GOLD = 'rgb(184, 134, 11)';
const NEUTRAL = 'rgb(111, 106, 100)';
const PALE = 'rgb(238, 250, 255)';

const viewports = [
  ['desktop-1440', 1440, 1000],
  ['desktop-1280', 1280, 800],
  ['tablet-1024', 1024, 768],
  ['seam-900', 900, 800],
  ['seam-899', 899, 800],
  ['tablet-768', 768, 1024],
  ['seam-767', 767, 900],
  ['mobile-390', 390, 844],
  ['mobile-360', 360, 800],
];

async function style(locator, pseudo = null) {
  return locator.evaluate((el, pseudoArg) => {
    const cs = getComputedStyle(el, pseudoArg || null);
    return {
      color: cs.color,
      backgroundColor: cs.backgroundColor,
      backgroundImage: cs.backgroundImage,
      backgroundSize: cs.backgroundSize,
      borderTopWidth: cs.borderTopWidth,
      borderBottomWidth: cs.borderBottomWidth,
      fontFamily: cs.fontFamily,
      fontWeight: cs.fontWeight,
      position: cs.position,
      display: cs.display,
      gridTemplateColumns: cs.gridTemplateColumns,
      textAlign: cs.textAlign,
      width: cs.width,
      content: cs.content,
    };
  }, pseudo);
}

async function box(locator) {
  return locator.evaluate((el) => {
    const r = el.getBoundingClientRect();
    return { top:r.top, bottom:r.bottom, left:r.left, right:r.right, width:r.width, height:r.height };
  });
}

async function waitForStyle(locator, property, expected, timeout = 1200) {
  await locator.evaluate(async (el, args) => {
    const started = performance.now();
    while (getComputedStyle(el)[args.property] !== args.expected) {
      if (performance.now() - started > args.timeout) {
        throw new Error(`${args.property} did not settle to ${args.expected}; got ${getComputedStyle(el)[args.property]}`);
      }
      await new Promise((resolve) => requestAnimationFrame(resolve));
    }
  }, { property, expected, timeout });
}

const browser = await chromium.launch({ headless:true });
const failures = [];
try {
  for (const [name, width, height] of viewports) {
    const context = await browser.newContext({ viewport:{ width, height } });
    const page = await context.newPage();
    try {
      const response = await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/fragmentos/`, { waitUntil:'domcontentloaded', timeout:20000 });
      assert.ok(response?.ok(), `${name}: ruta no carga`);
      await page.evaluate(() => document.fonts?.ready);

      const coverImg = page.locator('.book-cover img').first();
      await coverImg.waitFor({ state:'visible', timeout:10000 });
      await coverImg.evaluate(async (img) => {
        if (!img.complete) await new Promise((resolve, reject) => {
          img.addEventListener('load', resolve, { once:true });
          img.addEventListener('error', reject, { once:true });
        });
        if (typeof img.decode === 'function') await img.decode().catch(() => {});
      });

      assert.equal(await page.locator('html').getAttribute('data-editorial-context'), 'manecillas');
      assert.ok(await page.locator('body').getAttribute('data-reading-progress') !== null, `${name}: falta marcador de lectura`);
      const fragBlue = await page.locator('body').evaluate((el) => getComputedStyle(el).getPropertyValue('--frag-blue').trim());
      assert.equal(fragBlue, '#1d4f96', `${name}: capa Fragmentos no aplicada`);

      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      assert.ok(overflow <= 1, `${name}: overflow horizontal ${overflow}px`);

      const opening = await style(page.locator('.book-hero__copy>.eyebrow'));
      assert.match(opening.fontFamily.toLowerCase(), /yellowtail/);
      assert.equal(opening.color, GOLD);
      assert.notEqual(opening.backgroundImage, 'none');

      const h1 = await style(page.locator('.book-hero h1'));
      assert.equal(h1.color, BLUE);
      assert.equal(h1.fontWeight, '800');

      const cover = page.locator('.book-cover');
      const before = await style(cover, '::before');
      const after = await style(cover, '::after');
      assert.match(before.backgroundImage, /corner-bracket-blue-gold\.svg/);
      assert.match(after.backgroundImage, /corner-bracket-blue-gold\.svg/);
      const coverBox = await box(coverImg);
      assert.ok(coverBox.width > 70 && coverBox.height > 100, `${name}: portada sin caja visible`);

      const primary = page.locator('.book-actions .primary-action');
      const primaryCss = await style(primary);
      assert.match(primaryCss.fontFamily.toLowerCase(), /yellowtail/);
      assert.equal(primaryCss.color, BLUE);
      assert.equal(primaryCss.backgroundColor, 'rgba(0, 0, 0, 0)');

      if (width >= 768 && width <= 899) {
        const heroCss = await style(page.locator('.book-hero'));
        assert.equal(heroCss.display, 'grid', `${name}: hero tablet no conserva dos columnas`);
        const copyBox = await box(page.locator('.book-hero__copy'));
        assert.ok(coverBox.width >= 170, `${name}: portada tablet demasiado pequeña (${coverBox.width}px)`);
        assert.ok(coverBox.right <= copyBox.left - 8, `${name}: portada tablet invade copy`);
      }
      if (width <= 767) {
        const heroBefore = await style(page.locator('.book-hero'), '::before');
        assert.equal(heroBefore.width, '2.5px', `${name}: rail exterior móvil no es 2.5px`);
        assert.notEqual(heroBefore.content, 'none');
      }

      const introOpening = await style(page.locator('.book-hero + .v1-section>.eyebrow'));
      const introH2 = await style(page.locator('.book-hero + .v1-section>h2'));
      assert.match(introOpening.fontFamily.toLowerCase(), /yellowtail/);
      assert.equal(introOpening.color, GOLD);
      assert.equal(introH2.color, BLUE);

      const indexLinks = page.locator('.fragment-index__link');
      assert.equal(await indexLinks.count(), 3, `${name}: índice debe tener tres registros`);
      const registerCss = await style(indexLinks.first().locator('.fragment-index__register'));
      assert.equal(registerCss.color, NEUTRAL);

      await page.evaluate(() => { location.hash = '#fragmento-1'; });
      await page.waitForTimeout(180);
      const firstLink = indexLinks.first();
      assert.equal(await firstLink.getAttribute('data-current'), 'true', `${name}: hash no activa Registro I`);
      const activeCss = await style(firstLink);
      const activeRail = await style(firstLink, '::before');
      assert.equal(activeCss.backgroundColor, PALE);
      assert.equal(activeRail.width, '2.5px');
      assert.equal(activeRail.backgroundColor, BLUE);

      const excerpts = page.locator('.excerpt-section');
      assert.equal(await excerpts.count(), 3, `${name}: deben existir tres fragmentos`);
      const label = await style(excerpts.first().locator('.book-section__label>.eyebrow'));
      const excerptH2 = await style(excerpts.first().locator('.book-section__label h2'));
      const excerptMeta = await style(excerpts.first().locator('.tool-meta'));
      const proseRail = await style(excerpts.first().locator('.excerpt-field'));
      assert.match(label.fontFamily.toLowerCase(), /yellowtail/);
      assert.equal(label.color, GOLD);
      assert.equal(excerptH2.color, BLUE);
      assert.equal(excerptMeta.color, NEUTRAL);
      assert.match(proseRail.backgroundImage, /linear-gradient/);
      assert.match(proseRail.backgroundSize, /2\.5px\s+100%/);

      const pagers = page.locator('.fragment-pager');
      assert.equal(await pagers.count(), 3, `${name}: cada fragmento necesita pager`);
      const pagerTitle = await style(pagers.first().locator('.fragment-pager__title'));
      assert.match(pagerTitle.fontFamily.toLowerCase(), /yellowtail/);
      assert.equal(pagerTitle.color, BLUE);

      /* v1-book.css collapses excerpt sections to one column at <=899px. A
         pager left on grid-column:2 silently creates an implicit second track,
         compressing prose to half-width. Guard the actual geometry. */
      if (width <= 899) {
        const sectionBox = await box(excerpts.first());
        const fieldBox = await box(excerpts.first().locator('.excerpt-field'));
        const pagerBox = await box(pagers.first());
        assert.ok(fieldBox.width >= sectionBox.width * .88, `${name}: prosa comprimida por columna implícita (${fieldBox.width}/${sectionBox.width})`);
        assert.ok(Math.abs(fieldBox.left - sectionBox.left) <= 4, `${name}: prosa desplazada respecto a la sección`);
        assert.ok(pagerBox.width >= sectionBox.width * .88, `${name}: pager no ocupa el ancho de lectura (${pagerBox.width}/${sectionBox.width})`);
        assert.ok(Math.abs(pagerBox.left - sectionBox.left) <= 4, `${name}: pager sigue en una columna implícita`);
      }

      if (width <= 767) {
        const pagerCss = await style(pagers.nth(1));
        assert.equal(pagerCss.gridTemplateColumns.split(' ').length, 1, `${name}: pager móvil no se apila`);
        const nextCss = await style(pagers.nth(1).locator('.fragment-pager__link--next'));
        assert.equal(nextCss.textAlign, 'left');
      }

      const quote = await style(page.locator('.book-dedication'));
      assert.match(quote.backgroundImage, /linear-gradient/);

      const cta = page.locator('#cta-final');
      const ctaCss = await style(cta);
      const ctaOpening = await style(cta.locator(':scope > .eyebrow'));
      const ctaH2 = await style(cta.locator(':scope > h2'));
      const ctaAction = await style(cta.locator('.primary-action'));
      assert.equal(ctaCss.backgroundColor, PALE);
      assert.notEqual(ctaCss.borderTopWidth, '0px');
      assert.match(ctaOpening.fontFamily.toLowerCase(), /yellowtail/);
      assert.equal(ctaOpening.color, GOLD);
      assert.equal(ctaH2.color, BLUE);
      assert.match(ctaAction.fontFamily.toLowerCase(), /yellowtail/);
      assert.equal(ctaAction.color, BLUE);

      if (width <= 639) {
        const contextCss = await style(page.locator('.section-context'));
        assert.equal(contextCss.position, 'relative');
      }

      const footerHeading = await style(page.locator('.site-footer h2').first());
      assert.equal(footerHeading.color, BLUE);

      const launcher = page.locator('.assistant-widget__launcher');
      await launcher.waitFor({ state:'attached', timeout:4000 });
      const launcherCss = await style(launcher);
      if (width <= 1300) assert.equal(launcherCss.display, 'none', `${name}: launcher duplicado vuelve sobre lectura`);
      else assert.notEqual(launcherCss.display, 'none', `${name}: launcher desktop debería seguir visible`);

      const headerHome = page.locator('.header-home');
      await headerHome.hover();
      await waitForStyle(headerHome, 'color', HEADER_BLUE);
      await waitForStyle(headerHome, 'backgroundColor', PALE);

      await primary.hover();
      await waitForStyle(primary, 'color', DEEP);

      const indexSecondTitle = indexLinks.nth(1).locator('.fragment-index__title');
      await indexSecondTitle.hover();
      await waitForStyle(indexSecondTitle, 'color', DEEP);

      await page.mouse.move(0, 0);
      await page.evaluate(() => {
        history.replaceState(null, '', location.pathname);
        window.scrollTo({ top:0, left:0, behavior:'instant' });
      });
      await page.waitForTimeout(120);
      await page.screenshot({ path:path.join(OUT, `fragmentos-${name}.png`), fullPage:true });
      console.log(`ok /las-manecillas-del-recuerdo/fragmentos/ ${width}x${height}`);
    } catch (error) {
      failures.push({ name, message:error.message, stack:error.stack });
      console.error(`FAIL Fragmentos ${width}x${height}: ${error.message}`);
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}

fs.writeFileSync(path.join(OUT, 'manecillas-fragmentos-design-report.json'), JSON.stringify({ failures }, null, 2));
if (failures.length) process.exitCode = 1;
else console.log('manecillas-fragmentos-design-browser: PASS');
