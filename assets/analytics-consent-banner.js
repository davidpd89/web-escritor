// Minimal analytics-consent banner (2026-09-08): a small, non-blocking bar,
// not a full cookie-CMP -- the site deliberately has no banner for anything
// else (GoatCounter/Metricool never set cookies regardless of any choice
// here). Shown once; the choice persists in localStorage. This is the only
// legitimate way to get Clarity's full cross-page session data: reporting
// 'granted' without ever asking would misrepresent consent that was never
// collected, which is exactly the bug fixed earlier today.
//
// Split out of script.js (2026-09-08) so the legal pages (privacidad.html,
// aviso-legal.html) can load a working "Preferencias de analítica" control
// without pulling in the GoatCounter/Metricool/Clarity loaders that live in
// script.js -- those pages are contractually required to make zero external
// requests on a fresh visit (qa/privacy-contract-browser.mjs). Every page
// that loads script.js loads this file first (script.js calls the functions
// declared here); applyAnalyticsConsent() below is a no-op wherever
// window.clarity was never loaded, which is exactly the legal pages' case.
const ANALYTICS_CONSENT_KEY = "dp-analytics-consent";
const ANALYTICS_CONSENT_VERSION = 1;
// Explicit site-owner decision (2026-09-09): the very first scroll after the
// banner appears used to count as implicit accept, which meant a visitor who
// arrived and immediately scrolled never actually saw the banner before it
// vanished. This grace window keeps clicks/scrolls/unload from deciding
// anything for the first 30s the banner is on screen -- after that, the
// original "continued use = accept" behavior applies exactly as before.
// Overridable via window.__ANALYTICS_CONSENT_GRACE_MS__ so QA
// (qa/privacy-contract-browser.mjs) can verify the eventual implicit-accept
// behavior without a real 30s wait.
const ANALYTICS_CONSENT_GRACE_MS =
  typeof window.__ANALYTICS_CONSENT_GRACE_MS__ === "number"
    ? window.__ANALYTICS_CONSENT_GRACE_MS__
    : 30000;
// AEPD guidance treats a cookie consent as stale after long enough that the
// visitor may no longer remember giving it, and recommends re-asking rather
// than relying on it indefinitely -- 24 months, same ceiling the guidance
// itself uses.
const ANALYTICS_CONSENT_MAX_AGE_MS = 24 * 30 * 24 * 60 * 60 * 1000;

function getStoredAnalyticsConsent() {
  try {
    const raw = localStorage.getItem(ANALYTICS_CONSENT_KEY);
    if (!raw) return null;
    let parsed;
    if (raw === "granted" || raw === "denied") {
      // Pre-versioning format: a bare string with no timestamp, from before
      // 2026-09-08. Treated as a decision made right now (not instantly
      // expired) and re-saved below in the new shape so it carries a real
      // timestamp from this point on instead of surviving forever unmigrated.
      parsed = { value: raw, v: ANALYTICS_CONSENT_VERSION, ts: Date.now() };
      setStoredAnalyticsConsent(parsed.value);
    } else {
      parsed = JSON.parse(raw);
    }
    if (!parsed || (parsed.value !== "granted" && parsed.value !== "denied") || typeof parsed.ts !== "number") {
      return null;
    }
    if (Date.now() - parsed.ts > ANALYTICS_CONSENT_MAX_AGE_MS) return null;
    return parsed;
  } catch {
    return null;
  }
}

function setStoredAnalyticsConsent(value) {
  try {
    localStorage.setItem(ANALYTICS_CONSENT_KEY, JSON.stringify({ value, v: ANALYTICS_CONSENT_VERSION, ts: Date.now() }));
  } catch {
    // Storage blocked (private mode, disabled storage, etc.) -- the choice
    // just won't be remembered across visits; applyAnalyticsConsent still
    // runs for this pageview.
  }
}

function applyAnalyticsConsent(value) {
  if (window.clarity) {
    window.clarity("consentv2", { ad_Storage: "denied", analytics_Storage: value });
  }
}

