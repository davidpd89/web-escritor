import assert from 'node:assert/strict';
import { chromium } from 'playwright';

// El ejecutor proporciona un servidor local mediante SITE_ORIGIN.
assert.ok(process.env.SITE_ORIGIN, 'SITE_ORIGIN es obligatorio');
const ORIGIN = new URL(process.env.SITE_ORIGIN).origin;
const EVENT_SRC = '/assets/eventos/david-porto-diaz-lectores-feria-libro-madrid-2026-samuel.webp';
const IMAGE_SELECTOR = [
  '.yale-lead__media img',
  '.yale-tile-grid--works img',
  '.yale-feature-book__media img',
  '.home-event__media img'
].join(', ');

const EXPECTED = [
  ['/assets/manecillas-del-recuerdo-3d-transparent.webp', 700, 982, 'eager'],
  ['/assets/manecillas-del-recuerdo-3d-transparent.webp', 700, 982, 'lazy'],
  ['/assets/samuel_entre_mundos_3d.webp', 1530, 2400, 'lazy'],
  ['/assets/david-porto-memoria-sinfondo.webp', 447, 558, 'lazy'],
  ['/assets/samuel_entre_mundos_3d.webp', 1530, 2400, 'lazy'],
  [EVENT_SRC, 1086, 1448, 'lazy']
];

const browser = await chromium.launch({
  headless: true,
  ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH
    ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH }
    : {})
});

try {
  // Contexto nuevo: caché vacía, viewport móvil y sin Service Workers.
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 1,
    isMobile: true,
    hasTouch: true,
    serviceWorkers: 'block'
  });

  // Evitar solicitudes externas y mantener la prueba autocontenida.
  await context.route('**/*', (route) => {
    const url = new URL(route.request().url());
    if (url.origin !== ORIGIN) return route.abort();
    return route.continue();
  });

  // Evitar que la introducción bloquee el scroll; simular visitante recurrente.
  await context.addInitScript(() => {
    sessionStorage.setItem('dp-intro-seen', '1');
  });

  const page = await context.newPage();
  const eventRequests = [];
  page.on('request', (request) => {
    if (new URL(request.url()).pathname === EVENT_SRC) {
      eventRequests.push(request.url());
    }
  });

  await page.goto(`${ORIGIN}/`, { waitUntil: 'load' });
  await page.waitForFunction(() =>
    document.documentElement.dataset.homeEditorialV3 === 'true'
  );

  assert.equal(await page.evaluate(() => window.scrollY), 0,
    'La comprobación inicial debe realizarse sin scroll');

  const eventImage = page.locator('.home-event--lead img');
  assert.equal(await eventImage.count(), 1, 'Debe existir una imagen de Eventos');

  // La imagen debe estar lejos del viewport: Chrome puede anticipar lazy
  // cuando el elemento está próximo a la zona visible.
  const distance = await eventImage.evaluate((img) =>
    img.getBoundingClientRect().top - window.innerHeight
  );
  assert.ok(distance > 1500,
    `Eventos debe estar lejos del viewport inicial; distancia=${distance}px`);

  // Permitir que se registren solicitudes iniciadas durante el render.
  await page.waitForTimeout(500);
  assert.equal(eventRequests.length, 0,
    'La fotografía de Eventos no debe solicitarse durante la carga inicial');

  assert.equal(await eventImage.getAttribute('loading'), 'lazy');

  // Desplazarse hasta la imagen y comprobar que el navegador la descarga.
  await eventImage.scrollIntoViewIfNeeded();
  await page.waitForFunction(() => {
    const img = document.querySelector('.home-event--lead img');
    return Boolean(img && img.complete && img.naturalWidth > 0);
  }, null, { timeout: 15000 });

  assert.ok(eventRequests.length >= 1,
    'La fotografía de Eventos debe solicitarse al entrar en su sección');

  const images = page.locator(IMAGE_SELECTOR);
  assert.equal(await images.count(), EXPECTED.length,
    'Se esperan seis imágenes en el flujo editorial');

  // Forzar la entrada de cada imagen lazy en el viewport.
  for (let i = 0; i < EXPECTED.length; i += 1) {
    await images.nth(i).scrollIntoViewIfNeeded();
    await page.waitForFunction((index) => {
      const img = document.querySelectorAll(
        '.yale-lead__media img, .yale-tile-grid--works img, .yale-feature-book__media img, .home-event__media img'
      )[index];
      return Boolean(img && img.complete && img.naturalWidth > 0);
    }, i, { timeout: 15000 });
  }

  const actual = await images.evaluateAll((elements) => elements.map((img) => ({
    src: new URL(img.src).pathname,
    width: Number(img.getAttribute('width')),
    height: Number(img.getAttribute('height')),
    loading: img.loading,
    complete: img.complete,
    naturalWidth: img.naturalWidth,
    fetchPriority: img.fetchPriority
  })));

  assert.deepEqual(
    actual.map((img) => [img.src, img.width, img.height, img.loading]),
    EXPECTED,
    'Deben conservarse rutas, dimensiones y políticas de carga'
  );
  assert.ok(actual.every((img) => img.complete && img.naturalWidth > 0),
    'Todas las imágenes deben terminar de cargarse correctamente');
  assert.equal(actual[0].fetchPriority, 'high',
    'La imagen principal debe conservar prioridad alta');

  await context.close();
  console.log('PASS MW-0010: Playwright móvil, lazy loading y dimensiones');
} finally {
  await browser.close();
}
