import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1024, height: 900 }, reducedMotion: 'reduce' });

await context.addInitScript(() => {
  window.__samuelClsEntries = [];
  window.__samuelFrameSamples = [];

  const rect = selector => {
    const node = document.querySelector(selector);
    if (!node) return null;
    const r = node.getBoundingClientRect();
    return { x: r.x, y: r.y, width: r.width, height: r.height };
  };

  new PerformanceObserver(list => {
    for (const entry of list.getEntries()) {
      if (entry.hadRecentInput) continue;
      window.__samuelClsEntries.push({
        value: entry.value,
        startTime: entry.startTime,
        sources: (entry.sources || []).map(source => ({
          node: source.node instanceof Element
            ? `${source.node.tagName.toLowerCase()}${source.node.id ? `#${source.node.id}` : ''}${source.node.className && typeof source.node.className === 'string' ? `.${source.node.className.trim().replace(/\s+/g, '.')}` : ''}`
            : null,
          previousRect: source.previousRect ? {
            x: source.previousRect.x, y: source.previousRect.y,
            width: source.previousRect.width, height: source.previousRect.height,
          } : null,
          currentRect: source.currentRect ? {
            x: source.currentRect.x, y: source.currentRect.y,
            width: source.currentRect.width, height: source.currentRect.height,
          } : null,
        })),
      });
    }
  }).observe({ type: 'layout-shift', buffered: true });

  addEventListener('DOMContentLoaded', () => {
    const started = performance.now();
    let previousSignature = '';
    const sample = () => {
      const snapshot = {
        t: Math.round(performance.now() * 10) / 10,
        htmlClass: document.documentElement.className,
        bodyClass: document.body?.className || '',
        fonts: document.fonts?.status || null,
        header: rect('.site-header'),
        context: rect('.section-context'),
        threshold: rect('.samuel-threshold'),
        object: rect('.samuel-threshold__object'),
        cover: rect('.samuel-object'),
        copy: rect('.samuel-threshold__copy'),
        eyebrow: rect('.samuel-threshold__copy>.eyebrow'),
        h1: rect('#samuel-title'),
        lead: rect('.samuel-lead'),
        facts: rect('.samuel-facts'),
        actions: rect('.samuel-actions'),
        hook: rect('.samuel-hook'),
        route: rect('.samuel-threshold__route'),
      };
      const signature = JSON.stringify({
        hc: snapshot.header && [snapshot.header.y, snapshot.header.height],
        cc: snapshot.context && [snapshot.context.y, snapshot.context.height],
        th: snapshot.threshold && [snapshot.threshold.y, snapshot.threshold.height],
        ob: snapshot.object && [snapshot.object.y, snapshot.object.height],
        cp: snapshot.copy && [snapshot.copy.y, snapshot.copy.height],
        ey: snapshot.eyebrow && [snapshot.eyebrow.y, snapshot.eyebrow.height],
        h1: snapshot.h1 && [snapshot.h1.y, snapshot.h1.height],
        le: snapshot.lead && [snapshot.lead.y, snapshot.lead.height],
        fa: snapshot.facts && [snapshot.facts.y, snapshot.facts.height],
        ac: snapshot.actions && [snapshot.actions.y, snapshot.actions.height],
        ho: snapshot.hook && [snapshot.hook.y, snapshot.hook.height],
        ro: snapshot.route && [snapshot.route.y, snapshot.route.height],
        fonts: snapshot.fonts,
        htmlClass: snapshot.htmlClass,
        bodyClass: snapshot.bodyClass,
      });
      if (signature !== previousSignature) {
        window.__samuelFrameSamples.push(snapshot);
        previousSignature = signature;
      }
      if (performance.now() - started < 650) requestAnimationFrame(sample);
    };
    requestAnimationFrame(sample);
  }, { once: true });
});

const page = await context.newPage();
const response = await page.goto(`${ORIGIN}/libros/samuel-entre-mundos/`, { waitUntil: 'networkidle', timeout: 30000 });
if (!response?.ok()) throw new Error(`Samuel diagnostic HTTP ${response?.status()}`);
await page.waitForTimeout(350);

const report = await page.evaluate(() => {
  const rect = selector => {
    const node = document.querySelector(selector);
    if (!node) return null;
    const r = node.getBoundingClientRect();
    return { x: r.x, y: r.y, width: r.width, height: r.height };
  };
  const entries = window.__samuelClsEntries || [];
  return {
    cls: entries.reduce((sum, entry) => sum + entry.value, 0),
    entries,
    frameSamples: window.__samuelFrameSamples || [],
    fonts: {
      status: document.fonts?.status || null,
      yellowtail: document.fonts?.check('16px "Yellowtail"') ?? null,
      yellowtailStable: document.fonts?.check('16px "Yellowtail Samuel Stable"') ?? null,
      manrope: document.fonts?.check('16px "Manrope"') ?? null,
    },
    geometry: {
      header: rect('.site-header'),
      context: rect('.section-context'),
      threshold: rect('.samuel-threshold'),
      cover: rect('.samuel-object'),
      copy: rect('.samuel-threshold__copy'),
      firstSection: rect('#sinopsis-tecnica'),
      medallion: rect('#sinopsis-tecnica .samuel-register__split>div>img'),
    },
  };
});

console.log('SAMUEL_CLS_DIAGNOSTIC ' + JSON.stringify(report, null, 2));
await context.close();
await browser.close();
