import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {JSDOM} from 'jsdom';

for (const path of ['redes-sociales/index.html', 'prensa.html']) {
  test(`${path}: external conversion links isolate opener`, () => {
    const dom = new JSDOM(readFileSync(path, 'utf8'), {
      url: 'https://davidportodiaz.com/'
    });
    const links = [...dom.window.document.querySelectorAll('a[target="_blank"]')]
      .filter(a => new URL(a.href).origin !== dom.window.location.origin);
    assert.ok(links.length > 0, `${path}: no external links examined`);
    for (const a of links) {
      const url = new URL(a.href);
      const rel = new Set(a.rel.toLowerCase().split(/\s+/));
      assert.equal(url.protocol, 'https:', `${path}: insecure destination ${a.href}`);
      assert.ok(rel.has('noopener') || rel.has('noreferrer'),
        `${path}: opener exposed by ${a.href}`);
    }
  });
}