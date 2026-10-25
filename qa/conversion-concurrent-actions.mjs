import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';

const port = 18762;
const origin = process.env.QA_ORIGIN || `http://127.0.0.1:${port}`;
const server = process.env.QA_ORIGIN ? null : spawn('python3', ['-m', 'http.server', String(port), '--bind', '127.0.0.1'], { stdio: 'ignore' });

try {
  if (server) {
    let ready = false;
    for (let i = 0; i < 40; i++) {
      try { ready = (await fetch(origin + '/')).ok; } catch {}
      if (ready) break;
      await delay(100);
    }
    assert.ok(ready, 'Servidor local no disponible');
  }
  for (const route of ['/libros/', '/privacidad.html']) {
    const responses = await Promise.all(Array.from({ length: 12 }, async () => {
      const response = await fetch(origin + route, { signal: AbortSignal.timeout(10000) });
      assert.equal(response.status, 200, `${route}: HTTP ${response.status}`);
      return response.text();
    }));
    for (const [i, html] of responses.entries()) {
      const contact = html.match(/<a\b[^>]*class="header-contact"[^>]*>/i)?.[0];
      const buy = html.match(/<a\b[^>]*class="header-buy"[^>]*>/i)?.[0];
      assert.ok(contact, `${route} respuesta ${i}: falta contacto`);
      assert.match(contact, /href="\/prensa\.html#contacto"/, `${route} respuesta ${i}: destino contacto`);
      assert.ok(buy, `${route} respuesta ${i}: falta compra`);
      assert.match(buy, /href="https:\/\//, `${route} respuesta ${i}: destino compra`);
      assert.match(buy, /\bnoopener\b/, `${route} respuesta ${i}: falta noopener`);
      assert.match(buy, /\bnoreferrer\b/, `${route} respuesta ${i}: falta noreferrer`);
      assert.equal(contact, responses[0].match(/<a\b[^>]*class="header-contact"[^>]*>/i)?.[0], `${route}: contacto inestable`);
      assert.equal(buy, responses[0].match(/<a\b[^>]*class="header-buy"[^>]*>/i)?.[0], `${route}: compra inestable`);
    }
  }
  console.log('OK: acciones de contacto y compra estables');
} finally {
  server?.kill();
}