function showAnalyticsConsentBanner() {
  if (document.querySelector("[data-analytics-consent-banner]")) return;
  const bar = document.createElement("div");
  bar.setAttribute("data-analytics-consent-banner", "");
  bar.setAttribute("role", "region");
  bar.setAttribute("aria-label", "Preferencia de analítica");
  // A small bottom-left corner toast, not a full-width bar: this site
  // already has other fixed-position interactive UI sitewide (#sticky-cta
  // full-width on Manecillas/Samuel sample pages, the [data-intro-enter]
  // splash gate button on others) and a solid full-width bar fought them
  // for the same screen region, intercepting clicks meant for them (caught
  // by qa/manecillas-funnel-browser.mjs, qa/samuel-fragmento-design-cross-
  // engine.mjs, and qa/privacy-contract-browser.mjs in CI). Rather than
  // enumerating every such element sitewide, the container itself ignores
  // pointer events -- only the actual controls (link + two buttons) opt
  // back in -- so the banner's padding/background/text never intercepts a
  // click meant for whatever happens to render underneath it.
  // width uses %, not 100vw: vw is the raw window width and ignores a
  // reserved scrollbar gutter, so on a page tall enough to scroll this
  // corner box would sit a few pixels wider than the actual viewport
  // and overflow horizontally -- caught by qa/sitewide-reflow-browser.mjs's
  // F.2 200%-text-resize+spacing scenario, which reliably makes every
  // page tall enough to scroll. % correctly resolves against the
  // scrollbar-adjusted viewport.
  // Styled from the site's own V1 design tokens (assets/v1-tokens.css) with
  // hardcoded fallbacks -- this banner runs sitewide, including pages that
  // never load v1-tokens.css, matching the same var(--dp-ink,#171412)
  // fallback pattern already used by assets/assistant-widget.css and
  // assets/newsletter-popup.css for the same reason.
  // z-index 899, not 9999: assets/v1-home.css's full-screen ".intro" splash
  // (home and Samuel sample pages) is z-index:900. At 9999 this banner used
  // to render on top of that splash during its first few seconds, and a
  // taller banner (the longer copy below wraps to more lines than the
  // original one-line version) grew tall enough to actually overlap
  // .intro__enter's clickable area -- caught by qa/privacy-contract-browser
  // .mjs's intro-dismiss step timing out because the banner intercepted the
  // click. 899 keeps this banner above ordinary page chrome (z-header:200,
  // z-dialog:800 in assets/v1-tokens.css) but behind that one splash, which
  // paints nothing once dismissed so ordering against it stops mattering.
  // Sized to land close to the original banner's ~140px total height, not
  // just to look compact: "Rechazo ayudarte"/"Acepto ayudarte" (longer than
  // the original "Rechazar"/"Aceptar") and a longer explanatory sentence
  // both tried wider/taller variants first (300px, then 336px, then 380px
  // wide, with a 2-3 line paragraph each time), and each one grew the
  // banner tall and wide enough to fully cover a real, unrelated focusable
  // element somewhere on some page -- a link on Home, a button on a
  // Cuaderno article -- caught by qa/focus-not-obscured-audit.mjs's WCAG
  // 2.4.11 check, which focuses every interactive element in DOM order and
  // fails if any of them becomes entirely hit-tested by something else
  // (here, this banner). There is no width that avoids this in general --
  // wider covers more horizontally on narrow phones, narrower forces more
  // text wrapping and covers more vertically -- so the fix that actually
  // holds is keeping the banner as short as the original, at 328px with
  // tight-but-legible button padding/font-size, rather than picking a
  // width and hoping nothing sits underneath it.
  bar.style.cssText = "position:fixed;left:.75rem;bottom:.75rem;z-index:899;display:flex;flex-direction:column;gap:.5rem;width:328px;max-width:calc(100% - 1.5rem);padding:.85rem;background:var(--surface-page,#fff);color:var(--dp-ink,#171412);font:13px/1.4 var(--font-ui,system-ui,sans-serif);border:1px solid var(--dp-ink,#171412);border-radius:var(--radius-control,4px);box-shadow:0 4px 16px rgba(0,0,0,.18);pointer-events:none;";

  const text = document.createElement("p");
  text.style.cssText = "margin:0;";
  text.textContent = "¿Me ayudas a mejorar la web? Uso Clarity, nunca publicidad.";

  const actions = document.createElement("div");
  // flex-wrap: the two buttons' rem-based padding doubles under 200% root
  // font-size (WCAG 1.4.4), which can need more width than the narrow
  // corner box has to give at 320px -- without wrapping, a button got
  // pushed past the viewport edge instead of onto its own line (caught
  // by qa/text-resilience-report-gate.mjs's enforced F.2 gate).
  actions.style.cssText = "display:flex;flex-wrap:wrap;gap:.5rem;";

  // Both buttons share size/padding/weight/radius, but Aceptar is filled in
  // the site's own accent blue (var(--color-accent-strong)) and Rechazar
  // stays plain-outlined -- an explicit, deliberate choice (2026-09-08) to
  // make Aceptar the visually stronger of the two. AEPD guidance says accept
  // and reject should be offered "at the same time, at the same level, and
  // with the same visibility"; this asymmetry doesn't fully clear that bar,
  // which is worth knowing if this ever gets a compliance review, but it's
  // the look that was explicitly asked for over the initially-shipped
  // equal-weight version.
  // No white-space:nowrap here (on purpose): at 320px+200%-text-zoom, even
  // after flex-wrap above puts each button on its own row, "Rechazo
  // ayudarte" at doubled font size is still wider than the available
  // width, so the button itself must be able to break onto two lines
  // (min-width:0 lets it actually shrink instead of keeping nowrap's
  // full-phrase content-based minimum) -- caught by the same F.2 gate.
  const btnBaseCss = "padding:.5rem .55rem;min-height:var(--control-min-height,44px);min-width:0;border-radius:var(--radius-control,4px);font:600 .76rem/1.2 var(--font-ui,inherit);cursor:pointer;pointer-events:auto;text-align:center;";

  const rejectBtn = document.createElement("button");
  rejectBtn.type = "button";
  rejectBtn.textContent = "Rechazo ayudarte";
  rejectBtn.style.cssText = btnBaseCss + "border:1px solid var(--dp-ink,#171412);background:transparent;color:var(--dp-ink,#171412);";

  const acceptBtn = document.createElement("button");
  acceptBtn.type = "button";
  acceptBtn.textContent = "Acepto ayudarte";
  acceptBtn.style.cssText = btnBaseCss + "border:1px solid var(--color-accent-strong,#0075b8);background:var(--color-accent-strong,#0075b8);color:#fff;";

  const link = document.createElement("a");
  link.href = "/privacidad.html";
  link.textContent = "Privacidad";
  // padding bumps the link's own hit target to >=24x24 CSS px (WCAG 2.2
  // SC 2.5.8), which a plain text line this short falls short of on its
  // own -- caught by qa/sitewide-reflow-browser.mjs's target-size gate.
  link.style.cssText = "align-self:flex-start;display:inline-block;padding:.3rem 0;margin:-.3rem 0;color:var(--dp-ink,#171412);text-decoration:underline;font-size:.78rem;pointer-events:auto;";

  function decide(value) {
    setStoredAnalyticsConsent(value);
    applyAnalyticsConsent(value);
    bar.remove();
    document.removeEventListener("click", implicitAccept, true);
    document.removeEventListener("scroll", implicitAccept, true);
    window.removeEventListener("beforeunload", implicitAcceptOnUnload);
  }
  rejectBtn.addEventListener("click", () => decide("denied"));
  acceptBtn.addEventListener("click", () => decide("granted"));

  // Implicit-accept-by-continued-use: a deliberate product decision
  // (2026-09-08, explicit instruction from the site owner, made after the
  // AEPD-compliance tradeoff was explained) -- browsing the site without
  // clicking either button is treated as acceptance; clicking "Rechazo
  // ayudarte" is the only path to denied. Only clicks/scrolls OUTSIDE the
  // banner count (bar.contains guard), so choosing either button still
  // always goes through decide() directly above, never through this path.
  // graceUntil (2026-09-09): none of that fires during the first
  // ANALYTICS_CONSENT_GRACE_MS -- the visitor gets that long to actually see
  // the banner before an ordinary scroll or tap silently decides for them.
  const graceUntil = Date.now() + ANALYTICS_CONSENT_GRACE_MS;
  function implicitAccept(e) {
    if (bar.contains(e.target)) return;
    if (Date.now() < graceUntil) return;
    decide("granted");
  }
  function implicitAcceptOnUnload() {
    if (Date.now() < graceUntil) return;
    if (!getStoredAnalyticsConsent()) decide("granted");
  }
  document.addEventListener("click", implicitAccept, true);
  document.addEventListener("scroll", implicitAccept, true);
  window.addEventListener("beforeunload", implicitAcceptOnUnload);

  actions.append(rejectBtn, acceptBtn);
  bar.append(text, actions, link);
  document.body.appendChild(bar);
  avoidBottomBarOverlap(bar);
  avoidObscuringFocus(bar);
}

