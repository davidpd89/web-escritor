import assert from 'node:assert/strict';
import fs from 'node:fs';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const ROOT = process.cwd();
const OUT_DIR = process.env.QA_OUT || 'qa-artifacts';
const REPORT_PATH = path.join(OUT_DIR, 'sitewide-reflow-report.json');
const TEXT_RESILIENCE_MODE = process.env.TEXT_RESILIENCE_MODE || 'report';
if (!['off', 'report', 'enforce'].includes(TEXT_RESILIENCE_MODE)) {
  throw new Error(`TEXT_RESILIENCE_MODE inválido: ${TEXT_RESILIENCE_MODE}`);
}

const VIEWPORTS = [
  { width: 390, height: 900 },
  { width: 768, height: 1000 },
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
    const clippedText = id === 'legacy-reflow' ? [] : await measureClippedText(page);
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
const checks = [];
const failures = [];
const textResilienceChecks = [];
const textResilienceFailures = [];

// Preserve the historical Sitewide Reflow contract byte-for-byte in meaning:
// WCAG text spacing stress + CSS zoom=2 at the two established viewports.
for (const route of routes) {
  for (const vp of VIEWPORTS) {
    const result = await runScenario(browser, route, vp, {
      id: 'legacy-reflow',
      css: '*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}',
      zoom: 2,
    });
    checks.push(result);
    if (result.failure) failures.push(result);
  }
}

// F.2: do not use zoom as a substitute for text-only 200%. Run Resize Text
// and Text Spacing independently so the artifact names the failing contract.
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

const report = {
  origin: ORIGIN,
  routeCount: routes.length,
  viewportCount: VIEWPORTS.length,
  checks,
  failures,
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
fs.writeFileSync(REPORT_PATH, `${JSON.stringify(report, null, 2)}\n`, 'utf8');

if (failures.length) {
  throw new Error(`sitewide reflow failures (${failures.length})\n${failureLines(failures).join('\n')}`);
}

if (TEXT_RESILIENCE_MODE === 'enforce' && textResilienceFailures.length) {
  throw new Error(`sitewide text-resilience failures (${textResilienceFailures.length})\n${failureLines(textResilienceFailures).join('\n')}`);
}

console.log(
  `sitewide-reflow-browser: OK (${routes.length} routes, ${VIEWPORTS.length} legacy viewports, ${checks.length} legacy checks; ` +
  `text-resilience ${TEXT_RESILIENCE_MODE}: ${textResilienceChecks.length} checks, ${textResilienceFailures.length} findings)`
);
