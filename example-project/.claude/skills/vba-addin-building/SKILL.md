---
name: vba-addin-building
description: >
  Expert at building distributable Office VBA add-ins (.xlam / .ppam / .otm /
  Word .dotm) from plain-text .bas/.cls/.frm source by COM-driving Office to
  import modules, inject document-module and ribbon code, and re-seal the OpenXML
  container. Use this skill whenever the user wants to assemble, compile, or
  package a VBA add-in from version-controlled source files, set up or debug a
  text-source round-trip build (build/export scripts), wire static ribbon
  (customUI) XML into the container, handle UserForm (.frm/.frx) creation and the
  MSForms-version rebuild, share modules across multiple host add-ins, or fix a
  build that fails at VBComponents.Import, ThisWorkbook/ThisDocument injection,
  HRESULT 0x800AEA9D, or the .pptm→.ppam content-type step. Trigger on "build the
  add-in from source", "compile my .bas files into an .xlam", "set up a Git-
  friendly VBA build", "inject the ribbon XML", "round-trip export my modules",
  "rebuild the .frx", "why won't my .frm import". This skill owns the
  *source→binary assembly pipeline*. For deploying/signing the finished container
  use vba-distribution; for authoring the module/form code itself use
  vba-development and vba-userforms.
---

# VBA Add-in Building Skill

You build distributable Office add-ins from plain-text source. The deliverable is a
binary OpenXML container (`.xlam`, `.ppam`, Word `.dotm`, Outlook `.otm`) but the
**source of truth is flat `.bas`/`.cls`/`.frm` files in version control**. The build
is a COM-driven round-trip: drive a hidden Office instance, import the modules into a
fresh document's VBProject, inject the pieces that can't be imported, save in add-in
format, then surgically edit the resulting ZIP to wire in the ribbon.

Lead with the answer. State the host app and target format up front. Prefer the
smallest change to a working pipeline over a rewrite.

The reference implementation for everything below is this repo's `build/build.ps1`,
`build/export.ps1`, `build/export_forms.ps1`, and `build/forms.spec.json`. Read those
before changing the pipeline — this skill explains *why* they do what they do so you
don't regress a hard-won workaround.

---

## The core problem this pipeline solves

VBA normally lives *inside* the binary Office file. That is hostile to git: no diffs,
no review, merge conflicts are unresolvable. The fix is to keep code as flat text and
**reconstruct the container on every build**. That reconstruction has four hard
constraints that drive the whole design:

1. **Office owns the VBProject.** There is no offline compiler. You must automate a
   real (hidden) Excel/PowerPoint/Word instance over COM and ask *it* to import code.
   This requires **"Trust access to the VBA project object model"** enabled in that
   app's Trust Center (File → Options → Trust Center → Trust Center Settings → Macro
   Settings). Without it, `Document.VBProject` returns `Nothing` / access-denied.
2. **Source files carry no VBA headers, but `Import` needs them.** Committing the
   `Attribute VB_Name = "…"` / `VERSION 1.0 CLASS` preamble pollutes diffs and breaks
   when a file is renamed. So source is header-*less*; the build **injects headers
   into a temp copy** just before import, and export **strips them** on the way back.
3. **Some components cannot be imported — only their code can be injected.** Document
   modules (`ThisWorkbook`, `ThisDocument`, `ThisPresentation`, sheet/slide modules)
   already exist in any new document. `VBComponents.Import` would create a *duplicate*
   or fail. You must open the existing component and replace its `CodeModule` text.
4. **The ribbon is not VBA.** Static customUI XML lives as a *part* inside the OpenXML
   ZIP, not in the VBProject. Office's COM API won't write it. So after saving, you
   reopen the file as a ZIP and add the part + its content-type + relationship by hand.

Everything in the build script is one of those four constraints made concrete.

---

## Pipeline at a glance

