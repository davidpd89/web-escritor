import assert from 'node:assert/strict';
import fs from 'node:fs';

const read = (path) => fs.readFileSync(path, 'utf8');
const shellCss = read('assets/v1-shell.css');
const headerCss = read('assets/v1-shell-lrb-v2.css');
const interiorCss = read('assets/v1-editorial-interior-v4.css');
const shellJs = read('assets/v1-shell.js');
const interiorJs = read('assets/v1-editorial-interior-v4.js');
const navigation = JSON.parse(read('data/navigation.json'));

assert(shellCss.includes("/assets/v1-editorial-interior-v4.css"), 'shell must load V4 inner-page editorial CSS');
assert(shellJs.includes("/assets/v1-editorial-interior-v4.js"), 'V1 shell must load persistent inner-page navigation');

assert(headerCss.includes('--dp-lrb-utility-h:50px'), 'desktop utility bar must remain 50px');
assert(headerCss.includes('--dp-lrb-nav-h:40px'), 'desktop editorial nav must remain 40px');
// The transparent lettering logo is a wide wordmark; it is sized by width with
// natural height instead of a squashing max-height.
assert(headerCss.includes('.masthead__logo-image{display:block;width:min(70vw,760px);height:auto'), 'desktop lettering logo must size from its real proportions');
assert(headerCss.includes('font-size:.82rem'), 'desktop Home territory navigation must stay publication-sized');
assert(headerCss.includes('@media (max-width:639px)'), 'phone navigation breakpoint missing');
assert(headerCss.includes('.masthead-nav{display:none}'), 'phone must hand global navigation to the hamburger/Explore drawer');
assert(headerCss.includes('background:#d7e9ef'), 'hover/focus editorial blue feedback missing');

for (const [needle, label] of [
  ['3.25rem', 'inner H1 maximum'],
  ['2.35rem', 'inner section H2 maximum'],
  ['aspect-ratio:3/4', 'author portrait ratio'],
  ['aspect-ratio:4/5', 'press portrait ratio']
]) assert(interiorCss.includes(needle), `${label} contract missing`);

assert(interiorCss.includes('position:sticky'), 'contextual section navigation must remain sticky');
assert(interiorCss.includes('.section-context__links a[aria-current="page"]'), 'current local destination state missing');

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
