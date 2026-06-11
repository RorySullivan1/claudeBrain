---
name: VSTO-maintenance
description: >
  Expert VSTO add-in maintenance, troubleshooting, and lifecycle management specialist.
  Use this skill whenever a user reports that an existing VSTO add-in is broken,
  failing to load, crashing, or behaving unexpectedly after an Office update, Windows
  update, certificate change, or machine migration. Also trigger for questions about
  diagnosing disabled add-ins, interpreting Event Viewer errors, managing LoadBehavior,
  updating dependencies, migrating between Office versions, handling runtime deprecation,
  keeping add-ins working after Office 365 channel updates, or planning long-term
  support for a deployed VSTO solution. If the user says "my add-in stopped working",
  "users are getting errors", "it worked before the update", or "how do I keep this
  maintained", use this skill.
---

# VSTO Maintenance Skill

## Triage First — Get the Facts

Before diagnosing, collect:

| Information | How to Get It |
|---|---|
| **Error message verbatim** | Windows Event Viewer or Office error dialog |
| **When it broke** | After which update, migration, or change? |
| **Office version + build** | File → Account → About [App] (e.g., `16.0.17531.20108`) |
| **Office type** | Click-to-Run or MSI Office |
| **Office bitness** | File → Account → About — shows "(32-bit)" or "(64-bit)" |
| **Windows version** | `winver` in Run dialog |
| **.NET Framework version** | Control Panel → Programs → .NET versions |
| **VSTO Runtime installed** | Control Panel → Programs → "Microsoft Visual Studio Tools for Office Runtime" |
| **LoadBehavior current value** | PowerShell or regedit (see registry section) |

---

## Add-In Not Loading — Diagnostic Flowchart

Work through these in order. Each step either resolves the issue or narrows the next step.

### Step 1: Check Windows Event Viewer

```
Event Viewer → Windows Logs → Application
Filter by Source: "Microsoft Office [AppName]" or ".NET Runtime" or "Application Error"
```

Common event IDs and their meaning:

| Event ID | Source | Meaning |
|---|---|---|
| `1000` | Application Error | Unhandled exception at load — get the faulting module name |
| `4096`–`4099` | VSTO | VSTO runtime load errors — check for runtime version mismatch |
| `6158`–`6161` | Microsoft Office | Add-in disabled due to repeated failures |

Copy the **full event text**. The faulting module name and exception type tell you where to look next.

### Step 2: Check LoadBehavior

```powershell
# Check all four possible registry locations
$paths = @(
    "HKLM:\Software\Microsoft\Office\Excel\Addins\MyCompany.MyAddIn",
    "HKCU:\Software\Microsoft\Office\Excel\Addins\MyCompany.MyAddIn",
    "HKLM:\Software\WOW6432Node\Microsoft\Office\Excel\Addins\MyCompany.MyAddIn",
    "HKCU:\Software\WOW6432Node\Microsoft\Office\Excel\Addins\MyCompany.MyAddIn"
)
foreach ($p in $paths) {
    if (Test-Path $p) { Get-ItemProperty $p | Select-Object PSPath, LoadBehavior, Manifest }
}
```

| LoadBehavior Found | Meaning | Fix |
|---|---|---|
| `3` | Should load at startup — something else is wrong | Continue to Step 3 |
| `2` | Load on demand — Office likely reset it after a crash | Reset to `3` |
| `0` | Disconnected — Office disabled it after repeated failures | Check Disabled Items, reset to `3`, fix root cause |
| Key missing | Add-in not registered at all | Re-run installer or add key manually |

Reset to 3:
```powershell
Set-ItemProperty `
  -Path "HKCU:\Software\Microsoft\Office\Excel\Addins\MyCompany.MyAddIn" `
  -Name "LoadBehavior" -Value 3
```

### Step 3: Check Office's Disabled Items List

In Office: **File → Options → Add-ins → Manage: Disabled Items → Go**

If the add-in appears here:
1. Select it → Enable
2. Restart Office
3. If it reappears in Disabled Items, the root cause is a crash at load — proceed to step 4

### Step 4: Verify VSTO Runtime

```powershell
# Check installed VSTO runtime versions
Get-ItemProperty "HKLM:\Software\Microsoft\VSTO Runtime Setup\v4" -ErrorAction SilentlyContinue
Get-ItemProperty "HKLM:\Software\Microsoft\VSTO Runtime Setup\v4R" -ErrorAction SilentlyContinue
```

If missing or version mismatch:
1. Download the correct runtime from Microsoft: "Visual Studio 2010 Tools for Office Runtime"
2. Install on the affected machine
3. Restart and test

### Step 5: Verify Certificate Trust

