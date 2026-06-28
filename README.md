// When I wrote this code, only god & I understood what it did.
// Now,....only god knows.
// I have no idea why it works...

# FORENSICS_DISCORD

`FORENSICS_DISCORD` is a terminal-first Windows 11 forensic toolkit for Discord-focused DFIR collection, analysis, and case packaging.

The active product shape is a **portable CLI bundle**. It is designed to run from `cmd` or PowerShell without a GUI launcher, without a frontend web report, and without a Windows installer.

## Core workflow

- collect Discord-related artifacts from a live Windows workstation
- normalize evidence into the standard `01` through `08` case structure
- analyze browser artifacts, recovered messages, timeline data, and scoped indicators
- generate terminal-readable report outputs plus Markdown/JSON/CSV artifacts inside the saved case
- produce an Autopsy-ready export bundle under `05_Autopsy_Case`

## Case structure

Every case keeps the same canonical folders:

```text
01_Case_Info
02_Live_Response
03_Acquired_Files
04_Browser_Artifacts
05_Autopsy_Case
06_Screenshots
07_Exports
08_Report
```

## Distribution model

### Private source workspace

The source workspace is used only to develop, verify, and build the portable bundle.

### Public bundle release

The public GitHub release should contain only the portable runnable bundle and documentation:

- `fdctl.cmd`
- `fdctl.ps1`
- `launch-analysis-terminal.cmd`
- `activate-license.cmd`
- `fdctl_runtime\`
- `README.md`
- `USAGE_GUIDE.md`
- `COPYRIGHT_NOTICE.md`
- `CHANGELOG_version.md`
- `LICENSE_PROPRIETARY.md`
- `EULA.md`
- `BUILD_PROVENANCE.json`
- `SHA256SUMS.txt`

No Python source, frontend source, build script, or signing material should be published in the public release channel.

## Quick start

### Source mode

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
cd backend
python -m pip install -e .
cd ..
.\launch-analysis-terminal.cmd
```

### Portable bundle mode

Extract or clone the portable release to any drive, then run:

```powershell
.\fdctl.cmd --help
.\launch-analysis-terminal.cmd
```

The default portable workspace is stored beside the bundle:

```text
.\workspace
```

To store case data elsewhere:

```powershell
$env:FDCTL_DATA_ROOT="D:\FORENSICS_CASES"
.\fdctl.cmd apps detect
```

## Licensing

- the public bundle only accepts Gmail addresses ending with `@gmail.com`
- Gmail identities are canonicalized before matching, so dotted and plus-tag variants such as `abc.def@gmail.com` and `abcdef+case@gmail.com` resolve to the same inbox identity
- the public bundle starts with a `3-day` trial for the first Gmail address used on that device
- trial state is stored under `%LOCALAPPDATA%\FORENSICS_DISCORD\license`
- the bundle stores local masked email/license history so returning users can re-enter only their Gmail address when a valid local activation or trial already exists
- the user must enter both an email address and a license key prompt in the tool workflow
- a blank key only works when that Gmail address still has a valid local trial on the current device
- after trial expiry, the user must activate a signed key issued by the owner
- the public client bundle does not embed any owner master key or private signing secret
- owner-only access should use a separately issued signed owner key that stays outside the public bundle
- activation requires both the issued email address and the matching signed key
- an issued key only works for the Gmail address encoded inside that key
- issued customer keys are intended for `1 email + 1 device fingerprint`
- issued keys are rendered in grouped letters-only format such as `ABCD-EFGH-JKLM-NPQR-...`
- issued customer keys are stored under `D:\ForensicWorkspace` by default when `--out` is omitted
- end users can show their device fingerprint with `.\fdctl.cmd license machine`

Supported issued license types:

- `issued_7d`
- `issued_30d`
- `issued_365d`

## Reporting behavior

`report build` writes report artifacts into `08_Report`.

`report open` no longer launches a GUI or web viewer. It prints a terminal summary and the canonical report paths, including:

- `08_Report\Muc_luc_bao_cao.md`
- `08_Report\Bien_ban_ban_giao.md`
- `08_Report\case_snapshot.json`

## GitHub release strategy

- keep the real source repository private
- publish bundle-only outputs to the public GitHub repository
- publish each release as a versioned zip in GitHub Releases
- keep older versions downloadable through Releases so users can choose a compatible bundle

## Version snapshot

| Component | Version |
|---|---:|
| Operator release | `1.1.8` |
| Python package `fdctl` | `0.2.8` |
| Trial model | `3 days / first Gmail on one device` |
| Windows target | `11` |

## Owner

- Owner: `Truong Trieu Vy`
- Contact: `trieuvy9198@gmail.com`
- Copyright: [COPYRIGHT_NOTICE.md](./COPYRIGHT_NOTICE.md)
