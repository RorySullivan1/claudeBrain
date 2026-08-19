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
  overlay and modal patterns, scrolling, why direct manipulation (not pasting) replaces an
  X/Y/Width/Height formula with a constant, hit
  testing and z-order, and Theme-driven spacing and type. Boundaries: which control to place
  is powerapp-canvas-controls; the formulas in its properties are powerapp-canvas-development;
  reusable component contracts are power-apps-components; SVG visuals are power-apps-svg.
  This skill owns *where things sit and whether the user can actually touch them*.
---

# Canvas Design — geometry you cannot see, so you must compute

> **Docs source (meaning, not tokens):** the authoritative layout/control reference is
> `github.com/MicrosoftDocs/powerapps-docs` (esp. `create-responsive-layout.md`,
> `build-responsive-apps.md`, `working-with-large-apps.md`). See
> `.claude/context/powerapps-docs-source.md` for paths + fetch methods. It grounds layout
> BEHAVIOUR; the exact pa-yaml token still comes from a Studio code-view (`tools/studio-enums.json`).

You author blind. The render is on someone else's machine and comes back as a sentence. So
**layout is arithmetic done at author time**, not something to eyeball later. Every layout bug
this project has shipped was a number that was never worked out.

---

## 1. Plan the screen in bands, and write them down

Put the resolved numbers in the screen's header comment so Studio's values can be checked by
eye without evaluating `Theme.Space.*` by hand:

```
#      0 ..  64   appBar            (absolute, declared LAST)
#     64 .. 636   frmScroll         (scrolls)
#    636 .. 768   actionBar         (OPAQUE — the scroll cannot bleed under it)
```

Tablet is 1366×768. When a report disagrees with the table, one of you is looking at a stale
copy — and that is a much faster conversation than "it looks wrong".

## 2. Do the collision arithmetic

Two rectangles overlap when `a.x < b.right && b.x < a.right && a.y < b.bottom && b.y < a.bottom`.
Run it over every pair on the screen before hand-off. Real failures this caught:

- Picker fields **66px apart** with **132px** result galleries: each open dropdown covered the
  next two search boxes, and two open at once left the lower half of the first unclickable.
- A modal's people-picker results running past the card's Add/Cancel row.

Overlap is not always a bug — a dropdown *should* cover what's beneath it — but it must be
**deliberate and one-directional**.

## 3. Z-order is positional, and it decides hit testing

First child = bottom, last = top. There is no `ZIndex`.

