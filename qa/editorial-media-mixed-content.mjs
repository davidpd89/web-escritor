import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = (process.env.SITE_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const routes = ['/', '/las-manecillas-del-recuerdo/'];
const browser = await chromium.launch({headless:true});
try {
  const page = await browser.newPage();
  for (const route of routes) {
    const response = await page.goto(BASE + route, {waitUntil:'domcontentloaded'});
    assert.equal(response?.status(), 200, `${route}: HTTP ${response?.status()}`);
    const bad = await page.evaluate(() => {
      const results = [];
      const attributes = [
        ['img','src'],['img','srcset'],
        ['source','src'],['source','srcset'],
        ['video','src'],['video','poster'],
        ['audio','src'],['track','src']
      ];
      for (const [tag, attribute] of attributes) {
        for (const element of document.querySelectorAll(tag + '[' + attribute + ']')) {
          const raw = element.getAttribute(attribute) || '';
          const candidates = attribute === 'srcset' ? raw.split(',').map(v => v.trim().split(/\s+/)[0]) : [raw];
          for (const candidate of candidates) {
            if (!candidate) continue;
            const url = new URL(candidate, document.baseURI);
            if (url.protocol === 'http:' && url.hostname !== '127.0.0.1' && url.hostname !== 'localhost') {
              results.push({tag, attribute, value:candidate});
            }
          }
        }
      }
      return results;
    });
    assert.deepEqual(bad, [], `${route}: recursos multimedia HTTP inseguros: ${JSON.stringify(bad)}`);
  }
} finally {
  await browser.close();
}
console.log('PASS editorial media mixed content');