// K.3 regression: the dynamic Home "sponsored nofollow" decision must be
// scoped to the real amazon.es host (or the author's own amzn.to short-link
// domain), not a regex that also matches a lookalike host like
// amazon.evil.com. This actually executes the extracted source (not a
// re-derivation of the logic) against real/adversarial cases, unlike a
// text-contains check on the function body.
//
// 2026-09-05: MANECILLAS_BUY_URL is an amzn.to short link, which never
// carries a visible ?tag= (the tag lives server-side in the redirect
// target). The old isAmazonHost()+tag= two-step logic misclassified it as
// non-affiliate, so Home's dynamically-built Manecillas CTAs silently lost
// rel="sponsored nofollow" and the aria-label disclosure. isAmazonHost was
// folded into a single isAmazonAffiliateUrl() that treats amzn.to as
// affiliate outright and still requires tag= for amazon.es/etc.
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
const shortlinkHostsMatch = SRC.match(/const AMAZON_SHORTLINK_HOSTS = (\[[^\]]*\]);/);
assert.ok(shortlinkHostsMatch, "AMAZON_SHORTLINK_HOSTS allowlist not found");

const isAmazonAffiliateSrc = extractFunction(SRC, "isAmazonAffiliateUrl");
// eslint-disable-next-line no-new-func
const isAmazonAffiliateUrl = new Function(
  "AMAZON_HOSTS",
  "AMAZON_SHORTLINK_HOSTS",
  `${isAmazonAffiliateSrc}\nreturn isAmazonAffiliateUrl;`
)(
  new Function(`return ${amazonHostsMatch[1]};`)(),
  new Function(`return ${shortlinkHostsMatch[1]};`)()
);

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
  ["https://amzn.to/3SM4Oxu", true, "amzn.to short link (no tag=) must still be sponsored"],
  ["https://amzn.to/anything", true, "any amzn.to path must be sponsored"],
  ["https://amzn.to.evil.com/3SM4Oxu", false, "amzn.to.evil.com must NOT be sponsored"],
  ["https://evil-amzn.to/3SM4Oxu", false, "evil-amzn.to must NOT be sponsored"],
  ["https://www.amzn.to/3SM4Oxu", false, "www.amzn.to (exact-host allowlist, no subdomain match) must NOT be sponsored"],
];

for (const [href, expected, message] of cases) {
  assert.equal(isAmazonAffiliateUrl(href), expected, `${message} (href=${href})`);
}

console.log("home-amazon-host-scoping: OK");
