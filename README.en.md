# Forensics Suite — English

[![Author](https://img.shields.io/badge/Author-Trương%20Triệu%20Vỹ-blue?style=for-the-badge)](mailto:trieuvy9198@gmail.com)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge)](LICENSE_PROPRIETARY.md)
[![Design Reference](https://img.shields.io/badge/Reference-ISO%2FIEC%2027037-blue?style=for-the-badge)](#)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-brightgreen?style=for-the-badge)](#)

> Specialized digital forensics and incident response (DFIR) research toolkit for messaging applications on Windows.

```c
// When I wrote this code, only God and I understood what it did.
// Now, only God knows.
```

[Tiếng Việt](README.vi.md) · [Main Page](README.md) · [Usage Guide](USAGE_GUIDE.md)

---

## ⚡ Fast Download (Pre-built Executables)

The official compiled Windows release bundles Python, dependencies, and native machine-code libraries into standalone executables:

* 📦 **[Download latest Installer & Portable ZIP from GitHub Releases](https://github.com/Azynora/Forensic-Tools/releases/latest)**
  * `ForensicsSuite_Setup.exe` — Windows desktop installer with Start Menu integration.
  * `ForensicsSuite_portable.zip` — Standalone portable bundle for USB field triage (runs 100% offline without installation).

---

## 🛠️ Supported Applications & Forensic Capabilities

| Application | Support Level | Forensic Artifacts Acquired & Analyzed |
| :--- | :--- | :--- |
| **Discord Desktop** | **Supported** | LevelDB messages, user tokens, localStorage, cache, GPUCache, Chrome correlation, live TCP triage |
| **Telegram Desktop** | **Supported** | `tdata` session keys, maps, user_data media cache, voice notes, stickers, DC socket connections |
| **Zalo** | *Roadmap* | Architecture mapped; reserved for upcoming release pass |
| **WhatsApp / Signal** | *Roadmap* | Planned cross-platform triage modules |

### Key Technical Capabilities:
* **Designed with Reference to ISO/IEC 27037 Principles**: Non-invasive, zero-footprint live acquisition workflow with SHA-256 integrity verification hashes.
* **Target Window Screen Capture**: Isolates and captures only the target application window, eliminating desktop background privacy concerns.
* **Carved Media Gallery**: Automated contact sheet visual gallery with SHA-256 hashes and file sizes for media carved from local caches.
* **Autopsy-Compatible Evidence Export**: Generates structured case folders and standardized CSV schemas designed for ingest into Autopsy for in-depth lab examination.

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
3. **Enterprise Multi-Seat**: Domain-bound licensing with forensic report watermarking for law enforcement, SOC, and IR teams.

> **To obtain an official license key**:
> Contact author **Trương Triệu Vỹ** via:
> * 📧 **Email**: [trieuvy9198@gmail.com](mailto:trieuvy9198@gmail.com)
> * 💬 **Telegram**: [@azynora](https://t.me/azynora)
> * 🌐 **Facebook**: [facebook.com/azynora.vn](https://www.facebook.com/azynora.vn)

---

## ⚖️ Ownership, Copyright & Legal Notice

Copyright (c) 2026 **Trương Triệu Vỹ** (`Truong Trieu Vy`). All rights reserved.

* **Author & Copyright Owner**: Trương Triệu Vỹ (`Truong Trieu Vy`)
* **Email**: [trieuvy9198@gmail.com](mailto:trieuvy9198@gmail.com)
* **Telegram**: [@azynora](https://t.me/azynora)
* **Facebook**: [https://www.facebook.com/azynora.vn](https://www.facebook.com/azynora.vn)
* **License**: [LICENSE_PROPRIETARY.md](LICENSE_PROPRIETARY.md)
* **Terms of Use**: [EULA.md](EULA.md) · [COPYRIGHT_NOTICE.md](COPYRIGHT_NOTICE.md)

> ⚠️ **Legal Disclaimer & Limitations**:
> 1. This software is developed for research, educational, security testing, and authorized incident response (DFIR) purposes only.
> 2. Users bear full responsibility for complying with all applicable cybersecurity, data privacy, and criminal procedure laws in their jurisdiction.
> 3. The project makes no absolute claims regarding evidentiary completeness. Extracted artifacts should always be cross-validated against independent evidence sources.
