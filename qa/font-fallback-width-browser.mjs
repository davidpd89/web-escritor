// Each metric-matched fallback face (assets/v1-fonts.css) must set real prose
// at the same width as its webfont, for whichever local font resolves on this
// machine: Georgia/Arial on Windows and macOS, Liberation (or DejaVu) on Linux.
// font-display:optional keeps the fallback for the whole page view whenever
// the webfont misses its ~100ms window, so a wrong size-adjust is what readers
// actually see. The original faces promised "identical text width" but set
// /fragmento/ ~36% wider on Windows (the reading measure overflowed); this
// measures it instead of trusting it.
//
// Widths are compared at 200px: headless Chromium on Linux rounds each glyph
// advance to whole pixels, which at 20px moved narrow faces (Instrument Serif
// on Liberation) by up to 9% in CI while the same fonts measured <1% on
// Windows. size-adjust is a per-font ratio, so the large size checks the
// calibration itself (opsz pinned to 20 so Newsreader keeps its reading cut);
// the 20px ratio is still logged for diagnosis.
//
// The webfont is loaded from an ArrayBuffer under a private family name so
// that font-display:optional cannot silently swap the fallback in for it.
import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const TOLERANCE = 0.04;

const browser = await chromium.launch();
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await page.goto(`${ORIGIN}/fragmento/`, { waitUntil: 'networkidle' });
  const rows = await page.evaluate(async () => {
    const text = (document.querySelector('.article-prose')?.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 1500);
    const webSources = new Map();
    for (const sheet of document.styleSheets) {
      let rules;
      try { rules = sheet.cssRules; } catch { continue; }
      for (const rule of rules) {
        if (!(rule instanceof CSSFontFaceRule)) continue;
        const family = rule.style.getPropertyValue('font-family').replace(/["']/g, '').trim();
        const style = rule.style.getPropertyValue('font-style') || 'normal';
        const url = rule.style.getPropertyValue('src').match(/url\(["']?([^"')]+)/);
        if (url && !family.includes(' Fallback')) webSources.set(`${family}|${style}`, new URL(url[1], sheet.href || location.href).href);
      }
    }
    const width = (family, style, size = 200) => {
      const span = document.createElement('span');
      span.textContent = text;
      span.style.cssText = `position:absolute;white-space:nowrap;font-size:${size}px;font-weight:400;font-style:${style};font-family:"${family}",monospace;font-synthesis:none;font-variation-settings:"opsz" 20`;
      document.body.append(span);
      const w = span.getBoundingClientRect().width;
      span.remove();
      return w;
    };
    const out = [];
    const faces = [...document.fonts].filter((f) => f.family.replace(/["']/g, '').includes(' Fallback'));
    for (const face of faces) {
      const family = face.family.replace(/["']/g, '');
      const base = family.replace(/ Fallback.*$/, '');
      const url = webSources.get(`${base}|${face.style}`);
      if (!url) continue;
      try { await face.load(); } catch { /* local font not installed here */ }
      if (face.status !== 'loaded') { out.push({ family, style: face.style, resolved: false }); continue; }
      const web = new FontFace(`QA web ${base}`, await (await fetch(url)).arrayBuffer(), { style: face.style, weight: '100 900' });
      await web.load();
      document.fonts.add(web);
      out.push({ family, style: face.style, resolved: true, ratio: width(family, face.style) / width(`QA web ${base}`, face.style),
        ratio20: width(family, face.style, 20) / width(`QA web ${base}`, face.style, 20) });
      document.fonts.delete(web);
    }
    return { chars: text.length, out };
  });

  assert.ok(rows.chars > 500, `/fragmento/ prose sample too short (${rows.chars})`);
  const resolved = rows.out.filter((row) => row.resolved);
  for (const row of rows.out) {
    console.log(`${row.family} (${row.style}): ${row.resolved ? `${((row.ratio - 1) * 100).toFixed(1)}% (20px: ${((row.ratio20 - 1) * 100).toFixed(1)}%)` : 'local font not installed'}`);
  }
  assert.ok(resolved.some((row) => /^(Newsreader|Instrument Serif) Fallback/.test(row.family)),
    'no serif fallback face resolved on this machine: the check would prove nothing');
  for (const row of resolved) {
    assert.ok(Math.abs(row.ratio - 1) <= TOLERANCE,
      `${row.family} (${row.style}) sets prose ${((row.ratio - 1) * 100).toFixed(1)}% off its webfont width (tolerance ±${TOLERANCE * 100}%)`);
  }
  console.log(`PASS fallback width: ${resolved.length} resolved face(s) within ±${TOLERANCE * 100}%`);
} finally {
  await browser.close();
}
