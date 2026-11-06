# Forensics Suite

An extensible Windows workspace for digital forensics across messaging applications.

[Tiếng Việt](README.vi.md) · [English](README.en.md)

## Download

[Download the latest installer or portable ZIP from GitHub Releases](https://github.com/Azynora/Forensic-Tools/releases/latest).

Run `ForensicsSuite_Setup.exe` and open Forensics Suite from the Start menu. Python and dependencies are bundled.

## Run from source

```powershell
git clone https://github.com/Azynora/Forensic-Tools.git
cd Forensic-Tools
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
.\fdctl.cmd menu
```

Source users get the CLI menu. The GUI installer is for Windows users who want a desktop app.

## Applications and demo

- Discord collection, analysis, case reports, and Autopsy export are currently available.
- Zalo, Telegram, WhatsApp, Messenger, and Signal are shown as planned integrations. Selecting an unavailable app explains its status and returns to Discord.
- The built-in Demo page contains a populated fictional case with a timeline, accounts, illustrative files, and a report summary. Every item is synthetic; the demo never reads user data or creates evidence.
- Choose a workspace folder in Settings. The default is `Documents\Forensics Suite`.

The project is maintained by one owner. Full collection access uses a device-bound signed license issued manually; there is no online store or payment backend.

## Ownership and data

The source and release are proprietary. Case data can contain sensitive session artifacts, so use the tool only with authorization and protect the selected workspace.

**Owner:** Truong Trieu Vy · [trieuvy9198@gmail.com](mailto:trieuvy9198@gmail.com)
