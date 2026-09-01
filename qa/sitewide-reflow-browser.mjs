import assert from 'node:assert/strict';
import fs from 'node:fs';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { chromium } from 'playwright';
import { auditTargetSizes } from './target-size-audit.mjs';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const ROOT = process.cwd();
const OUT_DIR = process.env.QA_OUT || 'qa-artifacts';
const REPORT_PATH = path.join(OUT_DIR, 'sitewide-reflow-report.json');
const TARGET_REPORT_PATH = path.join(OUT_DIR, 'sitewide-target-size-report.json');
const TARGET_SIZE_MODE = (process.env.TARGET_SIZE_MODE || 'report').toLowerCase();
const TEXT_RESILIENCE_MODE = process.env.TEXT_RESILIENCE_MODE || 'report';
if (!['off', 'report', 'enforce'].includes(TEXT_RESILIENCE_MODE)) {
  throw new Error(`TEXT_RESILIENCE_MODE inválido: ${TEXT_RESILIENCE_MODE}`);
}
if (!['report', 'enforce'].includes(TARGET_SIZE_MODE)) {
  throw new Error(`TARGET_SIZE_MODE must be report or enforce, got ${TARGET_SIZE_MODE}`);
}

const VIEWPORTS = [
  { width: 390, height: 900, reflow: true },
  { width: 768, height: 1000, reflow: true },
  { width: 1280, height: 900, reflow: false },
];
const TEXT_RESILIENCE_VIEWPORTS = [
  { width: 320, height: 900 },
  { width: 390, height: 900 },
  { width: 768, height: 1000 },
];
const TEXT_RESILIENCE_SCENARIOS = [
  {
    id: 'resize-text-200',
    css: 'html{font-size:200%!important}',
    wcag: '1.4.4',
  },
  {
    id: 'text-spacing',
    css: '*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}',
    wcag: '1.4.12',
  },
];

const IGNORE_DIRS = new Set([
  '.git',
  '.github',
  'node_modules',
  'qa-artifacts',
  'docs',
  'lab',
  '_tools',
  '_reddit',
  // Build-time sources, never served as pages: scripts/templates/*.html son
  // fragmentos reutilizables con placeholders [[...]] sin <html> propio
  // (p.ej. video-source.component.html), y tests/fixtures/*.html son
  // fixtures de test. Sin CSS del sitio, cualquiera desborda por diseno.
  'scripts',
  'tests',
]);

function normalizeRoute(value) {
  if (!value) return null;
  let route = value.trim();
  if (!route) return null;
  if (/^https?:\/\//i.test(route)) {
    try {
      route = new URL(route).pathname;
    } catch {
      return null;
    }
  }
  if (!route.startsWith('/')) route = `/${route}`;
  route = route.replace(/\/index\.html$/i, '/');
  route = route.replace(/\/+/g, '/');
  if (route !== '/' && route.endsWith('//')) route = route.slice(0, -1);
  return route;
}

function routeFromHtmlPath(filePath) {
  const rel = path.relative(ROOT, filePath).replace(/\\/g, '/');
  if (rel === 'index.html') return '/';
  if (rel.endsWith('/index.html')) return `/${rel.slice(0, -'index.html'.length)}`;
  return `/${rel}`;
}

// Recorrer el disco metia en la puerta ficheros que no se publican: la copia
// de trabajo tiene carpetas de notas e ideas sin versionar con HTML suelto que
// desbordaba cientos de px. En CI no aparecian —no estan en el repo— asi que
// el gate salia verde por accidente, no por acuerdo. `git ls-files` da el
// mismo conjunto en local y en CI: lo que de verdad se publica.
function walkHtmlFiles(dirPath, out) {
  const tracked = execFileSync('git', ['ls-files', '-z', '*.html'], { cwd: ROOT, encoding: 'utf8' })
    .split('\u0000')
    .filter(Boolean);
  for (const rel of tracked) {
    const segments = rel.split('/');
    if (segments.some((segment) => IGNORE_DIRS.has(segment) || segment.startsWith('.'))) continue;
    out.push(path.join(ROOT, rel));
  }
}

