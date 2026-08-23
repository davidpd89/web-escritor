import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

const script = await fs.readFile(new URL('../script.js', import.meta.url), 'utf8');
const thanks = await fs.readFile(new URL('../gracias-suscripcion/index.html', import.meta.url), 'utf8');

assert.ok(script.includes('state === "pending_confirmation"'), 'frontend must require pending_confirmation');
assert.ok(script.includes('Revisa tu correo'), 'pending DOI copy must be visible');
assert.ok(!script.includes('localStorage.setItem("nl-subscribed", "1")'), 'initial submit must not mark confirmed');
assert.ok(!script.includes('localStorage.setItem(SUBSCRIBED_KEY, "1")'), 'popup submit must not mark confirmed');
assert.ok(!script.includes('left:-9999px'), 'honeypot must not create offscreen reflow');
assert.ok(script.includes('clip-path:inset(50%)'), 'honeypot uses clipped in-layout geometry');
assert.ok(script.includes('setAttribute("inert", "")'), 'dynamic honeypot must be removed from focus/a11y interaction');
assert.ok(script.includes('normalized.length <= 254'), 'client must reject overlong email locally');
assert.equal((script.match(/dataset\.submitting === "true"/g) || []).length, 3, 'quiz, generic and popup must guard duplicate submits');
assert.equal((script.match(/delete .*dataset\.submitting/g) || []).length, 3, 'all submit guards must reset after failure');
assert.ok(!script.includes('dupeTitle:'), 'legacy duplicate-success copy must not survive DOI migration');

assert.match(thanks, /<meta name="robots" content="noindex, follow"/);
assert.ok(thanks.includes('localStorage.setItem("nl-subscribed", "1")'), 'DOI return marks browser confirmed');
assert.ok(thanks.indexOf('localStorage.setItem("nl-subscribed", "1")') < thanks.indexOf('/script.js'), 'confirmed state must be set before global runtime');
assert.ok(thanks.includes('Suscripción confirmada'));

console.log('test-newsletter-doi-frontend: all assertions passed');
