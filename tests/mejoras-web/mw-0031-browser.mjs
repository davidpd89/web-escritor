import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.SITE_ORIGIN || '').replace(/\/$/, '');
assert(/^https?:\/\//.test(ORIGIN), 'SITE_ORIGIN debe indicar el servidor local de pruebas');

const WEBP = '/assets/samuel_entre_mundos_3d.webp';
const AVIF = '/assets/samuel_entre_mundos_3d.avif';
const browser = await chromium.launch({
  headless: true,
  ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH
    ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH }
    : {}),
});

async function verify(javaScriptEnabled) {
  const context = await browser.newContext({
    javaScriptEnabled,
    viewport: { width: 1400, height: 900 },
  });
  try {
    const page = await context.newPage();
    const requests = [];

    // The acceptance test depends exclusively on the locally served site.
    await page.route('**/*', (route) =>
      route.request().url().startsWith(`${ORIGIN}/`)
        ? route.continue()
        : route.abort());

    page.on('request', (request) => {
      if (request.resourceType() !== 'image') return;
      const pathname = new URL(request.url()).pathname;
      if (pathname === AVIF || pathname === WEBP) requests.push(pathname);
    });

    await page.goto(`${ORIGIN}/`, { waitUntil: 'domcontentloaded' });
    if (javaScriptEnabled) {
      await page.locator('html[data-home-editorial-v3="true"]').waitFor();
    }

    const selectors = javaScriptEnabled
      ? [
          `.yale-tile__media picture > img[src="${WEBP}"]`,
          `.yale-feature-book__media picture > img[src="${WEBP}"]`,
        ]
      : [`.promo-band > picture > img[src="${WEBP}"]`];

    assert.equal(selectors.length, javaScriptEnabled ? 2 : 1);

    for (const selector of selectors) {
      const image = page.locator(selector);
      assert.equal(await image.count(), 1, `Imagen no encontrada: ${selector}`);
      await image.scrollIntoViewIfNeeded();

      await page.waitForFunction((s) => {
        const img = document.querySelector(s);
        return Boolean(img && img.complete && img.naturalWidth > 0 &&
          img.currentSrc.endsWith('/assets/samuel_entre_mundos_3d.avif'));
      }, selector, { timeout: 15000 });

      const result = await image.evaluate((img) => {
        const picture = img.parentElement;
        const source = picture?.querySelector(':scope > source[type="image/avif"]');
        return {
          parentTag: picture?.tagName,
          source: source?.getAttribute('srcset'),
          previousTag: img.previousElementSibling?.tagName,
          src: img.getAttribute('src'),
          currentSrc: img.currentSrc,
          alt: img.getAttribute('alt'),
          width: img.getAttribute('width'),
          height: img.getAttribute('height'),
          loading: img.getAttribute('loading'),
          decoding: img.getAttribute('decoding'),
          naturalWidth: img.naturalWidth,
          naturalHeight: img.naturalHeight,
        };
      });

      assert.equal(result.parentTag, 'PICTURE');
      assert.equal(result.previousTag, 'SOURCE');
      assert.equal(result.source, AVIF);
      assert.equal(result.src, WEBP);
      assert(result.currentSrc.endsWith('.avif'), result.currentSrc);
      assert(result.alt && result.alt.trim().length > 0);
      assert.equal(result.width, '1530');
      assert.equal(result.height, '2400');
      assert.equal(result.naturalWidth, 1530);
      assert.equal(result.naturalHeight, 2400);
      assert.equal(result.decoding, 'async');
      assert.equal(
        result.loading,
        javaScriptEnabled && selector.includes('yale-feature-book') ? 'eager' : 'lazy',
      );
    }

    assert(requests.includes(AVIF), `AVIF no solicitado (JS=${javaScriptEnabled}): ${requests}`);
    assert(!requests.includes(WEBP), `Descarga WebP inesperada (JS=${javaScriptEnabled}): ${requests}`);
  } finally {
    await context.close();
  }
}

try {
  await verify(true);
  await verify(false);
  console.log('MW-0031 browser acceptance: PASS');
} finally {
  await browser.close();
}
