import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const path = '/redes-sociales/';
const html = readFileSync(new URL('../redes-sociales/index.html', import.meta.url), 'utf8');
const tags = [...html.matchAll(/<(?:script|link|img|iframe|source|meta)\b[^>]*>/gi)].map(m => m[0]);
const attr = (tag, name) => tag.match(new RegExp('\\b' + name + '="([^"]*)"', 'i'))?.[1] ?? null;

test('redes-sociales: recursos sin HTTP inseguro', () => {
  for (const tag of tags) {
    for (const name of ['src', 'href', 'content']) {
      const value = attr(tag, name);
      if (!value || !/^https?:\/\//i.test(value)) continue;
      assert.equal(new URL(value).protocol, 'https:', `${path}: ${name} inseguro: ${value}`);
    }
  }
});

test('redes-sociales: CSP efectiva para recursos activos', () => {
  const policies = tags.filter(tag => /http-equiv="Content-Security-Policy"/i.test(tag));
  assert.equal(policies.length, 1, `${path}: número de políticas CSP`);
  const policy = attr(policies[0], 'content');
  assert.ok(policy, `${path}: CSP vacía`);
  const directives = new Map(policy.split(';').map(part => part.trim().split(/\s+/)).filter(x => x[0]).map(([key, ...values]) => [key, values]));
  for (const key of ['default-src', 'script-src', 'object-src', 'base-uri']) {
    assert.ok(directives.has(key), `${path}: falta ${key}`);
  }
  assert.deepEqual(directives.get('object-src'), ["'none'"], `${path}: object-src inseguro`);
  assert.ok(!directives.get('script-src').includes("'unsafe-eval'"), `${path}: unsafe-eval`);
  assert.ok(!directives.get('script-src').includes("'unsafe-inline'"), `${path}: scripts inline sin restricción`);
  assert.ok(!directives.get('script-src').includes('*'), `${path}: script-src global`);
  assert.ok(!directives.get('base-uri').includes('*'), `${path}: base-uri global`);
});

test('redes-sociales: scripts ejecutables autorizados', () => {
  for (const match of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)) {
    const tag = '<script ' + match[1] + '>';
    const type = attr(tag, 'type');
    if (type === 'application/ld+json') continue;
    if (attr(tag, 'src')) continue;
    assert.equal(match[2].trim(), '', `${path}: script ejecutable inline no autorizado`);
  }
});