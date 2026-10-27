import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const fixtures = [
  {
    name: 'writer-tools',
    script: 'assets/writer-tools.js',
    input: '[data-wt-search]',
    cards: '.wt-card',
    html: `<form data-wt-filters><input data-wt-search><select data-wt-stage><option value=''></option></select><select data-wt-price><option value=''></option></select><input type='checkbox' data-wt-no-account><input type='checkbox' data-wt-local><input type='checkbox' data-wt-spanish><button type='button' data-wt-clear>Limpiar</button><p data-wt-count></p></form><section data-wt-grid><article class='wt-card' data-name='año' data-stages='escritura' data-price='gratis' data-account='0' data-local='1' data-spanish='1'>Año</article><article class='wt-card' data-name='ano' data-stages='escritura' data-price='gratis' data-account='0' data-local='1' data-spanish='1'>Ano</article><article class='wt-card' data-name='edición' data-stages='revision' data-price='gratis' data-account='0' data-local='1' data-spanish='1'>Edición</article></section><p data-wt-empty hidden></p>`
  },
  {
    name: 'atlas',
    script: 'assets/atlas-literario.js',
    input: '[data-atlas-search]',
    cards: '[data-atlas-card]',
    html: `<main data-atlas-index><input data-atlas-search><select data-atlas-category><option value=''></option></select><p data-atlas-count></p><article data-atlas-card data-category='libros' data-search='año'>Año</article><article data-atlas-card data-category='libros' data-search='ano'>Ano</article><article data-atlas-card data-category='libros' data-search='edición'>Edición</article></main>`
  }
];

const browser = await chromium.launch({headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
try {
  for (const fixture of fixtures) {
    const page = await browser.newPage();
    await page.setContent(fixture.html);
    await page.addScriptTag({path: fixture.script});
    for (const [query, expected] of [['ano', 'Ano'], ['AÑO', 'Año'], ['edicion', 'Edición'], ['EDICIÓN', 'Edición']]) {
      await page.locator(fixture.input).fill(query);
      const found = await page.locator(`${fixture.cards}:visible`).allTextContents();
      assert.deepEqual(found.map(x => x.trim()), [expected], `${fixture.name}: búsqueda ${query}`);
    }
    await page.close();
  }
  console.log('PASS linguistic search: ñ, n, accents and case');
} finally {
  await browser.close();
}
