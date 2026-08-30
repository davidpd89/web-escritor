const DEFAULT_MINIMUM = 24;

export const DEFAULT_PRODUCT_CONTRACTS = [
  {
    selector: '.explore-trigger',
    maxViewportWidth: 899,
    minWidth: 42,
    minHeight: 42,
    source: 'assets/v1-shell-lrb-v2.css + qa/home-map-interaction.mjs',
  },
  {
    selector: '.explore-trigger',
    minViewportWidth: 900,
    minWidth: 44,
    minHeight: 44,
    source: 'assets/v1-shell-base.css',
  },
  {
    selector: '.header-search',
    maxViewportWidth: 899,
    minWidth: 42,
    minHeight: 44,
    source: 'assets/v1-shell-lrb-v2.css',
  },
  {
    selector: '.header-search',
    minViewportWidth: 900,
    minWidth: 42,
    minHeight: 44,
    source: 'F01 blueprint + assets/v1-shell-base.css + assets/v1-shell-lrb-v2.css',
  },
];

export function pointToRectDistance(x, y, rect) {
  const dx = Math.max(rect.left - x, 0, x - rect.right);
  const dy = Math.max(rect.top - y, 0, y - rect.bottom);
  return Math.hypot(dx, dy);
}

export function spacingPasses(subject, others, minimum = DEFAULT_MINIMUM) {
  const radius = minimum / 2;
  for (const other of others) {
    if (other === subject) continue;
    if (other.undersized) {
      const distance = Math.hypot(subject.cx - other.cx, subject.cy - other.cy);
      if (distance < minimum) return false;
      continue;
    }
    if (pointToRectDistance(subject.cx, subject.cy, other.rect) < radius) return false;
  }
  return true;
}

export function contractApplies(contract, viewportWidth) {
  if (contract.minViewportWidth != null && viewportWidth < contract.minViewportWidth) return false;
  if (contract.maxViewportWidth != null && viewportWidth > contract.maxViewportWidth) return false;
  return true;
}

export function contractPasses(rect, contract) {
  if (contract.minWidth != null && rect.width < contract.minWidth) return false;
  if (contract.minHeight != null && rect.height < contract.minHeight) return false;
  return true;
}

