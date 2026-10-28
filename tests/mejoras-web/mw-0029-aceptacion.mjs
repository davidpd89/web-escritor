import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = (process.env.SITE_ORIGIN || '').replace(/\/+$/, '');
assert.ok(origin, 'SITE_ORIGIN es obligatorio');
const siteOrigin = new URL(origin).origin;
const browser = await chromium.launch({ headless: true });

async function waitIdle(page) {
  await page.waitForFunction(() =>
    document.querySelector('[data-assistant-form]')?.getAttribute('aria-busy') === 'false'
  );
}

try {
  for (const pathname of ['/asistente/', '/asistente/embed.html']) {
    const context = await browser.newContext();
    let releaseRemote;
    const remoteGate = new Promise(resolve => { releaseRemote = resolve; });
    try {
      // No se permite tráfico exterior. Turnstile y el servidor remoto
      // se sustituyen por respuestas locales controladas.
      await context.route('**/*', route => {
        if (new URL(route.request().url()).origin !== siteOrigin) return route.abort();
        return route.continue();
      });
      await context.route('**/assets/assistant-config.js', route => route.fulfill({
        status: 200,
        contentType: 'application/javascript',
        body: 'export const ASSISTANT_PUBLIC_CONFIG=Object.freeze({protocolVersion:1,remoteEnabled:true,assistantUrl:"/api/assistant",configUrl:"/api/assistant/config",turnstileSiteKey:"",queryMinLength:2,queryMaxLength:500});',
      }));
      await context.route('**/api/assistant/config', route => route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ protocol_version: 1, ok: true, enabled: true, turnstile_site_key: 'qa-site-key' }),
      }));
      await context.route('https://challenges.cloudflare.com/turnstile/v0/api.js*', route => route.fulfill({
        status: 200,
        contentType: 'application/javascript',
        body: 'globalThis.turnstile={render(_el,opts){globalThis.__mw29Turnstile=opts;return "qa"},execute(){queueMicrotask(()=>globalThis.__mw29Turnstile.callback("qa-token"))},reset(){}};',
      }));
      await context.route('**/api/assistant', async route => {
        if (route.request().method() !== 'POST') return route.continue();
        await remoteGate;
        // 200 con JSON no válido: provoca renderSearchFallback(query)
        // sin el texto especial de los errores HTTP 429.
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ protocol_version: 1, ok: true }),
        });
      });
      await context.route('**/pagefind/pagefind.js', route => route.fulfill({
        status: 200,
        contentType: 'application/javascript',
        body: 'export async function search(){return {results:[]}}',
      }));

      const page = await context.newPage();
      await page.goto(origin + pathname, { waitUntil: 'domcontentloaded' });
      const jump = page.locator('[data-assistant-jump-latest]');
      await jump.waitFor({ state: 'attached', timeout: 5000 });
      const log = page.locator('[data-assistant-log]');
      const input = page.locator('[data-assistant-query]');
      const send = page.locator('[data-assistant-submit]');
      const answers = log.locator('.assistant-message--assistant:not([data-pending])');

      assert.equal(await jump.count(), 1, `${pathname}: debe existir un solo botón`);
      assert.equal(await jump.isVisible(), false, `${pathname}: inicialmente oculto`);
      assert.equal(await log.getAttribute('role'), 'log');
      assert.equal(await log.getAttribute('aria-live'), 'polite');

      // Primera consulta: respuesta local conocida, con fuentes verificadas
      // en el registro del repositorio, sin depender del mock de Pagefind.
      await input.fill('¿De qué trata Las manecillas del recuerdo?');
      await send.click();
      await waitIdle(page);
      assert.equal(await answers.count(), 2, `${pathname}: bienvenida y primera respuesta`);
      assert.equal(await jump.count(), 1);
      assert.equal(await jump.isVisible(), true);
      assert.equal(await input.evaluate(el => el === document.activeElement), true,
        `${pathname}: el envío normal debe devolver el foco al campo`);
      const first = answers.last();
      const firstSources = first.locator('.assistant-message__sources a');
      assert.ok(await firstSources.count() > 0, `${pathname}: Manecillas debe incluir fuentes`);
      await jump.focus();
      await page.keyboard.press('Enter');
      assert.equal(await first.evaluate(el => el === document.activeElement && el.getAttribute('tabindex') === '-1'), true,
        `${pathname}: Enter debe enfocar la primera respuesta`);
      await page.keyboard.press('Tab');
      assert.equal(await firstSources.first().evaluate(el => el === document.activeElement), true,
        `${pathname}: Tab debe alcanzar el primer enlace`);

      // Segunda consulta: se detiene en un POST simulado mientras el usuario
      // lleva el foco al botón de salto, un control distinto de un enlace.
      const remoteRequest = page.waitForRequest(req =>
        req.method() === 'POST' && new URL(req.url()).pathname === '/api/assistant'
      );
      await input.fill('zznocoindide29');
      await send.click();
      await remoteRequest;
      await jump.focus();
      assert.equal(await jump.evaluate(el => el === document.activeElement), true);
      releaseRemote();
      await waitIdle(page);

      assert.equal(await jump.evaluate(el => el === document.activeElement), true,
        `${pathname}: la respuesta asíncrona no debe robar el foco al botón`);
      assert.equal(await answers.count(), 3, `${pathname}: deben existir dos respuestas completas`);
      assert.equal(await log.locator('.assistant-message--user').count(), 2);
      assert.equal(await jump.count(), 1, `${pathname}: no debe duplicarse el botón`);
      const second = answers.last();
      assert.match(await second.innerText(), /No encuentro una coincidencia clara/,
        `${pathname}: la respuesta no válida debe producir el fallback sin coincidencias`);
      const secondSources = second.locator('.assistant-message__sources a');
      assert.ok(await secondSources.count() > 0,
        `${pathname}: el fallback debe incluir enlaces de orientación`);
      await page.keyboard.press('Enter');
      assert.equal(await second.evaluate(el => el === document.activeElement && el.getAttribute('tabindex') === '-1'), true,
        `${pathname}: el botón debe apuntar a la segunda respuesta`);
      await page.keyboard.press('Tab');
      assert.equal(await secondSources.first().evaluate(el => el === document.activeElement), true,
        `${pathname}: Tab debe entrar en las fuentes de la segunda respuesta`);
      assert.equal(await log.getAttribute('role'), 'log');
      assert.equal(await log.getAttribute('aria-live'), 'polite');
    } finally {
      releaseRemote?.();
      await context.close();
    }
  }
} finally {
  await browser.close();
}

console.log('MW-0029: aceptación de teclado, respuestas consecutivas y foco asíncrono OK');