```
src/common/*.bas|cls|frm  ─┐
src/<host>/*.bas|cls|frm  ─┼─►  [1] header-inject + ANSI re-encode → %TEMP%\Name.ext
                           │         │
                           │         ▼
                           │    [2] New hidden doc → VBProject.VBComponents.Import(temp)
                           │         │
ThisWorkbook/ThisDocument ─┘         ▼
                                [3] inject doc-module code into existing component
                                     │
                                     ▼
                                [4] SaveAs add-in format (xlAddIn=55 / pptm=25)
                                     │
customui/<host>_customUI14.xml ─►   ▼
                                [5] reopen as ZIP: write customUI14.xml,
                                    patch [Content_Types].xml + _rels/.rels
                                     │
                                     ▼  (PowerPoint only)
                                [6] rewrite presentation content-type → addin,
                                    rename .pptm → .ppam
                                     │
                                     ▼
                                dist/xlVizer.xlam  /  dist/xlVizer.ppam
```

`export.ps1` runs this **in reverse** for the round-trip; `export_forms.ps1` pulls
`.frm`/`.frx` back out (forms need a separate pass — see *UserForms* below).

---

## Step-by-step methodology

### [1] Header injection + ANSI re-encoding

For each source file, write a temp copy with the correct header prepended, encoded as
**Windows-1252 (ANSI)** — `VBComponents.Import` chokes on UTF-8 BOMs and mis-decodes
non-ASCII. The header depends on the module type:

| Source ext | Component kind | Header to prepend |
|---|---|---|
| `.bas` | Standard module | `Attribute VB_Name = "<BaseName>"` |
| `.cls` | Class module | full `VERSION 1.0 CLASS` block + 5 `Attribute VB_*` lines (Name, GlobalNameSpace, Creatable, PredeclaredId, Exposed) |
| `.frm` | UserForm | **none** — `.frm` files carry their own header already; just re-encode to ANSI and copy the companion `.frx` alongside |

The class header is exact and order-sensitive:

```
VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "<BaseName>"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
```

> To ship a class as a **predeclared singleton** (callable like `clsThing.Method`
> without `New`), set `VB_PredeclaredId = True`. That bit is *only* expressible in the
> header — there is no source-code equivalent — so it must be encoded here, not lost.

Track every temp file in a **caller-owned list** so a mid-import exception still lets
the `finally` block delete them all. Never leave `%TEMP%\modFoo.bas` behind — a stale
temp can shadow the next build.

### [2] Import the standard modules, classes, and forms

```
$wb = $xl.Workbooks.Add()           # or $ppt.Presentations.Add()
$vbProj = $wb.VBProject             # $null here ⇒ Trust Center not enabled
foreach ($temp in $tempFiles) { $vbProj.VBComponents.Import($temp) }
```

**Import order rarely matters** — VBA resolves references at compile time, not import
time — but importing `src/common` *then* `src/<host>` keeps shared code first and is
the convention here. **Skip the document modules** (`ThisWorkbook.cls`,
`ThisDocument.cls`) in this loop; they are handled in step 3.

`src/common/` is imported into **both** add-ins. Anything you put there grows both
surfaces and must compile under both object models (no host-specific early-bound types
without `#If` host guards or late binding).

### [3] Inject document-module code (cannot be imported)

A blank document already has its document module. Find it and replace its code body —
do **not** `Import`:

```
$twb = $vbProj.VBComponents("ThisWorkbook")           # Excel: by name
$twb.CodeModule.DeleteLines(1, $twb.CodeModule.CountOfLines)
$twb.CodeModule.AddFromString( <file text> )
```

PowerPoint's document module isn't reliably named `ThisDocument`, so locate it **by
type** instead — iterate components for `Type = 100` (`vbext_ct_Document`) and take the
first. (`DeleteLines` with a zero count throws, so guard an already-empty module.)

### [4] Save in add-in format

| Host | Method | Format constant |
|---|---|---|
| Excel | `wb.SaveAs(path, 55)` | `55` = `xlAddIn` (`.xlam`) — or `18` for legacy `.xla` |
| PowerPoint | `pres.SaveAs(tmp, 25)` | `25` = `ppSaveAsOpenXMLPresentationMacroEnabled` (`.pptm`) |
| Word | `doc.SaveAs2(path, 15)` | `15` = `wdFormatXMLDocumentMacroEnabled` (`.dotm` via 14/template) |

