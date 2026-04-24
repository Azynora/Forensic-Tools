# Usage Guide

This guide describes the active `FORENSICS_DISCORD` product shape: a **terminal-only, portable Windows 11 bundle**.

## Product model

- no GUI launcher
- no frontend web report
- no Windows installer
- no mandatory installation path
- portable execution from any extracted or cloned folder

The supported end-user shells are:

- `cmd`
- PowerShell

## Requirements

### Public portable bundle

- Windows 11 64-bit
- no separate Python or Node.js installation required
- Administrator approval only when the forensic workflow needs elevation during collection

### Private source workspace

- Windows 11 64-bit
- Python `3.10+`
- Administrator access when elevated collection is required

## Running from a portable release

After downloading a GitHub release zip or cloning the bundle-only public repository, extract it to any drive and run:

```powershell
.\fdctl.cmd --help
.\fdctl.cmd apps detect
.\launch-analysis-terminal.cmd
```

Direct PowerShell usage also works:

```powershell
.\fdctl.ps1 --help
.\fdctl.ps1 license status
```

## Default storage behavior

The portable bundle stores case data beside the portable folder by default:

```text
.\workspace
```

Saved cases are stored under:

```text
.\workspace\cases\<case-id>
```

Runtime cases are stored under:

```text
.\workspace\runtime\<case-id>
```

### Override the case root

If you want to store forensic data on another drive:

```powershell
$env:FDCTL_DATA_ROOT="E:\DFIR_CASES"
.\fdctl.cmd apps detect
```

## Licensing

### Built-in trial

- starts after the user enters an email address
- valid for `3 days`
- only accepts Gmail addresses ending with `@gmail.com`
- bound to the first Gmail address that uses the tool on that device
- stored under `%LOCALAPPDATA%\FORENSICS_DISCORD\license`

That means one installed device only gets one free-trial Gmail identity. A second new Gmail address on the same device will be asked for a paid key instead of receiving another free trial.

### Owner-only access

The public client bundle does not contain any hard-coded owner master key.

- the owner should use a separately issued signed owner key kept outside the public bundle
- the owner key is generated only from the private source workspace
- the owner key is separate from customer-issued time-limited keys
- the public bundle only contains the public verification key, not the signing secret

### Activation after trial

Check status:

```powershell
.\fdctl.cmd license status
```

Activate by pasting a key:

```powershell
.\fdctl.cmd license activate --prompt
```

Or activate from a file:

```powershell
.\fdctl.cmd license activate --email user@gmail.com --key-file .\issued_30d.key
```

Activation succeeds only when the entered Gmail address matches the `issuedToEmail` value embedded in the signed key.
Issued keys are exported in grouped letters-only format, for example `ABCD-EFGH-JKLM-NPQR-...`.
Customer keys are issued for one Gmail address and one target device fingerprint.

### Guided activation in the terminal workflow

End users do not need to run the activation command manually if they use the guided launcher:

```powershell
.\launch-analysis-terminal.cmd
```

When the built-in 3-day trial for that device Gmail has expired, the workflow will prompt for:

- licensed email address
- issued license key

If the email does not match the email identity encoded in the key, activation is rejected.

Deactivate the local activation:

```powershell
.\fdctl.cmd license deactivate
```

Supported issued license types:

- `issued_7d`
- `issued_30d`
- `issued_365d`

Private source workspaces can also issue an owner-only unlimited key for the registered owner account.

### Issuing a customer key for one device

End users should send the machine fingerprint shown in their activation request. Then issue the key from the private source workspace:

```powershell
.\fdctl.cmd license issue --email user@gmail.com --type issued_30d --machine "<fingerprint-from-user>" --out ".\user_30d.key"
```

End users can print their device name and machine fingerprint with:

```powershell
.\fdctl.cmd license machine
```

If `--out` is omitted, the key is stored automatically in:

```text
D:\ForensicWorkspace
```

## Core commands

Detect supported applications:

```powershell
.\fdctl.cmd apps detect
```

Create a new case:

```powershell
.\fdctl.cmd case create --app discord --id discord_case_001
```

Create a scoped case:

```powershell
.\fdctl.cmd case create --app discord --id discord_case_001 --channel-url "https://discord.gg/example" --target-user "mavanvo2472"
```

Collect artifacts:

```powershell
.\fdctl.cmd collect --case discord_case_001
```

Analyze a case:

```powershell
.\fdctl.cmd analyze --case discord_case_001
```

Run supplemental completeness checks:

```powershell
.\fdctl.cmd supplement --case discord_case_001
```

Build the report bundle:

```powershell
.\fdctl.cmd report build --case discord_case_001
```

Open a terminal summary of the report:

```powershell
.\fdctl.cmd report open --case discord_case_001
```

Save the case:

```powershell
.\fdctl.cmd case save --case discord_case_001
```

Discard the case:

```powershell
.\fdctl.cmd case discard --case discord_case_001
```

Run the guided investigation workflow:

```powershell
.\fdctl.cmd menu --app discord
```

Or launch the guided terminal directly:

```powershell
.\launch-analysis-terminal.cmd
```

## End-to-end example

```powershell
.\fdctl.cmd case create --app discord --id discord_case_demo --channel-url "https://discord.gg/example" --target-user "mavanvo2472"
.\fdctl.cmd collect --case discord_case_demo
.\fdctl.cmd analyze --case discord_case_demo
.\fdctl.cmd supplement --case discord_case_demo
.\fdctl.cmd report build --case discord_case_demo
.\fdctl.cmd report open --case discord_case_demo
.\fdctl.cmd case save --case discord_case_demo
```

## Report outputs

The report is written entirely inside the saved case.

Most important files:

- `08_Report\Muc_luc_bao_cao.md`
- `08_Report\Bien_ban_ban_giao.md`
- `08_Report\case_snapshot.json`
- `08_Report\validation_summary.json`

Other key evidence remains in:

- `07_Exports\*.csv`
- `05_Autopsy_Case\`
- `01_Case_Info\`

## Internal build workflow

Build the portable bundle from the private source workspace:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-package.ps1
```

Outputs:

```text
.\dist\FORENSICS_DISCORD
.\dist\github-release
.\dist\FORENSICS_DISCORD_portable.zip
```

## Notes

- Discord is the primary supported target.
- Zalo remains a placeholder in the current build.
- Firefox collection is not part of the active pipeline.
- `05_Autopsy_Case` is an Autopsy-ready export bundle, not a native Autopsy project database.
