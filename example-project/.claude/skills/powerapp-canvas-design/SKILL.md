---
name: powerapp-canvas-design
description: >
  Screen layout, geometry and interaction design for canvas apps — where controls go, how big
  they are, what overlaps what, and which layouts survive a paste. Use this skill for any
  visual or spatial question: "lay out this form", "the dropdown covers the fields below",
  "controls are overlapping", "make this screen scroll", "make the form more compact", "build
  a modal", "why is my Y value hardcoded after pasting", "nothing on this screen is
  clickable", "design the header / nav". Covers: vertical band planning and the collision
  arithmetic that must be done at author time, auto-layout containers vs absolute positioning,
  overlay and modal patterns, scrolling, the paste-time freezing of X/Y/Width/Height, hit
  testing and z-order, and Theme-driven spacing and type. Boundaries: which control to place
  is powerapp-canvas-controls; the formulas in its properties are powerapp-canvas-development;
  reusable component contracts are power-apps-components; SVG visuals are power-apps-svg.
  This skill owns *where things sit and whether the user can actually touch them*.
---

# Canvas Design — geometry you cannot see, so you must compute

In a source-controlled canvas project you author blind: the render happens in Studio — often on
someone else's machine — and comes back to you as a sentence. So **layout is arithmetic done at
author time**, not something to eyeball later. Every layout bug that ships this way is a number
that was never worked out.

---

## 1. Plan the screen in bands, and write them down

Put the resolved numbers in the screen's header comment so Studio's values can be checked by
eye without evaluating `Theme.Space.*` by hand:

```
#      0 ..  64   appBar            (absolute, declared LAST)
#     64 .. 636   frmScroll         (scrolls)
#    636 .. 768   actionBar         (OPAQUE — the scroll cannot bleed under it)
```

A tablet app at the 16:9 default is 1366×768. When a report from Studio disagrees with the
table, one of you is looking at a stale copy — and that is a much faster conversation than
"it looks wrong".

## 2. Do the collision arithmetic

Two rectangles overlap when `a.x < b.right && b.x < a.right && a.y < b.bottom && b.y < a.bottom`.
Run it over every pair on the screen before hand-off. Real failures this has caught:

- Picker fields **66px apart** with **132px** result galleries: each open dropdown covered the
  next two search boxes, and two open at once left the lower half of the first unclickable.
- A modal's people-picker results running past the card's Add/Cancel row.

Overlap is not always a bug — a dropdown *should* cover what's beneath it — but it must be
**deliberate and one-directional**.

## 3. Z-order is positional, and it decides hit testing

First child = bottom, last = top. There is no `ZIndex`.

- Anything that floats (dropdown results, modal, app bar) is declared **LAST**.
- **A component instance intercepts every click inside its bounds.** A transparent `Fill` does
  not help. A full-screen instance with no `Visible` makes the entire screen dead — a real bug
  that ships more than once. Gate the *instance*, not just what it draws inside.
- A dynamic height is the other legitimate gate:
  `Height: =If(gNavOpen, Parent.Height, Theme.Space.HeaderH)` — full-screen only while open,
  when swallowing the click is the point.

## 4. Layout formulas FREEZE on paste — this changes everything

> *"After you write formulas for the X, Y, Width and Height properties of a control, your
> formulas will be overwritten with constant values if you subsequently drag the control in
> the canvas editor."* — MS Learn, *Create responsive layouts*

A paste positions controls, so **every layout formula lands as whatever it evaluated to at that
instant.** Consequences:

- **Never position a control off another control** (`Y: =Other.Y + Other.Height + Gap`). It
  will be evaluated mid-paste, when the referenced control may not be where it ends up, and
  frozen wrong. A gallery landed at `Y=193` on top of its own filter row this way.
- The landed app **is not responsive**. `Parent.Width - 48` becomes `1318`. Acceptable for a
  fixed-size tablet app; know that it is true.
- A wrong position is fixed **in the formula bar**, not by re-pasting — re-pasting re-freezes.
- Prefer **plain integers** for X/Y/Width/Height wherever the value is static anyway, so what
  lands equals what was authored.

## 5. Auto-layout containers are the one layout that survives

`GroupContainer@1.5.0` / `Variant: AutoLayout` children carry **no X/Y** — the container places
them. Since X/Y are exactly what freezes, container-laid-out content is **immune** to §4.

```yaml
- frmScroll:
    Control: GroupContainer@1.5.0
    Variant: AutoLayout
    Properties:
      LayoutDirection: =LayoutDirection.Vertical
      LayoutGap: =8
      LayoutOverflowY: =LayoutOverflow.Scroll
      Height: =Parent.Height - 64 - 132        # stop above the action bar
```

**A hidden child takes no space.** That single fact replaces the whole absolute-overlay
pattern: put a picker's results gallery *inline* after its search box and it expands the column
when it opens, collapses when it closes. No z-order, no covering, no one-open-at-a-time gate.

Put an **opaque** bar behind a fixed footer anyway. If a stale `Height` ever freezes in, an
opaque rectangle still stops content showing through the Save row.

## 6. Compactness comes from control choice, not from squeezing

A 40px selection strip becomes a 32px combobox. A typed date plus its "⚠ not a date" echo
label becomes one date picker. Reach for powerapp-canvas-controls before shrinking gaps — the
form loses a third of its height and gets *more* readable, not less.

## 7. Overlay patterns

**Inline expansion** (inside a container) — preferred. Results sit after the input.

**Beside, not below** (absolute layout) — `X = input.X + input.Width + 8`, same `Y`. Covers
the chip and empty space instead of the fields underneath.

**Modal** — scrim (full-screen, `OnSelect` closes) → card → fields → action buttons declared
last, everything gated on one `gXOpen` flag. Check the card's content bottom against the button
row before shipping.

## 8. Theme

All colour, size and spacing goes through the `Theme` named formula
(`Theme.Color.*`, `Theme.Size.*`, `Theme.Space.*`) so restyling is one edit. Two caveats:

- A **component cannot read app-scope named formulas** — colours inside a component are
  literals that mirror Theme, and must be kept in step by hand.
- Because layout formulas freeze (§4), `Theme.Space.*` only ever applies **at paste time**.
  Colours and sizes stay live; positions do not.