PowerPoint has **no direct "save as add-in" format constant** — that's why this build
saves a macro-enabled `.pptm` and converts it to `.ppam` in step 6.

### [5] Inject the ribbon (customUI) into the ZIP

The saved file is a ZIP. Open it in *Update* mode and make three coordinated edits —
all three are required or the ribbon silently won't load:

1. **Write the part:** `customUI/customUI14.xml` (the 2009 schema, namespace
   `http://schemas.microsoft.com/office/2009/07/customui`, supports Office 2010+).
   Use `customUI/customUI.xml` (2006 schema) only for Office 2007 compatibility.
   Delete any pre-existing customUI part first so rebuilds don't stack.
2. **Declare its content type** in `[Content_Types].xml`: add an
   `<Override PartName="/customUI/customUI14.xml" ContentType="application/xml"/>`
   (remove stale customUI overrides first).
3. **Relate it from the package root** in `_rels/.rels`: add a `<Relationship>` with
   `Type=".../2007/relationships/ui/extensibility"` and
   `Target="customUI/customUI14.xml"`.

Ribbon callbacks are wired by `onAction="OnBtnFoo"` attributes pointing at public subs
with the right signature (`Sub OnBtnFoo(control As IRibbonControl)`). Keep an
`onLoad="RibbonOnLoad"` handler that stashes the `IRibbonUI` so code can call
`.Invalidate` later. **Ribbon XML must be static** — this pipeline does not wire
`getContent`/`<dynamicMenu>` callbacks.

### [6] PowerPoint only — convert .pptm → .ppam

A `.ppam` is a `.pptm` with one content-type changed. After step 5, reopen the ZIP and
rewrite the presentation part's override:

```
//Override[@PartName='/ppt/presentation.xml']
  ContentType = "application/vnd.ms-powerpoint.addin.macroEnabled.main+xml"
```

Then rename the file `.pptm → .ppam`. (Excel needs no equivalent — `xlAddIn` already
wrote the add-in content type.)

---

## UserForms (.frm / .frx) — the fragile part

A UserForm is **two files**: `.frm` (text: header + control declarations + code-behind)
and `.frx` (binary: a serialized `OleObjectBlob` of the control layout). They must stay
paired and consistent.

Rules that cause silent, non-obvious failures when violated:

- **`.frm` must use LF line endings.** `VBComponents.Import` rejects CRLF on a `.frm`
  when its `.frx` is present/absent in the wrong combination. Normalize to LF before
  import; configure the editor/`.gitattributes` to preserve it.
- **Keep the `.frx` next to the `.frm` temp copy.** The import step copies the
  companion `.frx` into `%TEMP%` alongside the re-encoded `.frm`. Lose it and the form
  imports with no controls.
- **`.frx` is MSForms-version-specific.** The blob is serialized against the MSForms
  build on the machine that created it. On a machine with an incompatible MSForms, the
  build fails with **HRESULT `0x800AEA9D`** ("OleObjectBlob could not be set"). The fix
  is **not** to edit the `.frx` — regenerate the pair against the *local* MSForms.

### Regenerating forms (the 0x800AEA9D fix)

