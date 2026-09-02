// F.4 · WCAG 2.2 SC 2.4.11 Focus Not Obscured (Minimum), AA.
// https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html
//
// Per docs/web-improvement-ideas/F04-PRODUCTION-REVALIDATION-2026-08-30.md:
// reuse the shared Sitewide Reflow harness's browser/route plumbing, add one
// geometric helper, and run it over a small curated set of representative
// journeys -- not a blind tab-through of every focusable node on every route.
//
// Method: focus each visible, non-inert focusable element in DOM order, then
// sample its four corners + center via document.elementFromPoint(). If none
// of those points resolve back to the focused element (or a descendant/
// ancestor of it -- covers e.g. a <button> whose visible label is a child
// span), the element counts as fully obscured by whatever author-created
// content IS at those points (sticky header/footer, dialog, overlay --
// the mechanism doesn't matter, only the resulting geometry does, which is
// what the SC actually cares about). An element entirely outside the
// viewport box is reported separately (not what 2.4.11 governs, but a
// keyboard-trap-adjacent smell worth surfacing).

const FOCUSABLE_SELECTOR = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
  'summary',
  '[contenteditable="true"]',
].join(',');

export async function auditFocusNotObscured(page, { maxStops = 60 } = {}) {
  return page.evaluate(async ({ selector, maxStops }) => {
    function describe(el) {
      if (!el) return null;
      let s = el.tagName.toLowerCase();
      if (el.id) s += `#${el.id}`;
      else if (typeof el.className === 'string' && el.className.trim()) {
        s += '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.');
      }
      return s;
    }
    function isVisible(el) {
      const cs = getComputedStyle(el);
      if (cs.visibility === 'hidden' || cs.display === 'none') return false;
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0;
    }
    const all = [...document.querySelectorAll(selector)]
      .filter((el) => isVisible(el) && !el.closest('[hidden],[inert]'))
      .slice(0, maxStops);

    const failures = [];
    for (const el of all) {
      el.focus({ preventScroll: false });
      if (document.activeElement !== el) continue;
      // Some focus-revealed elements (e.g. .skip-link) animate into place via
      // a CSS transition on :focus. Even a near-instant transition (reduced-
      // motion sites often set ~0.00001s, not 0s) still needs a real
      // transitionrun->transitionend cycle to resolve, which two
      // requestAnimationFrame callbacks were not reliably enough to catch
      // (measured: still mid-transition at 2xRAF, fully settled by 500ms) --
      // use a short fixed wait instead of guessing frame counts.
      await new Promise((resolve) => setTimeout(resolve, 60));
      // Focusing an off-screen element scrolls it into view by default (the
      // real behavior a keyboard user gets, and part of what this check
      // means to exercise) -- but that scroll can trigger unrelated page
      // behavior (e.g. a scroll-depth popup) that steals focus during the
      // settle wait above. Re-check rather than trust the stale reference.
      if (document.activeElement !== el) continue;
      const r = el.getBoundingClientRect();
      const inViewport = r.bottom > 0 && r.top < window.innerHeight && r.right > 0 && r.left < window.innerWidth;
      if (!inViewport) {
        failures.push({ selector: describe(el), reason: 'entirely-outside-viewport', rect: r });
        continue;
      }
      const pad = 1;
      const points = [
        [r.left + pad, r.top + pad],
        [r.right - pad, r.top + pad],
        [r.left + pad, r.bottom - pad],
        [r.right - pad, r.bottom - pad],
        [(r.left + r.right) / 2, (r.top + r.bottom) / 2],
      ];
      let hitTarget = false;
      let blocker = null;
      for (const [x, y] of points) {
        const hit = document.elementFromPoint(x, y);
        if (hit && (hit === el || el.contains(hit) || hit.contains(el))) {
          hitTarget = true;
          break;
        }
        if (hit && !blocker) blocker = describe(hit);
      }
      if (!hitTarget) {
        failures.push({
          selector: describe(el),
          reason: 'fully-obscured',
          rect: { x: r.x, y: r.y, width: r.width, height: r.height },
          blocker,
        });
      }
    }
    return { total: all.length, failures };
  }, { selector: FOCUSABLE_SELECTOR, maxStops });
}
