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
    // Sample each line box, not the bounding box: an inline link that wraps has a
    // bounding rect spanning most of the paragraph, so its center and quarter
    // points land on plain text and read as "obstructed" depending on where the
    // runner's fonts break the line (Post-deploy deep audit, /cuaderno/ 2026-10-25).
    const points = [];
    for (const box of [...el.getClientRects()]) {
      const left = Math.max(0, box.left);
      const right = Math.min(innerWidth, box.right);
      const top = Math.max(0, box.top);
      const bottom = Math.min(innerHeight, box.bottom);
      if (right <= left || bottom <= top) continue;
      points.push(
        [(left + right) / 2, (top + bottom) / 2],
        [left + (right - left) * 0.25, top + (bottom - top) * 0.5],
        [left + (right - left) * 0.75, top + (bottom - top) * 0.5],
      );
    }
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
      reason: hidden ? 'inside aria-hidden/inert' : `rect ${Math.round(r.left)},${Math.round(r.top)} ${Math.round(r.width)}x${Math.round(r.height)} in ${innerWidth}x${innerHeight}${transparent ? '; opacity 0' : ''}${unobstructed ? '' : '; obstructed'}; visibility ${s.visibility}`,
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
