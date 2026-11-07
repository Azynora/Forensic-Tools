# Forensics Suite

[![Author](https://img.shields.io/badge/Author-Trương%20Triệu%20Vỹ-blue?style=for-the-badge)](mailto:trieuvy9198@gmail.com)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge)](LICENSE_PROPRIETARY.md)
[![Standard](https://img.shields.io/badge/Standard-ISO%2FIEC%2027037-orange?style=for-the-badge)](#forensic-integrity--iso-27037)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-brightgreen?style=for-the-badge)](#)

> An extensible, enterprise-grade Windows workspace for digital forensics and live incident response across messaging applications.

```c
// When I wrote this code, only God and I understood what it did.
// Now, only God knows.
```

[Tiếng Việt](README.vi.md) · [English](README.en.md) · [Documentation & Usage](USAGE_GUIDE.md)

---

## ⚡ Quick Download (Ready to Run)

The official compiled Windows release bundles Python, dependencies, and native machine-code libraries into standalone executables:

* 📦 **[Download latest Installer & Portable ZIP from GitHub Releases](https://github.com/Azynora/Forensic-Tools/releases/latest)**
  * `ForensicsSuite_Setup.exe` — Windows desktop installer with Start Menu integration.
  * `ForensicsSuite_portable.zip` — Standalone portable bundle for USB field triage (runs 100% offline without installation).

---

## 🛠️ Supported Applications & Forensic Capabilities

| Application | Support Level | Forensic Artifacts Acquired & Analyzed |
| :--- | :--- | :--- |
| **Discord Desktop** | **Full Production** | LevelDB messages, user tokens, localStorage, cache, GPUCache, Chrome correlation, live TCP triage |
| **Telegram Desktop** | **Full Production** | `tdata` session keys, maps, user_data media cache, voice notes, stickers, DC socket connections |
| **Zalo** | *Roadmap* | Architecture mapped; reserved for upcoming release pass |
| **WhatsApp / Signal** | *Roadmap* | Planned cross-platform triage modules |

### Key Architectural Capabilities:
* **ISO/IEC 27037:2012 Compliance**: Non-invasive, zero-footprint live acquisition ensuring digital evidence integrity.
* **Target Window Screen Capture**: Isolates and captures only the target application window, eliminating desktop background privacy concerns.
* **Carved Media Evidence Gallery**: Automated contact sheet visual gallery with SHA-256 hashes and file sizes for media carved from encrypted caches.
* **Autopsy Ingest Ready**: Generates Autopsy-compatible CSV schemas and structured case folders for court presentation.

---

## 💻 Run from Source (CLI Terminal)

Developers and security researchers can run the CLI terminal workflow from source:

```powershell
git clone https://github.com/Azynora/Forensic-Tools.git
cd Forensic-Tools
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# Launch interactive CLI menu
.\fdctl.cmd menu

# Or execute direct investigation commands:
# 1. Telegram acquisition:
.\fdctl.cmd case create --app telegram --id case_tele_01
.\fdctl.cmd collect --case case_tele_01
.\fdctl.cmd report build --case case_tele_01

# 2. Discord acquisition:
.\fdctl.cmd case create --app discord --id case_discord_01
.\fdctl.cmd collect --case case_discord_01
.\fdctl.cmd report build --case case_discord_01
```

> For exhaustive step-by-step commands and workflows, consult [📖 USAGE_GUIDE.md](USAGE_GUIDE.md).

*(Source execution provides the interactive CLI terminal workflow. Compiled standalone desktop binaries are distributed via GitHub Releases).*

---

## 🔑 Licensing & Deployment Models

Forensics Suite utilizes cryptographic Ed25519 asymmetric verification for software licensing:

1. **Free Community Trial**: 7-day built-in synthetic evaluation mode with populated timeline and demo cases.
2. **Portable USB / Field Triage (Recommended)**: Drop-in `license.key` placed directly on a triage USB drive. Runs 100% offline on any suspect PC without machine locking or leaving traces.
3. **Enterprise Multi-Seat**: Domain-bound licensing (`@company.com`) with forensic report watermarking for law enforcement, SOC, and IR teams.

> **To obtain an official license key**:
> Contact author **Trương Triệu Vỹ** via email: [trieuvy9198@gmail.com](mailto:trieuvy9198@gmail.com).

---

## ⚖️ Ownership, Copyright & Legal Notice

Copyright (c) 2026 **Trương Triệu Vỹ** (`Truong Trieu Vy`). All rights reserved.

* **Author & Copyright Owner**: Trương Triệu Vỹ
* **Email**: [trieuvy9198@gmail.com](mailto:trieuvy9198@gmail.com)
* **License**: [LICENSE_PROPRIETARY.md](LICENSE_PROPRIETARY.md)
* **Terms of Use**: [EULA.md](EULA.md) · [COPYRIGHT_NOTICE.md](COPYRIGHT_NOTICE.md)

*This software is proprietary. Digital evidence and case data contain sensitive user artifacts. Use this toolkit only with proper legal authorization and protect all acquired case workspaces in compliance with applicable law.*
