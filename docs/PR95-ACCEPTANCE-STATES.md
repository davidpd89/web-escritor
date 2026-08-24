# PR #95 — Acceptance states

This note exists so the final local pass cannot be reduced to a static visual approximation.

## A — Top of Home

- Utility controls remain fixed.
- Left cluster: assistant, home, menu control according to the expanded-state visibility rule.
- Right: Comprar.
- Supplied David Porto central logo is rendered as an image, not reconstructed text.
- Editorial nav sits immediately below with tight spacing.
- The top utility bar reads as a clean near-white sheet, not the same flat surface as the content below.
- A restrained shadow/rule separates the utility bar from the warmer masthead paper.
- Masthead uses a warm paper tone; navigation below it is one shade deeper so the three layers read separately without looking like cards.

## B — Early scroll

- Central logo + editorial nav remain sticky for the first scroll interval.
- No layout jump or content collision.
- The layered white → warm paper → deeper navigation hierarchy is preserved while sticky.

## C — Deep scroll

- Expanded masthead collapses/disappears.
- Compact utility header remains fixed.
- Hamburger is visible on the left.
- Comprar remains on the right.
- Compact state must still retain the subtle depth/rule of the utility header instead of collapsing to featureless white.

## D — Newspaper / river grid materiality

- The river section is a full-width tonal field; it must not look like a narrow white island centered on an otherwise white page.
- Reading content remains capped to the editorial max width inside that full-width field.
- Desktop uses three disciplined columns; tablet uses two; mobile becomes one continuous editorial column.
- Column spacing is deliberate and consistent. Dividing rules sit on cell edges and never float through text or misalign between rows.
- Internal padding is large enough that copy does not sit against separators.
- Most cells use warm paper variants rather than pure white.
- At least one middle cell changes tone subtly to break the six-identical-box effect.
- `Del cuaderno` is the deliberate blue interruption: blue surface, darker petrol title, softer blue-grey metadata/body copy.
- Title, byline and summary have three distinct tonal/size levels. The byline must read lighter and lower than the title, not as the same text block.
- Image cells bleed to their own column edge and align to the same grid geometry as text cells.
- Shadows are restrained and layer-level, not card shadows on every article.

## Responsive material acceptance

### Desktop — 1440 × 900
- Three-column newspaper geometry is balanced.
- Full-width field is visible at both sides of the capped content.
- Gutters and rules are visually even.
- Blue block has enough contrast to feel intentional but remains part of the same editorial system.

### Tablet — 1024 × 768 / 768 × 1024
- Grid recomposes to two columns without inheriting incorrect desktop right borders.
- Lead and Feria rows span both columns cleanly.
- Middle pairs have one separator between them, not doubled/missing lines.

### Mobile — 390 × 844
- One-column stack keeps the warm field around the content.
- No tiny card gaps, horizontal overflow or clipped shadows.
- Hairlines become horizontal separators only.
- Type sizes remain editorial, not oversized desktop leftovers.

## Interaction acceptance

- Explore opens from the left.
- Home icon always links to `/` on interior V1 pages.
- Territory submenus are traversable by pointer without closing in the gap.
- Keyboard: Tab, Shift+Tab, Escape and `aria-expanded` are correct.
- Touch has an explicit disclosure control.

The final comparison must be done side by side against https://www.lrb.co.uk/ at desktop, tablet and mobile sizes. Compare not only structure but also perceived depth: surface changes, rules, gutters, title/byline hierarchy and the blue editorial interruption.
