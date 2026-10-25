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
    const key = el.id || el.getAttribute('href') || el.getAttribute('name') || el.getAttribute('aria-label') || el.textContent?.trim().slice(0, 60) || el.tagName;
    state = {
      key: String(key),
      ok: !hidden && s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < innerHeight && r.right > 0 && r.left < innerWidth,
      reason: hidden ? 'inside aria-hidden/inert' : `rect ${Math.round(r.left)},${Math.round(r.top)} ${Math.round(r.width)}x${Math.round(r.height)}`,
    };
  }
  return requireUsable ? (state.ok && state) : state;
}

export async function waitForKeyboardFocusState(page, timeout = 4000) {
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
