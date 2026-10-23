import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { chromium } from 'playwright';

const root = process.cwd();
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'atlas-filter-'));
let browser;
try {
  const source = JSON.parse(fs.readFileSync('data/atlas-literario.json', 'utf8'));
  const titles = ['Biblioteca Áurea', 'Ruta de Cervantes', 'Biblioteca Negra'];
  const categories = ['bibliotecas', 'rutas-literarias', 'bibliotecas'];
  source.items = source.items.slice(0, 3).map((item, i) => ({
    ...item, title: titles[i], category: categories[i], status: 'published',
    verified_date: '2026-08-20',
    image: {src: '/assets/fixture.webp', alt: 'Imagen', credit: 'QA', license: 'CC0', source_url: 'https://example.org/image'}
  }));
  const sourceFile = path.join(tmp, 'source.json');
  fs.writeFileSync(sourceFile, JSON.stringify(source));
  const out = path.join(tmp, 'atlas');
  const generated = spawnSync('python3', ['scripts/build-atlas-literario.py', sourceFile, '--out', out], {cwd: root, encoding: 'utf8'});
  assert.equal(generated.status, 0, generated.stderr);
  const html = fs.readFileSync(path.join(out, 'index.html'), 'utf8').replace(/<script src="\/assets\/atlas-literario\.js" defer><\/script>/, '');
  browser = await chromium.launch({headless: true});
  const page = await browser.newPage();
  await page.route('**/*', route => route.abort());
  await page.setContent(html);
  await page.addScriptTag({path: path.join(root, 'assets/atlas-literario.js')});
  const search = page.locator('[data-atlas-search]');
  const category = page.locator('[data-atlas-category]');
  const check = async (visible, label) => {
    assert.equal(await page.locator('[data-atlas-card]:visible').count(), visible, label);
    assert.match(await page.locator('[data-atlas-count]').innerText(), new RegExp('^' + visible + ' '));
  };
  await check(3, 'inicial');
  await search.fill('BIBLIOTECA');
  await check(2, 'mayúsculas');
  await search.fill('aurea');
  await check(1, 'sin tilde');
  await category.selectOption('rutas-literarias');
  await check(0, 'intersección vacía');
  await search.fill('');
  await check(1, 'recuperación parcial');
  await category.selectOption('');
  await check(3, 'restablecimiento completo');
  await page.close();
} finally {
  if (browser) await browser.close();
  fs.rmSync(tmp, {recursive: true, force: true});
}
console.log('atlas-generated-filter-state-matrix: PASS');