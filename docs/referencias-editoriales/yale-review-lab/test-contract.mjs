import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const html = await fs.readFile(path.join(here, 'prototype.html'), 'utf8');
const css = await fs.readFile(path.join(here, 'prototype.css'), 'utf8');

const failures = [];
const expect = (condition, message) => {
  if (!condition) failures.push(message);
};

expect(/<meta\s+name="robots"\s+content="noindex,nofollow"/i.test(html), 'prototype must be noindex,nofollow');
expect(html.includes('/assets/v1-fonts.css'), 'prototype must consume project fonts');
expect(html.includes('/assets/v1-tokens.css'), 'prototype must consume project tokens');
expect(!/https?:\/\//i.test(html), 'prototype must not load external resources');
expect(!/GT\s*Cinetype|YaleNew|Yale\s*2024/i.test(css), 'prototype CSS must not reference proprietary Yale/GT font families');
expect(!/url\(\s*["']?https?:\/\//i.test(css), 'prototype CSS must not load external assets');
expect(css.includes('var(--font-display)'), 'prototype must use project display font token');
expect(css.includes('var(--font-reading)'), 'prototype must use project reading font token');
expect(css.includes('var(--font-ui)'), 'prototype must use project UI font token');
expect(css.includes('var(--page-gutter)'), 'prototype must use project gutter token');
expect(css.includes('border-radius:0'), 'prototype controls should demonstrate square editorial treatment');
expect(/min-height:\s*44px/.test(css), 'interactive controls must retain 44px minimum target');
expect(css.includes('@media(max-width:900px)'), 'tablet/mobile collapse contract missing');
expect(css.includes('@media(max-width:639px)'), 'mobile single-column contract missing');
expect(css.includes('@media(prefers-reduced-motion:reduce)'), 'reduced-motion contract missing');
expect(!/translateY\(|scale\(/.test(css), 'prototype hover/motion must not depend on lifting or scaling');
expect(html.includes('yr-ledger__list'), 'prototype must include a ledger/list phase');
expect(html.includes('yr-filters'), 'prototype must demonstrate Browse/filter phase');
expect(html.includes('yr-feature'), 'prototype must demonstrate asymmetric feature phase');
expect(html.includes('yr-promo'), 'prototype must demonstrate post-value conversion phase');

if (failures.length) {
  console.error(`Yale reference lab contract FAIL (${failures.length})`);
  for (const item of failures) console.error(`- ${item}`);
  process.exit(1);
}

console.log('Yale reference lab contract PASS');
console.log('- no external/proprietary runtime dependencies');
console.log('- project typography/tokens reused');
console.log('- responsive + reduced-motion contracts present');
console.log('- feature → browse → ledger → conversion pattern present');
