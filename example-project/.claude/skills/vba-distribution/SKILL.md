---
name: vba-distribution
description: >
  Expert VBA packaging, signing, and deployment specialist for getting Excel/Word/
  Outlook/PowerPoint macros and add-ins onto end-user machines. Use this skill
  whenever the user asks how to package, sign, distribute, or install VBA — choosing
  `.xlsm` vs `.xlam` vs exported `.bas`, building and installing an add-in, code-signing
  a VBAProject with a certificate, configuring Trusted Locations or the Trust Center,
  dealing with Mark-of-the-Web / Protected View / "macros blocked" on downloaded or
  network files, registering UDF categories, deploying across a locked-down corporate
  fleet, or setting up a text-source round-trip build. Trigger on "how do I deploy this
  macro", "package as an add-in", "sign my VBA", "macros are blocked", "install the
  .xlam", "Trusted Location", "ship this to the team". For C#/VB.NET (VSTO/ClickOnce/MSI)
  add-ins use VSTO-distribution instead; this skill is VBA-container distribution.
---

# VBA Distribution Skill

You get VBA off the developer's machine and running on everyone else's — reliably,
signed, and trusted. Never recommend a method without knowing the environment.
**Always test on a machine other than the development one before declaring done** —
reference, trust-center, and signing problems usually surface only on a clean install.

## First — Gather Deployment Context

| Required information | Why it matters |
|---|---|
| **Host + deliverable** | Excel macro vs. reusable add-in changes the format (below) |
| **Audience size** | 1 person → email the file; a team → shared add-in; a fleet → GPO + signed |
| **Machine management** | Corporate-managed (Trusted Locations / cert via GPO) vs. BYOD |
| **File origin** | Will users download it (Mark-of-the-Web → Protected View) or get it from a trusted share? |
| **Update cadence** | Frequent → loader/network add-in; stable → copy-to-AddIns |
| **Signing available?** | Is there a corporate code-signing cert, or only self-signed? |

---

## Choose the Deliverable Format

| Format | Use for | Notes |
|---|---|---|
| **`.xlsm`** | A workbook whose macros operate on *that* workbook's own data | Macros travel with the data; not reusable across files |
| **`.xlam`** (Excel add-in) | Reusable library/UDFs/ribbon used across many workbooks | `IsAddin = True`, not visible; installs once, available everywhere |
| **`.dotm` / template** (Word) | Document-automation distributed as a template | Word's equivalent of the reusable container |
| **Exported `.bas`/`.cls`/`.frm`** | Source for version control / round-trip build | Text in Git; build rebuilds the binary container (not an end-user deliverable) |

Default a reusable Excel tool to a **single consolidated `.xlam`** with module prefixes for
separation, rather than asking users to install several add-ins by hand.

---

## Packaging an `.xlam`

```vba
' In ThisWorkbook of the add-in
Private Sub Workbook_Open()
    RegisterFunctionsOnce
End Sub
```

```vba
' modSetup — register UDF categories once (guarded), resolve paths relatively
Public Sub RegisterFunctionsOnce()
    On Error Resume Next   ' MacroOptions throws if the category already exists
    Application.MacroOptions Macro:="Acme_GetTimeSeries", _
        Description:="Fetch a time series", Category:="Acme"
    On Error GoTo 0
End Sub

Public Function ConfigPath() As String
    ' Ship-with-add-in files: relative to ThisWorkbook.Path. User config: %AppData%.
    ConfigPath = Environ$("AppData") & "\Acme\config.json"
End Function
```

Rules: set `IsAddin = True`; public procedures in standard modules become callable from any
workbook once installed (no manual reference needed). **Never hardcode paths** — resolve
shipped files relative to `ThisWorkbook.Path`, user config via `Environ("AppData")` or the
registry.

