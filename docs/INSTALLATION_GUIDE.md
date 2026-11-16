# MonkeyBots | Desktop Installation & Setup Guide

**Version:** 1.0.0 (Production Desktop Release)  
**Target Operating System:** Windows 10 / 11 (64-bit)  
**Execution Mode:** 100% Local-First & Air-Gapped (Zero Cloud Dependency)

---

## 1. System Requirements

### Minimum Specifications:
- **Operating System:** Windows 10 (Build 19041+) or Windows 11 (64-bit)
- **CPU:** Dual-core x86_64 processor (Intel Core i3 / AMD Ryzen 3 or higher)
- **RAM:** 4 GB system memory
- **Storage:** 1.5 GB available local disk space
- **Graphics:** Direct3D 11 / WebGL 2.0 compatible GPU (for Three.js digital twin viewport)
- **Network:** None required. Operates completely offline.

### Recommended Engineering Workstation:
- **CPU:** Quad-core 3.0+ GHz x86_64 processor
- **RAM:** 8 GB+ system memory
- **GPU:** Dedicated NVIDIA or AMD GPU with hardware WebGL acceleration
- **Display:** 1920 × 1080 (Full HD) or higher resolution

---

## 2. Software Prerequisites

MonkeyBots executes completely on the local workstation. It requires:

1. **Python Runtime (Version 3.10, 3.11, or 3.12)**
   - Download official Windows installer from: [https://www.python.org/downloads/](https://www.python.org/downloads/)
   - *Important:* Ensure **"Add Python to PATH"** is checked during installation.
2. **Microsoft Visual C++ Redistributable (2015–2022)**
   - Required by the native MuJoCo physics library C++ binaries.
   - Pre-installed on most modern Windows systems.

---

## 3. Quick-Start Desktop Installation

### Option A: Standard Automated Launcher (Recommended)
1. Clone or extract the MonkeyBots repository to your desired directory (e.g., `D:\MonkeyBots`):
   ```powershell
   git clone https://github.com/MackenzieCampbelAndross/MonkeyBots.git
   cd MonkeyBots
   ```
2. Double-click **`start_monkeybots.bat`** (or execute `.\start_monkeybots.ps1` in PowerShell).
3. The launcher automatically:
   - Verifies the Python runtime and dependencies.
   - Installs any missing packages into the local environment (`pip install -r requirements.txt`).
   - Starts the headless Python simulation daemon on loopback port `127.0.0.1:8765`.
   - Launches the native Windows desktop application window.

### Option B: Manual Environment Setup
If installing inside an isolated Python virtual environment:
```powershell
# 1. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install core robotics engine dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Launch backend simulation server
python -m uvicorn server.monkeybots_server.main:app --host 127.0.0.1 --port 8765

# 4. In a second terminal, build and run the frontend desktop application
cd app
npm install
npm run build
npm run preview
```

---

## 4. Verifying Installation Integrity

Run the automated system diagnostics probe to verify hardware and software readiness:
```powershell
python -c "from core.monkeybots.diagnostics import run_system_diagnostics; report = run_system_diagnostics(); print('Status:', report.overall_status); [print(f' - [{c.status}] {c.name}: {c.message}') for c in report.checks]"
```

Expected diagnostic output:
```
Status: HEALTHY
 - [PASS] Python Engine: Python 3.11.x (64bit) meets required specifications (>= 3.10).
 - [PASS] MuJoCo Engine & Bindings: MuJoCo native C library verified and operational.
 - [PASS] Host Memory (RAM): Headroom verified for 500 Hz simulation stepping.
 - [PASS] Local Project Storage Write Permissions: Verified read/write access.
 - [PASS] Local-First Offline Operation: 100% offline verified: Zero cloud databases.
```

---

## 5. Security & Air-Gap Compliance

MonkeyBots was engineered from the ground up for proprietary robotics R&D:
- **No Outbound Traffic:** No telemetry, usage statistics, or user tracking is collected.
- **Local Loopback Communication:** Frontend and backend communicate strictly via `127.0.0.1` (TCP port `8765`).
- **Filesystem Isolation:** All models, CAD meshes, simulation logs, and reports reside in local project folders (`./projects/`).
