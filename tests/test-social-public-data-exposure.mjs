import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const root = new URL('../redes-sociales/', import.meta.url);
const paths = ['social-metrics.json', 'panel.js', 'gpt_social_reader.mjs'];
const forbidden = /^(?:brand_?id|client_?id|client_?secret|access_?token|refresh_?token|api_?key|authorization|password|session_?id)$/i;

function check(value, path) {
  if (Array.isArray(value)) {
    value.forEach((item, i) => check(item, `${path}[${i}]`));
    return;
  }
  if (!value || typeof value !== 'object') return;
  for (const [key, item] of Object.entries(value)) {
    assert.ok(!forbidden.test(key), `/redes-sociales/social-metrics.json: campo privado ${path}.${key}`);
    check(item, `${path}.${key}`);
  }
}

test('redes-sociales: JSON público sin campos privados anidados', () => {
  const data = JSON.parse(readFileSync(new URL('social-metrics.json', root), 'utf8'));
  check(data, '$');
  assert.equal(data.schema_version, 1, '/redes-sociales/social-metrics.json: versión inesperada');
  for (const row of data.networks) {
    const url = new URL(row.profile_url);
    assert.equal(url.protocol, 'https:', `/redes-sociales/: URL pública insegura para ${row.id}`);
    assert.equal(url.username, '', `/redes-sociales/: usuario incrustado en URL de ${row.id}`);
    assert.equal(url.password, '', `/redes-sociales/: contraseña incrustada en URL de ${row.id}`);
    // Facebook pages without a vanity name are addressed only by their numeric id.
    assert.match(url.search, row.id === 'facebook' ? /^\?id=\d+$/ : /^$/, `/redes-sociales/: parámetros de consulta en perfil ${row.id}`);
  }
});

test('redes-sociales: recursos públicos sin credenciales literales', () => {
  for (const path of paths) {
    const content = readFileSync(new URL(path, root), 'utf8');
    assert.doesNotMatch(content, /(?:Bearer\s+[A-Za-z0-9._~+\/-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,})/, `/redes-sociales/${path}: posible credencial publicada`);
  }
});