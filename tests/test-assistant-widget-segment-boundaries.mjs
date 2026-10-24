import assert from 'node:assert/strict';
import { assistantContextStarters, shouldMountAssistantWidget } from '../assets/assistant-widget-core.mjs';

const generic = assistantContextStarters('/');
const fixtures = [
  '/herramientas-falsas/',
  '/editoriales-inventadas/',
  '/prensa-simulada.html',
  '/eventos-falsos/',
  '/las-manecillas-del-recuerdo-extra/',
  '/libros/samuel-entre-mundos-falso/',
  '/universo/noveris-falso/'
];
for (const pathname of fixtures) {
  assert.deepEqual(assistantContextStarters(pathname), generic, `${pathname}: leaked context across path segment`);
  assert.equal(shouldMountAssistantWidget(pathname), true, `${pathname}: widget unexpectedly suppressed`);
}
assert.equal(shouldMountAssistantWidget('/asistente/'), false);
assert.equal(shouldMountAssistantWidget('/asistente/embed.html'), false);
assert.equal(shouldMountAssistantWidget('/asistente-falso/'), true);
console.log('PASS assistant route-segment boundaries');
