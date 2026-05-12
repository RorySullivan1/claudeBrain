---
name: VSTO-distribution
description: >
  Expert VSTO deployment and distribution specialist for Office add-ins. Use this
  skill whenever the user asks about packaging, deploying, installing, or distributing
  a VSTO add-in — including ClickOnce publishing, MSI/WiX installer creation, Group
  Policy deployment, code signing certificates, VSTO runtime prerequisites, registry
  registration, or getting an add-in onto end-user machines. Also trigger for questions
  about update mechanisms, rollback, ClickOnce trust prompts, silent installation,
  Office Click-to-Run vs MSI Office, 32 vs 64-bit targeting, or enterprise IT rollout
  planning. If the user says "how do I deploy", "how do I install", "how do I
  distribute", or describes a deployment failure, use this skill.
---

# VSTO Distribution Skill

## First — Gather Deployment Context

Never recommend a method without knowing the environment. Ask for all unknowns upfront:

| Required Information | Why It Matters |
|---|---|
| **Office installation type** | Click-to-Run (C2R) vs. MSI Office affects installer compatibility |
| **Office bitness** | 32-bit vs 64-bit — add-in must match |
| **Target environment** | Corporate IT/GPO vs. standalone vs. BYOD |
| **Number of machines** | 1–10 → ClickOnce; 10–100 → varies; 100+ → MSI/GPO |
| **Update frequency** | Frequent updates favor ClickOnce; stable releases favor MSI |
| **Internet access on machines** | Offline machines cannot use hosted ClickOnce |
| **IT admin involvement** | GPO deployment requires admin rights; ClickOnce can be per-user |

---

## Method Selection Guide

Choose the deployment method before writing any configuration:

| Method | Best For | Avoid When |
|---|---|---|
| **ClickOnce** | Small/medium teams, self-updating, non-IT-managed desktops | Strict GPO environments, offline machines, complex prerequisites |
| **MSI (WiX)** | Enterprise IT, GPO deployment, complex prerequisites, stable releases | Rapid iteration or frequent updates |
| **Group Policy (GPO)** | Large corporate rollouts managed by IT | Consumer/BYOD environments, no domain controller |
| **Manual XCOPY + reg** | Developer machines only | **Never in production** |

---

## ClickOnce Deployment

### When to Use
- Self-updating is required
- Users have internet/network access to the publish location
- No strict Group Policy restrictions on unsigned code
- Certificate budget exists for a trusted code signing cert

### Publish Configuration Checklist

In Visual Studio → Project Properties → Publish:

```
Publish Location:     \\server\share\MyAddIn\   (UNC) or https://intranet/addins/
Installation URL:     Same as publish location (never use mapped drives)
Update Behavior:      Check for updates before application starts
Publish Version:      Increment on every release (Major.Minor.Build.Revision)
Prerequisites:        ✅ .NET Framework [target version]
                      ✅ Visual Studio Tools for Office Runtime
                      ✅ Windows Installer [if bundled]
```

### Signing the Manifest

**Always use a trusted certificate in production.** Self-signed certs cause trust prompts on every install.

```xml
<!-- In .csproj, reference your code signing cert -->
<PropertyGroup>
  <ManifestCertificateThumbprint>ABCDEF1234567890...</ManifestCertificateThumbprint>
  <ManifestKeyFile>MyCert.pfx</ManifestKeyFile>
</PropertyGroup>
```

To sign manually via CLI:
```bash
# Sign the deployment manifest
mage.exe -Sign MyAddIn.vsto -CertHash <thumbprint>

# Sign the application manifest
mage.exe -Sign MyAddIn.dll.manifest -CertHash <thumbprint>
```

### ClickOnce Registry Entry (auto-created on install)
```
HKCU\Software\Microsoft\Office\Excel\Addins\MyCompany.MyAddIn
  Description    REG_SZ    "My Add-In Description"
  FriendlyName   REG_SZ    "My Add-In"
  LoadBehavior   REG_DWORD 3
  Manifest       REG_SZ    "https://server/addins/MyAddIn.vsto|vstolocal"
```

