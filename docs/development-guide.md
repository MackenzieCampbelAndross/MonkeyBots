# MonkeyBots Development & Toolchain Guide

This guide describes how to configure, develop, test, and run MonkeyBots locally on Windows 11, Linux, and macOS.

---

## 1. Prerequisites

Verify installed tools on your system:
- **Python**: 3.11.x (64-bit)
- **Node.js**: v20+ or v22+
- **Rust & Cargo**: 1.77+ (1.92+ verified)
- **Git**: 2.40+

---

## 2. Python Backend & Simulation Environment Setup

### 2.1 Create and Activate Virtual Environment

```powershell
# Navigate to repository root
cd d:\Mac\project\MonkeyBots

# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Upgrade packaging tools
python -m pip install --upgrade pip setuptools wheel
```

### 2.2 Install Dependencies

```powershell
# Install core simulation dependencies
pip install -r requirements.txt

# Install development & testing tools
pip install -r requirements-dev.txt
```

### 2.3 Verify MuJoCo and Simulation Core

```powershell
python -c "import mujoco, numpy, scipy, fastapi, open3d; print('All core modules imported successfully! MuJoCo version:', mujoco.__version__)"
```

---

## 3. Running the Backend Service

```powershell
# Run the FastAPI / WebSocket simulation gateway
uvicorn server.monkeybots_server.main:app --host 127.0.0.1 --port 8765 --reload
```

Interactive API documentation will be accessible at:
- Swagger UI: `http://127.0.0.1:8765/docs`
- Redoc: `http://127.0.0.1:8765/redoc`

---

## 4. Running the Desktop Application (Tauri + React)

```powershell
# Navigate to the app directory
cd app

# Install Node dependencies
npm install

# Run frontend in browser development mode
npm run dev

# Run full native Tauri desktop application
cargo tauri dev
```

---

## 5. Running Automated Tests

```powershell
# Run unit tests
pytest tests/unit -v

# Run integration tests
pytest tests/integration -v
```
