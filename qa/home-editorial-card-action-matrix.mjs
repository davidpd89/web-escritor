import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { localPage, readyHome } from './home-family-local-fixture.mjs';

const browser = await chromium.launch({ headless: true });
try {
  const { context, page } = await localPage(browser);
  await readyHome(page);

  const results = await page.locator([
    '.yale-tile', '.yale-rail-card',
    '.yale-works-card', '.home-event'
  ].join(',')).evaluateAll(cards => cards.map(card => {
    const title = card.querySelector('h3 a');
    const action = card.querySelector('.yale-text-link, .home-event__link');
    const media = card.querySelector('a[class*="__media"]');
    return {
      title: title?.getAttribute('href') || '',
      action: action?.getAttribute('href') || '',
      media: media?.getAttribute('href') || '',
      text: card.textContent.trim().slice(0, 80)
    };
  }));

  assert(results.length >= 8, 'Cobertura insuficiente de tarjetas');
  for (const card of results) {
    if (card.title && card.action) {
      assert.equal(card.action, card.title, card.text);
    }
    if (card.media && card.title) {
      assert.equal(card.media, card.title, card.text);
    }
  }

  const affiliateLinks = await page.locator('.editorial-home-flow a[href^="http"]').evaluateAll(links =>
    links.filter(a => /amazon\.|amzn\.to/.test(new URL(a.href).hostname)).map(a => ({
      href: a.href,
      rel: a.rel.split(/\s+/),
      name: a.getAttribute('aria-label') || a.textContent
    }))
  );
  assert(affiliateLinks.length > 0);
  for (const link of affiliateLinks) {
    for (const token of ['sponsored', 'nofollow', 'noopener', 'noreferrer']) {
      assert(link.rel.includes(token), `${link.href}: falta ${token}`);
    }
    assert.match(link.name, /afiliado/i, link.href);
  }

  await context.close();
  console.log('PASS home-editorial-card-action-matrix');
} finally {
  await browser.close();
}