// WCAG 2.2 SC 2.4.11 Focus Not Obscured (Minimum): a keyboard user tabbing
// through the page must be able to see whatever currently has focus. No
// fixed size/position for this banner is safe in general -- the page has
// ~130 focusable links/buttons across dozens of routes, tabbing scrolls
// each one into view, and any one of them can land underneath this corner
// box depending on where it happens to sit on that particular page (caught
// on Home's "Lectores beta" footer link and a Cuaderno article's TOC toggle
// -- unrelated content, not something to chase link-by-link). The
// compliant pattern the SC's own understanding doc names for exactly this
// case is to move sticky/fixed UI out of the way of whatever is focused,
// not to guess a size that never overlaps anything. transform, not
// visibility/display, so the banner stays in normal tab order -- a
// visibility:hidden banner would be skipped entirely by Tab, making it
// unreachable right when a user tabs from the element that triggered the
// hide toward the banner itself.
function avoidObscuringFocus(bar) {
  function reposition() {
    const active = document.activeElement;
    // Narrow, deliberate exception: the <main> landmark itself, focused via
    // tabindex="-1" as a script-only target (never reachable by Tab). This
    // site's own v1-shell.js does exactly that -- `main.focus()` -- once the
    // Home intro closes. <main> wraps essentially the whole page by
    // definition, so its bounding box always "overlaps" this corner banner
    // under the plain rect-intersection test below, which shoved the banner
    // down by a full viewport height every time (reported live: banner
    // invisible after the intro, only reappearing/disappearing as that
    // page-spanning rect's viewport-relative position swept past the corner
    // on scroll). This does NOT generalize to every tabindex="-1" element:
    // that pattern is also used for genuinely visible, boundable focus
    // targets this check must keep protecting -- an error message, a modal
    // heading, a "skip to" destination that isn't the whole page. Only the
    // <main>-landmark case is exempt, matched by tag, not by tabIndex alone.
    const isMainLandmarkFocusSink = active && active.tagName === "MAIN" && active.tabIndex === -1;
    if (!active || active === document.body || bar.contains(active) || isMainLandmarkFocusSink) {
      bar.style.transform = "";
      return;
    }
    // offsetTop/offsetLeft/offsetWidth/offsetHeight, not
    // getBoundingClientRect(): for a position:fixed element these are the
    // resting layout position regardless of any transform currently
    // applied, since transform is paint-only and never affects offset*.
    // An earlier version reset bar.style.transform to "" and then called
    // getBoundingClientRect() to measure the resting position -- reasonable
    // in isolation, but broke down (measured empirically) once focus moved
    // quickly enough that a still-pending reposition() from the PREVIOUS
    // focus target could re-apply its own shift after this one's reset,
    // so this call's own already-computed barRect (captured before that
    // interleaving) stayed correct while the DOM had already been shifted
    // out from under it. Reading layout-only geometry sidesteps that
    // ordering question entirely instead of trying to win the race.
    const barRect = {
      left: bar.offsetLeft,
      top: bar.offsetTop,
      right: bar.offsetLeft + bar.offsetWidth,
      bottom: bar.offsetTop + bar.offsetHeight,
    };
    const elRect = active.getBoundingClientRect();
    const overlaps = elRect.width > 0 && elRect.height > 0 &&
      elRect.right > barRect.left && elRect.left < barRect.right &&
      elRect.bottom > barRect.top && elRect.top < barRect.bottom;
    bar.style.transform = overlaps ? `translateY(${window.innerHeight - barRect.top + 24}px)` : "";
  }
  // Focusing an off-screen element triggers the browser's own scroll-into-
  // view, which is not necessarily finished by the time the synchronous
  // focusin handler runs, or even by the next animation frame in a headless
  // test runner (confirmed: both a plain synchronous check and a
  // requestAnimationFrame-deferred one missed the exact case this exists
  // for, because the focused element's rect was still its pre-scroll
  // position at that point). A short timeout reliably lands after the
  // scroll settles; the scroll listener re-runs it again for a real,
  // possibly-longer smooth-scroll (this site's own QA runs with
  // reducedMotion, where the jump is instant).
  let scheduled = false;
  function scheduleReposition() {
    if (scheduled) return;
    scheduled = true;
    setTimeout(() => {
      scheduled = false;
      reposition();
    }, 30);
  }
  document.addEventListener("focusin", scheduleReposition);
  document.addEventListener("focusout", () => setTimeout(scheduleReposition, 0));
  window.addEventListener("scroll", scheduleReposition, { passive: true });
}

