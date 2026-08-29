import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const OUT = process.env.QA_OUT || 'artifacts/sitewide-reflow';
fs.mkdirSync(OUT, { recursive: true });

const BLUE = 'rgb(29, 79, 150)';
const DEEP = 'rgb(13, 44, 87)';
const HEADER_BLUE = 'rgb(10, 77, 159)';
const GOLD = 'rgb(184, 134, 11)';
const NEUTRAL = 'rgb(111, 106, 100)';
const PALE = 'rgb(238, 250, 255)';
const WHITE = 'rgb(255, 255, 255)';

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

async function css(locator, pseudo = null) {
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
      borderLeftColor: cs.borderLeftColor,
      borderLeftWidth: cs.borderLeftWidth,
      borderRadius: cs.borderRadius,
      display: cs.display,
      fontFamily: cs.fontFamily,
      fontWeight: cs.fontWeight,
      gridTemplateColumns: cs.gridTemplateColumns,
      paddingLeft: cs.paddingLeft,
      paddingRight: cs.paddingRight,
      position: cs.position,
      width: cs.width,
      height: cs.height,
      textTransform: cs.textTransform,
    };
  }, pseudo);
}

async function box(locator) {
  const value = await locator.boundingBox();
  assert.ok(value, `no bounding box for ${await locator.evaluate(el => el.className || el.id || el.tagName)}`);
  return { ...value, right: value.x + value.width, bottom: value.y + value.height };
}

async function waitForStyle(locator, property, expected, timeout = 1200) {
  await locator.evaluate(async (el, args) => {
    const start = performance.now();
    while (getComputedStyle(el)[args.property] !== args.expected) {
      if (performance.now() - start > args.timeout) {
        throw new Error(`${args.property} did not settle to ${args.expected}; got ${getComputedStyle(el)[args.property]}`);
      }
      await new Promise(resolve => requestAnimationFrame(resolve));
    }
  }, { property, expected, timeout });
}

