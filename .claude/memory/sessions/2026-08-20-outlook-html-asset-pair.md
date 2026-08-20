# 2026-08-20 — Outlook HTML asset pair (skill + agent)

**Request:** create Claude assets for HTML design specifically for Outlook — an
`outlook-html-designer` agent and an `outlook-html-specifications` skill. User named the
pair; both built into `example-project/.claude/` as consumer assets.

## What was built

**`outlook-html-specifications` (skill)** — the *rendering contract*: everything follows
from the one documented fact that classic Outlook for Windows renders with Word's engine
(KB 2739063). Sections: the classic-vs-new/web/Mac engine split (targeting decision first);
the Word-engine support matrix; the MSO dialect (conditional comments, ghost tables, `mso-`
properties); the spacing model (td padding, `mso-line-height-rule: exactly`, forwarding-gap
rows, the ~1790px table split); VML backgrounds/buttons and their documented
incompatibilities; images/DPI/fonts (the PixelsPerInch block, the Times New Roman
fallback-skip trap); dark mode; a failure-modes triage list ("body renders solid black →
parse error, not design").

**`outlook-html-designer` (agent)** — the executor, modeled on the `vba-developer`
template (Read/Grep/Glob/Edit/Write/Bash, acceptEdits, sonnet). Orient → build per the
contract → **verify mechanically**: it parse-validates the HTML with a real parser, which
is a load-bearing gate because malformed HTML renders as a solid black body in classic
Outlook. Honesty posture mirrors vba-developer: no Outlook here, so it never claims a
visual pass — it ships the parser result, the failure-mode audit, and a manual test
procedure (clients × light/dark × 100%/150% scaling). Complies with the verifying-agent
rule (no `permissionMode: plan`).

## Layering / boundaries

- `outlook-html-specifications` owns *what Outlook's renderer does to your HTML*.
- The global `email-newsletter` skill owns the broader design system, cross-client
  (Gmail/Apple Mail) tables, and delivery automation — referenced "where available" since
  it's a synced global skill, not in example-project.
- `branding` owns identity; vba-development family owns driving Outlook itself.
- The agent composes all of the above; defers facts to the skill so they live once.

## Truth gate (run at authoring, per the standing pattern)

Grounded before writing: KB 2739063 (Word engine), Microsoft's live Dynamics
rendering-troubleshooting page (8 classic-Outlook behaviors incl. the verbatim td-padding
fix, transparent-bg-treated-as-image, VML button×background incompatibility, the
forwarding-gap workaround markup, black-body-on-malformed-HTML), and the Dynamics
dark-mode page (#1A1A1A/#F5F5F5, colors inverted but images preserved).

**Five claims labelled field-settled in place** rather than laundered: the
`o:PixelsPerInch` DPI fix, the font fallback-skip to Times New Roman, the ~1790px table
split, GIF-first-frame-only, base64 images not displaying. None appears in the cited MS
pages; all are email-dev field canon.

Ledger 78 → **83 rows** (3 confirmed-doc-settled batches, 1 experience-settled batch,
1 agent-posture compliance row).

**Standing gap unchanged:** no live Outlook/Windows host, so no claim was confirmed by
actually rendering — same class as the VBA step-4 gap already recorded.
