#!/usr/bin/env python3
from pathlib import Path

path = Path('qa/cuaderno-browser.mjs')
text = path.read_text(encoding='utf-8')

later = '''  const parsed = await page.locator('script[type="application/ld+json"]').evaluateAll(nodes => nodes.map(node => JSON.parse(node.textContent)));
  assert.ok(parsed.length >= 1, `${spec.key}: JSON-LD ausente`);

'''
if text.count(later) != 1:
    raise SystemExit(f'expected one later parsed block, got {text.count(later)}')
text = text.replace(later, '', 1)

anchor = '''  const ids = data.headings.map(h => h.id).filter(Boolean);
  assert.equal(new Set(ids).size, ids.length, `${spec.key}: heading ids duplicados`);
'''
if text.count(anchor) != 1:
    raise SystemExit(f'expected one validation anchor, got {text.count(anchor)}')
insert = anchor + '''  const parsed = await page.locator('script[type="application/ld+json"]').evaluateAll(nodes => nodes.map(node => JSON.parse(node.textContent)));
  assert.ok(parsed.length >= 1, `${spec.key}: JSON-LD ausente`);
'''
text = text.replace(anchor, insert, 1)
path.write_text(text, encoding='utf-8')
print('QA ORDER FIX APPLIED')