```powershell
# Check if the signing cert is in Trusted Publishers
Get-ChildItem Cert:\LocalMachine\TrustedPublisher | Where-Object { $_.Subject -like "*MyCompany*" }
Get-ChildItem Cert:\CurrentUser\TrustedPublisher  | Where-Object { $_.Subject -like "*MyCompany*" }
```

If absent or expired:
- For ClickOnce: reinstall from the publish URL to re-trigger trust prompt
- For MSI: push updated certificate via GPO or re-run installer with new cert
- For expired cert: renew, re-sign manifests, republish

### Step 6: Test on a Clean Profile

Create a new Windows user profile and test the add-in fresh. If it works on the new profile:
- The issue is per-user registry corruption or conflicting per-user settings
- Export/delete the `HKCU\Software\Microsoft\Office\...\Addins\MyCompany.MyAddIn` key and re-register

### Step 7: Enable VSTO Load Logging

```powershell
# Enable detailed VSTO diagnostic logging
New-ItemProperty -Path "HKCU:\Software\Microsoft\VSTO\Security" `
  -Name "EnableLogging" -Value 1 -PropertyType DWORD -Force

# Log written to: %TEMP%\VSTOInstaller.log and %APPDATA%\Microsoft\VSTO\
```

---

## Office Update Breakage

The most common post-update failures and their fixes:

### Office 365 Monthly Channel Updated
- **Symptom:** Add-in loads, but API calls fail or behave unexpectedly
- **Check:** Whether the Office build changed a behavior you depend on (e.g., event firing order)
- **Fix:** Test on Semi-Annual Channel for stability; file feedback with Microsoft if regression confirmed

### PIA Version Mismatch After Office Upgrade
- **Symptom:** `System.IO.FileNotFoundException` or `BadImageFormatException` at load
- **Check:** The interop assemblies your add-in was compiled against vs. the installed Office version
- **Fix:** Recompile against the PIAs matching the installed Office version; embed interop types (`Embed Interop Types = true`) to reduce version sensitivity

### .NET Framework Update Broke Something
- **Symptom:** Works on some machines, not others; started after a Windows Update
- **Check:** `<supportedRuntime>` element in your add-in's `.dll.config` or `app.config`
- **Fix:** Ensure config specifies the correct runtime version range

```xml
<!-- MyAddIn.dll.config -->
<configuration>
  <startup>
    <supportedRuntime version="v4.0" sku=".NETFramework,Version=v4.7.2" />
  </startup>
</configuration>
```

---

## Dependency Maintenance

### NuGet Package Updates

Don't update packages blindly. Follow this process:

1. **Check changelog** for breaking changes before updating
2. **Update one package at a time** in a dev branch
3. **Test with the minimum supported Office version**, not just the latest
4. **Verify COM release patterns still hold** if interop-adjacent packages changed
5. **Update `packages.lock.json`** and commit it to lock transitive dependencies

### PIA Versioning Rules

- Compile against **the lowest Office version you need to support** to maximize compatibility
- Never mix PIAs from different Office versions in the same project
- With `Embed Interop Types = true`, most PIA version differences are handled at compile time

Check current embedded interop setting:
```xml
<!-- In .csproj, for each Office interop reference -->
<Reference Include="Microsoft.Office.Interop.Excel">
  <EmbedInteropTypes>True</EmbedInteropTypes>
</Reference>
```

### Certificate Renewal Process

1. Obtain new certificate (minimum 2-year validity recommended)
2. Test signing in development environment first
3. Re-sign all manifests:
   ```bash
   mage.exe -Sign MyAddIn.dll.manifest -CertHash <new-thumbprint>
   mage.exe -Sign MyAddIn.vsto -CertHash <new-thumbprint>
   ```
4. Republish to ClickOnce location, or rebuild MSI with new cert
5. Push new cert to Trusted Publishers via GPO if machine-wide trust is required
6. Update deployment runbook with new thumbprint and expiry date

---

## Versioning and Updates

### Version Number Strategy

Use semantic versioning adapted for Office add-ins:

```
Major.Minor.Patch.Build
  │     │     │     └── CI build number (auto-increment)
  │     │     └────── Bug fixes, no behavior change
  │     └──────────── New features, backward compatible
  └────────────────── Breaking changes or Office version requirement change
```

Tag releases in source control:
```bash
git tag -a "v2.3.1-office365" -m "Fix COM leak in worksheet iterator; targets Office 365+"
git push origin v2.3.1-office365
```

### ClickOnce Update Testing

Before pushing an update to the production URL:
1. Test update path from **n-1 version** to current — not just a clean install
2. Verify `LoadBehavior` survives the update (ClickOnce should preserve it; confirm)
3. Confirm manifest signature is valid with the current cert
4. Test on both 32-bit and 64-bit Office if you support both

### MSI Upgrade Testing

```
Clean machine → install v1.0 → run smoke test
                              → install v2.0 over it (MajorUpgrade)
                              → verify old files removed, new files present
                              → verify LoadBehavior = 3 in registry
                              → run smoke test
