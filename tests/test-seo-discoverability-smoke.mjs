// Comprehensive SEO & Discoverability Smoke Test.
// Validates canonicals, OpenGraph, Twitter cards, meta descriptions,
// JSON-LD schemas, sitemap.xml, robots.txt, and llms.txt across all build output.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const ROOT = process.cwd();
const DIST = process.env.SITEWIDE_DIST || path.join(ROOT, '.preview-dist-sitewide-qa');

if (!process.env.SITEWIDE_SKIP_BUILD && !fs.existsSync(DIST)) {
  const py = process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
  execFileSync(py, ['scripts/build-public-dist.py', '--out', DIST], { cwd: ROOT, stdio: 'inherit' });
}

function collectHtmlFiles(dir, base = dir) {
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...collectHtmlFiles(full, base));
    else if (entry.name.endsWith('.html')) out.push(path.relative(base, full).replaceAll('\\', '/'));
  }
  return out;
}

const htmlFiles = collectHtmlFiles(DIST);
console.log(`Auditing SEO & Schema on ${htmlFiles.length} published HTML pages...`);

const failures = [];
let totalChecks = 0;

function check(page, condition, msg) {
  totalChecks++;
  if (!condition) {
    failures.push(`[${page}] ${msg}`);
  }
}

for (const rel of htmlFiles) {
  const full = path.join(DIST, rel);
  const content = fs.readFileSync(full, 'utf8');

  // Check noindex status
  const isNoIndex = /<meta\s+name=["']robots["']\s+content=["'][^"']*noindex/i.test(content);

  // 1. Title
  const hasTitle = /<title>[^<]+<\/title>/i.test(content);
  check(rel, hasTitle, 'Missing or empty <title>');

  // 2. Viewport & Charset
  check(rel, /<meta\s+charset=["']?utf-8/i.test(content), 'Missing UTF-8 charset');
  check(rel, /<meta\s+name=["']viewport["']/i.test(content), 'Missing viewport meta tag');

  if (!isNoIndex) {
    // 3. Meta description
    const descMatch = content.match(/<meta\s+name=["']description["']\s+content=["']([^"']+)["']/i);
    check(rel, !!descMatch && descMatch[1].trim().length >= 30, 'Missing or too short (<30 chars) meta description');

    // 4. Canonical link
    const canonMatch = content.match(/<link\s+rel=["']canonical["']\s+href=["'](https:\/\/davidportodiaz\.com[^"']*)["']/i);
    check(rel, !!canonMatch, 'Missing or invalid canonical link (must be https://davidportodiaz.com/...)');

    // 5. OpenGraph Tags
    check(rel, /<meta\s+property=["']og:title["']/i.test(content), 'Missing og:title');
    check(rel, /<meta\s+property=["']og:description["']/i.test(content), 'Missing og:description');
    check(rel, /<meta\s+property=["']og:image["']/i.test(content), 'Missing og:image');
    check(rel, /<meta\s+property=["']og:url["']/i.test(content), 'Missing og:url');

    // 6. Twitter Card
    check(rel, /<meta\s+name=["']twitter:card["']/i.test(content), 'Missing twitter:card');

    // 7. JSON-LD Structured Data
    const jsonLdBlocks = [...content.matchAll(/<script\s+type=["']application\/ld\+json["']>([\s\S]*?)<\/script>/gi)];
    check(rel, jsonLdBlocks.length > 0, 'No JSON-LD structured data block found');

    for (let i = 0; i < jsonLdBlocks.length; i++) {
      const rawJson = jsonLdBlocks[i][1];
      try {
        const parsed = JSON.parse(rawJson);
        const hasContext = parsed['@context'] === 'https://schema.org' || parsed['@context'] === 'http://schema.org';
        check(rel, hasContext, `JSON-LD block ${i + 1} missing @context https://schema.org`);
        check(rel, !!parsed['@type'] || !!parsed['@graph'], `JSON-LD block ${i + 1} missing @type or @graph`);
      } catch (err) {
        check(rel, false, `JSON-LD block ${i + 1} contains malformed JSON: ${err.message}`);
      }
    }
  }
}

// 8. Sitemap and Robots
const robotsPath = path.join(DIST, 'robots.txt');
check('robots.txt', fs.existsSync(robotsPath), 'robots.txt missing in dist');
if (fs.existsSync(robotsPath)) {
  const robots = fs.readFileSync(robotsPath, 'utf8');
  check('robots.txt', robots.includes('Sitemap: https://davidportodiaz.com/sitemap.xml'), 'robots.txt missing Sitemap declaration');
}

const sitemapPath = path.join(DIST, 'sitemap.xml');
check('sitemap.xml', fs.existsSync(sitemapPath), 'sitemap.xml missing in dist');
if (fs.existsSync(sitemapPath)) {
  const sitemap = fs.readFileSync(sitemapPath, 'utf8');
  check('sitemap.xml', sitemap.includes('<urlset') && sitemap.includes('https://davidportodiaz.com/'), 'sitemap.xml invalid structure');
}

const llmsPath = path.join(DIST, 'llms.txt');
check('llms.txt', fs.existsSync(llmsPath), 'llms.txt missing in dist');

console.log(`SEO & Schema Smoke: ${totalChecks - failures.length}/${totalChecks} assertions passed.`);
if (failures.length > 0) {
  console.error(`\nFailures (${failures.length}):`);
  for (const f of failures) console.error(` - ${f}`);
  process.exit(1);
} else {
  console.log('ALL SEO & DISCOVERABILITY CHECKS PASSED 100%!');
}