- Anything that floats (dropdown results, modal, app bar) is declared **LAST**.
- **A component cannot be placed inside a Gallery or a Form at all** (MS Learn, canvas component
  known limitations #4). Per-row visuals are plain controls inlined in the template — an `Image`
  with an SVG data URI, a `Label`, a `Rectangle`. The validator fails the build on it.
- **A component instance intercepts every click inside its bounds.** A transparent `Fill` does
  not help. A full-screen instance with no `Visible` makes the entire screen dead — that is a
  real bug this app shipped. Gate the *instance*, not just what it draws inside.
- **A transparent full-template button makes every control declared BEFORE it unclickable.**
  Galleries here end each row template with one, because a gallery's own `OnSelect` does not
  fire reliably when the click lands on a child. It covers the whole row, so a per-row icon —
  delete, flag, anything — must be declared **after** it, or shrunk out from under it. The icon
  still RENDERS either way, so getting this wrong looks like a dead control rather than a
  layering bug, and you can stare at the geometry for a long time before suspecting z-order.
  `tools/validate_pa_yaml.py` emits a NOTE for this shape, but only catches the blatant case —
  it cannot tell whether a *reduced* overlay is reduced enough, and an auto-layout child has no
  `X` in the source for it to reason about. Treat the NOTE as a prompt, not a proof.
- A dynamic height is the other legitimate gate:
  `Height: =If(gNavOpen, Parent.Height, Theme.Space.HeaderH)` — full-screen only while open,
  when swallowing the click is the point.

## 4. DIRECT MANIPULATION writes back a constant. Pasting does not.

> *"After you write formulas for the X, Y, Width and Height properties of a control, your
> formulas will be overwritten with constant values if you subsequently drag the control in
> the canvas editor."* — MS Learn, *Create responsive layouts*

Read that quote for what it says: **dragging**. This section used to be titled "Layout formulas
FREEZE on paste" and treated the two as the same event. They are not, and the difference was
settled by experiment — `tests/scrProbe-layout-freeze.pa.yaml`, run in Studio 2026-08-13.
Formulas came through a code-view paste **live**: `Parent` arithmetic, references to a control
declared earlier, references to one declared later, and a container's own `Width` all kept
recomputing afterwards. Changing an input moved the controls, which a constant cannot do.

Dragging is not the special case — it is one instance of **direct manipulation**, and so are the
resize handles and the position/size boxes in the properties pane. All of them write back a
number, because a number is what the gesture produces. The formula bar is the one place that
keeps what you type.

So:

- **Positioning a control off another control is allowed.** `Y: =Other.Y + Other.Height + Gap`
  survives and stays live.
- **The landed app IS responsive**, to the extent it is authored to be. `Parent.Width - 48`
  stays `Parent.Width - 48`.
- **Once a property is a formula, set it only through the formula bar.** This is the real hazard,
  and it is invisible: a nudge or a spinner silently replaces the formula with the number it
  happened to be at.
- A wrong position is still fixed **in the formula bar**.

**BUT THE PROBE ONLY TESTED ONE PASTE SCOPE, AND THE OTHER BEHAVES DIFFERENTLY.**
`scrProbe-layout-freeze` pasted CONTROLS onto a blank screen. Pasting a WHOLE SCREEN is not the
same event: on 2026-08-18 a control's `X` was **lost** in a screen-scope paste while `Y`, `Width`,
`Height` and every other property came through — and it was lost both as `Parent.TemplateWidth - 32`
and as a sibling `rowTaskBody.Width + 10`. Pasting that same control on its own kept `X`. The
mechanism is unexplained; what is established is that **"formulas survive a paste" is a
control-scope result and must not be assumed at screen scope.**

So for anything that will be re-pasted as a whole screen: **prefer owning no `X` at all.** Make the
control an auto-layout child and let the container place it (§5). A child with no `X` has nothing
to lose, which is why `icoDeleteProject` survived every paste that dropped its absolutely-positioned
siblings. Absolute `X` is still fine on a screen you only ever paste control-by-control.

**The one paste hazard that IS real, and is a different mechanism:** if a control lands with a
suffixed name (`txtProjSearch_1`), every reference to `txtProjSearch` in that same paste
resolves to the old control or to nothing. Deleting a screen before pasting it back avoids this
entirely, which is this project's working practice.

## 5. Auto-layout containers, and what they are actually for

`GroupContainer@1.5.0` / `Variant: AutoLayout` children carry **no X/Y** — the container places
them. That is worth reaching for because it expresses intent (a row, a stack, a gap) instead of
arithmetic, and because inserting a child re-flows its siblings for free.

It is **not** a way to escape freezing — nothing needs escaping (§4). The container's own
`Width`/`Height` are ordinary layout formulas and stay live like any other.

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

### The other variant: `GridLayout` — usable, but not yet authorable

`GroupContainer@1.5.0` also takes **`Variant: GridLayout`**, confirmed from Studio code view
2026-08-10. Its children place themselves with four numeric properties instead of X/Y:
`LayoutGridColumnStart` / `LayoutGridColumnEnd` / `LayoutGridRowStart` / `LayoutGridRowEnd`.
Studio writes `X`/`Y` on those children anyway, exactly as it does for auto-layout children
whose X/Y are ignored — the container places them regardless of what those properties say.

**What is NOT known is how the grid's own shape is declared** — no column count, row count or
track sizes appear anywhere in the sample. So a grid is placeable but not creatable from here:
fill one Studio has already made, and don't author the container blind. Token detail and the
verbatim sample live in powerapp-canvas-controls.

**A child's explicit Width/Height is ADVISORY until you turn flexible sizing off.** Every child
of an auto-layout container starts with *Flexible width* (or height, along the parent's
`Direction`) **on**, and the container then divides space by `FillPortions` — so setting a fixed
width appears to do nothing. Pin it with `FillPortions: =0`, and add `LayoutMinWidth` as a floor:

```yaml
FillPortions:   =0        # claim none of the spare space
LayoutMinWidth: =220      # and never shrink below this
Width:          =220
```

**A hidden child takes no space.** That single fact replaces the whole absolute-overlay
pattern: put a picker's results gallery *inline* after its search box and it expands the column
when it opens, collapses when it closes. No z-order, no covering, no one-open-at-a-time gate.

Put an **opaque** bar behind a fixed footer anyway. If a `Height` is ever wrong, an opaque
rectangle still stops content showing through the Save row.

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
  sizes do (§4). What breaks the link is dragging that control, not pasting it.

## Scale-to-fit vs Lock-aspect-ratio: Studio and the player DIVERGE (2026-08-12)

> **This section is about geometry only.** It was first written as the answer to a
> squished-and-black report and that was WRONG — see the next section for the real cause and the
> one-question test that separates them. Keep this for what it is: a real divergence worth
> configuring correctly, which explains distortion and nothing else.

MS Learn documents the two surfaces diverging under exactly one
configuration — *Change screen size and orientation of canvas apps*:

| Scale to fit | Lock aspect ratio | Behaviour |
|---|---|---|
| On | On | Screen size is the maker's; **the screen scales to the window**. Dark bars where the window's ratio differs. |
| On | **Off** | **In Studio the screen scales to the window. In the END-USER experience Power Apps scales to the smallest edge, then FILLS the larger edge.** ← the divergence |
| Off | Off | Genuinely responsive. You must write the layout for it. |

The preview docs say the same in fewer words: *"If Scale To Fit is on and Lock Aspect Ratio is
off, your preview won't be accurate. This configuration isn't recommended."*

**So: Studio scales; the player stretches.** A fixed-canvas app then looks correct to its author
and distorted to everyone else — the worst possible split, because authoring never reveals it.

### Which setting a given app wants

Decide from the SOURCE, not from taste. Count the absolute placements:

    grep -rcE '^\s+(X|Y): =Theme\.Space' src/Screens/*.pa.yaml

- **Absolute bands, hardcoded design width, `X`/`Y` arithmetic** → the app is a fixed canvas.
  It wants **Scale to fit ON + Lock aspect ratio ON**. It will letterbox on odd window shapes,
  and that is correct behaviour, not a bug — the alternative is distortion.
- **Auto-layout containers all the way down, no absolute X/Y, no design-size constants** → it can
  take **both OFF** and be truly responsive.

Turning both off on a fixed-canvas app does not make it responsive. It removes the scaling that
was hiding the absolute positioning, and the layout falls apart at every size but one.

## "Squished and black" is `Theme` RESOLVING BLANK — and here is the one-control test

Root-caused 2026-08-12 after a wrong turn through the display settings above. When `Theme` is not
available, **one cause produces every symptom at once**, because a blank coerces to 0 and to black:

| Symptom | Mechanism |
|---|---|
| Screens are black | `Fill: =Theme.Color.Bg` → blank → black |
| Everything is squished into the corner | every `X`/`Y`/`Height` off `Theme.Space.*` → 0 |
| **The app bar is simply GONE** | its `Height` is `Theme.Space.HeaderH` → 0 |

**THE TEST IS THE APP BAR.** Its height is Theme-derived, so it is a pure probe: no display
setting, aspect ratio or window size can make a control vanish. Distortion stretches things; it
never deletes them. So:

- **App bar missing** → `Theme` is blank. It is `App.Formulas`, full stop.
- **App bar present but the layout is distorted** → geometry. Now read the table above.

Ask for that one observation before theorising. "Squished and black" is ambiguous; "the app bar
isn't there" is not.

### Why it can be blank in the PUBLISHED app while Studio is perfect

Studio always runs the latest **saved** version; the player runs the last **published** one. If
the published version predates the `App.Formulas` paste — or captured a moment when it was
mid-edit — `Theme` genuinely does not exist for end users while the author sees nothing wrong.
**Republish first; it costs a minute and tests the whole hypothesis.** If a republish does not fix
it, `App.Formulas` did not actually commit: check App checker, and paste the comment-free body
from `tools/formula_bar_body.py --bare`.

### The architectural tell that makes this readable

In this repo **screens paint with `Theme`; components paint with LITERALS** — `AccessAppScope:
false` forced every component onto hardcoded RGBA. So with `Theme` blank, any component internals
that do render still show their real colours against a black screen. Component-coloured content on
black is not two bugs; it is one, seen through both halves of that split.
