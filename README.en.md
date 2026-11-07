# Forensics Suite — English

[![Author](https://img.shields.io/badge/Author-Trương%20Triệu%20Vỹ-blue?style=for-the-badge)](mailto:trieuvy9198@gmail.com)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge)](LICENSE_PROPRIETARY.md)
[![Design Reference](https://img.shields.io/badge/Reference-ISO%2FIEC%2027037-blue?style=for-the-badge)](#)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-brightgreen?style=for-the-badge)](#)

> Specialized digital forensics and incident response (DFIR) research toolkit for messaging applications across Windows and Linux.

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

Developers and security researchers can run the CLI terminal workflow from source on Windows or Linux:

### 1. On Windows:
```powershell
git clone https://github.com/Azynora/Forensic-Tools.git
cd Forensic-Tools
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# Launch interactive CLI menu
.\fdctl.cmd menu

# Or execute direct investigation commands:
.\fdctl.cmd case create --app telegram --id case_tele_01
.\fdctl.cmd collect --case case_tele_01
.\fdctl.cmd report build --case case_tele_01
```

### 2. On Linux (Ubuntu, Debian, Fedora, Arch, Kali Linux):
```bash
git clone https://github.com/Azynora/Forensic-Tools.git
cd Forensic-Tools
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Make executable and launch menu:
chmod +x fdctl fdctl.sh
./fdctl menu

# Or execute direct commands:
./fdctl apps detect
./fdctl case create --app discord --id case_discord_01
./fdctl collect --case case_discord_01
./fdctl report build --case case_discord_01
```

> For step-by-step guidance and complete command documentation, see [📖 USAGE_GUIDE.md](USAGE_GUIDE.md).

*(Source code runs the cross-platform CLI terminal interface. Compiled GUI releases are distributed exclusively via GitHub Releases).*

---

## 🔑 Licensing & Architecture Integrity

Forensics Suite utilizes asymmetric Ed25519 digital cryptography for tamper-resistant licensing:

1. **Trial License (7 Days)**: Bundled with simulated demo cases for zero-risk workflow evaluation.
2. **Portable USB License (Recommended)**: Drop the `license.key` file onto a USB drive; executes offline on target machines without hardware locking.
3. **Enterprise License**: Cryptographically signed against corporate domains with institutional watermarking on generated evidence reports.

> **Licensing Inquiries**:
> Contact the author directly:
> * 📧 **Email**: [trieuvy9198@gmail.com](mailto:trieuvy9198@gmail.com)
> * 💬 **Telegram**: [@azynora](https://t.me/azynora)
> * 🌐 **Facebook**: [facebook.com/azynora.vn](https://www.facebook.com/azynora.vn)

---

## ⚖️ Intellectual Property & Legal Notice

Copyright (c) 2026 **Trương Triệu Vỹ** (`Truong Trieu Vy`). All rights reserved.

* **Owner & Author**: **Trương Triệu Vỹ** (`Truong Trieu Vy`)
* **Email**: [trieuvy9198@gmail.com](mailto:trieuvy9198@gmail.com)
* **Telegram**: [@azynora](https://t.me/azynora)
* **Facebook**: [https://www.facebook.com/azynora.vn](https://www.facebook.com/azynora.vn)
* **License Agreement**: [LICENSE_PROPRIETARY.md](LICENSE_PROPRIETARY.md)
* **User Terms**: [EULA.md](EULA.md) · [COPYRIGHT_NOTICE.md](COPYRIGHT_NOTICE.md)

> ⚠️ **Legal Disclaimer & Limitations of Liability**:
> 1. This software is developed strictly for scientific research, academic education, authorized cybersecurity testing, and legitimate DFIR workflows.
> 2. Users bear full legal responsibility for operating this tool on target systems in compliance with applicable cybersecurity, privacy, and penal procedural legislation.
> 3. In accordance with consumer protection and advertising standards, no superlative or absolute claims are asserted. All forensic findings should be corroborated with independent evidence before drawing legal conclusions.
