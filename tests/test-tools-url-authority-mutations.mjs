import assert from 'node:assert/strict';
import { httpsUrl, buildMetaTags } from '../assets/metadatos-libro.js';

const candidates = [
  'https://usuario:secreto@example.test/libro/',
  'https://usuario@example.test/libro/',
  'https://example.test@otro.example/libro/',
  'https://editorial.example.test.evil.test/libro/',
  'https://example.test/%0aotro',
  'https://example.test:443/libro/',
  'https://mañana.example/libro/',
  'https://example.test\\@evil.test/libro/',
  'javascript:alert(1)',
  'data:text/html,malicioso',
];

for (const candidate of candidates) {
  const canonical = httpsUrl(candidate);
  if (canonical) {
    const url = new URL(canonical);
    assert.equal(url.protocol,'https:',candidate);
    assert.equal(url.username,'',`credencial usuario emitida: ${candidate}`);
    assert.equal(url.password,'',`contraseña emitida: ${candidate}`);
    assert(!/[\u0000-\u001f]/.test(canonical),candidate);
  }
  const built = buildMetaTags({book:'Libro de prueba',url:candidate,image:candidate,authorUrl:candidate});
  assert(!built.lines.includes('usuario:secreto@'),`credenciales expuestas: ${candidate}`);
  assert(!built.lines.includes('href="javascript:'),`enlace ejecutable: ${candidate}`);
  assert(!built.lines.includes('content="data:text/html'),`URL data emitida: ${candidate}`);
}
console.log('PASS tools URL authority mutations');