function collectRoutes() {
  const routes = new Set();

  const sitemap = path.join(ROOT, 'sitemap.xml');
  if (fs.existsSync(sitemap)) {
    const xml = fs.readFileSync(sitemap, 'utf8');
    const matches = [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)];
    for (const match of matches) {
      const route = normalizeRoute(match[1]);
      if (route) routes.add(route);
    }
  }

  const registryPath = path.join(ROOT, 'data', 'content-registry.json');
  if (fs.existsSync(registryPath)) {
    const payload = JSON.parse(fs.readFileSync(registryPath, 'utf8'));
    for (const item of payload?.routes || []) {
      if (!item || item.status === 'draft') continue;
      if (item.url) {
        const route = normalizeRoute(item.url);
        if (route) routes.add(route);
      }
      if (typeof item.sourceFile === 'string' && item.sourceFile.endsWith('.html')) {
        const route = normalizeRoute(routeFromHtmlPath(path.join(ROOT, item.sourceFile)));
        if (route) routes.add(route);
      }
    }
  }

  const htmlFiles = [];
  walkHtmlFiles(ROOT, htmlFiles);
  for (const filePath of htmlFiles) {
    const route = normalizeRoute(routeFromHtmlPath(filePath));
    if (route?.startsWith('/data/')) continue;
    if (route) routes.add(route);
  }

  // Explicit machine/readability surfaces that are part of release smoke.
  routes.add('/ai/');
  routes.add('/privacidad.html');
  routes.add('/aviso-legal.html');
  routes.add('/asistente/');

  return [...routes].sort((a, b) => a.localeCompare(b));
}

async function applyInspectorStyles(context, page, cssText) {
  const cdp = await context.newCDPSession(page);
  await cdp.send('Page.enable');
  await cdp.send('DOM.enable');
  await cdp.send('CSS.enable');
  const { frameTree } = await cdp.send('Page.getFrameTree');
  const { styleSheetId } = await cdp.send('CSS.createStyleSheet', { frameId: frameTree.frame.id });
  await cdp.send('CSS.setStyleSheetText', { styleSheetId, text: cssText });
}

async function settle(page) {
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
}

async function expandClosedDetails(page) {
  return page.evaluate(() => {
    const changed = [...document.querySelectorAll('details')].filter((details) => !details.open);
    window.__qaTargetSizeClosedDetails = changed;
    for (const details of changed) details.open = true;
    return changed.length;
  });
}

async function restoreClosedDetails(page) {
  await page.evaluate(() => {
    for (const details of window.__qaTargetSizeClosedDetails || []) details.open = false;
    window.__qaTargetSizeClosedDetails = [];
  });
}

async function measureOverflow(page) {
  return page.evaluate(() => {
    function hasHorizontalScrollerAncestor(node) {
      let parent = node.parentElement;
      while (parent && parent !== document.body) {
        const style = window.getComputedStyle(parent);
        if ((style.overflowX === 'auto' || style.overflowX === 'scroll') && parent.clientWidth > 0) {
          return true;
        }
        parent = parent.parentElement;
      }
      return false;
    }

    function selectorFor(el) {
      if (el.id) return `#${CSS.escape(el.id)}`;
      const parts = [];
      let node = el;
      while (node && node !== document.body && parts.length < 4) {
        let part = node.tagName.toLowerCase();
        if (node.classList.length) {
          part += [...node.classList].slice(0, 3).map((name) => `.${CSS.escape(name)}`).join('');
        }
        const parent = node.parentElement;
        if (parent) {
          const siblings = [...parent.children].filter((child) => child.tagName === node.tagName);
          if (siblings.length > 1) part += `:nth-of-type(${siblings.indexOf(node) + 1})`;
        }
        parts.unshift(part);
        node = parent;
      }
      return parts.join(' > ');
    }

    const zoom = Number.parseFloat(window.getComputedStyle(document.documentElement).zoom || '1') || 1;
    const vw = document.documentElement.clientWidth;
    let maxOverflow = 0;
    const offenders = [];

    for (const el of document.querySelectorAll('body *')) {
      const style = window.getComputedStyle(el);
      if (style.display === 'none' || style.visibility === 'hidden') continue;
      if (hasHorizontalScrollerAncestor(el)) continue;

      const rect = el.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0) continue;

      const rightOverflow = rect.right / zoom - vw;
      const leftOverflow = -(rect.left / zoom);
      const overflow = Math.max(0, rightOverflow, leftOverflow);
      if (overflow > maxOverflow) maxOverflow = overflow;
      if (overflow > 1) {
        offenders.push({
          selector: selectorFor(el),
          tag: el.tagName.toLowerCase(),
          classes: [...el.classList].slice(0, 8),
          overflow: Math.ceil(overflow),
          left: Math.round(rect.left / zoom),
          right: Math.round(rect.right / zoom),
          width: Math.round(rect.width / zoom),
          clientWidth: el.clientWidth,
          scrollWidth: el.scrollWidth,
          whiteSpace: style.whiteSpace,
          minWidth: style.minWidth,
          maxWidth: style.maxWidth,
          overflowX: style.overflowX,
          text: (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 120),
        });
      }
    }

    offenders.sort((a, b) => b.overflow - a.overflow || b.width - a.width);
    return {
      overflow: Math.ceil(Math.max(0, maxOverflow)),
      offenders: offenders.slice(0, 12),
    };
  });
}

