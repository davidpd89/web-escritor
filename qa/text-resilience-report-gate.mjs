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

export function reconcileTextResilience(report) {
  const checks = report?.textResilience?.checks || [];
  const reconciledChecks = [];
  const allowedVisualHiding = {};

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
    reconciledChecks.push({
      route: check.route,
      viewport: check.viewport,
      scenario: check.scenario,
      wcag: check.wcag || null,
      overflow: Number(check.overflow || 0),
      offenders: check.offenders || [],
      clippedText: residualClips,
      ignoredClips,
      failure,
    });
  }

  const failures = reconciledChecks.filter((check) => check.failure);
  return {
    generatedAt: new Date().toISOString(),
    sourceMode: report?.textResilience?.mode || null,
    checkCount: reconciledChecks.length,
    failureCount: failures.length,
    allowedVisualHiding,
    checks: reconciledChecks,
    failures,
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
