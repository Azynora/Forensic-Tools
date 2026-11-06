# FORENSICS_DISCORD

Windows app for Discord forensic collection, analysis and case reporting.

[Tiếng Việt](README.vi.md) · [English](README.en.md)

## Download

[Download the latest Windows Setup or ZIP from GitHub Releases](https://github.com/Azynora/Forensic-Tools/releases/latest).

Run `FORENSICS_DISCORD_Setup.exe` and open the app from the Start menu. The installer bundles Python and required libraries. No Python installation or pip command is needed.

## Run from source (CLI)

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
- In-app synthetic demo labeled `SAMPLE`; it does not read real Discord or Chrome data.
- Zalo is under development. Selecting it returns to Discord selection.
- Select a workspace folder in app Settings; default is Documents.

The local 7-day trial enables the synthetic demo only. Paid access uses a device-bound signed license key issued by the owner. This personal project does not use an online store or payment backend.

## Project and handling

The public repository contains source code. The installer packages the Python runtime and dependencies for easier use; packaging cannot guarantee absolute protection against reverse engineering. Use the tool only with authorization. Case data may contain sensitive session artifacts.

**Owner:** Truong Trieu Vy · [trieuvy9198@gmail.com](mailto:trieuvy9198@gmail.com)

**Release:** 1.2.0