async function measureClippedText(page) {
  return page.evaluate(() => {
    function selectorFor(el) {
      if (el.id) return `#${CSS.escape(el.id)}`;
      const parts = [];
      let node = el;
      while (node && node !== document.body && parts.length < 4) {
        let part = node.tagName.toLowerCase();
        if (node.classList.length) {
          part += [...node.classList].slice(0, 3).map((name) => `.${CSS.escape(name)}`).join('');
        }
        const parent = node.parentElement;
        if (parent) {
          const siblings = [...parent.children].filter((child) => child.tagName === node.tagName);
          if (siblings.length > 1) part += `:nth-of-type(${siblings.indexOf(node) + 1})`;
        }
        parts.unshift(part);
        node = parent;
      }
      return parts.join(' > ');
    }

    const clipped = [];
    for (const el of document.querySelectorAll('body *')) {
      const style = window.getComputedStyle(el);
      if (style.display === 'none' || style.visibility === 'hidden') continue;
      const hasOwnText = [...el.childNodes].some(node => node.nodeType === Node.TEXT_NODE && node.textContent.trim());
      if (!hasOwnText) continue;
      const clipsX = style.overflowX === 'hidden' || style.overflowX === 'clip';
      const clipsY = style.overflowY === 'hidden' || style.overflowY === 'clip';
      const hiddenX = clipsX && el.scrollWidth - el.clientWidth > 1;
      const hiddenY = clipsY && el.scrollHeight - el.clientHeight > 1;
      if (!hiddenX && !hiddenY) continue;
      clipped.push({
        selector: selectorFor(el),
        tag: el.tagName.toLowerCase(),
        hiddenX: hiddenX ? Math.ceil(el.scrollWidth - el.clientWidth) : 0,
        hiddenY: hiddenY ? Math.ceil(el.scrollHeight - el.clientHeight) : 0,
        overflowX: style.overflowX,
        overflowY: style.overflowY,
        textOverflow: style.textOverflow,
        whiteSpace: style.whiteSpace,
        text: (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 120),
      });
    }
    clipped.sort((a, b) => (b.hiddenX + b.hiddenY) - (a.hiddenX + a.hiddenY));
    return clipped.slice(0, 12);
  });
}

async function runScenario(browser, route, vp, { id, css, wcag, zoom = null }) {
  const context = await browser.newContext({
    viewport: { width: vp.width, height: vp.height },
    javaScriptEnabled: true,
    reducedMotion: 'reduce',
  });
  const page = await context.newPage();
  const key = `${route}@${vp.width}x${vp.height}/${id}`;
  try {
    const response = await page.goto(`${ORIGIN}${route}`, { waitUntil: 'networkidle' });
    assert.ok(response, `${key}: missing response`);
    assert.equal(response.status(), 200, `${key}: expected HTTP 200`);
    if (css) await applyInspectorStyles(context, page, css);
    await settle(page);
    if (zoom != null) {
      await page.evaluate(value => { document.documentElement.style.zoom = String(value); }, zoom);
      await settle(page);
    }
    const measurement = await measureOverflow(page);
    const clippedText = await measureClippedText(page);
    return {
      route,
      viewport: `${vp.width}x${vp.height}`,
      scenario: id,
      wcag: wcag || null,
      overflow: measurement.overflow,
      offenders: measurement.offenders,
      clippedText,
      failure: measurement.overflow > 1 || clippedText.length > 0,
    };
  } catch (error) {
    return {
      route,
      viewport: `${vp.width}x${vp.height}`,
      scenario: id,
      wcag: wcag || null,
      error: String(error?.message || error),
      failure: true,
    };
  } finally {
    await context.close();
  }
}

