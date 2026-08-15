---
name: powerapp-canvas-design
description: >
  Screen layout, geometry and interaction design for canvas apps — where controls go, how big
  they are, what overlaps what, and which layouts survive a paste. Use this skill for any
  visual or spatial question: "lay out this form", "the dropdown covers the fields below",
  "controls are overlapping", "make this screen scroll", "make the form more compact", "build
  a modal", "why is my Y value hardcoded / my formula replaced by a number", "nothing on this
  screen is clickable", "design the header / nav", "the app looks stretched for users". Boundaries: which control to place
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
- **A component cannot be placed inside a Gallery or a Form at all** (MS Learn, canvas component
  known limitations). Per-row visuals are plain controls inlined in the template — an `Image`
  with an SVG data URI, a `Label`, a `Rectangle`. Check this before designing any per-row
  visual as a component; Studio refuses the control, so the paste fails with nothing to point at.
- **A component instance intercepts every click inside its bounds.** A transparent `Fill` does
  not help. A full-screen instance with no `Visible` makes the entire screen dead — a real bug
  that ships more than once. Gate the *instance*, not just what it draws inside.
- A dynamic height is the other legitimate gate:
  `Height: =If(gNavOpen, Parent.Height, Theme.Space.HeaderH)` — full-screen only while open,
  when swallowing the click is the point.

## 4. DIRECT MANIPULATION writes back a constant. Pasting does not.

> *"After you write formulas for the X, Y, Width and Height properties of a control, your
> formulas will be overwritten with constant values if you subsequently drag the control in
> the canvas editor."* — MS Learn, *Create responsive layouts*

Read that quote for what it says: **dragging**. This section used to be titled "Layout formulas
FREEZE on paste" and treated the two as the same event. They are not, and the difference was
settled by experiment (a probe screen — e.g. `tests/scrProbe-layout-freeze.pa.yaml` — run in
Studio, 2026-08-13). Formulas came through a code-view paste **live**: `Parent` arithmetic,
references to a control declared earlier, references to one declared later, and a container's
own `Width` all kept recomputing afterwards. Changing an input moved the controls, which a
constant cannot do.

Dragging is not the special case — it is one instance of **direct manipulation**, and so are the
resize handles and the position/size boxes in the properties pane. All of them write back a
number, because a number is what the gesture produces. The formula bar is the one place that
keeps what you type.

So:

- **Positioning a control off another control is allowed.** `Y: =Other.Y + Other.Height + Gap`
  survives and stays live.
- **The landed app IS responsive**, to the extent it is authored to be. `Parent.Width - 48`
  stays `Parent.Width - 48`.
- **Once a property is a formula, set it only through the formula bar.** This is the real
  hazard, and it is invisible: a nudge or a spinner silently replaces the formula with the
  number it happened to be at.
- A wrong position is still fixed **in the formula bar**. Re-pasting is fine too — it does not
  re-freeze anything.

**The one paste hazard that IS real, and is a different mechanism:** if a control lands with a
suffixed name (`txtSearch_1`), every reference to `txtSearch` in that same paste resolves to
the old control or to nothing. Deleting a screen before pasting it back avoids this entirely.

## 5. Auto-layout containers, and what they are actually for

`GroupContainer@1.5.0` / `Variant: AutoLayout` children carry **no X/Y** — the container places
them. That is worth reaching for because it expresses intent (a row, a stack, a gap) instead of
arithmetic, and because inserting a child re-flows its siblings for free. It is **not** a way to
escape freezing — nothing needs escaping (§4). The container's own `Width`/`Height` are ordinary
layout formulas and stay live like any other.

A second structural win: **mixing proportional and edge-pinned anchoring is the collision bug.**
Two absolutely-placed siblings — one at `X = Parent.Width * 0.54`, the other pinned to the right
edge with a fixed width — are individually reasonable and converge as the container narrows;
collision arithmetic run at ONE width proves nothing, because the question is always "at which
width does this first collide". Making the row an auto-layout container ends the class: children
carry no X, so overlap is structurally impossible. Give each column `FillPortions` +
`LayoutMinWidth` (a child of an auto-layout container is flexible by default, so a declared
`Width` alone is advisory — see below).

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

