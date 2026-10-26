import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = (process.env.SITE_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const browser = await chromium.launch();
const paths = ['/editoriales/', '/editoriales/minotauro/'];

try {
  for (const width of [375, 1440]) {
    const page = await browser.newPage({viewport:{width,height:900}});
    for (const path of paths) {
      const response = await page.goto(BASE + path, {waitUntil:'load'});
      assert.equal(response.status(), 200, `${path}: HTTP inesperado`);
      const result = await page.evaluate(() => {
        const graphs = [...document.querySelectorAll('script[type="application/ld+json"]')].flatMap(s => {
          const value = JSON.parse(s.textContent);
          return value['@graph'] || [value];
        });
        const breadcrumb = graphs.find(x => x['@type'] === 'BreadcrumbList');
        const entries = breadcrumb?.itemListElement || [];
        const nav = [...document.querySelectorAll('nav[aria-label]')].find(n => /migas|breadcrumb|ruta de navegación/i.test(n.getAttribute('aria-label') || ''));
        const links = nav ? [...nav.querySelectorAll('a[href]')].filter(a => {
          const s = getComputedStyle(a);
          return s.display !== 'none' && s.visibility !== 'hidden' && a.getClientRects().length > 0;
        }) : [];
        return {
          entries:entries.map(x => ({position:x.position,url:new URL(typeof x.item === 'string' ? x.item : x.item?.['@id'] || x.item?.url,location.href).href})),
          links:links.map(a => ({url:a.href,text:a.textContent.trim(),rect:(() => {const r=a.getBoundingClientRect();return {left:r.left,right:r.right,width:r.width,height:r.height};})()}))
        };
      });
      assert.ok(result.entries.length >= 2, `${path}: BreadcrumbList ausente o incompleto`);
      assert.deepEqual(result.entries.map(x => x.position), result.entries.map((_,i) => i+1), `${path}: posiciones BreadcrumbList discontinuas`);
      if (result.links.length) {
        assert.deepEqual(result.links.map(x => x.url), result.entries.slice(0,result.links.length).map(x => x.url), `${path}: migas visibles distintas del JSON-LD`);
        for (const link of result.links) {
          assert.ok(link.text && link.rect.width > 0 && link.rect.height > 0 && link.rect.left >= -1 && link.rect.right <= width+1, `${path} ${width}px: miga ilegible o recortada: ${JSON.stringify(link)}`);
        }
      }
    }
    await page.close();
  }
} finally {
  await browser.close();
}
console.log('OK: BreadcrumbList y navegación visible coherentes');