import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import { chromium } from 'playwright';

const html = await fs.readFile(new URL('../publicar-web/index.html', import.meta.url), 'utf8');
const browser = await chromium.launch({ headless: true });
const cases = [
  ['breve', 'Mapa'],
  ['larga-con-espacios', 'Consulta de recursos para escritores '.repeat(12)],
  ['larga-sin-espacios', 'ValidacionDeMetadatosEditoriales'.repeat(15)],
  ['unicode', 'Edición «Ñandú» — revisión editorial '.repeat(14)],
];

try {
  for (const [name, replacement] of cases) {
    const mutated = html.replace('Sitemap generado', replacement);
    assert.notEqual(mutated, html, 'El punto de mutación desapareció');
    const page = await browser.newPage({ viewport: { width: 320, height: 800 } });
    await page.route('**/*', route => route.abort());
    await page.setContent(mutated);
    const result = await page.evaluate(() => ({
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      anchors: [...document.querySelectorAll('main a[href]')].map(a => ({
        text: a.textContent,
        visible: a.getClientRects().length > 0,
      })),
    }));
    assert.ok(result.overflow <= 1, `${name}: overflow ${result.overflow}px`);
    assert.ok(result.anchors.some(a => a.text === replacement && a.visible), `${name}: mutación no visible`);
    await page.close();
  }
  console.log(`PASS publicar-web: ${cases.length} mutaciones de longitud`);
} finally {
  await browser.close();
}