This repo uses the external [VBABuilder](https://github.com/RorySullivan1/VBABuilder)
`vba-build-forms`, driven by `build/forms.spec.json`:

```
vba-build-forms --spec build/forms.spec.json --project-root .
```

The spec is a **design-time mirror** of whatever the runtime builds. If the form's
controls are also created at runtime (e.g. a `BuildControls` sub), the spec's control
names/layout must match that sub **name-by-name**, so design-time and runtime agree.
`vba-build-forms` preserves existing code-behind by default; commit the regenerated
`.frm`/`.frx` pair together. Only run this when the build actually fails with
0x800AEA9D — a working `.frx` should be left alone.

> **Two ways to populate a form's controls — know which you're using.** (a) *Design-
> time*: controls live in the `.frx`, laid out in the VBA designer / `forms.spec.json`.
> (b) *Runtime*: a sub adds controls via `.Controls.Add` on form load. Runtime building
> sidesteps `.frx` version pain entirely (the form ships nearly empty) at the cost of
> code verbosity. This project does **both** and keeps them in sync via the spec —
> that's why the spec carries a `_note` pointing at the runtime builder.

---

## The export round-trip (build in reverse)

`export.ps1` opens a *built* add-in and writes its components back to `src/`, so edits
made in the Office VBA IDE (handy for debugging with breakpoints) can be recovered into
version control. The inverse of every build transform applies:

- **Strip headers on the way out.** Remove the leading `Attribute …` lines (`.bas`) or
  the `VERSION/BEGIN/END/MultiUse/Attribute` block (`.cls`) so committed source stays
  header-less. `.frm` keeps its header.
- **Route shared modules back to `src/common/`.** Build a lookup of filenames already
  in `common/`; if a component's file lives there, write it back there, not into the
  host folder. Otherwise a `common` module silently forks into two host copies.
- **Component type → extension:** `1`→`.bas`, `2`→`.cls`, `3`→`.frm`, `100`→document
  module. Export the *main* document module (`ThisWorkbook`/`ThisDocument`) only when
  it has real code (`CountOfLines > 2`); skip empty sheet/slide modules.
- **Forms need their own pass** (`export_forms.ps1`) because `.Export` on a `Type=3`
  component writes both `.frm` and `.frx`. PowerPoint can't `Presentations.Open` a
  `.ppam` directly — copy it to `.pptm` first, or load it via `AddIns.Add` and find its
  VBProject through `Application.VBE.VBProjects` by `FileName`.

Round-trip is **lossy in one direction only**: header bytes and predeclared-ID flags
are reconstructed from convention on the way back in. Keep the conventions
(`mod`/`cls`/`frm` prefixes, headers-stripped) airtight or the next build mis-headers a
file and the IDE won't warn you until import fails.

---

## COM lifecycle — the part that hangs your machine if you skip it

Automating Office leaves orphaned `EXCEL.EXE`/`POWERPNT.EXE` processes if you don't tear
down cleanly. Every build/export must:

- Set `Application.Visible = $false` (Excel) / `Visible = msoTrue (-1)` (PowerPoint —
  it resists being fully hidden) and `DisplayAlerts = $false` so a modal dialog can't
  block a headless run.
- Wrap the whole body in `try { … } finally { … }`. In `finally`: `Application.Quit()`,
  then `[Runtime.InteropServices.Marshal]::ReleaseComObject($app)`, then delete temp
  files. Quit/Release must run **even on failure**, each guarded with its own
  `try/catch` (PowerPoint's `Quit` throws if it already died).
- **PowerPoint needs a `Start-Sleep -Milliseconds 500` before `Quit`** — it tears down
  asynchronously and releasing the COM object too fast raises RPC errors. Excel does
  not need this.
- Never reuse a running user instance. `New-Object -ComObject` spins a dedicated
  automation instance; closing it won't disturb the user's open Office.

---

## Multi-host add-ins (shared `src/common/`)

When the same codebase ships to more than one host (here: Excel + PowerPoint):

- `src/common/` is imported into **every** target. It must compile under all of them.
  Avoid host-only early-bound types; prefer late binding or `#If`-guarded host
  constants. A module that references `ActiveSheet` cannot live in `common`.
- Each host gets its **own** ribbon XML (`customui/<host>_customUI14.xml`) and its own
  document-module file. Callback sub names can overlap across hosts because they live in
  separate VBProjects.
- The version constant (`APP_VERSION` in `modConstants.bas`) is shared — bump it in one
  place at release time only. Do not bump on `dev-*` branches.

---

## Decision tables

### Which output format?

| Goal | Excel | PowerPoint | Word |
|---|---|---|---|
| Distributable add-in (loads via Add-ins manager, no visible document) | `.xlam` (SaveAs 55) | `.ppam` (SaveAs 25 → content-type rewrite) | `.dotm` template / global |
| Macro-enabled document the user opens directly | `.xlsm` (52) | `.pptm` (25) | `.docm` (13) |
| Legacy (Office 97–2003) | `.xla` (18) | n/a | n/a |

### Which ribbon schema?

| customUI part | Schema namespace year | Min Office | Use when |
|---|---|---|---|
| `customUI/customUI14.xml` | 2009/07 | 2010 | **Default.** Supports `getVisible`, backstage, etc. |
| `customUI/customUI.xml` | 2006/01 | 2007 | Only if Office 2007 must be supported |

### Build failure → cause

| Symptom | Likely cause |
|---|---|
| `VBProject` is `Nothing` / "programmatic access" error | Trust access to VBA project object model not enabled in that host |
| `Import` throws on a `.frm` | CRLF line endings, or missing companion `.frx` |
| HRESULT `0x800AEA9D` on form import | `.frx` serialized against an incompatible MSForms — regenerate with `vba-build-forms` |
| Ribbon tab missing after build | One of the three ZIP edits skipped (part / content-type / relationship), or callback names don't match `onAction` |
| Duplicate `ThisWorkbook` code / import error on doc module | Document module was `Import`ed instead of code-injected |
| Module-level `Dim` "compile error" after import | Declarations placed *between* procedures in source — must be in the Declarations section at the top of the file |
| Orphaned `EXCEL.EXE` after build | Missing `finally` with `Quit` + `ReleaseComObject` |
| `.ppam` opens as a normal presentation | content-type of `/ppt/presentation.xml` not rewritten (step 6) |

---

## Source-file conventions the build depends on (will not warn you)

These are import-time landmines — the VBA IDE accepts them, but `VBComponents.Import`
or the next compile fails:

- **No headers in committed source.** No `Attribute VB_Name`, `VERSION 1.0 CLASS`,
  `BEGIN`, etc. The build injects them; export strips them.
- **Module-level variables live in the Declarations section**, above the first
  `Sub`/`Function`. A `Private`/`Public`/`Dim` *between* procedures passes the IDE but
  breaks at import.
- **`Const` cannot hold a function call** (`ChrW$`, `RGB`, `Now`). It compiles in the
  IDE but fails post-import — use a `Function` returning the value instead.
- **`.frm` = LF endings.** Always.
- **Naming:** `mod*` standard module, `cls*` class, `frm*` UserForm. Export routing and
  type inference rely on it.
- **ANSI-safe content.** Source may be UTF-8 on disk, but the build re-encodes to
  Windows-1252; characters outside CP-1252 will be mangled on import. Build non-ASCII
  strings with `ChrW$()` at runtime rather than embedding the literal glyph.

---

## Standard commands (this repo)

```powershell
cd build
.\build.ps1 -Target all          # Build both → dist/xlVizer.xlam, dist/xlVizer.ppam
.\build.ps1 -Target excel        # Excel only
.\build.ps1 -Target powerpoint   # PowerPoint only

.\export.ps1                     # Round-trip: built .xlam → src/excel + src/common
.\export.ps1 -Target powerpoint  # Built .ppam → src/powerpoint + src/common
.\export_forms.ps1               # Pull .frm/.frx UserForms out of both built add-ins
```

```bash
# Only when build fails with HRESULT 0x800AEA9D:
vba-build-forms --spec build/forms.spec.json --project-root .
```

There is no CI, linter, or automated test runner — verify by building, installing the
add-ins in Office, and smoke-testing the ribbon flows. After any build-pipeline change,
build **both** targets and confirm the module import list and "Build complete" lines.

---

## Before you finish

- Did you change a header-injection or encoding rule? Re-run `export.ps1` and confirm a
  clean round-trip (no spurious diffs in `src/`).
- Did you touch the ribbon? Confirm all three ZIP edits and that every `onAction`
  resolves to a real public sub.
- Did you touch a form? Build on the target MSForms machine; commit the `.frm`/`.frx`
  pair together; confirm controls render at runtime.
- Did you add a `src/common/` module? Confirm it compiles under **both** hosts.
