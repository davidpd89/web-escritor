// Validacion empirica del auditor de pagina de libro (N.2, 2026-08-23).
//
// Ejecuta el motor real (assets/book-page-audit-rules.js) contra un
// corpus reproducible de 5 estructuras suficientemente distintas -- 2
// paginas REALES publicadas del propio sitio (leidas directamente de
// disco, no copiadas: si la pagina real cambia, este test lo nota) + 3
// fixtures representativos derivados de patrones reales de pagina de
// libro -- y compara el resultado contra las expectativas documentadas en
// tests/fixtures/book-page-audit-corpus/expectations.json.
//
// No depende de red en CI: todo el corpus vive en el propio repositorio.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { auditBookPageHtml } from '../assets/book-page-audit-rules.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const CORPUS_DIR = path.join(__dirname, 'fixtures', 'book-page-audit-corpus');
const expectations = JSON.parse(fs.readFileSync(path.join(CORPUS_DIR, 'expectations.json'), 'utf-8'));

let failures = 0;

function findingsById(result) {
  const map = new Map();
  for (const group of Object.values(result.findings)) {
    for (const item of group) map.set(item.id, item);
  }
  return map;
}

function check(condition, label) {
  if (condition) {
    console.log(`  ok   ${label}`);
  } else {
    console.log(`  FAIL ${label}`);
    failures += 1;
  }
}

for (const testCase of expectations.cases) {
  console.log(`\n=== ${testCase.id} (${testCase.kind}) ===`);
  const html = fs.readFileSync(path.join(ROOT, testCase.sourceFile), 'utf-8');
  const result = auditBookPageHtml(html, { url: `https://example.com/${testCase.id}/` });
  const byId = findingsById(result);

  for (const id of testCase.expectOk || []) {
    check(byId.get(id)?.status === 'ok', `${id} debe ser 'ok' (obtenido: ${byId.get(id)?.status})`);
  }
  for (const id of testCase.expectReview || []) {
    check(byId.get(id)?.status === 'review', `${id} debe ser 'review' (obtenido: ${byId.get(id)?.status})`);
  }
  for (const id of testCase.expectInfo || []) {
    check(byId.get(id)?.status === 'info', `${id} debe ser 'info' (obtenido: ${byId.get(id)?.status})`);
  }
  for (const id of testCase.expectOptional || []) {
    check(byId.get(id)?.status === 'optional', `${id} debe ser 'optional' (obtenido: ${byId.get(id)?.status})`);
  }
  if (testCase.expectSchemaOk) {
    check(result.findings.structured[0]?.status === 'ok', `book_schema debe ser 'ok' (obtenido: ${result.findings.structured[0]?.status})`);
  }
  if (testCase.expectNoConsistencyIssues) {
    check(result.findings.consistency.length === 0, `no debe haber inconsistencias (obtenidas: ${result.findings.consistency.map(f => f.id).join(', ') || 'ninguna'})`);
  }
  for (const id of testCase.expectConsistencyIssues || []) {
    check(result.findings.consistency.some(f => f.id === id), `debe detectarse la inconsistencia ${id}`);
  }
  for (const id of testCase.expectNoConsistencyIssueIds || []) {
    check(!result.findings.consistency.some(f => f.id === id), `NO debe detectarse la inconsistencia ${id} (falso positivo)`);
  }
}

if (failures > 0) {
  console.error(`\n${failures} FALLO(S)`);
  process.exitCode = 1;
} else {
  console.log('\ntests/test-book-page-audit-corpus: OK');
}
