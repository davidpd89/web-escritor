import assert from 'node:assert/strict';
import fs from 'node:fs';

const html = fs.readFileSync('offline.html', 'utf8');
const worker = fs.readFileSync('service-worker.js', 'utf8');
const shell = worker.match(/const APP_SHELL = \[([\s\S]*?)\];/)?.[1];
assert.ok(shell, 'APP_SHELL declaration missing');
assert.ok(shell.includes('/offline.html'), 'Offline document not precached');
assert.match(html, /<html\b[^>]*\blang\s*=\s*["']es(?:-[A-Za-z]+)?["']/i);
assert.match(html, /<title\b[^>]*>[^<]+<\/title>/i);
assert.match(html, /<main\b/i);
assert.match(html, /<h1\b/i);
assert.match(html, /<a\b[^>]*href\s*=/i);
assert.ok(/data-retry|location\.reload|window\.location/.test(html), 'No recovery action found');

const external = [...html.matchAll(/<(?:script|link|img)\b[^>]*(?:src|href)\s*=\s*["'](https?:\/\/[^"']+)/gi)];
assert.equal(external.length, 0, `External offline dependencies: ${external.map(item => item[1]).join(', ')}`);
console.log('PASS: offline document structure and local dependencies');