// K.3 regression: the dynamic Home "sponsored nofollow" decision must be
// scoped to the real amazon.es host, not a regex that also matches a
// lookalike host like amazon.evil.com. This actually executes the extracted
// source (not a re-derivation of the logic) against real/adversarial cases,
// unlike a text-contains check on the function body.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const SRC = readFileSync(path.join(ROOT, "assets/v1-home-editorial-v3.js"), "utf8");

function extractFunction(src, name) {
  const start = src.indexOf(`function ${name}(`);
  assert.ok(start >= 0, `function ${name}() not found in assets/v1-home-editorial-v3.js`);
  const braceStart = src.indexOf("{", start);
  let depth = 0;
  let end = -1;
  for (let i = braceStart; i < src.length; i += 1) {
    if (src[i] === "{") depth += 1;
    else if (src[i] === "}") {
      depth -= 1;
      if (depth === 0) { end = i + 1; break; }
    }
  }
  assert.ok(end > 0, `could not find end of function ${name}()`);
  return src.slice(start, end);
}

const amazonHostsMatch = SRC.match(/const AMAZON_HOSTS = (\[[^\]]*\]);/);
assert.ok(amazonHostsMatch, "AMAZON_HOSTS allowlist not found");

const isAmazonHostSrc = extractFunction(SRC, "isAmazonHost");
// eslint-disable-next-line no-new-func
const isAmazonHost = new Function(
  "AMAZON_HOSTS",
  `${isAmazonHostSrc}\nreturn isAmazonHost;`
)(new Function(`return ${amazonHostsMatch[1]};`)());

function isSponsored(href) {
  return isAmazonHost(href) && /[?&]tag=/.test(href);
}

const cases = [
  ["https://www.amazon.es/dp/B0GB6LGQFH?tag=davidporto-21", true, "amazon.es + tag must be sponsored"],
  ["https://amazon.es/dp/B0GB6LGQFH?tag=davidporto-21", true, "bare amazon.es + tag must be sponsored"],
  ["https://www.amazon.es/dp/B0GB6LGQFH", false, "amazon.es without tag= must NOT be sponsored"],
  ["https://example.com/?tag=davidporto-21", false, "non-Amazon host with tag= must NOT be sponsored"],
  ["https://amazon.evil.com/dp/x?tag=davidporto-21", false, "lookalike host amazon.evil.com must NOT be sponsored"],
  ["https://amazon.es.evil.com/?tag=davidporto-21", false, "amazon.es.evil.com must NOT be sponsored"],
  ["https://notamazon.es/?tag=davidporto-21", false, "notamazon.es must NOT be sponsored"],
  ["https://www.casadellibro.com/libro-x/123", false, "Casa del Libro must NOT be sponsored"],
  ["mailto:davidportodiaz@gmail.com", false, "mailto: links must NOT be sponsored"],
];

for (const [href, expected, message] of cases) {
  assert.equal(isSponsored(href), expected, `${message} (href=${href})`);
}

console.log("home-amazon-host-scoping: OK");
