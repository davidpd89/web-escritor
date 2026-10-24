import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { spawn } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const server = createServer((req, res) => {
  res.writeHead(503, { 'Content-Type': req.url.endsWith('.css') ? 'text/css' : 'text/html' });
  res.end('SIMULATED-SERVICE-UNAVAILABLE');
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}/`;
const directory = mkdtempSync(join(tmpdir(), 'compression-http-'));
const output = join(directory, 'report.json');
try {
  const result = await new Promise((resolve, reject) => {
    const child = spawn(process.execPath, ['qa/live-compression-origin.mjs'], {
      cwd: process.cwd(),
      env: { ...process.env, LIVE_COMPRESSION_BASE_URL: origin, LIVE_COMPRESSION_OUTPUT: output },
      stdio: ['ignore', 'pipe', 'pipe']
    });
    let stderr = '';
    child.stderr.on('data', chunk => { stderr += chunk; });
    child.on('error', reject);
    child.on('close', code => resolve({ code, stderr }));
  });
  const report = JSON.parse(readFileSync(output, 'utf8'));
  assert.equal(report.summary.observations, 9);
  assert.ok(report.results.every(item => item.status === 503));
  assert.equal(report.summary.failed, 9, 'Las respuestas 503 fueron clasificadas como observaciones correctas');
  assert.notEqual(result.code, 0, 'El auditor terminó con éxito pese a recibir únicamente HTTP 503');
} finally {
  await new Promise(resolve => server.close(resolve));
  rmSync(directory, { recursive: true, force: true });
}
console.log('PASS: auditor de compresión falla ante respuestas HTTP 503');