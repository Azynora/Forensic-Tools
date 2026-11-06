# FORENSICS_DISCORD — English

A portable Windows 11 command-line DFIR tool for collecting and reviewing local Discord artifacts.

[Tiếng Việt](./README.vi.md) · [Main page](./README.md) · [Download Windows ZIP](https://github.com/Azynora/Forensic-Tools/releases/latest)

## Run the release

1. Download the latest ZIP from [GitHub Releases](https://github.com/Azynora/Forensic-Tools/releases/latest).
2. Extract it to a writable folder.
3. Run `launch-analysis-terminal.cmd`, or open PowerShell in that folder:

```powershell
.\fdctl.cmd --help
.\fdctl.cmd apps detect
```

Python is not required for the release bundle. Collection may require Administrator privileges. Cases are stored in the bundle's `workspace` folder by default.

## Run from source

Install Python 3.10+, clone the repository, then run from its root:

```powershell
git clone https://github.com/Azynora/Forensic-Tools.git
cd Forensic-Tools
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
.\fdctl.cmd --help
```

The public repository exposes its source code. The release ZIP is a convenient portable build; it does not hide source published in the repository. **Version: 1.1.9.**

See [USAGE_GUIDE.md](./USAGE_GUIDE.md) for the CLI investigation workflow.

## Create a case and report

```powershell
.\fdctl.cmd case create --app discord --id case_001
.\fdctl.cmd collect --case case_001
.\fdctl.cmd analyze --case case_001
.\fdctl.cmd report build --case case_001
.\fdctl.cmd case save --case case_001
```

## Scope and handling

Discord is the primary adapter. Zalo is a placeholder and Firefox is not currently supported by the collection pipeline. This tool supports triage; validate recovered findings against source artifacts. Collected data may include cookies or session data. Protect case folders and collect only with proper authorization.

The executable is distributed in a portable bundle with its required runtime. Packaging cannot guarantee absolute protection against extraction or reverse engineering.
