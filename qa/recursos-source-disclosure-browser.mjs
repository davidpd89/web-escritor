import assert from 'node:assert/strict';
import { browserCase, DIRECTORY } from './recursos-risk-harness.mjs';

await browserCase(DIRECTORY, async page => {
  const cards = page.locator('.wt-card');
  assert.equal(await cards.count(), 8);

  for (let i = 0; i < await cards.count(); i++) {
    const card = cards.nth(i);
    const name = (await card.locator('h2').innerText()).trim();
    const details = card.locator('details');
    assert.equal(await details.count(), 1, `${name}: faltan fuentes`);
    assert.equal(await details.locator('summary').count(), 1);
    await details.locator('summary').click();
    assert.equal(await details.evaluate(el => el.open), true);

    const official = card.locator('.id-card__actions a');
    assert.equal(await official.count(), 1, `${name}: enlace oficial`);
    const sources = details.locator('.tool-source-list a');
    assert.ok(await sources.count() >= 1, `${name}: fuente primaria ausente`);
    const links = await card.locator('.tool-source-list a, .id-card__actions a').evaluateAll(nodes =>
      nodes.map(node => ({ href: node.href, target: node.target, rel: node.rel })));
    for (const link of links) {
      assert.equal(new URL(link.href).protocol, 'https:', `${name}: ${link.href}`);
      if (link.target === '_blank') {
        assert.ok(link.rel.includes('noopener') && link.rel.includes('noreferrer'), `${name}: rel inseguro`);
      }
    }
  }
  console.log('PASS recursos: fuentes y enlaces oficiales');
});
