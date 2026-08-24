# PR #95 — Acceptance states

This note exists so the final local pass cannot be reduced to a static visual approximation.

## A — Top of Home

- Utility controls remain fixed.
- Left cluster: assistant, home, menu control according to the expanded-state visibility rule.
- Right: Comprar.
- Supplied David Porto central logo is rendered as an image, not reconstructed text.
- Editorial nav sits immediately below with tight spacing.

## B — Early scroll

- Central logo + editorial nav remain sticky for the first scroll interval.
- No layout jump or content collision.

## C — Deep scroll

- Expanded masthead collapses/disappears.
- Compact utility header remains fixed.
- Hamburger is visible on the left.
- Comprar remains on the right.

## Interaction acceptance

- Explore opens from the left.
- Home icon always links to `/` on interior V1 pages.
- Territory submenus are traversable by pointer without closing in the gap.
- Keyboard: Tab, Shift+Tab, Escape and `aria-expanded` are correct.
- Touch has an explicit disclosure control.

The final comparison must be done side by side against https://www.lrb.co.uk/ at desktop, tablet and mobile sizes.