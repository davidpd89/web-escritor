import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });

async function runCase(name, { blockFonts = false } = {}) {
  const context = await browser.newContext({ viewport: { width: 1024, height: 900 }, reducedMotion: 'reduce' });
  if (blockFonts) {
    await context.route(/\.woff2(?:\?|$)/, route => route.abort('blockedbyclient'));
  }

  await context.addInitScript(() => {
    window.__samuelClsEntries = [];
    window.__samuelFrameSamples = [];
    window.__samuelFontEvents = [];

    const rect = selector => {
      const node = document.querySelector(selector);
      if (!node) return null;
      const r = node.getBoundingClientRect();
      return { x: r.x, y: r.y, width: r.width, height: r.height };
    };
    const style = selector => {
      const node = document.querySelector(selector);
      if (!node) return null;
      const s = getComputedStyle(node);
      return {
        display: s.display,
        width: s.width,
        minHeight: s.minHeight,
        paddingTop: s.paddingTop,
        paddingBottom: s.paddingBottom,
        marginTop: s.marginTop,
        marginBottom: s.marginBottom,
        fontFamily: s.fontFamily,
        fontSize: s.fontSize,
        fontWeight: s.fontWeight,
        lineHeight: s.lineHeight,
        maxWidth: s.maxWidth,
      };
    };
    const resources = () => performance.getEntriesByType('resource')
      .filter(entry => /\.(?:css|woff2)(?:\?|$)/.test(entry.name))
      .map(entry => ({
        name: entry.name.replace(location.origin, ''),
        startTime: Math.round(entry.startTime * 10) / 10,
        responseEnd: Math.round(entry.responseEnd * 10) / 10,
        duration: Math.round(entry.duration * 10) / 10,
        initiatorType: entry.initiatorType,
      }));

    new PerformanceObserver(list => {
      for (const entry of list.getEntries()) {
        if (entry.hadRecentInput) continue;
        window.__samuelClsEntries.push({
          value: entry.value,
          startTime: entry.startTime,
          stateAtCallback: {
            fonts: document.fonts?.status || null,
            threshold: rect('.samuel-threshold'),
            object: rect('.samuel-threshold__object'),
            cover: rect('.samuel-object'),
            copy: rect('.samuel-threshold__copy'),
            h1: rect('#samuel-title'),
            hook: rect('.samuel-hook'),
            thresholdStyle: style('.samuel-threshold'),
            objectStyle: style('.samuel-object'),
            h1Style: style('#samuel-title'),
            loadedResources: resources(),
          },
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

    const bindFontEvents = () => {
      if (!document.fonts || document.fonts.__samuelDiagnosticBound) return;
      document.fonts.__samuelDiagnosticBound = true;
      for (const type of ['loading', 'loadingdone', 'loadingerror']) {
        document.fonts.addEventListener(type, () => {
          window.__samuelFontEvents.push({ type, t: Math.round(performance.now() * 10) / 10 });
        });
      }
    };
    bindFontEvents();

    addEventListener('DOMContentLoaded', () => {
      bindFontEvents();
      const started = performance.now();
      let previousSignature = '';
      const sample = () => {
        const snapshot = {
          t: Math.round(performance.now() * 10) / 10,
          fonts: document.fonts?.status || null,
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
          h1Style: style('#samuel-title'),
          objectStyle: style('.samuel-object'),
        };
        const signature = JSON.stringify(snapshot);
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
  if (!response?.ok()) throw new Error(`Samuel diagnostic ${name} HTTP ${response?.status()}`);
  await page.waitForTimeout(350);

  const report = await page.evaluate(() => {
    const entries = window.__samuelClsEntries || [];
    return {
      cls: entries.reduce((sum, entry) => sum + entry.value, 0),
      entries,
      frameSamples: window.__samuelFrameSamples || [],
      fontEvents: window.__samuelFontEvents || [],
      resources: performance.getEntriesByType('resource')
        .filter(entry => /\.(?:css|woff2)(?:\?|$)/.test(entry.name))
        .map(entry => ({
          name: entry.name.replace(location.origin, ''),
          startTime: Math.round(entry.startTime * 10) / 10,
          responseEnd: Math.round(entry.responseEnd * 10) / 10,
          duration: Math.round(entry.duration * 10) / 10,
          initiatorType: entry.initiatorType,
        })),
      fonts: {
        status: document.fonts?.status || null,
        yellowtail: document.fonts?.check('16px "Yellowtail"') ?? null,
        manrope: document.fonts?.check('16px "Manrope"') ?? null,
        newsreader: document.fonts?.check('16px "Newsreader"') ?? null,
      },
    };
  });

  console.log(`SAMUEL_CLS_DIAGNOSTIC_${name.toUpperCase()} ` + JSON.stringify(report, null, 2));
  await context.close();
  return report;
}

const normal = await runCase('normal');
const noFonts = await runCase('no_fonts', { blockFonts: true });
console.log('SAMUEL_CLS_DIAGNOSTIC_COMPARISON ' + JSON.stringify({
  normal: normal.cls,
  noFonts: noFonts.cls,
  delta: normal.cls - noFonts.cls,
}, null, 2));

await browser.close();
