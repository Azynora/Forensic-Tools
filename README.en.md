# Forensics Suite — English

An extensible Windows workspace for digital forensics across messaging applications.

[Tiếng Việt](README.vi.md) · [Main page](README.md)

## Download

[Download the latest installer or portable ZIP from GitHub Releases](https://github.com/Azynora/Forensic-Tools/releases/latest).

Run `ForensicsSuite_Setup.exe`, then launch Forensics Suite from the Start menu. Python and required libraries are bundled.

## Run from source

```powershell
git clone https://github.com/Azynora/Forensic-Tools.git
cd Forensic-Tools
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
.\fdctl.cmd menu
```

The source checkout opens the CLI menu. The GUI installer is for Windows users who prefer a desktop app.

## Applications and demo

- Discord collection, analysis, case reporting, and Autopsy export are currently available.
- Zalo, Telegram, WhatsApp, Messenger, and Signal are planned integrations. Selecting an unavailable app explains its status and returns to Discord.
- The Demo page includes a fictional case with a timeline, synthetic accounts, illustrative files, and a report summary. All content is generated; the demo does not read user data or create evidence.
- Choose a workspace folder in Settings. The default is `Documents\Forensics Suite`.

This personal project is maintained by one owner. Full collection access uses a device-bound signed license issued manually; there is no online store or payment backend.

## Ownership and data

The source and release are proprietary. Case data can contain sensitive session artifacts, so use the tool only with authorization and protect the selected workspace.

**Owner:** Truong Trieu Vy · [trieuvy9198@gmail.com](mailto:trieuvy9198@gmail.com)
