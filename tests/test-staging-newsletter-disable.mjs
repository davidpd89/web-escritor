// Point 23 of the 2026-08-20 corrective audit: staging must never create
// real Brevo contacts. script.js computes IS_STAGING from
// window.location.hostname against a small STAGING_HOSTNAMES allowlist and
// every newsletter submit handler short-circuits to a
// "Formulario desactivado en el entorno de pruebas." message when true.
//
// script.js is a plain global-scope browser script (no exports, heavy DOM
// use throughout) and is explicitly NOT being modularized as part of this
// pass, so this test does not import it as an ES module. Instead it
// extracts and re-checks the exact STAGING_HOSTNAMES/IS_STAGING source
// text, so a future edit that removes or typos the staging hostname (the
// actual risk here — a silent regression that would let staging create
// real subscribers) fails this test immediately.

import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const source = readFileSync(path.join(ROOT, 'script.js'), 'utf8');

// The known-good Cloudflare Pages preview hostname (confirmed working
// 2026-08-20 by the project owner directly against the live URL).
const STAGING_HOSTNAME = 'david-porto-preview.davidpd89.workers.dev';
const PRODUCTION_HOSTNAME = 'davidportodiaz.com';

// 1. The staging hostname must actually be present in the STAGING_HOSTNAMES set.
const setMatch = source.match(/STAGING_HOSTNAMES\s*=\s*new Set\(\[([^\]]*)\]\)/);
assert.ok(setMatch, 'STAGING_HOSTNAMES set not found in script.js');
const listed = setMatch[1];
assert.ok(listed.includes(STAGING_HOSTNAME), `STAGING_HOSTNAMES must include ${STAGING_HOSTNAME}`);
assert.ok(!listed.includes(PRODUCTION_HOSTNAME), 'STAGING_HOSTNAMES must never include the production hostname');

// 2. IS_STAGING must be derived from STAGING_HOSTNAMES.has(window.location.hostname),
// not some other check that could silently diverge.
assert.match(
  source,
  /IS_STAGING\s*=\s*STAGING_HOSTNAMES\.has\(window\.location\.hostname\)/,
  'IS_STAGING must be computed from STAGING_HOSTNAMES.has(window.location.hostname)'
);

// 3. Every newsletter submit handler must check IS_STAGING before doing
// anything else with the form (email validation, fetch to the Worker).
// Count occurrences of the disabled-message assignment: one per form
// (quiz, generic newsletter forms via submitNewsletter, popup) = 3.
const disabledMessageUses = (source.match(/STAGING_DISABLED_MESSAGE/g) || []).length;
// 1 definition + at least 3 usages (one per submit handler).
assert.ok(disabledMessageUses >= 4, `expected STAGING_DISABLED_MESSAGE to be defined once and used at least 3 times, found ${disabledMessageUses} occurrence(s)`);

console.log('test-staging-newsletter-disable: all assertions passed');
