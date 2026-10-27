import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const html = readFileSync(new URL('../redes-sociales/index.html', import.meta.url), 'utf8');
const data = JSON.parse(readFileSync(new URL('../redes-sociales/social-metrics.json', import.meta.url), 'utf8'));
const expected = new Map(data.networks.map(row => [row.id, row.profile_url]));

function attr(tag, name) {
  return tag.match(new RegExp('\\b' + name + '="([^"]*)"', 'i'))?.[1] ?? null;
}

for (const [id, profile] of expected) {
  test(`redes-sociales: identidad oficial de ${id}`, () => {
    const card = html.match(new RegExp('<li\\b[^>]*class="social-card"[^>]*data-network="' + id + '"[^>]*>([\\s\\S]*?)<\\/li>', 'i'));
    assert.ok(card, `/redes-sociales/: falta tarjeta ${id}`);
    const anchor = card[1].match(/<a\b[^>]*>/i);
    assert.ok(anchor, `/redes-sociales/: falta enlace ${id}`);
    const href = attr(anchor[0], 'href');
    assert.equal(href, profile, `/redes-sociales/: perfil ${id}: ${href} != ${profile}`);
    assert.equal(new URL(href).protocol, 'https:', `/redes-sociales/: ${id} no usa HTTPS`);
    assert.equal(attr(anchor[0], 'target'), '_blank', `/redes-sociales/: target de ${id}`);
    const rel = new Set((attr(anchor[0], 'rel') ?? '').split(/\s+/));
    assert.ok(rel.has('noopener') && rel.has('noreferrer'), `/redes-sociales/: ${id} carece de aislamiento externo`);
  });
}

test('redes-sociales: ninguna identidad duplicada', () => {
  assert.equal(expected.size, 6);
  assert.equal(new Set(expected.values()).size, expected.size, '/redes-sociales/: perfiles duplicados');
});