// Reopens the banner on demand so a visitor can change an earlier choice
// without knowing how to clear site data in their browser -- wired to any
// element carrying [data-analytics-preferences] (see privacidad.html).
// Re-running decide() through the existing banner UI, rather than a
// separate toggle, is what actually tells Clarity via consentv2 when
// switching granted -> denied; Microsoft's own docs say that call is what
// makes Clarity drop its cookies and end the current session. On the legal
// pages, where Clarity was never loaded, this still updates the stored
// choice correctly -- applyAnalyticsConsent()'s window.clarity guard just
// no-ops, and the new value takes effect the next time Clarity does load,
// on whichever non-legal page the visitor goes to next.
function openAnalyticsPreferences() {
  const existing = document.querySelector("[data-analytics-consent-banner]");
  if (existing) existing.remove();
  showAnalyticsConsentBanner();
}
document.addEventListener("click", (e) => {
  const trigger = e.target.closest("[data-analytics-preferences]");
  if (trigger) {
    e.preventDefault();
    openAnalyticsPreferences();
  }
});

// Mobile Safari (and some Android browsers) position `position:fixed`
// elements against the LAYOUT viewport, which starts out taller than the
// VISUAL viewport while the browser's own UI (URL bar, bottom toolbar) is
// still fully expanded on first paint. A fixed bottom-anchored element can
// therefore render below the currently-visible area -- reported live on a
// phone as "the Clarity banner only shows up once I scroll all the way
// down" -- because scrolling is what makes the toolbar auto-collapse and
// the layout viewport catch up to the visual one. window.visualViewport
// (supported in every current mobile browser) reports the real visible
// size directly, so adding the gap between it and window.innerHeight as
// extra bottom offset keeps the banner inside the actually-visible area
// from the first paint, without waiting for a scroll to fix itself.
function visualViewportInset() {
  const vv = window.visualViewport;
  if (!vv) return 0;
  return Math.max(0, window.innerHeight - (vv.height + vv.offsetTop));
}