Put an **opaque** bar behind a fixed footer anyway. If a `Height` is ever wrong, an opaque
rectangle still stops content showing through the Save row.

### The other variant: `GridLayout` — usable, but not yet fully authorable

`GroupContainer@1.5.0` also takes **`Variant: GridLayout`** (confirmed from Studio code view,
2026-08-10). Its children place themselves with four numeric properties instead of X/Y:
`LayoutGridColumnStart` / `LayoutGridColumnEnd` / `LayoutGridRowStart` / `LayoutGridRowEnd`.
Studio writes `X`/`Y` on those children anyway — the container places them regardless of what
those properties say. **What is NOT known is how the grid's own shape is declared** — no column
count, row count or track sizes appeared in the grounding sample. So a grid is placeable but not
creatable blind: fill one Studio has already made; don't author the container itself. Token
detail belongs to `powerapp-canvas-controls`.

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
- `Theme.Space.*` in a layout formula stays **live** — positions recompute like colours and
  sizes do (§4). What breaks the link is direct manipulation of that control, not pasting it.

## Scale-to-fit vs Lock-aspect-ratio: Studio and the player DIVERGE

This section is about geometry only — it explains distortion and nothing else (a
squished-AND-black app is the Theme diagnosis below, not this). MS Learn documents the two
surfaces diverging under exactly one configuration — *Change screen size and orientation*:

| Scale to fit | Lock aspect ratio | Behaviour |
|---|---|---|
| On | On | Screen size is the maker's; **the screen scales to the window**. Dark bars where the window's ratio differs. |
| On | **Off** | **In Studio the screen scales to the window. In the END-USER experience Power Apps scales to the smallest edge, then FILLS the larger edge.** ← the divergence |
| Off | Off | Genuinely responsive. You must write the layout for it. |

**Studio scales; the player stretches.** A fixed-canvas app then looks correct to its author and
distorted to everyone else — the worst possible split, because authoring never reveals it.

Decide the setting from the SOURCE, not from taste — count the absolute placements:

- **Absolute bands, hardcoded design width, X/Y arithmetic** → the app is a fixed canvas. It
  wants **Scale to fit ON + Lock aspect ratio ON**. Letterboxing on odd window shapes is correct
  behaviour, not a bug — the alternative is distortion.
- **Auto-layout containers all the way down, no absolute X/Y, no design-size constants** → it
  can take **both OFF** and be truly responsive.

Turning both off on a fixed-canvas app does not make it responsive — it removes the scaling that
was hiding the absolute positioning, and the layout falls apart at every size but one.

## "Squished and black" is the theme RESOLVING BLANK — and the one-control test

When the app's theme named formula is not available, **one cause produces every symptom at
once**, because a blank coerces to 0 and to black: screens are black (`Fill: =Theme.Color.Bg` →
blank → black), everything is squished into the corner (every X/Y/Height off `Theme.Space.*` →
0), and any bar whose `Height` is theme-derived is simply **gone**.

**THE TEST IS THAT THEME-SIZED BAR** (a header or app bar). Its height is a pure probe: no
display setting, aspect ratio or window size can make a control *vanish* — distortion stretches
things, it never deletes them. So: bar missing → the theme is blank; it is `App.OnStart` /
`App.Formulas`, full stop. Bar present but distorted → geometry; read the scale-to-fit table
above. Ask for that one observation before theorising — "squished and black" is ambiguous; "the
app bar isn't there" is not.

Why it can be blank in the PUBLISHED app while Studio is perfect: Studio runs the latest
**saved** version; the player runs the last **published** one. If the published version predates
the theme paste — or captured it mid-edit — the theme genuinely does not exist for end users
while the author sees nothing wrong. **Republish first; it costs a minute and tests the whole
hypothesis.** The transfer-side failure modes of the App-object paste itself (the `=` and `//`
traps) are `studio-transfer`'s.