const browser = await chromium.launch({ headless: true });
const failures = [];
try {
  for (const [name, width, height] of viewports) {
    const context = await browser.newContext({ viewport: { width, height }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    try {
      const response = await page.goto(`${ORIGIN}/libros/samuel-entre-mundos/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
      assert.ok(response?.ok(), `${name}: Samuel no carga`);
      await page.evaluate(() => document.fonts?.ready);

      const coverImg = page.locator('.samuel-object img');
      await coverImg.waitFor({ state: 'visible', timeout: 10000 });
      await coverImg.evaluate(async img => {
        if (!img.complete) await new Promise((resolve, reject) => {
          img.addEventListener('load', resolve, { once: true });
          img.addEventListener('error', reject, { once: true });
        });
        if (typeof img.decode === 'function') await img.decode().catch(() => {});
      });

      assert.equal(await page.locator('html').getAttribute('data-editorial-context'), 'samuel');
      assert.equal(await page.locator('main').getAttribute('data-family'), 'book-samuel');
      const token = await page.locator('body').evaluate(el => getComputedStyle(el).getPropertyValue('--sam-blue').trim());
      assert.equal(token, '#1d4f96', `${name}: capa Samuel no aplicada`);

      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      assert.ok(overflow <= 1, `${name}: overflow horizontal ${overflow}px`);

      const opening = await css(page.locator('.samuel-threshold__copy>.eyebrow'));
      assert.match(opening.fontFamily.toLowerCase(), /yellowtail/, `${name}: apertura hero sin Yellowtail`);
      assert.equal(opening.color, GOLD, `${name}: apertura hero fuera del dorado`);
      assert.notEqual(opening.backgroundImage, 'none', `${name}: apertura hero sin highlight azul`);

      const h1 = await css(page.locator('#samuel-title'));
      assert.equal(h1.color, BLUE, `${name}: H1 fuera del azul`);
      assert.equal(h1.fontWeight, '800', `${name}: H1 sin peso editorial`);

      const cover = page.locator('.samuel-object');
      const before = await css(cover, '::before');
      const after = await css(cover, '::after');
      assert.match(before.backgroundImage, /corner-bracket-blue-gold\.svg/, `${name}: falta bracket superior`);
      assert.match(after.backgroundImage, /corner-bracket-blue-gold\.svg/, `${name}: falta bracket inferior`);
      const coverBox = await box(coverImg);
      assert.ok(coverBox.width > 100 && coverBox.height > 150, `${name}: portada demasiado pequeña`);

      const threshold = page.locator('.samuel-threshold');
      const rail = await css(threshold, '::before');
      assert.equal(rail.width, '2.5px', `${name}: rail hero no es 2.5px`);
      assert.equal(rail.backgroundColor, BLUE, `${name}: rail hero no es azul`);
      if (width > 900) {
        const thresholdCss = await css(threshold);
        assert.ok(thresholdCss.gridTemplateColumns.split(' ').length >= 2, `${name}: hero desktop perdió dos columnas`);
      } else {
        const thresholdCss = await css(threshold);
        assert.equal(thresholdCss.gridTemplateColumns.split(' ').length, 1, `${name}: hero portable no apila`);
        assert.equal(rail.position, 'absolute');
      }

      const facts = page.locator('.samuel-facts');
      const factsCss = await css(facts);
      assert.equal(factsCss.borderTopColor, BLUE, `${name}: facts sin regla azul`);
      assert.equal((await css(facts.locator('dt').first())).color, NEUTRAL, `${name}: metadata hero no neutral`);

      const heroPrimary = page.locator('.samuel-actions .primary-action').first();
      const primaryCss = await css(heroPrimary);
      assert.match(primaryCss.fontFamily.toLowerCase(), /yellowtail/, `${name}: CTA principal sin Yellowtail`);
      assert.equal(primaryCss.color, BLUE, `${name}: CTA principal fuera del azul`);
      assert.equal(primaryCss.backgroundColor, 'rgba(0, 0, 0, 0)', `${name}: CTA principal volvió a botón relleno`);

      const heads = page.locator('.samuel-section__head');
      assert.ok(await heads.count() >= 14, `${name}: faltan registros Samuel`);
      const firstHead = heads.first();
      const firstFolio = await css(firstHead.locator(':scope > .folio'));
      const firstEyebrow = await css(firstHead.locator(':scope > div > .eyebrow'));
      const firstH2 = await css(firstHead.locator('h2'));
      const firstHeadBody = await css(firstHead.locator(':scope > div'));
      assert.equal(firstFolio.color, NEUTRAL, `${name}: folio no neutral`);
      assert.match(firstEyebrow.fontFamily.toLowerCase(), /yellowtail/, `${name}: apertura de registro sin Yellowtail`);
      assert.equal(firstEyebrow.color, GOLD, `${name}: apertura de registro no dorada`);
      assert.equal(firstH2.color, BLUE, `${name}: H2 de registro no azul`);
      assert.match(firstHeadBody.backgroundSize, /2\.5px\s+100%/, `${name}: cabecera de registro sin rail 2.5px`);

      const registerProse = await css(page.locator('.samuel-register__prose'));
      assert.match(registerProse.backgroundSize, /2\.5px\s+100%/, `${name}: prosa principal sin rail`);

      const ledger = page.locator('.samuel-ledger').first();
      assert.equal((await css(ledger)).borderTopColor, BLUE, `${name}: ledger técnico sin regla azul`);
      assert.equal((await css(ledger.locator('dt').first())).color, NEUTRAL, `${name}: dt técnico no neutral`);

      const fit = page.locator('.samuel-fit__split').first();
      const fitCss = await css(fit);
      assert.equal(fitCss.borderTopColor, BLUE, `${name}: fit sin azul superior`);
      assert.equal(fitCss.borderBottomColor, GOLD, `${name}: fit sin dorado inferior`);
      if (width <= 900) {
        const fitSecond = await css(fit.locator(':scope > div').nth(1));
        assert.equal(fitSecond.paddingLeft, '0px', `${name}: segunda mitad del fit conserva sangría desktop`);
        assert.equal(fitSecond.paddingRight, '0px', `${name}: segunda mitad del fit conserva padding desktop`);
        assert.equal(fitSecond.borderLeftWidth, '0px', `${name}: split apilado conserva borde vertical`);
        assert.equal(fitSecond.borderTopColor, BLUE, `${name}: split apilado pierde regla azul horizontal`);
      }

      const routeList = page.locator('.samuel-route-list').first();
      assert.equal((await css(routeList)).borderTopColor, BLUE, `${name}: route ledger sin azul`);
      const routeAction = routeList.locator('li>a').first();
      assert.match((await css(routeAction)).fontFamily.toLowerCase(), /yellowtail/, `${name}: acción de ruta sin Yellowtail`);

      const mechanics = page.locator('.samuel-mechanics__ledger');
      assert.equal((await css(mechanics)).borderTopColor, BLUE, `${name}: mecánica sin regla azul`);
      assert.equal((await css(mechanics.locator('h3').first())).color, BLUE, `${name}: mecánica sin jerarquía azul`);

      const reviews = page.locator('.samuel-proof__stream');
      assert.ok(await reviews.locator('li').count() >= 9, `${name}: stream de reseñas incompleto`);
      assert.equal((await css(reviews)).borderTopColor, BLUE, `${name}: reseñas sin regla azul`);
      assert.equal((await css(reviews.locator('cite').first())).color, NEUTRAL, `${name}: cita de reseña no neutral`);

      const buyRows = page.locator('#comprar .ledger__row');
      assert.equal(await buyRows.count(), 5, `${name}: ledger de compra debe tener cinco opciones`);
      const buyAction = buyRows.first().locator('.ledger__action');
      assert.match((await css(buyAction)).fontFamily.toLowerCase(), /yellowtail/, `${name}: compra sin acción manuscrita`);
      assert.equal((await css(buyAction)).color, BLUE, `${name}: compra fuera de azul`);

      const signed = await css(page.locator('#ejemplar-firmado .samuel-narrow'));
      assert.equal(signed.backgroundColor, PALE, `${name}: firmado sin énfasis práctico`);
      assert.equal(signed.borderLeftWidth, '0px', `${name}: firmado vuelve a border fraccional cuantizable`);
      assert.match(signed.backgroundImage, /linear-gradient/, `${name}: firmado sin rail robusto`);
      assert.match(signed.backgroundSize, /2\.5px\s+100%/, `${name}: rail firmado no conserva 2.5px efectivos`);

      const worldAction = page.locator('.samuel-world__split .text-action');
      assert.match((await css(worldAction)).fontFamily.toLowerCase(), /yellowtail/, `${name}: Noveris sin acción manuscrita`);

      const quiz = page.locator('#samuel-quiz-app');
      const quizCss = await css(quiz);
      assert.equal(quizCss.backgroundColor, PALE, `${name}: quiz no usa superficie azul pálida`);
      assert.equal(quizCss.borderTopColor, BLUE, `${name}: quiz sin borde azul`);
      assert.equal(quizCss.borderBottomColor, GOLD, `${name}: quiz sin acento dorado`);
      assert.equal(quizCss.borderRadius, '0px', `${name}: quiz volvió a card redondeada`);
      const progress = await css(quiz.locator('.quiz-progress-bar'));
      assert.match(progress.backgroundImage, /linear-gradient/, `${name}: progreso quiz sin gradiente azul/dorado`);
      assert.equal((await css(quiz.locator('.quiz-step-label'))).color, GOLD, `${name}: paso quiz no dorado`);
      assert.equal((await css(quiz.locator('.quiz-question-text'))).color, BLUE, `${name}: pregunta quiz no azul`);
      const option = quiz.locator('.quiz-option').first();
      assert.equal((await css(option)).backgroundColor, WHITE, `${name}: opción quiz no blanca`);
      await option.hover();
      await waitForStyle(option, 'color', DEEP);

      // Modal: visual contract plus native-dialog/focus restoration behaviour.
      const modalTrigger = page.locator('.samuel-actions [data-buy-modal]').first();
      await modalTrigger.scrollIntoViewIfNeeded();
      await modalTrigger.focus();
      await modalTrigger.click();
      const dialog = page.locator('#buy-dialog');
      await dialog.waitFor({ state: 'visible', timeout: 4000 });
      await page.waitForFunction(() => getComputedStyle(document.querySelector('#buy-dialog')).borderTopColor === 'rgb(29, 79, 150)');
      const dialogCss = await css(dialog);
      assert.equal(dialogCss.backgroundColor, WHITE, `${name}: modal compra conserva material beige`);
      assert.equal(dialogCss.borderTopColor, BLUE, `${name}: modal compra sin borde azul`);
      assert.equal(dialogCss.borderBottomColor, GOLD, `${name}: modal compra sin acento dorado`);
      assert.equal(dialogCss.borderRadius, '0px', `${name}: modal compra conserva card redondeada`);
      const modalTitle = await css(dialog.locator('.buy-dialog-title'));
      const modalEyebrow = await css(dialog.locator('.buy-dialog-eyebrow'));
      assert.equal(modalTitle.color, BLUE, `${name}: título modal no azul`);
      assert.match(modalEyebrow.fontFamily.toLowerCase(), /yellowtail/, `${name}: eyebrow modal sin Yellowtail`);
      assert.equal(modalEyebrow.color, GOLD, `${name}: eyebrow modal no dorado`);
      const modalPrimary = await css(dialog.locator('.buy-option--primary'));
      assert.equal(modalPrimary.backgroundColor, PALE, `${name}: opción primaria modal no azul pálido`);
      if (width === 1280 || width === 390) {
        await page.screenshot({ path: path.join(OUT, `samuel-modal-${name}.png`), fullPage: false });
      }
      await dialog.locator('.buy-dialog-close').click();
      await dialog.waitFor({ state: 'hidden', timeout: 2000 });
      assert.equal(await modalTrigger.evaluate(el => el === document.activeElement), true, `${name}: modal no restaura foco`);

      if (width <= 639) {
        assert.equal((await css(page.locator('.section-context'))).position, 'relative', `${name}: context nav sigue sticky en móvil estrecho`);
      }

      const footerHeading = await css(page.locator('.site-footer h2').first());
      assert.equal(footerHeading.color, BLUE, `${name}: footer no unificado`);

      const launcher = page.locator('.assistant-widget__launcher');
      await launcher.waitFor({ state: 'attached', timeout: 4000 });
      const launcherCss = await css(launcher);
      if (width <= 1300) assert.equal(launcherCss.display, 'none', `${name}: launcher duplicado sobre página larga`);
      else assert.notEqual(launcherCss.display, 'none', `${name}: launcher desktop debería seguir visible`);

      const headerHome = page.locator('.header-home');
      await headerHome.hover();
      await waitForStyle(headerHome, 'color', HEADER_BLUE);
      await waitForStyle(headerHome, 'backgroundColor', PALE);

      await page.mouse.move(0, 0);
      await page.evaluate(() => {
        history.replaceState(null, '', location.pathname);
        window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
      });
      await page.waitForTimeout(120);
      await page.screenshot({ path: path.join(OUT, `samuel-${name}.png`), fullPage: true });
      console.log(`ok Samuel ${width}x${height}`);
    } catch (error) {
      failures.push({ name, message: error.message, stack: error.stack });
      console.error(`FAIL Samuel ${width}x${height}: ${error.message}`);
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}

fs.writeFileSync(path.join(OUT, 'samuel-design-report.json'), JSON.stringify({ failures }, null, 2));
if (failures.length) process.exitCode = 1;
else console.log('samuel-design-browser: PASS');
