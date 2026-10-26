import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {JSDOM} from 'jsdom';

const endpoint = 'https://subscribe.davidpd89.workers.dev';
const client = readFileSync('assets/newsletter-general.js', 'utf8');

test('newsletter client retains authorized HTTPS destination', () => {
  assert.match(client, /const ENDPOINT\s*=\s*['"]https:\/\/subscribe\.davidpd89\.workers\.dev['"]/);
});

for (const path of ['redes-sociales/index.html', 'prensa.html']) {
  test(`${path}: newsletter submission remains origin restricted`, () => {
    const doc = new JSDOM(readFileSync(path, 'utf8')).window.document;
    const forms = [...doc.querySelectorAll('form[data-newsletter-source]')];
    assert.ok(forms.length, `${path}: no newsletter forms`);
    const scripts = [...doc.querySelectorAll('script[src]')].map(s => s.getAttribute('src'));
    assert.ok(scripts.some(s => /^\/assets\/newsletter-general\.js(?:\?|$)/.test(s)),
      `${path}: newsletter client missing`);
    const csp = doc.querySelector('meta[http-equiv="Content-Security-Policy"]')?.content;
    assert.ok(csp, `${path}: missing CSP`);
    const connect = csp.split(';').map(s => s.trim()).find(s => s.startsWith('connect-src '));
    assert.ok(connect, `${path}: connect-src missing`);
    assert.ok(connect.split(/\s+/).includes(endpoint), `${path}: subscription endpoint blocked`);
    assert.ok(!connect.split(/\s+/).includes('*'), `${path}: unrestricted connections`);
    for (const form of forms) {
      const action = form.getAttribute('action');
      assert.ok(!action || action.startsWith('/') || action.startsWith('#'),
        `${path}: unexpected form destination ${action}`);
    }
  });
}