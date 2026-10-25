import assert from 'node:assert/strict';
import { isTrustedWidgetMessage } from '../assets/assistant-widget-core.mjs';

const expectedOrigin = 'https://davidportodiaz.com';
const frame = {};
const otherFrame = {};

assert.equal(isTrustedWidgetMessage(expectedOrigin, expectedOrigin, frame, frame), true);

for (const origin of ['', 'http://davidportodiaz.com', 'https://www.davidportodiaz.com', 'https://davidportodiaz.com.evil.example', 'https://evil.example', 'null', 'HTTPS://DAVIDPORTODIAZ.COM']) {
  assert.equal(isTrustedWidgetMessage(origin, expectedOrigin, frame, frame), false, `Origen aceptado: ${origin}`);
}

for (const source of [null, undefined, otherFrame, {}, false, 0]) {
  assert.equal(isTrustedWidgetMessage(expectedOrigin, expectedOrigin, source, frame), false);
}

assert.equal(isTrustedWidgetMessage(expectedOrigin, '', frame, frame), false);
assert.equal(isTrustedWidgetMessage('', '', frame, frame), false);
assert.equal(isTrustedWidgetMessage(expectedOrigin, expectedOrigin, frame, otherFrame), false);
console.log('assistant-widget-message-trust-matrix: OK');