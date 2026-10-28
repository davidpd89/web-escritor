import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const siteOrigin = process.env.SITE_ORIGIN;
assert.ok(siteOrigin, 'SITE_ORIGIN es obligatorio');

const origin = new URL(siteOrigin).origin;
const mediaPath = '/assets/video/hero-tinta-david-porto.mp4';
const mediaSrc = `${mediaPath}?v=2`;

const browser = await chromium.launch({ headless: true });

async function scenario(name, options) {
  const {
    seen = false,
    reducedMotion = 'no-preference',
    javaScriptEnabled = true,
    shouldLoad = false,
  } = options;

  const context = await browser.newContext({
    serviceWorkers: 'block',
    reducedMotion,
    javaScriptEnabled,
  });

  const mediaRequests = [];
  const inlineCspErrors = [];

  try {
    // Sin recursos externos: únicamente se permite el servidor local.
    // El contexto nuevo y el enrutamiento garantizan caché fría.
    await context.route('**/*', route => {
      const target = new URL(route.request().url());
      if (target.origin !== origin) return route.abort();
      return route.continue();
    });

    context.on('request', request => {
      const target = new URL(request.url());
      if (target.origin === origin && target.pathname === mediaPath) {
        mediaRequests.push(request.url());
      }
    });

    if (seen) {
      await context.addInitScript(() => {
        sessionStorage.setItem('dp-intro-seen', '1');
      });
    }

    if (javaScriptEnabled) {
      // Instrumentación previa a los scripts de la página: comprueba
      // que initHeroVideo() no llame a play() antes de asignar src.
      await context.addInitScript(() => {
        const originalPlay = HTMLMediaElement.prototype.play;
        HTMLMediaElement.prototype.play = function (...args) {
          if (this.hasAttribute('data-hero-video')) {
            window.__mw0009SourceAtPlay = this.querySelector('source')?.getAttribute('src') ?? null;
          }
          return originalPlay.apply(this, args);
        };
      });
    }

    const page = await context.newPage();
    page.on('console', message => {
      if (message.type() === 'error' &&
          /Refused to execute inline script/i.test(message.text())) {
        inlineCspErrors.push(message.text());
      }
    });

    const response = await page.goto(`${origin}/`, {
      waitUntil: 'load',
      timeout: 30000,
    });
    assert.equal(response?.status(), 200, `${name}: portada no disponible`);

    if (shouldLoad) {
      await page.waitForFunction(
        () => Object.prototype.hasOwnProperty.call(window, '__mw0009SourceAtPlay'),
        null,
        { timeout: 10000 },
      );
    }

    // Se observa también el intervalo posterior al evento load para
    // detectar solicitudes diferidas, sin depender de la caché del navegador.
    await page.waitForTimeout(400);

    const source = page.locator('[data-hero-video] source');
    assert.equal(await source.count(), 1, `${name}: fuente MP4 ausente`);

    const state = await source.evaluate(element => ({
      src: element.getAttribute('src'),
      dataSrc: element.getAttribute('data-src'),
      type: element.getAttribute('type'),
      preload: element.parentElement.preload,
      poster: element.parentElement.getAttribute('poster'),
    }));

    assert.equal(state.dataSrc, mediaSrc, `${name}: falta URL diferida`);
    assert.equal(state.type, 'video/mp4', `${name}: formato alterado`);
    assert.equal(state.preload, 'auto', `${name}: preload alterado`);
    assert.equal(state.poster, '/assets/hero-tinta-poster.webp?v=2', `${name}: poster alterado`);

    if (shouldLoad) {
      assert.equal(state.src, mediaSrc, `${name}: src no activado`);
      assert.ok(mediaRequests.length > 0, `${name}: el navegador no solicitó el MP4`);
      assert.ok(
        mediaRequests.every(url => new URL(url).search === '?v=2'),
        `${name}: versión inesperada del vídeo`,
      );

      const srcAtPlay = await page.evaluate(() => window.__mw0009SourceAtPlay);
      assert.equal(srcAtPlay, mediaSrc, `${name}: play() se ejecutó antes de asignar src`);
    } else {
      assert.equal(state.src, null, `${name}: src asignado indebidamente`);
      assert.equal(mediaRequests.length, 0, `${name}: hubo solicitudes al MP4`);
      if (javaScriptEnabled) {
        const played = await page.evaluate(
          () => Object.prototype.hasOwnProperty.call(window, '__mw0009SourceAtPlay'),
        );
        assert.equal(played, false, `${name}: se intentó reproducir el vídeo`);
      }
    }

    assert.deepEqual(inlineCspErrors, [], `${name}: script inline bloqueado por CSP`);
    console.log(`PASS MW-0009: ${name}`);
  } finally {
    await context.close();
  }
}

try {
  await scenario('sesión con introducción vista', {
    seen: true,
    shouldLoad: false,
  });

  await scenario('movimiento reducido en primera visita', {
    reducedMotion: 'reduce',
    shouldLoad: false,
  });

  await scenario('primera visita con movimiento normal', {
    shouldLoad: true,
  });

  await scenario('JavaScript desactivado', {
    javaScriptEnabled: false,
    shouldLoad: false,
  });

  console.log('MW-0009: todos los escenarios de aceptación superados');
} finally {
  await browser.close();
}
