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
  ['seam-1200', 1200, 850],
  ['seam-1199', 1199, 850],
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
      borderLeftWidth: cs.borderLeftWidth,
      borderTopWidth: cs.borderTopWidth,
      borderBottomWidth: cs.borderBottomWidth,
      fontFamily: cs.fontFamily,
      fontWeight: cs.fontWeight,
      textTransform: cs.textTransform,
      position: cs.position,
      display: cs.display,
      content: cs.content,
    };
  }, pseudo);
}

async function box(locator) {
  return locator.evaluate((el) => {
    const r = el.getBoundingClientRect();
    return { top: r.top, bottom: r.bottom, left: r.left, right: r.right, width: r.width, height: r.height };
  });
}

/* Interaction rules use transitions. Assert the settled state rather than
   sampling an arbitrary intermediate frame, which can quantize one RGB channel
   by a point while the transition is still running. */
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

const browser = await chromium.launch({ headless: true });
const failures = [];
try {
  for (const [name, width, height] of viewports) {
    const context = await browser.newContext({ viewport: { width, height } });
    const page = await context.newPage();
    try {
      const response = await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
      assert.ok(response?.ok(), `${name}: ruta no carga`);
      await page.evaluate(() => document.fonts?.ready);

      const coverImg = page.locator('.book-cover img').first();
      await coverImg.waitFor({ state: 'visible', timeout: 10000 });
      await coverImg.evaluate(async (img) => {
        if (!img.complete) await new Promise((resolve, reject) => {
          img.addEventListener('load', resolve, { once: true });
          img.addEventListener('error', reject, { once: true });
        });
        if (typeof img.decode === 'function') await img.decode().catch(() => {});
      });

      assert.equal(await page.locator('html').getAttribute('data-editorial-context'), 'manecillas');
      assert.equal(await page.locator('.book-page--manecillas').count(), 1);
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
      const coverBox = await coverImg.boundingBox();
      assert.ok(coverBox && coverBox.width > 60 && coverBox.height > 90, `${name}: portada sin caja visible`);
      assert.ok(await coverImg.evaluate((img) => img.naturalWidth > 0), `${name}: portada no cargada`);

      const primaryLocator = page.locator('.book-actions .primary-action');
      const primary = await style(primaryLocator);
      assert.match(primary.fontFamily.toLowerCase(), /yellowtail/);
      assert.equal(primary.color, BLUE);
      assert.equal(primary.backgroundColor, 'rgba(0, 0, 0, 0)');
      assert.equal(primary.textTransform, 'none');

      const dt = await style(page.locator('.book-meta-ledger dt').first());
      const dd = await style(page.locator('.book-meta-ledger dd').first());
      assert.equal(dt.color, NEUTRAL);
      assert.match(dd.color, /rgb\((5, 5, 5|0, 0, 0)\)/);

      const seam = await style(page.locator('.book-seam span'));
      const diamond = await style(page.locator('.book-seam span'), '::after');
      assert.match(seam.backgroundImage, /linear-gradient/);
      assert.notEqual(diamond.content, 'none');

      const sectionOpening = await style(page.locator('#sinopsis .book-section__label>.eyebrow'));
      assert.match(sectionOpening.fontFamily.toLowerCase(), /yellowtail/);
      assert.equal(sectionOpening.color, GOLD);

      const anchor = await style(page.locator('.book-anchor-alias').first());
      assert.equal(anchor.position, 'absolute', `${name}: el alias #muestra vuelve a participar en el grid`);

      const fragmentSection = page.locator('#fragmento');
      const fragmentLabel = fragmentSection.locator('.book-section__label');
      const fragmentProse = fragmentSection.locator('.prose-field');
      const labelBox = await box(fragmentLabel);
      const proseBox = await box(fragmentProse);
      if (width >= 900) {
        assert.ok(labelBox.right <= proseBox.left + 2, `${name}: Muestra vuelve a solapar/intercambiar columnas`);
        assert.ok(Math.abs(labelBox.top - proseBox.top) <= 4, `${name}: Muestra pierde alineación superior entre label y prosa`);
      } else {
        assert.ok(proseBox.top >= labelBox.bottom - 1, `${name}: Muestra no se apila label→prosa`);
      }

      const note = await style(page.locator('.book-margin-note'));
      assert.equal(note.backgroundColor, PALE);
      assert.equal(note.borderLeftWidth, '0px');
      assert.match(note.backgroundImage, /linear-gradient/);
      assert.match(note.backgroundSize, /2\.5px\s+100%/);

      const themes = page.locator('.book-theme');
      assert.equal(await themes.count(), 3);
      const themeLabel = await style(themes.first().locator('.eyebrow'));
      assert.equal(themeLabel.color, NEUTRAL);

      const availability = await style(page.locator('.availability-section'));
      assert.equal(availability.backgroundColor, PALE);
      assert.notEqual(availability.borderTopWidth, '0px');
      assert.notEqual(availability.borderBottomWidth, '0px');

      const newsletter = await style(page.locator('.book-newsletter'));
      assert.notEqual(newsletter.borderTopWidth, '0px');
      const submitLocator = page.locator('.book-newsletter .form-submit');
      const submit = await style(submitLocator);
      assert.equal(submit.backgroundColor, BLUE);

      if (width <= 639) {
        const contextCss = await style(page.locator('.section-context'));
        assert.equal(contextCss.position, 'relative');
      }

      if (width <= 899) {
        const themeList = await style(page.locator('.book-theme-list'));
        assert.equal(themeList.display, 'grid');
      }

      const footerHeading = await style(page.locator('.site-footer h2').first());
      assert.equal(footerHeading.color, BLUE);

      const launcher = page.locator('.assistant-widget__launcher');
      await launcher.waitFor({ state: 'attached', timeout: 4000 });
      const launcherCss = await style(launcher);
      if (width <= 1300) assert.equal(launcherCss.display, 'none', `${name}: launcher duplicado vuelve a cubrir lectura`);
      else assert.notEqual(launcherCss.display, 'none', `${name}: launcher desktop debería seguir disponible`);

      /* Interaction-state closure: inherited shell rules must not reintroduce
         teal/legacy accents once pointer/focus states have settled. */
      const headerHome = page.locator('.header-home');
      await headerHome.hover();
      await waitForStyle(headerHome, 'color', HEADER_BLUE);
      await waitForStyle(headerHome, 'backgroundColor', PALE);

      await primaryLocator.hover();
      await waitForStyle(primaryLocator, 'color', DEEP);

      await submitLocator.hover();
      await waitForStyle(submitLocator, 'backgroundColor', DEEP);
      assert.equal((await style(submitLocator)).color, 'rgb(255, 255, 255)');

      const social = page.locator('.site-footer .social-icon').first();
      await social.hover();
      await waitForStyle(social, 'backgroundColor', BLUE);
      assert.equal((await style(social)).color, 'rgb(255, 255, 255)');

      await page.locator('[data-explore-open]').click();
      const dialog = page.locator('[data-explore-dialog]');
      await dialog.waitFor({ state: 'visible', timeout: 3000 });
      const toggle = dialog.locator('.explore-row__toggle').first();
      assert.equal((await style(toggle)).color, BLUE, `${name}: toggle Explorar conserva acento legacy`);
      await toggle.hover();
      await waitForStyle(toggle, 'backgroundColor', BLUE);
      await waitForStyle(toggle, 'color', 'rgb(255, 255, 255)');
      await dialog.locator('[data-explore-close]').click();
      await page.waitForTimeout(100);

      await page.mouse.move(0, 0);
      await page.screenshot({ path: path.join(OUT, `manecillas-${name}.png`), fullPage: true });
      console.log(`ok /las-manecillas-del-recuerdo/ ${width}x${height}`);
    } catch (error) {
      failures.push({ name, message: error.message, stack: error.stack });
      console.error(`FAIL Manecillas ${width}x${height}: ${error.message}`);
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}

fs.writeFileSync(path.join(OUT, 'manecillas-design-report.json'), JSON.stringify({ failures }, null, 2));
if (failures.length) process.exitCode = 1;
else console.log('manecillas-design-browser: PASS');
