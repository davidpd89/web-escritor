import assert from 'node:assert/strict';
import { chromium, firefox, webkit } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const BLUE = 'rgb(29, 79, 150)';
const GOLD = 'rgb(184, 134, 11)';
const PALE = 'rgb(238, 250, 255)';
const engines = { chromium, firefox, webkit };
const viewports = [
  ['desktop', 1440, 900],
  ['mobile', 390, 844],
];

for (const [engineName, launcher] of Object.entries(engines)) {
  const browser = await launcher.launch({ headless: true });
  try {
    for (const [mode, width, height] of viewports) {
      const context = await browser.newContext({ viewport: { width, height }, reducedMotion: 'reduce' });
      const page = await context.newPage();
      try {
        const response = await page.goto(`${ORIGIN}/fragmento/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
        assert.equal(response?.ok(), true, `${engineName}/${mode}: fragmento no carga`);
        await page.evaluate(() => document.fonts?.ready);

        const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
        assert.ok(overflow <= 1, `${engineName}/${mode}: overflow ${overflow}px`);

        const opening = await page.locator('.article-header .eyebrow').evaluate(el => {
          const s = getComputedStyle(el);
          return { family: s.fontFamily, color: s.color };
        });
        assert.match(opening.family.toLowerCase(), /yellowtail/, `${engineName}/${mode}: apertura sin Yellowtail`);
        assert.equal(opening.color, GOLD, `${engineName}/${mode}: apertura no dorada`);
        assert.equal(await page.locator('#article-title').evaluate(el => getComputedStyle(el).color), BLUE, `${engineName}/${mode}: H1 no azul`);

        const proseRail = await page.locator('.article-prose').evaluate(el => {
          const s = getComputedStyle(el);
          return { image: s.backgroundImage, size: s.backgroundSize };
        });
        assert.match(proseRail.image, /linear-gradient/, `${engineName}/${mode}: lectura sin rail`);
        assert.match(proseRail.size, /2\.5px\s+100%/, `${engineName}/${mode}: rail no es 2.5px`);

        const cta = await page.locator('.fragment-cta-box').evaluate(el => {
          const s = getComputedStyle(el);
          return { bg: s.backgroundColor, image: s.backgroundImage };
        });
        assert.equal(cta.bg, PALE, `${engineName}/${mode}: CTA final no pale`);
        assert.match(cta.image, /linear-gradient/, `${engineName}/${mode}: CTA final sin reglas`);

        const headerAssistant = page.locator('.header-search');
        assert.notEqual(await headerAssistant.evaluate(el => getComputedStyle(el).display), 'none', `${engineName}/${mode}: Asistente del header no disponible`);
        const assistantLauncher = page.locator('.assistant-widget__launcher');
        await assistantLauncher.waitFor({ state: 'attached', timeout: 2500 }).catch(() => {});
        if (await assistantLauncher.count()) {
          assert.equal(await assistantLauncher.evaluate(el => getComputedStyle(el).display), 'none', `${engineName}/${mode}: launcher flotante invade la lectura`);
        }

        await page.evaluate(() => {
          const total = document.body.scrollHeight - innerHeight;
          scrollTo(0, total * .70);
        });
        await page.waitForFunction(() => document.querySelector('#sticky-cta')?.classList.contains('visible'), null, { timeout: 3000 });
        const sticky = page.locator('#sticky-cta');
        const stickyData = await sticky.evaluate(el => {
          const s = getComputedStyle(el);
          const r = el.getBoundingClientRect();
          const action = getComputedStyle(el.querySelector('.primary-action'));
          return {
            image: s.backgroundImage,
            height: r.height,
            actionColor: action.color,
            actionFamily: action.fontFamily,
          };
        });
        assert.match(stickyData.image, /linear-gradient/, `${engineName}/${mode}: sticky sin reglas`);
        assert.equal(stickyData.actionColor, BLUE, `${engineName}/${mode}: sticky action no azul`);
        assert.match(stickyData.actionFamily.toLowerCase(), /yellowtail/, `${engineName}/${mode}: sticky action sin Yellowtail`);
        assert.ok(stickyData.height <= (width <= 620 ? 76 : 88), `${engineName}/${mode}: sticky demasiado alto ${stickyData.height}px`);

        if (await assistantLauncher.count()) {
          assert.equal(await assistantLauncher.evaluate(el => getComputedStyle(el).display), 'none', `${engineName}/${mode}: launcher intercepta sticky visible`);
        }

        await sticky.locator('#sticky-cta-close').click();
        assert.equal(await sticky.evaluate(el => el.classList.contains('visible')), false, `${engineName}/${mode}: sticky no cierra`);
        if (await assistantLauncher.count()) {
          assert.equal(await assistantLauncher.evaluate(el => getComputedStyle(el).display), 'none', `${engineName}/${mode}: launcher reaparece tras cerrar sticky`);
        }
        assert.notEqual(await headerAssistant.evaluate(el => getComputedStyle(el).display), 'none', `${engineName}/${mode}: Asistente del header desaparece tras cerrar sticky`);
        console.log(`ok [${engineName}] Samuel fragmento ${mode}`);
      } finally {
        await context.close();
      }
    }
  } finally {
    await browser.close();
  }
}

console.log('samuel-fragmento-design-cross-engine: PASS');
