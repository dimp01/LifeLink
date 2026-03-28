@echo off
title LifeLink AI - Launcher
color 0A

echo.
echo  =====================================================
echo    LifeLink AI - One-Click Launcher
echo  =====================================================
echo.

REM ── Check Python ──────────────────────────────────────
where python >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Please install Python 3.10+
    echo          https://www.python.org/downloads/
    pause
    exit /b 1
)
echo  [OK] Python found

REM ── Check Node.js ─────────────────────────────────────
where node >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Node.js not found. Please install Node.js 18+
    echo          https://nodejs.org/
    pause
    exit /b 1
)
echo  [OK] Node.js found

REM ── Check for backend .env ────────────────────────────
if not exist "backend\.env" (
    echo.
    echo  [WARNING] backend\.env not found!
    echo  Please create backend\.env with your DATABASE_URL and JWT_SECRET.
    echo  See README.md for the required format.
    echo.
    pause
    exit /b 1
)
echo  [OK] backend\.env found

REM ── Create virtual environment if needed ─────────────
if not exist ".venv\Scripts\activate.bat" (
    echo.
    echo  [SETUP] Creating Python virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo  [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo  [OK] Virtual environment created
)

REM ── Install Python dependencies ───────────────────────
echo.
echo  [SETUP] Installing / verifying Python dependencies...
call .venv\Scripts\activate.bat
pip install -r backend\requirements.txt --quiet
if errorlevel 1 (
    echo  [ERROR] pip install failed. Check backend\requirements.txt
    pause
    exit /b 1
)
echo  [OK] Python dependencies ready

REM ── Install Node.js dependencies ──────────────────────
echo.
if not exist "frontend\node_modules" (
    echo  [SETUP] Installing Node.js dependencies (first run)...
    cd frontend
    npm install
    if errorlevel 1 (
        echo  [ERROR] npm install failed.
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo  [OK] Node.js dependencies installed
) else (
    echo  [OK] Node.js dependencies already installed
)

REM ── Start Backend ─────────────────────────────────────
echo.
echo  [START] Launching FastAPI backend on http://localhost:8000 ...
start "LifeLink AI - Backend" cmd /k "cd /d %~dp0backend && ..\\.venv\Scripts\activate.bat && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM Give the backend a moment to start
timeout /t 2 /nobreak >nul

REM ── Start Frontend ────────────────────────────────────
echo  [START] Launching Vue frontend on http://localhost:5173 ...
start "LifeLink AI - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

REM ── Done ──────────────────────────────────────────────
echo.
echo  =====================================================
echo    Both servers are starting in separate windows.
echo.
echo    Frontend : http://localhost:5173
echo    Backend  : http://localhost:8000
echo    API Docs : http://localhost:8000/docs
echo  =====================================================
echo.
echo  Press any key to close this launcher window...
pause >nul