### ClickOnce Gotchas
- **URL permanence is critical.** Changing the publish URL after deployment breaks all installed clients. Document the URL in your runbook and treat it as permanent.
- **Certificate expiry silently breaks updates.** Set a calendar reminder 60 days before cert expiry to renew and re-sign.
- **C2R Office and ClickOnce VSTO can coexist**, but require the correct VSTO runtime version that matches the C2R Office channel.

---

## MSI Deployment (WiX)

### When to Use
- Enterprise IT manages deployment via Group Policy or SCCM/Intune
- Complex prerequisites beyond what ClickOnce bootstrapper handles
- Stable, infrequent release cadence

### WiX Product.wxs Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="*"
           Name="My Add-In"
           Language="1033"
           Version="$(var.Version)"
           Manufacturer="My Company"
           UpgradeCode="{YOUR-FIXED-GUID-HERE}">

    <Package InstallerVersion="500" Compressed="yes" InstallScope="perMachine" />

    <!-- Always define MajorUpgrade to handle version transitions cleanly -->
    <MajorUpgrade DowngradeErrorMessage="A newer version is already installed." />

    <MediaTemplate EmbedCab="yes" />

    <!-- VSTO Runtime prerequisite -->
    <PropertyRef Id="VSTORUNTIMEREDIST_40_INSTALLED" />

    <Condition Message="Visual Studio Tools for Office Runtime 4.0 is required.">
      <![CDATA[VSTORUNTIMEREDIST_40_INSTALLED]]>
    </Condition>

    <Feature Id="ProductFeature" Title="My Add-In" Level="1">
      <ComponentGroupRef Id="ProductComponents" />
      <ComponentGroupRef Id="RegistryComponents" />
    </Feature>
  </Product>

  <Fragment>
    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="ProgramFilesFolder">
        <Directory Id="INSTALLFOLDER" Name="MyCompany\MyAddIn" />
      </Directory>
    </Directory>
  </Fragment>

  <Fragment>
    <ComponentGroup Id="ProductComponents" Directory="INSTALLFOLDER">
      <Component Id="MainDll" Guid="*">
        <File Source="$(var.MyAddIn.TargetPath)" KeyPath="yes" />
      </Component>
      <Component Id="VstoManifest" Guid="*">
        <File Source="$(var.MyAddIn.TargetDir)MyAddIn.vsto" />
      </Component>
    </ComponentGroup>

    <!-- Machine-wide registry registration -->
    <ComponentGroup Id="RegistryComponents" Directory="INSTALLFOLDER">
      <Component Id="RegistryEntry" Guid="*">
        <RegistryKey Root="HKLM"
                     Key="Software\Microsoft\Office\Excel\Addins\MyCompany.MyAddIn">
          <RegistryValue Name="Description"  Type="string"  Value="My Add-In" />
          <RegistryValue Name="FriendlyName" Type="string"  Value="My Add-In" />
          <RegistryValue Name="LoadBehavior" Type="integer" Value="3" />
          <RegistryValue Name="Manifest"     Type="string"
                         Value="[INSTALLFOLDER]MyAddIn.vsto|vstolocal"
                         KeyPath="yes" />
        </RegistryKey>
      </Component>
    </ComponentGroup>
  </Fragment>
</Wix>
```

### LoadBehavior Reference

| Value | Behavior | Use For |
|---|---|---|
| `0` | Disconnected (not loaded) | Disabled state |
| `2` | Load on demand (user must manually activate) | Optional add-ins |
| `3` | **Load at startup** ← standard production value | All production add-ins |
| `8` | Load next time, then set to 2 | One-time load |
| `9` | Load at startup, set to 8 on error | Crash-resilient, but Office may disable after errors |
| `16` | Load on demand (connected) | Rare |

**Always deploy with `LoadBehavior = 3`.** If Office detects repeated load failures, it will reset this to `2` or `0` and add the add-in to Disabled Items.

### MSI Gotchas
- **UpgradeCode must never change** across versions. It's how Windows Installer recognizes your product as an upgrade vs. a new install. Generate it once and commit it to source control.
- **HKLM vs HKCU:** Machine-wide installs require admin rights and write to `HKLM`. Per-user installs write to `HKCU` and don't require elevation. Choose before building — changing this later requires an uninstall/reinstall.
- **`|vstolocal` suffix on Manifest path** tells VSTO to load from the local installation path rather than fetching from a network location. Required for MSI-deployed add-ins.

---

## Group Policy (GPO) Deployment

### Use When
- 50+ machines in an Active Directory domain
- IT department manages software via SCCM, Intune, or traditional GPO
- Consistent version enforcement is required

### Setup Steps
1. Package as MSI with machine-scope install (`InstallScope="perMachine"`)
2. Place MSI on a network share accessible to all target machines
3. In Group Policy Management Console: Computer Configuration → Software Settings → Software Installation → New Package
4. Point to the UNC path of the MSI: `\\dc\software\MyAddIn\MyAddIn.msi`
5. Choose **Assigned** (not Published) so the software installs on next login without user action

### Verify GPO Deployment
```powershell
# On a target machine, check applied policies
gpresult /r /scope computer

