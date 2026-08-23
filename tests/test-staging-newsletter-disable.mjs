// Point 23 of the 2026-08-20 corrective audit: staging must never create
// real Brevo contacts. script.js computes IS_STAGING from
// window.location.hostname against a small STAGING_HOSTNAMES allowlist.
//
// H.1 (2026-08-23) extracted the newsletter popup into
// assets/newsletter-popup.js. The staging contract therefore spans two
// classic browser scripts now: script.js owns the staging authority and the
// generic newsletter handler; newsletter-popup.js consumes the same authority
// for the popup handler. This test follows that architecture instead of
// relying on a stale occurrence count inside script.js alone.

import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const source = readFileSync(path.join(ROOT, 'script.js'), 'utf8');
const popupSource = readFileSync(path.join(ROOT, 'assets', 'newsletter-popup.js'), 'utf8');

// The known-good Cloudflare preview hostname (confirmed working 2026-08-20).
const STAGING_HOSTNAME = 'david-porto-preview.davidpd89.workers.dev';
const PRODUCTION_HOSTNAME = 'davidportodiaz.com';
const STAGING_GUARD_RE = /if\s*\(IS_STAGING\)\s*\{?[\s\S]{0,180}?STAGING_DISABLED_MESSAGE/;

// 1. The staging hostname must actually be present in STAGING_HOSTNAMES.
const setMatch = source.match(/STAGING_HOSTNAMES\s*=\s*new Set\(\[([^\]]*)\]\)/);
assert.ok(setMatch, 'STAGING_HOSTNAMES set not found in script.js');
const listed = setMatch[1];
assert.ok(listed.includes(STAGING_HOSTNAME), `STAGING_HOSTNAMES must include ${STAGING_HOSTNAME}`);
assert.ok(!listed.includes(PRODUCTION_HOSTNAME), 'STAGING_HOSTNAMES must never include the production hostname');

// 2. IS_STAGING must be derived from the shared hostname authority.
assert.match(
  source,
  /IS_STAGING\s*=\s*STAGING_HOSTNAMES\.has\(window\.location\.hostname\)/,
  'IS_STAGING must be computed from STAGING_HOSTNAMES.has(window.location.hostname)'
);

// 3. The disabled message has one authority in script.js. Extracted modules
// consume that binding; they must not copy their own staging hostname/message.
const definitions = source.match(/const\s+STAGING_DISABLED_MESSAGE\s*=/g) || [];
assert.equal(definitions.length, 1, 'STAGING_DISABLED_MESSAGE must have exactly one definition in script.js');
assert.doesNotMatch(
  popupSource,
  /const\s+(?:STAGING_HOSTNAMES|IS_STAGING|STAGING_DISABLED_MESSAGE)\s*=/,
  'newsletter-popup.js must consume the shared staging authority, not duplicate it'
);

// 4. Every current newsletter submit path must fail closed on staging before
// calling postNewsletter. The old Noveris quiz handler was removed by H.1 as
// dead code; the two live paths are the generic forms and the extracted popup.
assert.match(source, STAGING_GUARD_RE, 'generic newsletter forms must stop on staging');
assert.match(popupSource, STAGING_GUARD_RE, 'newsletter popup must stop on staging');

for (const [label, text] of [['generic newsletter forms', source], ['newsletter popup', popupSource]]) {
  const guard = text.search(/if\s*\(IS_STAGING\)/);
  const request = text.search(/postNewsletter\s*\(/);
  assert.ok(guard >= 0, `${label}: staging guard missing`);
  assert.ok(request >= 0, `${label}: postNewsletter call missing`);
  assert.ok(guard < request, `${label}: staging guard must execute before postNewsletter`);
}

console.log('test-staging-newsletter-disable: all assertions passed');