export async function auditTargetSizes(
  page,
  { minimum = DEFAULT_MINIMUM, productContracts = DEFAULT_PRODUCT_CONTRACTS } = {},
) {
  return page.evaluate(({ min, contracts }) => {
    const TARGET_SELECTOR = [
      'a[href]',
      'button',
      'input:not([type="hidden"])',
      'select',
      'textarea',
      'summary',
      '[role="button"]',
      '[role="link"]',
      '[role="checkbox"]',
      '[role="radio"]',
      '[tabindex]:not([tabindex="-1"])',
    ].join(',');

    function selectorFor(el) {
      if (el.id) return `#${CSS.escape(el.id)}`;
      const parts = [];
      let node = el;
      while (node && node !== document.body && parts.length < 4) {
        let part = node.tagName.toLowerCase();
        if (node.classList.length) {
          part += [...node.classList].slice(0, 3).map((name) => `.${CSS.escape(name)}`).join('');
        }
        const parent = node.parentElement;
        if (parent) {
          const siblings = [...parent.children].filter((child) => child.tagName === node.tagName);
          if (siblings.length > 1) part += `:nth-of-type(${siblings.indexOf(node) + 1})`;
        }
        parts.unshift(part);
        node = parent;
      }
      return parts.join(' > ');
    }

    function isRenderedPointerTarget(el) {
      if (!(el instanceof HTMLElement) && !(el instanceof SVGElement)) return false;
      if (el.closest('[inert]')) return false;
      if ('disabled' in el && el.disabled) return false;

      // Browsers may still return geometry for descendants of a closed
      // <details>. Only its summary is exposed as a pointer target until open.
      // Sitewide Reflow runs a second explicit state with every <details>
      // expanded so those descendants are still audited when they are usable.
      const closedDetails = el.closest('details:not([open])');
      if (closedDetails) {
        const visibleSummary = closedDetails.querySelector(':scope > summary');
        if (el !== visibleSummary && !visibleSummary?.contains(el)) return false;
      }

      const style = window.getComputedStyle(el);
      if (style.display === 'none' || style.visibility === 'hidden' || style.visibility === 'collapse') return false;
      if (style.pointerEvents === 'none') return false;
      const rect = el.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0;
    }

    function rectData(rect) {
      return {
        left: rect.left,
        top: rect.top,
        right: rect.right,
        bottom: rect.bottom,
        width: rect.width,
        height: rect.height,
      };
    }

    function isInlineException(el) {
      if (!el.matches('a[href]')) return false;
      const style = window.getComputedStyle(el);
      if (style.display !== 'inline') return false;
      return Boolean(el.closest('p, dd, dt, figcaption, blockquote'));
    }

    function hasCompliantAssociatedLabel(el) {
      if (!(el instanceof HTMLInputElement)) return false;
      // A label for checkbox/radio toggles that control; a label for a file
      // input opens the same file picker. These are verifiable equivalent
      // pointer targets. Labels for ordinary text inputs merely move focus,
      // so they are not treated as a blanket Equivalent exception here.
      if (!['checkbox', 'radio', 'file'].includes(el.type)) return false;
      for (const label of el.labels || []) {
        if (!isRenderedPointerTarget(label)) continue;
        const rect = label.getBoundingClientRect();
        if (rect.width >= min && rect.height >= min) return true;
      }
      return false;
    }

    function pointToRectDistance(x, y, rect) {
      const dx = Math.max(rect.left - x, 0, x - rect.right);
      const dy = Math.max(rect.top - y, 0, y - rect.bottom);
      return Math.hypot(dx, dy);
    }

    function contractApplies(contract) {
      if (contract.minViewportWidth != null && window.innerWidth < contract.minViewportWidth) return false;
      if (contract.maxViewportWidth != null && window.innerWidth > contract.maxViewportWidth) return false;
      return true;
    }

    function matchingContract(el) {
      return contracts.find((contract) => contractApplies(contract) && el.matches(contract.selector)) || null;
    }

    const nodes = [...document.querySelectorAll(TARGET_SELECTOR)].filter(isRenderedPointerTarget);
    const targets = nodes.map((el) => {
      const rect = el.getBoundingClientRect();
      const data = rectData(rect);
      const productContract = matchingContract(el);
      return {
        el,
        selector: selectorFor(el),
        tag: el.tagName.toLowerCase(),
        role: el.getAttribute('role'),
        type: el instanceof HTMLInputElement ? el.type : null,
        text: (el.getAttribute('aria-label') || el.textContent || el.getAttribute('value') || '')
          .replace(/\s+/g, ' ')
          .trim()
          .slice(0, 100),
        rect: data,
        cx: data.left + data.width / 2,
        cy: data.top + data.height / 2,
        undersized: data.width < min || data.height < min,
        productContract,
      };
    });

    const results = [];
    for (const target of targets) {
      let status = 'pass';
      let reason = 'size';

      if (target.productContract) {
        const { minWidth, minHeight } = target.productContract;
        const widthPass = minWidth == null || target.rect.width >= minWidth;
        const heightPass = minHeight == null || target.rect.height >= minHeight;
        if (!widthPass || !heightPass) {
          status = 'fail';
          reason = 'product_contract_below_minimum';
        }
      }

      if (status === 'pass' && target.undersized) {
        if (isInlineException(target.el)) {
          reason = 'inline_exception';
        } else if (hasCompliantAssociatedLabel(target.el)) {
          reason = 'associated_label_target';
        } else {
          const radius = min / 2;
          let spacingPass = true;
          for (const other of targets) {
            if (other === target) continue;
            if (other.undersized) {
              const distance = Math.hypot(target.cx - other.cx, target.cy - other.cy);
              if (distance < min) {
                spacingPass = false;
                break;
              }
            } else if (pointToRectDistance(target.cx, target.cy, other.rect) < radius) {
              spacingPass = false;
              break;
            }
          }
          if (spacingPass) {
            reason = 'spacing_exception';
          } else {
            status = 'fail';
            reason = 'undersized_and_too_close';
          }
        }
      }

      results.push({
        selector: target.selector,
        tag: target.tag,
        role: target.role,
        type: target.type,
        text: target.text,
        width: Math.round(target.rect.width * 100) / 100,
        height: Math.round(target.rect.height * 100) / 100,
        status,
        reason,
        productContract: target.productContract ? {
          selector: target.productContract.selector,
          minWidth: target.productContract.minWidth ?? null,
          minHeight: target.productContract.minHeight ?? null,
          source: target.productContract.source || null,
        } : null,
      });
    }

    const failures = results.filter((item) => item.status === 'fail');
    const exceptions = results.filter((item) => item.reason !== 'size' && item.status === 'pass');
    const productContractChecks = results.filter((item) => item.productContract);
    return {
      minimumCssPx: min,
      targetCount: results.length,
      failureCount: failures.length,
      exceptionCount: exceptions.length,
      productContractCheckCount: productContractChecks.length,
      failures,
      exceptions,
      productContractChecks,
    };
  }, { min: minimum, contracts: productContracts });
}
