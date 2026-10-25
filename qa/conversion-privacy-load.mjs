import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';

const port = 18763;
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
  const results = await Promise.all(Array.from({ length: 24 }, async (_, i) => {
    const response = await fetch(origin + '/privacidad.html', { signal: AbortSignal.timeout(10000) });
    return { i, status: response.status, html: await response.text() };
  }));
  for (const { i, status, html } of results) {
    const msg = `/privacidad.html solicitud ${i}: HTTP ${status}, ${html.length} caracteres`;
    assert.equal(status, 200, msg);
    assert.match(html, /<title>Política de privacidad/i, msg);
    assert.match(html, /name="robots" content="noindex, follow"/i, msg);
    assert.match(html, /rel="canonical" href="https:\/\/davidportodiaz\.com\/privacidad\.html"/i, msg);
    assert.match(html, /tratamiento de datos personales/i, msg);
    assert.match(html, /<\/html>/i, msg);
  }
  console.log('OK: política de privacidad disponible en 24 solicitudes');
} finally {
  server?.kill();
}