function failureLines(items, limit = 30) {
  const lines = [];
  for (const item of items.slice(0, limit)) {
    if (item.error) {
      lines.push(`${item.route} ${item.viewport} ${item.scenario}: ${item.error}`);
      continue;
    }
    lines.push(`${item.route} ${item.viewport} ${item.scenario}: overflow ${item.overflow}px, clipped ${item.clippedText?.length || 0}`);
    for (const offender of (item.offenders || []).slice(0, 3)) {
      lines.push(`  -> overflow ${offender.overflow}px ${offender.selector} [width=${offender.width}, white-space=${offender.whiteSpace}, min-width=${offender.minWidth}] ${JSON.stringify(offender.text)}`);
    }
    for (const clipped of (item.clippedText || []).slice(0, 3)) {
      lines.push(`  -> clipped ${clipped.selector} [x=${clipped.hiddenX}, y=${clipped.hiddenY}, overflow=${clipped.overflowX}/${clipped.overflowY}] ${JSON.stringify(clipped.text)}`);
    }
  }
  return lines;
}

const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH || undefined,
});
await fs.promises.mkdir(OUT_DIR, { recursive: true });

const routes = collectRoutes();
const reflowFailures = [];
const reflowChecks = [];
const targetFailures = [];
const targetChecks = [];
const textResilienceChecks = [];
const textResilienceFailures = [];

async function recordTargetAudit(page, route, vp, state) {
  const measurement = await auditTargetSizes(page, { minimum: 24 });
  const check = {
    route,
    viewport: `${vp.width}x${vp.height}`,
    state,
    ...measurement,
  };
  targetChecks.push(check);
  for (const failure of measurement.failures) {
    targetFailures.push({ route, viewport: `${vp.width}x${vp.height}`, state, ...failure });
  }
}

// F.1 + legacy reflow: one context per route/viewport covers target-size
// (default + expanded <details>) and the historical WCAG text-spacing +
// zoom=2 reflow contract, byte-for-byte in meaning with the pre-F.1 gate.
for (const route of routes) {
  for (const vp of VIEWPORTS) {
    const context = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      javaScriptEnabled: true,
      reducedMotion: 'reduce',
    });
    const page = await context.newPage();
    const key = `${route}@${vp.width}x${vp.height}`;
    let stage = 'page-load';
    try {
      const response = await page.goto(`${ORIGIN}${route}`, { waitUntil: 'networkidle' });
      assert.ok(response, `${key}: missing response`);
      assert.equal(response.status(), 200, `${key}: expected HTTP 200`);

      // F.1 default state: inspect the unmodified rendered page before
      // text-spacing/zoom mutations. 24x24 is WCAG 2.2 SC 2.5.8's minimum,
      // with inline/equivalent/spacing exceptions classified separately and
      // the small set of project-local product contracts checked as well.
      stage = 'target-default';
      await recordTargetAudit(page, route, vp, 'default');

      // A closed <details> makes its descendants unavailable, so default-state
      // geometry cannot audit the links/controls that appear after disclosure.
      // Open every initially-closed details element, audit that real state,
      // then restore it before the historical reflow mutation.
      const expandedCount = await expandClosedDetails(page);
      if (expandedCount > 0) {
        await settle(page);
        stage = 'target-expanded-details';
        await recordTargetAudit(page, route, vp, 'expanded-details');
        await restoreClosedDetails(page);
        await settle(page);
      }

      if (!vp.reflow) continue;

      stage = 'reflow';
      await applyInspectorStyles(
        context,
        page,
        '*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}'
      );
      await settle(page);
      await page.evaluate(() => {
        document.documentElement.style.zoom = '2';
      });
      await settle(page);
      const measurement = await measureOverflow(page);
      const { overflow, offenders } = measurement;
      reflowChecks.push({ route, viewport: `${vp.width}x${vp.height}`, overflow, offenders });
      if (overflow > 1) {
        reflowFailures.push({ route, viewport: `${vp.width}x${vp.height}`, overflow, offenders });
      }
    } catch (error) {
      const failure = {
        route,
        viewport: `${vp.width}x${vp.height}`,
        stage,
        error: String(error?.message || error),
      };
      if (stage.startsWith('target') || (!vp.reflow && stage !== 'reflow')) {
        targetFailures.push(failure);
      } else {
        reflowFailures.push(failure);
      }
    } finally {
      await context.close();
    }
  }
}

// F.2: do not use zoom as a substitute for text-only 200%. Run Resize Text
// and Text Spacing independently, in their own fresh contexts, so the
// artifact names the failing contract instead of conflating it with the
// legacy zoom-based reflow check above.
if (TEXT_RESILIENCE_MODE !== 'off') {
  for (const route of routes) {
    for (const vp of TEXT_RESILIENCE_VIEWPORTS) {
      for (const scenario of TEXT_RESILIENCE_SCENARIOS) {
        const result = await runScenario(browser, route, vp, scenario);
        textResilienceChecks.push(result);
        if (result.failure) textResilienceFailures.push(result);
      }
    }
  }
}

