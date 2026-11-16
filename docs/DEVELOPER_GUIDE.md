# MonkeyBots | Developer Onboarding & Contribution Guide

**Version:** 1.0.0 (Production Release)

---

## 1. Development Environment Setup

### Prerequisites
- **Python:** 3.10, 3.11, or 3.12 (64-bit)
- **Node.js:** 20.x or 22.x LTS
- **Rust Toolchain:** `rustc` and `cargo` 1.80+ (for Tauri desktop binary compilation)
- **Git**

### Clone Repository & Install Dependencies
```powershell
git clone https://github.com/MackenzieCampbelAndross/MonkeyBots.git
cd MonkeyBots

# 1. Setup Python Virtual Environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 2. Setup Node.js Frontend Dependencies
cd app
npm install
cd ..
```

---

## 2. Running in Development Mode

Run the backend and frontend concurrently in two terminals:

### Terminal 1: Python Simulation Backend
```powershell
python -m uvicorn server.monkeybots_server.main:app --host 127.0.0.1 --port 8765 --reload
```

### Terminal 2: Vite Development Server or Tauri Shell
```powershell
cd app
npm run dev
# Or launch the native Tauri desktop shell in development mode:
npm run tauri dev
```

---

## 3. Running the Test Suite

MonkeyBots maintains strict 100% test pass requirements across unit, integration, and robustness suites:

```powershell
# Run full automated test suite (109+ tests)
pytest tests/ -v

# Run only Stage 13 20-step End-to-End integration test
pytest tests/integration/test_end_to_end_workflow.py -v

# Run system robustness, memory leak, and stress tests
pytest tests/integration/test_system_robustness.py -v
```

---

## 4. Frontend Code Quality & Builds

```powershell
cd app
# Typecheck & Vite production build
npm run build

# Fast linter check
npm run lint
```
