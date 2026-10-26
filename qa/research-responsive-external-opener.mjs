import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = (process.env.SITE_BASE_URL || 'https://davidportodiaz.com').replace(/\/$/, '');
const ROUTES = ['/', '/herramientas/', '/editoriales/', '/prensa.html'];
const WIDTHS = [320,768,1024,1440];
const browser = await chromium.launch({headless:true});

try {
  for (const width of WIDTHS) {
    for (const route of ROUTES) {
      const page = await browser.newPage({viewport:{width,height:900}});
      try {
        const response = await page.goto(BASE + route, {waitUntil:'load'});
        assert.equal(response?.status(),200,`${route} @ ${width}px: HTTP ${response?.status()}`);
        const links = await page.locator('a[target="_blank"][href]').evaluateAll(nodes => nodes.map(a => ({href:a.href,rel:a.rel,external:new URL(a.href).origin !== location.origin})));
        const unsafe = links.filter(link => link.external && !link.rel.toLowerCase().split(/\s+/).includes('noopener') && !link.rel.toLowerCase().split(/\s+/).includes('noreferrer'));
        for (const link of unsafe) {
          const result = await page.evaluate(href => {
            const opened = window.open(href, '_blank');
            if (!opened) return {blocked:true};
            const isolated = opened.opener === null;
            opened.close();
            return {blocked:false,isolated};
          }, link.href);
          assert.ok(result.blocked || result.isolated,`${route} @ ${width}px: enlace externo sin aislamiento: ${link.href}`);
        }
      } finally {
        await page.close();
      }
    }
  }
} finally {
  await browser.close();
}