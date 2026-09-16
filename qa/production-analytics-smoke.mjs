// Real-production smoke, run manually/on-demand (NOT part of automatic PR
// or per-deploy CI): unlike qa/sitewide-console-errors-browser.mjs (which
// crawls 127.0.0.1, where the #520 production-hostname allowlist means
// trackers never fire), this hits the real davidportodiaz.com and the real
// staging preview host, to positively confirm trackers load exactly where
// they should after the #520 rewrite -- not just that they're absent where
// they shouldn't be. It generates real, small, one-time synthetic traffic
// in the real Clarity/GoatCounter/Metricool dashboards by design; that's
// the point, not a side effect. Deliberately NOT wired into deploy-pages.yml
// or any pull_request trigger, to avoid reintroducing the kind of repeated
// CI-generated pollution #516/#518 fixed, just at a smaller, real-hostname
// scale. Run by hand (`node qa/production-analytics-smoke.mjs`) when
// verifying an analytics-loading change.
//
// 2026-09-16 fix: the first version of this script only console.log'd the
// counts -- no assert, no exit(1). It "passed" by a human reading the
// output, which is exactly the failure mode this whole audit stretch is
// about (a green run that proves nothing). Now it actually fails the
// process if production isn't exactly 1/1/1 with zero issues.
//
// Staging is asserted at 0/0/0 -- true today (STAGING_STALE below is a
// known, tracked exception, not a silent skip) because that worker is
// running script.js?v=202609-launch-1 (main is at launch-24, no deploy
// automation for it exists in this repo -- see PR #522's description).
// Once it's redeployed, flip STAGING_STALE to false so this starts
// enforcing 0/0/0 for real instead of just logging the leak.
import { chromium } from 'playwright';

const PROD = 'https://davidportodiaz.com';
const STAGING = 'https://david-porto-preview.davidpd89.workers.dev';
const STAGING_STALE = true;

async function crawl(url, { label, waitMs = 4000, interact = true }) {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  const issues = [];
  const trackerHits = { goatcounter: 0, metricool: 0, clarity: 0 };

  page.on('console', (msg) => {
    const type = msg.type();
    if (type === 'error' || type === 'warning') issues.push(`console.${type}: ${msg.text()}`);
  });
  page.on('pageerror', (err) => issues.push(`pageerror: ${err.message}`));
  await page.exposeFunction('__reportRejection', (r) => issues.push(`unhandledrejection: ${r}`));
  await page.addInitScript(() => {
    window.addEventListener('unhandledrejection', (e) => {
      window.__reportRejection(e.reason && e.reason.message ? e.reason.message : String(e.reason));
    });
  });
  page.on('request', (req) => {
    const u = req.url();
    if (/gc\.zgo\.at\/count\.js/.test(u)) trackerHits.goatcounter++;
    if (/tracker\.metricool\.com\/resources\/be\.js/.test(u)) trackerHits.metricool++;
    if (/clarity\.ms\/tag\//.test(u)) trackerHits.clarity++;
  });
  page.on('response', (res) => {
    if (res.status() >= 400) issues.push(`http-error: ${res.status()} ${res.url()}`);
  });

  const t0 = Date.now();
  await page.goto(url, { waitUntil: 'load', timeout: 30000 });
  await page.waitForTimeout(waitMs); // catch scheduleBackgroundIdle's deferred Clarity injection + any late async error
  if (interact) {
    const navLink = page.locator('a[href^="/"]:visible').first();
    if (await navLink.count() > 0) {
      await navLink.hover().catch(() => {});
      await page.mouse.wheel(0, 400).catch(() => {});
    }
    await page.waitForTimeout(500);
  }
  const elapsed = Date.now() - t0;

  await browser.close();
  console.log(`\n=== ${label} (${url}) -- ${elapsed}ms ===`);
  console.log('tracker hits:', JSON.stringify(trackerHits));
  if (issues.length) {
    console.log(`issues (${issues.length}):`);
    for (const i of issues) console.log(`  - ${i}`);
  } else {
    console.log('issues: none');
  }
  return { trackerHits, issues };
}

const results = {};
results.production = await crawl(`${PROD}/`, { label: 'PRODUCTION Home' });
results.staging = await crawl(`${STAGING}/`, { label: 'STAGING Home', waitMs: 4000, interact: false });

console.log('\n=== SUMMARY ===');
console.log(`Production: goatcounter=${results.production.trackerHits.goatcounter} metricool=${results.production.trackerHits.metricool} clarity=${results.production.trackerHits.clarity} issues=${results.production.issues.length}`);
console.log(`Staging:    goatcounter=${results.staging.trackerHits.goatcounter} metricool=${results.staging.trackerHits.metricool} clarity=${results.staging.trackerHits.clarity} issues=${results.staging.issues.length}`);

const failures = [];
function check(condition, message) { if (!condition) failures.push(message); }

check(results.production.trackerHits.goatcounter === 1, `production GoatCounter: expected 1 hit, got ${results.production.trackerHits.goatcounter}`);
check(results.production.trackerHits.metricool === 1, `production Metricool: expected 1 hit, got ${results.production.trackerHits.metricool}`);
check(results.production.trackerHits.clarity === 1, `production Clarity: expected 1 hit, got ${results.production.trackerHits.clarity}`);
check(results.production.issues.length === 0, `production issues: expected 0, got ${results.production.issues.length} (${results.production.issues.join(' | ')})`);

if (STAGING_STALE) {
  console.log('\nSTAGING_STALE=true: not enforcing 0/0/0 on staging (known stale deploy, see file header). Logged above for visibility only.');
} else {
  check(results.staging.trackerHits.goatcounter === 0, `staging GoatCounter: expected 0 hits, got ${results.staging.trackerHits.goatcounter}`);
  check(results.staging.trackerHits.metricool === 0, `staging Metricool: expected 0 hits, got ${results.staging.trackerHits.metricool}`);
  check(results.staging.trackerHits.clarity === 0, `staging Clarity: expected 0 hits, got ${results.staging.trackerHits.clarity}`);
  check(results.staging.issues.length === 0, `staging issues: expected 0, got ${results.staging.issues.length} (${results.staging.issues.join(' | ')})`);
}

if (failures.length) {
  console.error(`\nproduction-analytics-smoke FAILED (${failures.length}):`);
  for (const f of failures) console.error(`  - ${f}`);
  process.exit(1);
}
console.log('\nproduction-analytics-smoke: PASS');