# Verify registry key was written
Get-ItemProperty "HKLM:\Software\Microsoft\Office\Excel\Addins\MyCompany.MyAddIn"
```

---

## Registry Quick Reference

### Check Current LoadBehavior
```powershell
# Application-level (machine-wide)
Get-ItemProperty "HKLM:\Software\Microsoft\Office\Excel\Addins\MyCompany.MyAddIn"

# Application-level (per-user)
Get-ItemProperty "HKCU:\Software\Microsoft\Office\Excel\Addins\MyCompany.MyAddIn"

# 64-bit OS, 32-bit Office
Get-ItemProperty "HKLM:\Software\WOW6432Node\Microsoft\Office\Excel\Addins\MyCompany.MyAddIn"
```

### Re-enable a Disabled Add-In via Registry
```powershell
# Reset LoadBehavior to 3 (Office sets it to 2 or 0 after repeated failures)
Set-ItemProperty `
  -Path "HKCU:\Software\Microsoft\Office\Excel\Addins\MyCompany.MyAddIn" `
  -Name "LoadBehavior" `
  -Value 3
```

---

## Prerequisites Checklist

Every deployment must confirm:

- [ ] **VSTO Runtime** version matches the .NET Framework target — available at Microsoft Download Center
- [ ] **.NET Framework** version installed on target machines
- [ ] **Office bitness** confirmed — 32-bit Office needs 32-bit add-in; 64-bit needs 64-bit (or AnyCPU)
- [ ] **Code signing certificate** installed in Trusted Publishers store on target machines
- [ ] **Office type** confirmed — Click-to-Run (C2R) vs. MSI Office (cannot coexist on same machine)
- [ ] **Admin rights** available for machine-scope MSI installs

---

## Deployment Runbook Template

Document this before every production release:

```markdown
## MyAddIn v[X.Y.Z] Deployment Runbook

**Release date:** YYYY-MM-DD
**Office targets:** Excel 2016, 2019, 365 (32-bit and 64-bit)
**Method:** ClickOnce / MSI / GPO

### Locations
- Publish URL / UNC path: [URL or path]
- Certificate thumbprint: [hex thumbprint]
- Certificate expiry: [date] — renewal reminder set for [date - 60 days]

### Rollback
- Previous version location: [path]
- Registry restore script: [path to .reg file]

### Verification Steps
1. Install on clean VM with target Office version
2. Open Office → File → Options → Add-ins → verify add-in appears and is active
3. Trigger core functionality smoke test
4. Check Windows Event Viewer for any load errors

### Known Issues
- [any version-specific caveats]
```

---

## Watch Out

1. **Office Click-to-Run and MSI Office cannot coexist.** Know which is installed before choosing a deployment method. Running `Get-ItemProperty "HKLM:\Software\Microsoft\Office\16.0\Common\InstallRoot"` will show the install type. C2R will have a `VersionToReport` property.
2. **Missing VSTO runtime is the #1 cause of silent add-in load failure.** Always bundle it as a prerequisite in ClickOnce or MSI. Don't assume it's present.
3. **ClickOnce update failures after cert expiry are silent.** Office will continue loading the cached version without warning the user that updates have stopped. Monitor cert expiry dates actively.
