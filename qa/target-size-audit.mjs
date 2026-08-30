const DEFAULT_MINIMUM = 24;

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

export async function auditTargetSizes(page, { minimum = DEFAULT_MINIMUM } = {}) {
  return page.evaluate((min) => {
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

      // `.sr-only` controls are intentionally removed from the visual/pointer
      // surface and operated through an equivalent visible control. Measuring
      // their 1px accessibility box as a pointer target creates false failures.
      if (el.classList?.contains('sr-only')) return false;

      // Browsers may still return geometry for descendants of a closed
      // <details>. Only its summary is exposed as a pointer target until open.
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
      if (!['checkbox', 'radio'].includes(el.type)) return false;
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

    const nodes = [...document.querySelectorAll(TARGET_SELECTOR)].filter(isRenderedPointerTarget);
    const targets = nodes.map((el) => {
      const rect = el.getBoundingClientRect();
      const data = rectData(rect);
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
      };
    });

    const results = [];
    for (const target of targets) {
      let status = 'pass';
      let reason = 'size';

      if (target.undersized) {
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
      });
    }

    const failures = results.filter((item) => item.status === 'fail');
    const exceptions = results.filter((item) => item.reason !== 'size' && item.status === 'pass');
    return {
      minimumCssPx: min,
      targetCount: results.length,
      failureCount: failures.length,
      exceptionCount: exceptions.length,
      failures,
      exceptions,
    };
  }, minimum);
}
