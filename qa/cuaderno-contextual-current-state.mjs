import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const cases = [
  {
    route: '/cuaderno/temas/',
    label: 'Índice de colecciones'
  },
  {
    route: '/cuaderno/temas/fantasia-de-portales/',
    label: 'Colección Fantasía de portales'
  }
];

const browser = await chromium.launch({
  headless: true,
  ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH
    ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH }
    : {})
});

try {
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    javaScriptEnabled: false
  });

  await context.route('**/*', route => {
    const url = new URL(route.request().url());
    if (url.origin !== new URL(BASE).origin) {
      return route.abort();
    }
    return route.continue();
  });

  const page = await context.newPage();

  for (const spec of cases) {
    const response = await page.goto(new URL(spec.route, BASE).href);
    assert.equal(response?.status(), 200, `${spec.label}: documento accesible`);

    const state = await page.locator('nav.section-context').evaluateAll(navs =>
      navs.flatMap(nav => [...nav.querySelectorAll('a[aria-current="page"]')]
        .map(link => ({
          href: new URL(link.getAttribute('href'), document.baseURI).pathname,
          label: link.textContent.trim()
        })))
    );

    for (const link of state) {
      assert.equal(
        link.href,
        spec.route,
        `${spec.label}: «${link.label}» está marcado como página actual, pero conduce a ${link.href}`
      );
    }

    const breadcrumb = page.locator('main nav[aria-label="Ruta de navegación"]');
    assert.equal(await breadcrumb.count(), 1, `${spec.label}: breadcrumb disponible`);
    assert.equal(
      await breadcrumb.locator('[aria-current="page"]').count(),
      1,
      `${spec.label}: una única ubicación actual en el breadcrumb`
    );
  }

  await context.close();
} finally {
  await browser.close();
}