### Install path (per-user)
Copy the `.xlam` to `%APPDATA%\Microsoft\AddIns\`, then **File → Options → Add-ins → Manage:
Excel Add-ins → Go → tick the box.** This is *not* obvious to non-developers — document it (see
the README template).

---

## Code Signing (the durable trust fix)

Unsigned macros are governed entirely by each machine's macro setting; a signed project can be
trusted once and then run under "disable all except digitally signed".

1. **Get a certificate.** A corporate/CA code-signing cert for production; `SELFCERT.EXE`
   (ships with Office) only for a single dev machine — self-signed is **not** trusted on other
   machines unless you push the cert to their Trusted Publishers.
2. **Sign the project:** VBA editor → **Tools → Digital Signature → Choose** → select the cert.
   Signing is per-VBAProject; re-sign after every code change (the signature covers the code).
3. **Distribute the public cert** to users' **Trusted Publishers** store (manually, or via GPO
   for a fleet). Once present, the add-in loads under stricter macro policies without prompting.
4. **Watch expiry** — a lapsed cert invalidates the signature silently; users fall back to the
   machine macro policy. Put a renewal reminder 60 days out and re-sign on renewal.

---

## Trust: Why Macros Get Blocked

The three things that stop a perfectly good macro from running:

| Symptom | Cause | Fix |
|---|---|---|
| **Yellow "macros disabled" bar** | Macros not from a Trusted Location and not signed/trusted | Add the folder as a **Trusted Location**, or sign + trust the publisher |
| **Red "blocked" bar, no Enable button** (downloaded file) | **Mark-of-the-Web** from internet/email + the modern "block macros from the internet" policy | Distribute via a **Trusted Location** UNC share, or have users *Unblock* (file Properties) — not from the internet zone |
| **Protected View** | MOTW on a downloaded file | Comes from the same MOTW; a Trusted Location or removing MOTW clears it |

**Trusted Locations** (File → Options → Trust Center → Trusted Locations) are the cleanest
corporate answer: put the `.xlam`/`.xlsm` on a managed share marked trusted (allow network
locations, set via GPO), and macros run without per-file prompts and without signing.

---

## Corporate Fleet Deployment

Expect on managed Windows with no admin rights:

- **Macros from network locations are blocked** unless the location is a Trusted Location → coordinate with IT to mark the share, pushed by GPO.
- **Downloaded files carry Mark-of-the-Web** and open in Protected View → prefer an internal trusted share over email/web download.
- **Code-signing may be mandatory** → sign the project and push the cert to Trusted Publishers by GPO.
- **Updates:** for frequent changes, ship a thin **loader `.xlam`** that installs/updates sibling add-ins from the trusted share at `Workbook_Open`, so users never reinstall manually.

---

## Source Export & Round-Trip Build

For version control and reproducible packaging:

- Export every module to text: `.bas` (standard), `.cls` (class), `.frm` **+** `.frx` (form — the binary `.frx` must be committed).
- Prefer a **round-tripped build** (text source in Git → a build step rebuilds the `.xlam`/`.xlsm`) over committing the binary container. The binary is an artifact; the text is the source of truth.
- Tag releases and bump a visible version constant (`Public Const ADDIN_VERSION = "2.3.1"`) so support can confirm what a user is running.

---

## Install README Template

Ship this next to the file — "copy it and tick the box" is not obvious to the desk:

```markdown
## Acme Add-In v2.3.1 — Install

1. Close Excel.
2. Copy `Acme.xlam` to:  %APPDATA%\Microsoft\AddIns\
   (paste that path into the File Explorer address bar)
3. Open Excel → File → Options → Add-ins
4. Manage: **Excel Add-ins** → **Go…**
5. Tick **Acme** → OK.
6. Confirm: the **Acme** ribbon tab appears / `=Acme_…` functions autocomplete.

Trouble? If a yellow/red macro bar appears, the file isn't in a Trusted Location —
contact IT to add the share, or right-click the file → Properties → **Unblock**.
```

---

## Watch Out

1. **A signature is invalidated by the next code edit.** Signing is per-project over the current code — change one line and you must re-sign before redistributing, or users get an "invalid signature" warning that's worse than unsigned.
2. **Mark-of-the-Web is the silent killer of emailed/downloaded add-ins.** Modern Office hard-blocks internet-origin macros with no Enable button. Distribute from a Trusted internal share, not as a download, or the file simply won't run no matter how good the code is.
3. **Self-signed certs don't travel.** `SELFCERT.EXE` trusts only the machine that made it. For anyone else, either push the public cert to their Trusted Publishers or use a Trusted Location instead — don't assume self-signing solved distribution.
4. **Test on a clean machine.** References, trust, and signing all "work on my machine" by definition. The deployment isn't done until it runs on a second machine that never had the dev environment.