// #sticky-cta (Manecillas/Samuel sample pages) is also left:0;right:0;
// bottom:0 -- a corner position alone doesn't clear a full-width sibling,
// only a real vertical offset does. Measured, not hardcoded, because its
// height varies by viewport and it slides in/out (transform, not
// display:none) after the reader scrolls a threshold.
function avoidBottomBarOverlap(bar) {
  const conflict = document.getElementById("sticky-cta");
  const reposition = () => {
    let basePx = 12; // matches the original bottom:.75rem default (16px root font-size)
    if (conflict) {
      const rect = conflict.getBoundingClientRect();
      const overlapping = rect.height > 0 && rect.top < window.innerHeight && rect.bottom > 0;
      if (overlapping) basePx = Math.max(12, window.innerHeight - rect.top + 12);
    }
    bar.style.bottom = `${basePx + visualViewportInset()}px`;
  };
  reposition();
  window.addEventListener("resize", reposition);
  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", reposition);
    window.visualViewport.addEventListener("scroll", reposition);
  }
  if (!conflict) return;
  // #sticky-cta slides in/out via a CSS transform transition (220ms), not an
  // instant class toggle -- reading its rect the instant the class changes
  // (MutationObserver fires synchronously with the mutation, before the
  // transition has run) captures its pre-animation position, not where it
  // ends up. Re-measure once the transition actually finishes, plus a
  // fallback timer in case a future change drops the transition entirely.
  conflict.addEventListener("transitionend", reposition);
  new MutationObserver(() => {
    reposition();
    setTimeout(reposition, 260);
  }).observe(conflict, { attributes: true, attributeFilter: ["class", "style"] });
}
