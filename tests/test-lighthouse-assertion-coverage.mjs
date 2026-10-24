import assert from 'node:assert/strict';
import fs from 'node:fs';

const configs = [
  'lighthouserc.json',
  'qa/lighthouserc-findability.json',
  'qa/samuel-ecosystem-lighthouserc.json',
  'qa/tools-events-memory-lighthouserc.json'
];
let checked = 0;
const problems = [];
for (const path of configs) {
  const config = JSON.parse(fs.readFileSync(path, 'utf8'));
  const urls = config.ci?.collect?.url;
  assert.ok(Array.isArray(urls) && urls.length > 0, `${path}: URLs ausentes`);
  assert.equal(new Set(urls).size, urls.length, `${path}: URLs duplicadas`);
  assert.ok(config.ci.collect.numberOfRuns >= 3, `${path}: pocas ejecuciones`);
  const matrix = config.ci?.assert?.assertMatrix;
  const globalAssertions = config.ci?.assert?.assertions;
  assert.ok(matrix?.length || globalAssertions, `${path}: no hay assertions`);
  for (const url of urls) {
    const parsed = new URL(url);
    assert.equal(parsed.hostname, 'localhost', `${path}: URL no local`);
    const matching = matrix ? matrix.filter(group => new RegExp(group.matchingUrlPattern).test(url)) : [];
    if (matrix) {
      if (matching.length !== 1) problems.push(`${path}: ${url} coincide con ${matching.length} matrices`);
    }
    const assertions = matrix ? matching[0]?.assertions : globalAssertions;
    if (!assertions) continue;
    const a11y = assertions['categories:accessibility'];
    if (!Array.isArray(a11y) || a11y[0] !== 'error') problems.push(`${path}: accesibilidad no bloqueante en ${url}`);
    if (parsed.pathname === '/404.html') continue;
    const status = assertions['http-status-code'];
    if (!Array.isArray(status) || status[0] !== 'error' || status[1]?.minScore !== 1) {
      problems.push(`${path}: ${url} no bloquea explícitamente HTTP 4xx/5xx`);
    }
    checked++;
  }
}
assert.deepEqual(problems, [], '\n' + problems.join('\n'));
console.log(`PASS: ${checked} URLs Lighthouse tienen cobertura y contrato HTTP explícito`);