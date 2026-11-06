# FORENSICS_DISCORD — English

A Windows app for Discord forensic collection, analysis and case reporting.

[Tiếng Việt](README.vi.md) · [Main page](README.md)

## Download and install

[Download the latest Setup.exe or ZIP from GitHub Releases](https://github.com/Azynora/Forensic-Tools/releases/latest).

Run `FORENSICS_DISCORD_Setup.exe`, then launch the app from the Start menu. Python and required libraries are bundled; no Python or pip installation is needed.

## Run from source using the CLI

```powershell
git clone https://github.com/Azynora/Forensic-Tools.git
cd Forensic-Tools
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
.\fdctl.cmd menu
```

The source checkout opens the terminal menu. See [USAGE_GUIDE.md](USAGE_GUIDE.md) for CLI commands.

## Features

- Discord artifact collection, analysis, reports and Autopsy export.
- Synthetic demo labeled `SAMPLE`; it does not read real Discord or Chrome data.
- Zalo is under development. Selecting it returns to Discord selection.
- Choose a workspace in Settings; Documents is the default.

The local 7-day trial unlocks the synthetic demo only. Paid access uses a device-bound signed key issued manually by the owner. This personal project does not use an online store or payment backend.

## Source and data handling

The public repository contains the source code. The installer bundles Python/runtime for convenience, but cannot guarantee absolute protection against reverse engineering. Use only with authorization; case data may contain sensitive session artifacts.

**Owner:** Truong Trieu Vy · [trieuvy9198@gmail.com](mailto:trieuvy9198@gmail.com)

**Version:** 1.2.0
