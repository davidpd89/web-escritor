import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const OUT = process.env.QA_OUT || 'artifacts/sitewide-reflow';
fs.mkdirSync(OUT, { recursive: true });

const BLUE = 'rgb(29, 79, 150)';
const GOLD = 'rgb(184, 134, 11)';
const NEUTRAL = 'rgb(111, 106, 100)';
const PALE_BLUE = 'rgb(238, 250, 255)';
const viewports = [
  ['desktop-1440', 1440, 1000],
  ['desktop-1280', 1280, 800],
  ['tablet-1024', 1024, 768],
  ['seam-901', 901, 800],
  ['seam-900', 900, 800],
  ['tablet-768', 768, 1024],
  ['stack-600', 600, 900],
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
      borderLeftWidth: cs.borderLeftWidth,
      fontFamily: cs.fontFamily,
      fontWeight: cs.fontWeight,
      textTransform: cs.textTransform,
      position: cs.position,
      display: cs.display,
      width: cs.width,
      height: cs.height,
      content: cs.content,
    };
  }, pseudo);
}

async function box(locator) {
  return locator.evaluate((el) => {
    const r = el.getBoundingClientRect();
    return { top: r.top, bottom: r.bottom, left: r.left, right: r.right };
  });
}

const browser = await chromium.launch({ headless: true });
const failures = [];
try {
  for (const [name, width, height] of viewports) {
    const context = await browser.newContext({ viewport: { width, height } });
    const page = await context.newPage();
    try {
      const response = await page.goto(`${ORIGIN}/libros/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
      assert.ok(response?.ok(), `${name}: /libros/ no carga`);
      await page.evaluate(async () => {
        await document.fonts?.ready;
        const images = [...document.querySelectorAll('main[data-family="books-index"] .books-stage__media img')];
        await Promise.all(images.map(async (img) => {
          if (!img.complete) await new Promise((resolve) => img.addEventListener('load', resolve, { once: true }));
          if (typeof img.decode === 'function') await img.decode().catch(() => {});
        }));
      });

      assert.equal(await page.locator('html').getAttribute('data-editorial-context'), 'obras');
      assert.equal(await page.locator('main[data-family="books-index"]').count(), 1);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      assert.ok(overflow <= 1, `${name}: overflow horizontal ${overflow}px`);

      const opening = await computed(page.locator('.v1-masthead .coordinate').first());
      assert.match(opening.fontFamily.toLowerCase(), /yellowtail/);
      assert.equal(opening.color, GOLD);
      assert.notEqual(opening.backgroundImage, 'none');

      const h1 = await computed(page.locator('main[data-family="books-index"] .v1-masthead h1'));
      assert.equal(h1.color, BLUE);
      assert.equal(h1.fontWeight, '800');

      const folio = await computed(page.locator('main[data-family="books-index"] .folio').first());
      assert.equal(folio.color, NEUTRAL);

      const current = await computed(page.locator('.section-context__links a[aria-current="page"]'));
      assert.equal(current.color, BLUE);
      assert.equal(current.backgroundColor, PALE_BLUE);

      const media = page.locator('main[data-family="books-index"] .books-stage__media');
      assert.equal(await media.count(), 3);
      for (let i = 0; i < 3; i++) {
        const before = await computed(media.nth(i), '::before');
        const after = await computed(media.nth(i), '::after');
        assert.match(before.backgroundImage, /corner-bracket-blue-gold\.svg/);
        assert.match(after.backgroundImage, /corner-bracket-blue-gold\.svg/);
        const image = media.nth(i).locator('img');
        assert.equal(await image.evaluate((img) => img.complete && img.naturalWidth > 0), true, `${name}: portada ${i + 1} no cargada`);
      }

      const primary = await computed(page.locator('.books-stage__actions .primary-action').first());
      assert.match(primary.fontFamily.toLowerCase(), /yellowtail/);
      assert.equal(primary.color, BLUE);
      assert.equal(primary.backgroundColor, 'rgba(0, 0, 0, 0)');
      assert.equal(primary.textTransform, 'none');
      assert.equal(primary.borderLeftWidth, '0px');

      const resources = await computed(page.locator('#recursos .v1-section__head>.eyebrow'));
      assert.match(resources.fontFamily.toLowerCase(), /yellowtail/);
      assert.equal(resources.color, GOLD);
      const resourceAction = await computed(page.locator('#recursos .ledger__action').first());
      assert.match(resourceAction.fontFamily.toLowerCase(), /yellowtail/);
      assert.equal(resourceAction.color, BLUE);

      const stage = page.locator('main[data-family="books-index"] .books-stage').first();
      const copy = stage.locator('.books-stage__copy');
      const stageBox = await box(stage);
      const copyBox = await box(copy);
      const copyCss = await computed(copy);
      const outerRail = await computed(stage, '::before');
      if (width >= 901) {
        assert.match(copyCss.backgroundImage, /linear-gradient/);
        assert.match(copyCss.backgroundSize, /2\.5px\s+100%/);
        assert.ok(Math.abs(copyBox.top - stageBox.top) <= 1.1, `${name}: rail no toca arriba`);
        assert.ok(Math.abs(copyBox.bottom - stageBox.bottom) <= 1.1, `${name}: rail no toca abajo`);
        assert.ok(outerRail.content === 'none' || outerRail.content === 'normal');
      } else {
        assert.equal(copyCss.backgroundImage, 'none');
        assert.notEqual(outerRail.content, 'none');
        assert.equal(outerRail.width, '2.5px');
      }

      if (width <= 639) {
        const contextCss = await computed(page.locator('.section-context'));
        assert.equal(contextCss.position, 'relative');
      }

      const footerHeading = await computed(page.locator('.site-footer h2').first());
      assert.equal(footerHeading.color, BLUE);

      const launcher = page.locator('.assistant-widget__launcher');
      await launcher.waitFor({ state: 'attached', timeout: 4000 });
      const launcherCss = await computed(launcher);
      if (width <= 1300) assert.equal(launcherCss.display, 'none', `${name}: launcher duplicado vuelve a cubrir lectura`);
      else assert.notEqual(launcherCss.display, 'none', `${name}: launcher desktop debería seguir disponible`);

      await page.screenshot({ path: path.join(OUT, `libros-${name}.png`), fullPage: true });
      console.log(`ok /libros/ ${width}x${height}`);
    } catch (error) {
      failures.push({ name, message: error.message, stack: error.stack });
      console.error(`FAIL /libros/ ${width}x${height}: ${error.message}`);
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}

fs.writeFileSync(path.join(OUT, 'books-index-design-report.json'), JSON.stringify({ failures }, null, 2));
if (failures.length) process.exitCode = 1;
else console.log('books-index-design-browser: PASS');
