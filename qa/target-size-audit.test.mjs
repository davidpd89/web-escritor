import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {
  DEFAULT_EQUIVALENT_TARGETS,
  DEFAULT_PRODUCT_CONTRACTS,
  contractApplies,
  contractPasses,
  pointToRectDistance,
  spacingPasses,
} from './target-size-audit.mjs';

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
  const b = target(24, 0, 24, 24);
  assert.equal(spacingPasses(a, [b]), true);
});

test('undersized target fails when its 24px circle intersects a compliant target', () => {
  const a = target(0, 0, 20, 20);
  const b = target(23.99, 0, 24, 24);
  assert.equal(spacingPasses(a, [b]), false);
});

test('responsive product contracts select the intentional <=899px and desktop Explore bars', () => {
  const mobile = DEFAULT_PRODUCT_CONTRACTS.find((item) => item.selector === '.explore-trigger' && contractApplies(item, 390));
  const desktop = DEFAULT_PRODUCT_CONTRACTS.find((item) => item.selector === '.explore-trigger' && contractApplies(item, 1280));
  assert.deepEqual({ minWidth: mobile?.minWidth, minHeight: mobile?.minHeight }, { minWidth: 42, minHeight: 42 });
  assert.deepEqual({ minWidth: desktop?.minWidth, minHeight: desktop?.minHeight }, { minWidth: 44, minHeight: 44 });
});

test('42px mobile Explore remains valid while a silent 42->24 shrink fails the product contract', () => {
  const mobile = DEFAULT_PRODUCT_CONTRACTS.find((item) => item.selector === '.explore-trigger' && contractApplies(item, 390));
  assert.equal(contractPasses({ width: 42, height: 42 }, mobile), true);
  assert.equal(contractPasses({ width: 24, height: 24 }, mobile), false);
});

test('header search preserves its 44px height while allowing the intentional 42px mobile width', () => {
  const mobile = DEFAULT_PRODUCT_CONTRACTS.find((item) => item.selector === '.header-search' && contractApplies(item, 768));
  assert.equal(contractPasses({ width: 42, height: 44 }, mobile), true);
  assert.equal(contractPasses({ width: 42, height: 43.99 }, mobile), false);
});

test('desktop header search also preserves the historical 42px width regression bar', () => {
  const desktop = DEFAULT_PRODUCT_CONTRACTS.find((item) => item.selector === '.header-search' && contractApplies(item, 1280));
  assert.equal(contractPasses({ width: 42, height: 44 }, desktop), true);
  assert.equal(contractPasses({ width: 24, height: 44 }, desktop), false);
});

test('the only declared equivalent target is source-backed object-record import -> visible open button', () => {
  assert.deepEqual(DEFAULT_EQUIVALENT_TARGETS, [
    {
      selector: '[data-record-import]',
      equivalentSelector: '[data-record-open]',
      source: 'assets/objeto-heredado.js',
    },
  ]);
});

test('object-record Equivalent exception remains functionally true', () => {
  const source = fs.readFileSync('assets/objeto-heredado.js', 'utf8');
  assert.match(
    source,
    /\$\('\[data-record-open\]'\)\.addEventListener\('click', \(\) => fileInput\.click\(\)\);/,
    'Abrir JSON must keep invoking the hidden file input while F.1 relies on Equivalent',
  );
});
