import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

const script = await fs.readFile(new URL('../script.js', import.meta.url), 'utf8');
const popup = await fs.readFile(new URL('../assets/newsletter-popup.js', import.meta.url), 'utf8');
const thanks = await fs.readFile(new URL('../gracias-suscripcion/index.html', import.meta.url), 'utf8');

assert.ok(script.includes('state === "pending_confirmation"'), 'frontend must require pending_confirmation');
assert.ok(script.includes('Revisa tu correo'), 'pending DOI copy must be visible');
assert.ok(!script.includes('localStorage.setItem("nl-subscribed", "1")'), 'initial submit must not mark confirmed');
assert.ok(!popup.includes('localStorage.setItem(SUBSCRIBED_KEY, "1")'), 'popup submit must not mark confirmed');
assert.ok(!script.includes('left:-9999px'), 'honeypot must not create offscreen reflow');
assert.ok(script.includes('clip-path:inset(50%)'), 'honeypot uses clipped in-layout geometry');
assert.ok(script.includes('setAttribute("inert", "")'), 'dynamic honeypot must be removed from focus/a11y interaction');
assert.ok(script.includes('normalized.length <= 254'), 'client must reject overlong email locally');
// El quiz de Noveris (tercer guard original) se elimino como codigo muerto
// en H.1 (2026-08-23, PR #61): id="quiz-noveris-app" no existia en ningun
// HTML real del sitio. El popup se extrajo a assets/newsletter-popup.js
// en la misma PR (antes vivia en script.js), asi que su guard hay que
// contarlo ahi, no aqui. Quedan dos guards reales en script.js: el
// submitNewsletter() generico (home/fragmento/manecillas/cuaderno/explore,
// comparten una sola implementacion) y el formulario dedicado de
// lectores-beta.
assert.equal((script.match(/dataset\.submitting === "true"/g) || []).length, 2, 'generic newsletter and lectores-beta must guard duplicate submits');
assert.equal((script.match(/delete .*dataset\.submitting/g) || []).length, 2, 'both script.js submit guards must reset after failure');
assert.equal((popup.match(/dataset\.submitting === "true"/g) || []).length, 1, 'popup must guard duplicate submits');
assert.equal((popup.match(/delete .*dataset\.submitting/g) || []).length, 1, 'popup submit guard must reset after failure');
assert.ok(!script.includes('dupeTitle:'), 'legacy duplicate-success copy must not survive DOI migration');
assert.ok(!popup.includes('dupeTitle:'), 'legacy duplicate-success copy must not survive DOI migration in popup');

assert.match(thanks, /<meta name="robots" content="noindex, follow"/);
assert.ok(thanks.includes('localStorage.setItem("nl-subscribed", "1")'), 'DOI return marks browser confirmed');
assert.ok(thanks.indexOf('localStorage.setItem("nl-subscribed", "1")') < thanks.indexOf('/script.js'), 'confirmed state must be set before global runtime');
assert.ok(thanks.includes('Suscripción confirmada'));

console.log('test-newsletter-doi-frontend: all assertions passed');