```

---

## Long-Term Support Planning

### Office Version Lifecycle Tracking

Monitor these and update your test matrix when versions go end-of-life:
- **Office 2016 Extended Support End:** October 2025
- **Office 2019 Extended Support End:** October 2025
- **Office 2021 Extended Support End:** October 2026
- **Microsoft 365 Apps:** Evergreen — always test against current + previous Semi-Annual Channel build

### Migration Path Awareness

VSTO is a .NET Framework technology. Microsoft has not announced end-of-support, but be aware:
- **.NET Framework 4.x** is in maintenance mode (security fixes only)
- **Office JavaScript Add-ins** are Microsoft's stated future direction — not a drop-in replacement, but worth tracking for new feature development
- **ExcelDNA** is an alternative for Excel-only add-ins that supports .NET 6+ — relevant if .NET Framework support becomes a blocker

### Deprecation Watchlist

Watch for changes in these areas across Office updates:
- `Application.FileDialog` — behavior changed in some 365 builds
- Outlook security prompts — triggered by object model access patterns, affected by security updates
- Custom Task Pane persistence — behavior varies by Office version and docking state

---

## Health Check Script

Run this PowerShell on a target machine to snapshot add-in health:

```powershell
# VSTO Add-In Health Check
# Usage: .\health-check.ps1 -ProgId "MyCompany.MyAddIn" -OfficeApp "Excel"

param(
    [string]$ProgId    = "MyCompany.MyAddIn",
    [string]$OfficeApp = "Excel"
)

Write-Host "=== VSTO Add-In Health Check ===" -ForegroundColor Cyan

# 1. Registry check
$regPaths = @(
    "HKLM:\Software\Microsoft\Office\$OfficeApp\Addins\$ProgId",
    "HKCU:\Software\Microsoft\Office\$OfficeApp\Addins\$ProgId",
    "HKLM:\Software\WOW6432Node\Microsoft\Office\$OfficeApp\Addins\$ProgId"
)

foreach ($path in $regPaths) {
    if (Test-Path $path) {
        $props = Get-ItemProperty $path
        Write-Host "Found at: $path" -ForegroundColor Green
        Write-Host "  LoadBehavior: $($props.LoadBehavior)"
        Write-Host "  Manifest: $($props.Manifest)"
    }
}

# 2. VSTO runtime check
$vstoKey = "HKLM:\Software\Microsoft\VSTO Runtime Setup\v4R"
if (Test-Path $vstoKey) {
    $vstoVer = (Get-ItemProperty $vstoKey).Version
    Write-Host "VSTO Runtime: $vstoVer" -ForegroundColor Green
} else {
    Write-Host "VSTO Runtime: NOT FOUND" -ForegroundColor Red
}

# 3. Trusted publishers
$certs = Get-ChildItem Cert:\LocalMachine\TrustedPublisher, Cert:\CurrentUser\TrustedPublisher `
         -ErrorAction SilentlyContinue
Write-Host "Trusted Publisher certs: $($certs.Count) found"
$certs | ForEach-Object { Write-Host "  $($_.Subject) [Expires: $($_.NotAfter)]" }

# 4. Recent Event Viewer errors
$events = Get-WinEvent -FilterHashtable @{
    LogName   = 'Application'
    StartTime = (Get-Date).AddDays(-7)
    Level     = 1,2  # Critical, Error
} -ErrorAction SilentlyContinue |
Where-Object { $_.Message -like "*$ProgId*" -or $_.Message -like "*VSTO*" }

if ($events) {
    Write-Host "Recent errors ($($events.Count)):" -ForegroundColor Yellow
    $events | Select-Object -First 5 | ForEach-Object {
        Write-Host "  [$($_.TimeCreated)] $($_.Message.Substring(0, [Math]::Min(120, $_.Message.Length)))"
    }
} else {
    Write-Host "No recent errors in Event Viewer" -ForegroundColor Green
}
```

---

## Watch Out

1. **Office 365's Monthly Channel updates can silently break event behavior.** Behaviors that worked in one build may change in the next. Pin critical production users to the Semi-Annual Enterprise Channel and test each update before promoting.
2. **LoadBehavior resets to `2` or `0` after crashes are Office's self-protection.** Resetting it to `3` without fixing the underlying crash will just get it disabled again. Always find and fix the root cause.
3. **Certificate expiry causes silent update failure, not visible load failure.** Users keep running the cached version indefinitely, unaware updates stopped. The only indication is checking the cert expiry date in the manifest. Put a recurring calendar reminder 60 days before expiry.