await browser.close();

const reflowReport = {
  origin: ORIGIN,
  routeCount: routes.length,
  viewportCount: VIEWPORTS.filter((item) => item.reflow).length,
  checks: reflowChecks,
  failures: reflowFailures,
  textResilience: {
    mode: TEXT_RESILIENCE_MODE,
    viewports: TEXT_RESILIENCE_VIEWPORTS.map(vp => `${vp.width}x${vp.height}`),
    scenarios: TEXT_RESILIENCE_SCENARIOS.map(({ id, wcag }) => ({ id, wcag })),
    checkCount: textResilienceChecks.length,
    failureCount: textResilienceFailures.length,
    checks: textResilienceChecks,
    failures: textResilienceFailures,
  },
};
fs.writeFileSync(REPORT_PATH, `${JSON.stringify(reflowReport, null, 2)}\n`, 'utf8');

const targetReport = {
  origin: ORIGIN,
  mode: TARGET_SIZE_MODE,
  minimumCssPx: 24,
  routeCount: routes.length,
  viewportCount: VIEWPORTS.length,
  viewports: VIEWPORTS.map(({ width, height }) => `${width}x${height}`),
  states: [...new Set(targetChecks.map((item) => item.state))],
  checkCount: targetChecks.length,
  targetCount: targetChecks.reduce((sum, item) => sum + item.targetCount, 0),
  exceptionCount: targetChecks.reduce((sum, item) => sum + item.exceptionCount, 0),
  productContractCheckCount: targetChecks.reduce((sum, item) => sum + (item.productContractCheckCount || 0), 0),
  failureCount: targetFailures.length,
  checks: targetChecks,
  failures: targetFailures,
};
fs.writeFileSync(TARGET_REPORT_PATH, `${JSON.stringify(targetReport, null, 2)}\n`, 'utf8');

const errorSections = [];
if (reflowFailures.length) {
  const lines = [];
  for (const item of reflowFailures.slice(0, 30)) {
    if (item.error) {
      lines.push(`${item.route} ${item.viewport} [${item.stage || 'reflow'}]: ${item.error}`);
      continue;
    }
    lines.push(`${item.route} ${item.viewport}: overflow ${item.overflow}px`);
    for (const offender of (item.offenders || []).slice(0, 3)) {
      lines.push(`  -> ${offender.overflow}px ${offender.selector} [width=${offender.width}, white-space=${offender.whiteSpace}, min-width=${offender.minWidth}] ${JSON.stringify(offender.text)}`);
    }
  }
  errorSections.push(`sitewide reflow failures (${reflowFailures.length})\n${lines.join('\n')}`);
}

if (TARGET_SIZE_MODE === 'enforce' && targetFailures.length) {
  const lines = targetFailures.slice(0, 40).map((item) => {
    if (item.error) return `${item.route} ${item.viewport} [${item.state || item.stage || 'target'}]: ${item.error}`;
    const contract = item.productContract
      ? ` product-contract=${item.productContract.selector} min=${item.productContract.minWidth ?? '-'}x${item.productContract.minHeight ?? '-'}`
      : '';
    return `${item.route} ${item.viewport} [${item.state || 'default'}]: ${item.selector} ${item.width}x${item.height}px ` +
      `reason=${item.reason}${contract} (${JSON.stringify(item.text)})`;
  });
  errorSections.push(`target-size failures (${targetFailures.length})\n${lines.join('\n')}`);
}

if (TEXT_RESILIENCE_MODE === 'enforce' && textResilienceFailures.length) {
  errorSections.push(`sitewide text-resilience failures (${textResilienceFailures.length})\n${failureLines(textResilienceFailures).join('\n')}`);
}

if (errorSections.length) {
  throw new Error(errorSections.join('\n\n'));
}

console.log(
  `sitewide-reflow-browser: OK (${routes.length} routes, ${reflowChecks.length} reflow checks; ` +
  `target-size ${TARGET_SIZE_MODE}: ${targetChecks.length} state checks, ${targetFailures.length} findings; ` +
  `text-resilience ${TEXT_RESILIENCE_MODE}: ${textResilienceChecks.length} checks, ${textResilienceFailures.length} findings)`
);
