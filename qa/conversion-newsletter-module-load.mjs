import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { Script } from 'node:vm';

const port = 18764;
const origin = process.env.QA_ORIGIN || `http://127.0.0.1:${port}`;
const server = process.env.QA_ORIGIN ? null : spawn('python3', ['-m', 'http.server', String(port), '--bind', '127.0.0.1'], { stdio: 'ignore' });
const route = '/assets/newsletter-popup.js';
const digest = bytes => createHash('sha256').update(bytes).digest('hex');

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
  const expected = await readFile('assets/newsletter-popup.js');
  const expectedHash = digest(expected);
  const results = await Promise.all(Array.from({ length: 30 }, async (_, i) => {
    const response = await fetch(origin + route, { signal: AbortSignal.timeout(10000) });
    return { i, status: response.status, type: response.headers.get('content-type'), bytes: Buffer.from(await response.arrayBuffer()) };
  }));
  for (const result of results) {
    const msg = `${route} solicitud ${result.i}: HTTP ${result.status}, ${result.bytes.length} bytes`;
    assert.equal(result.status, 200, msg);
    assert.match(result.type || '', /javascript/i, msg);
    assert.equal(digest(result.bytes), expectedHash, `${msg}: contenido distinto del fichero publicado`);
    const source = result.bytes.toString('utf8');
    assert.doesNotThrow(() => new Script(source), `${msg}: JavaScript incompleto`);
    for (const token of ['isValidNewsletterEmail', 'postNewsletter', 'newsletterErrorMessage', 'pending_confirmation']) {
      assert.ok(source.includes(token), `${msg}: falta ${token}`);
    }
  }
  console.log('OK: 30 respuestas completas del módulo newsletter');
} finally {
  server?.kill();
}