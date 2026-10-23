import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';

const BASE = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const registry = JSON.parse(fs.readFileSync('data/content-registry.json', 'utf8'));
const groups = new Map();
for (const x of registry.entries) {
  if ((x.status ?? registry.defaults.status) !== 'public' || !String(x.sourceFile || '').endsWith('.html')) continue;
  const key = x.territory || x.type || 'other';
  if (!groups.has(key)) groups.set(key, []);
  groups.get(key).push(x);
}
const routes = [...groups.values()].flatMap(rows => rows.sort((a,b) => a.url.localeCompare(b.url)).slice(0, 2)).map(x => x.url);
assert(routes.length >= 8, 'Muestra insuficiente');
const browser = await chromium.launch({ headless: true });
const failures = [];
let checked = 0;
try {
  for (const route of routes) {
    for (const width of [390, 1440]) {
      const page = await browser.newPage({ viewport: { width, height: 900 } });
      await page.route('**/*', r => {
        const u = new URL(r.request().url());
        return u.origin === new URL(BASE).origin || ['data:', 'blob:'].includes(u.protocol) ? r.continue() : r.abort();
      });
      try {
        await page.goto(BASE + route, { waitUntil: 'load' });
        const images = await page.evaluate(() => [...document.querySelectorAll('main img')].map(img => {
          const r = img.getBoundingClientRect();
          return {
            src: img.getAttribute('src'),
            loading: img.loading,
            area: r.width * r.height,
            visible: r.bottom > 0 && r.top < innerHeight && r.right > 0 && r.left < innerWidth
          };
        }).filter(x => x.visible && x.area >= 10000));
        checked += images.length;
        for (const image of images) {
          if (image.loading === 'lazy') failures.push(`${route} ${width}px: ${image.src}`);
        }
      } finally {
        await page.close();
      }
    }
  }
} finally {
  await browser.close();
}
assert(checked > 0, 'No se observaron imágenes críticas');
assert.deepEqual(failures, [], failures.join('\n'));
console.log(`PASS ${checked} imágenes visibles inicialmente`);
