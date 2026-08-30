import test from 'node:test';
import assert from 'node:assert/strict';
import { pointToRectDistance, spacingPasses } from './target-size-audit.mjs';

function target(cx, cy, width, height) {
  return {
    cx,
    cy,
    undersized: width < 24 || height < 24,
    rect: {
      left: cx - width / 2,
      right: cx + width / 2,
      top: cy - height / 2,
      bottom: cy + height / 2,
      width,
      height,
    },
  };
}

test('pointToRectDistance is zero inside a rectangle', () => {
  assert.equal(pointToRectDistance(10, 10, { left: 0, right: 20, top: 0, bottom: 20 }), 0);
});

test('pointToRectDistance measures diagonal clearance', () => {
  assert.equal(pointToRectDistance(0, 0, { left: 3, right: 5, top: 4, bottom: 6 }), 5);
});

test('two undersized targets pass when their 24px circles do not intersect', () => {
  const a = target(0, 0, 20, 20);
  const b = target(24, 0, 20, 20);
  assert.equal(spacingPasses(a, [b]), true);
});

test('two undersized targets fail when their 24px circles intersect', () => {
  const a = target(0, 0, 20, 20);
  const b = target(23.99, 0, 20, 20);
  assert.equal(spacingPasses(a, [b]), false);
});

test('undersized target passes when its center is at least 12px from a compliant target', () => {
  const a = target(0, 0, 20, 20);
  const b = target(36, 0, 24, 24);
  assert.equal(spacingPasses(a, [b]), true);
});

test('undersized target fails when its 24px circle intersects a compliant target', () => {
  const a = target(0, 0, 20, 20);
  const b = target(35.99, 0, 24, 24);
  assert.equal(spacingPasses(a, [b]), false);
});
