// Runs in the page, both as a snapshot and as a requestAnimationFrame predicate.
export function readKeyboardFocusState(requireUsable = false) {
  const el = document.activeElement;
  let state;
  if (!el || el === document.body) {
    state = { key: 'BODY', ok: false, reason: 'focus on body' };
  } else {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    const hidden = el.closest('[aria-hidden="true"],[inert]');
    let transparent = false;
    for (let node = el; node && node.nodeType === 1; node = node.parentElement || node.getRootNode()?.host) {
      if (Number(getComputedStyle(node).opacity) === 0) {
        transparent = true;
        break;
      }
    }
    const left = Math.max(0, r.left);
    const right = Math.min(innerWidth, r.right);
    const top = Math.max(0, r.top);
    const bottom = Math.min(innerHeight, r.bottom);
    const visibleArea = right > left && bottom > top;
    const points = visibleArea ? [
      [(left + right) / 2, (top + bottom) / 2],
      [left + (right - left) * 0.25, top + (bottom - top) * 0.25],
      [left + (right - left) * 0.75, top + (bottom - top) * 0.25],
      [left + (right - left) * 0.25, top + (bottom - top) * 0.75],
      [left + (right - left) * 0.75, top + (bottom - top) * 0.75],
    ] : [];
    const hitBelongsToFocus = (hit) => {
      for (let node = hit; node; node = node.parentElement || node.getRootNode()?.host) {
        if (node === el) return true;
      }
      return false;
    };
    const unobstructed = points.some(([x, y]) => hitBelongsToFocus(document.elementFromPoint(x, y)));
    const key = el.id || el.getAttribute('href') || el.getAttribute('name') || el.getAttribute('aria-label') || el.textContent?.trim().slice(0, 60) || el.tagName;
    state = {
      key: String(key),
      ok: !hidden && !transparent && unobstructed && s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < innerHeight && r.right > 0 && r.left < innerWidth,
      reason: hidden ? 'inside aria-hidden/inert' : `rect ${Math.round(r.left)},${Math.round(r.top)} ${Math.round(r.width)}x${Math.round(r.height)}`,
    };
  }
  return requireUsable ? (state.ok && state) : state;
}

export async function waitForKeyboardFocusState(page, timeout = 1500) {
  // Tab can be acknowledged before Chromium paints its native focus scroll.
  // Observe that scroll; never focus or scroll the target from the audit itself.
  let handle;
  try {
    handle = await page.waitForFunction(readKeyboardFocusState, true, { timeout, polling: 'raf' });
    return await handle.jsonValue();
  } catch (error) {
    if (error.name !== 'TimeoutError') throw error;
    return await page.evaluate(readKeyboardFocusState, false);
  } finally {
    await handle?.dispose();
  }
}
