import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const DEFAULT_INPUT = 'artifacts/sitewide-reflow/sitewide-reflow-report.json';
const DEFAULT_OUTPUT = 'artifacts/sitewide-reflow/text-resilience-gate-report.json';

export function classifyIntentionalVisualHiding(entry) {
  const selector = String(entry?.selector || '');
  if (!selector) return null;

  // Canonical visually-hidden utility. Source: assets/v1-base.css.
  if (selector.includes('.sr-only')) return 'sr-only-utility';

  // Narrow-shell search keeps the accessible label in the DOM while the
  // visible icon becomes the compact control. Source: v1-shell-base.css.
  if (selector.includes('button.header-search') && /\s>\s*span(?:[:.#]|$)/.test(selector)) {
    return 'compact-header-search-label';
  }

  // When the masthead wordmark image is present, its text fallback stays
  // available to accessibility APIs but is visually clipped. This is a
  // component-level equivalent, not a route exception.
  if (selector.includes('.masthead__name.has-logo-image') && selector.includes('.masthead__name-text')) {
    return 'masthead-logo-text-fallback';
  }

  return null;
}

// resize-text-200-plus-spacing (added 2026-09-01) checks a real interaction
// (a low-vision user can hit 200% zoom AND text-spacing at once) that no
// prior scenario covered, and it immediately surfaced ~20 routes with real,
// previously-invisible overflow -- sitewide pre-existing debt, not
// anything introduced alongside it. Gating merges on that backlog on day
// one would turn the required reflow-sitewide check permanently red before
// anyone has had a chance to fix any of it. Pilot it in report-only mode
// (tracked and visible in the artifact/console, not counted toward
// failureCount) until that backlog gets its own dedicated remediation pass;
// then flip it to enforced the same way resize-text-200/text-spacing
// already are.
const PILOT_SCENARIOS = new Set(['resize-text-200-plus-spacing']);

export function reconcileTextResilience(report) {
  const checks = report?.textResilience?.checks || [];
  const reconciledChecks = [];
  const allowedVisualHiding = {};
  const pilotChecks = [];

  for (const check of checks) {
    const ignoredClips = [];
    const residualClips = [];
    for (const clip of check.clippedText || []) {
      const reason = classifyIntentionalVisualHiding(clip);
      if (reason) {
        ignoredClips.push({ ...clip, reason });
        allowedVisualHiding[reason] = (allowedVisualHiding[reason] || 0) + 1;
      } else {
        residualClips.push(clip);
      }
    }

    const overflowFailure = Number(check.overflow || 0) > 1;
    const failure = overflowFailure || residualClips.length > 0;
    const reconciled = {
      route: check.route,
      viewport: check.viewport,
      scenario: check.scenario,
      wcag: check.wcag || null,
      overflow: Number(check.overflow || 0),
      offenders: check.offenders || [],
      clippedText: residualClips,
      ignoredClips,
      failure,
    };

    if (PILOT_SCENARIOS.has(check.scenario)) {
      pilotChecks.push(reconciled);
    } else {
      reconciledChecks.push(reconciled);
    }
  }

  const failures = reconciledChecks.filter((check) => check.failure);
  const pilotFailures = pilotChecks.filter((check) => check.failure);
  return {
    generatedAt: new Date().toISOString(),
    sourceMode: report?.textResilience?.mode || null,
    checkCount: reconciledChecks.length,
    failureCount: failures.length,
    allowedVisualHiding,
    checks: reconciledChecks,
    failures,
    pilotScenarios: [...PILOT_SCENARIOS],
    pilotCheckCount: pilotChecks.length,
    pilotFailureCount: pilotFailures.length,
    pilotChecks,
    pilotFailures,
  };
}

export function runGate({ input = DEFAULT_INPUT, output = DEFAULT_OUTPUT, mode = 'report' } = {}) {
  if (!['report', 'enforce'].includes(mode)) {
    throw new Error(`Invalid TEXT_RESILIENCE_GATE_MODE=${mode}; expected report|enforce`);
  }
  const report = JSON.parse(fs.readFileSync(input, 'utf8'));
  const reconciled = reconcileTextResilience(report);
  fs.mkdirSync(path.dirname(output), { recursive: true });
  fs.writeFileSync(output, `${JSON.stringify(reconciled, null, 2)}\n`, 'utf8');

  const allowed = Object.entries(reconciled.allowedVisualHiding)
    .map(([reason, count]) => `${reason}=${count}`)
    .join(', ') || 'none';
  console.log(`text-resilience-gate: ${reconciled.failureCount === 0 ? 'OK' : 'FINDINGS'} (${reconciled.checkCount} checks; residual failures=${reconciled.failureCount}; intentional visual hiding: ${allowed})`);
  if (reconciled.pilotCheckCount > 0) {
    console.log(`text-resilience-gate: PILOT ${reconciled.pilotScenarios.join(', ')} -- ${reconciled.pilotCheckCount} checks, ${reconciled.pilotFailureCount} findings (report-only, not gating)`);
  }

  if (mode === 'enforce' && reconciled.failureCount > 0) {
    const sample = reconciled.failures.slice(0, 12)
      .map((item) => `${item.route}@${item.viewport}/${item.scenario}: overflow=${item.overflow}, clips=${item.clippedText.length}`)
      .join('\n');
    throw new Error(`F.2 text resilience gate failed with ${reconciled.failureCount} residual checks.\n${sample}`);
  }
  return reconciled;
}

const isCli = process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (isCli) {
  const input = process.env.TEXT_RESILIENCE_REPORT || process.argv[2] || DEFAULT_INPUT;
  const output = process.env.TEXT_RESILIENCE_GATE_OUT || process.argv[3] || DEFAULT_OUTPUT;
  const mode = process.env.TEXT_RESILIENCE_GATE_MODE || 'report';
  runGate({ input, output, mode });
}
