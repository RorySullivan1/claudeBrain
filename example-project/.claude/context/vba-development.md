# VBA Development — Orientation Brief

This is a thin pointer. The authoritative how-to for VBA work lives in the **VBA
skill family** under `.claude/skills/`; those skills are triggered automatically
and teach the behavior. This brief exists only to orient and to hold the small
amount of reference-tier material the skills assume rather than restate.

## Where the how-to lives — map your concern to a skill

| Concern | Skill |
| --- | --- |
| Writing / scaffolding / architecting macros, add-ins, UDFs, classes, HTTP+JSON | `vba-development` |
| Reviewing, auditing, or critiquing pasted VBA | `vba-review` |
| Debugging runtime errors, fixing post-update breakage, refactoring legacy, perf fixes, 32↔64-bit, Git source export | `vba-maintenance` |
| Packaging (`.xlsm`/`.xlam`/`.bas`), code-signing, Trusted Locations, Mark-of-the-Web, fleet deployment, install READMEs | `vba-distribution` |
| Building UserForms / dialogs and wiring controls and validation | `vba-userforms` |
| Writing/running tests (Rubberduck, fallback harness, making code testable) | `vba-code-test-writing` |

Don't duplicate worked examples, recipes, or checklists here — read them from the
owning skill.

## House defaults (project-specific decisions the skills inherit)

- **`Option Explicit` is non-negotiable** in every module. Never ship a module without it.
- **Default to late binding** for cross-version objects (`Scripting.Dictionary`,
  `MSXML2.ServerXMLHTTP.6.0`, FileSystemObject) so users need not set references manually;
  use early binding only for host-universal references, dev-only IntelliSense, or measured
  hot loops. (Rationale and consistency rules: `vba-development`.)
- **Library/add-in public procedures are name-prefixed** (e.g. `Acme_GetTimeSeries`) to
  substitute for VBA's missing namespaces and avoid cross-workbook collisions.
- **Round-trip text source is preferred over committing the binary `.xlam`** — rebuild the
  artifact from exported `.bas`/`.cls`/`.frm` (+ binary `.frx`, which is committed).
- **Verify on a clean machine** before declaring a deployment done — reference, trust-centre,
  and signing issues surface only off the dev box.
- **VBA when VBA is asked for** — do not pitch Power Query, Office Scripts, or Python as a
  substitute unless the user raises it.

## Reference: naming conventions

VBA has no namespaces, so naming carries the load. Use these prefixes consistently:

| Kind | Prefix | Example |
| --- | --- | --- |
| Standard module | `mod` | `modHttpClient`, `modConfig` |
| Class module | `cls` | `clsApiClient`, `clsCache` |
| UserForm | `frm` | `frmSettings` |
| Public library function | `Lib_Fn` | `MyLib_ParseDate` |
| Private helper | none | `parseDateInternal` |
| Module-level constant | `c_` or `ALL_CAPS` | `c_DefaultTimeout`, `MAX_RETRIES` |
| Module-level variable | `m_` | `m_isInitialised` |
