import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await page.goto(`${BASE}/recomendaciones/libros/coraline/`);
  const links = page.locator('a[data-purchase-format]:visible');
  const count = await links.count();
  assert.ok(count > 0, 'La ficha debe mostrar enlaces de compra');
  for (let i = 0; i < count; i++) {
    const link = links.nth(i);
    await link.focus();
    assert.equal(await link.evaluate(el => document.activeElement === el), true);
    const info = await link.evaluate(el => ({ tag: el.tagName, href: el.getAttribute('href'), label: el.getAttribute('aria-label') || el.innerText.trim() }));
    assert.equal(info.tag, 'A');
    assert.ok(info.href);
    assert.ok(info.label.trim(), 'Enlace comercial sin nombre accesible');
    assert.equal(await link.getAttribute('tabindex'), '-1', 'El enlace no debe excluirse del orden natural del teclado');
  }
} finally {
  await browser.close();
}