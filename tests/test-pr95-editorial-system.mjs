import assert from 'node:assert/strict';
import fs from 'node:fs';

const read = (path) => fs.readFileSync(path, 'utf8');
const shellCss = read('assets/v1-shell.css');
const headerCss = read('assets/v1-shell-lrb-v2.css');
const interiorCss = read('assets/v1-editorial-interior-v4.css');
const placeholderCss = read('assets/v1-editorial-placeholders-v4.css');
const shellJs = read('assets/v1-shell.js');
const interiorJs = read('assets/v1-editorial-interior-v4.js');
const navigation = JSON.parse(read('data/navigation.json'));

assert(shellCss.includes("/assets/v1-editorial-interior-v4.css"), 'shell must load V4 inner-page editorial CSS');
assert(shellCss.includes("/assets/v1-editorial-placeholders-v4.css"), 'shell must load final-banner placeholder CSS');
assert(shellJs.includes("/assets/v1-editorial-interior-v4.js"), 'V1 shell must load persistent inner-page navigation');

assert(headerCss.includes('--dp-lrb-utility-h:50px'), 'desktop utility bar must remain 50px');
assert(headerCss.includes('--dp-lrb-nav-h:40px'), 'desktop editorial nav must remain 40px');
// The real supplied logo (assets/london-david-porto-logo-central.png) is a
// two-line stacked wordmark, ratio ~1.91:1 -- the original 800x86 single-line
// assumption was wrong (finalization doc: "el asset real manda"). It is
// sized by width with natural height instead of a squashing max-height.
assert(headerCss.includes('.masthead__logo-image{display:block;width:min(46vw,420px);height:auto'), 'desktop supplied logo must size from its real proportions');
assert(headerCss.includes('font-size:.82rem'), 'desktop Home territory navigation must stay publication-sized');
assert(headerCss.includes('@media (max-width:639px)'), 'phone navigation breakpoint missing');
assert(headerCss.includes('.masthead-nav{display:none}'), 'phone must hand global navigation to the hamburger/Explore drawer');
assert(headerCss.includes('background:#d7e9ef'), 'hover/focus editorial blue feedback missing');

for (const [needle, label] of [
  ['height:400px', '>=1440 banner height 400'],
  ['height:360px', '1200-1439 banner height 360'],
  ['height:320px', '900-1199 banner height 320'],
  ['height:290px', '640-899 banner height 290'],
  ['height:250px', '<=639 banner height 250'],
  ['height:230px', '<=349 banner height 230'],
  ['3.25rem', 'inner H1 maximum'],
  ['2.35rem', 'inner section H2 maximum'],
  ['aspect-ratio:3/4', 'author portrait ratio'],
  ['aspect-ratio:4/5', 'press portrait ratio']
]) assert(interiorCss.includes(needle), `${label} contract missing`);

assert(interiorCss.includes('position:sticky'), 'contextual section navigation must remain sticky');
assert(interiorCss.includes('.section-context__links a[aria-current="page"]'), 'current local destination state missing');
assert(placeholderCss.includes('.feature-banner--placeholder-only .feature-banner__image{opacity:0}'), 'temporary banner fallback must not masquerade as final art');
assert(interiorJs.includes("path.startsWith('/assets/banners/')"), 'final banner assets must be distinguished from temporary fallbacks');
assert(interiorJs.includes('2400 × 900 px'), 'banner source-size instruction must be visible in empty slots');

for (const family of ['obras', 'manecillas', 'samuel', 'cuaderno', 'herramientas', 'autor', 'prensa']) {
  assert(Array.isArray(navigation.localNavSets?.[family]), `data/navigation.json missing localNavSets.${family}`);
  assert(navigation.localNavSets[family].length >= 3, `${family} local navigation is too sparse`);
  assert(interiorJs.includes(`key: '${family}'`), `runtime contextual navigation missing ${family}`);
}

for (const path of [
  'index.html',
  'las-manecillas-del-recuerdo/index.html',
  'libros/samuel-entre-mundos/index.html',
  'autor.html',
  'prensa.html',
  'cuaderno/index.html',
  'herramientas/index.html'
]) {
  const html = read(path);
  assert(html.includes('v1-shell.css'), `${path}: V4 CSS cannot reach this representative page`);
  assert(html.includes('v1-shell.js'), `${path}: V4 navigation runtime cannot reach this representative page`);
}

console.log('test-pr95-editorial-system: OK');
