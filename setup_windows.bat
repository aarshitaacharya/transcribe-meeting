@echo off
setlocal enabledelayedexpansion

echo.
echo ================================================
echo   Meeting Transcriber -- Windows Setup
echo ================================================
echo.

REM ── Check Python ──────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    echo.
    echo   1. Go to https://python.org/downloads
    echo   2. Download Python 3.11 or later
    echo   3. During install: check "Add Python to PATH"
    echo   4. Re-run this script
    echo.
    pause
    exit /b 1
)
echo [OK] Python found
python --version

REM ── Check ffmpeg ──────────────────────────────────
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [WARNING] ffmpeg not found. Attempting install via winget...
    winget install ffmpeg
    if errorlevel 1 (
        echo.
        echo   Could not auto-install ffmpeg.
        echo   Manual install: https://ffmpeg.org/download.html
        echo   Add ffmpeg/bin to your PATH environment variable.
        echo.
    )
) else (
    echo [OK] ffmpeg found
)

REM ── Install Python packages ────────────────────────
echo.
echo [*] Installing Python packages (this may take a few minutes)...
pip install --quiet --upgrade pip
pip install --quiet openai-whisper sounddevice numpy

echo [OK] Packages installed

REM ── Check for VB-Cable ───────────────────────────
echo.
python -c "import sounddevice as sd; names=[d['name'] for d in sd.query_devices()]; found=[n for n in names if 'cable' in n.lower()]; print('[OK] VB-Cable found: ' + found[0]) if found else print('[WARNING] VB-Cable not detected. Install from https://vb-audio.com/Cable and restart your PC.')"

REM ── Create transcripts folder ────────────────────
if not exist "C:\Transcripts" mkdir "C:\Transcripts"
echo [OK] Transcripts folder: C:\Transcripts

REM ── Launch ───────────────────────────────────────
echo.
echo ================================================
echo   Starting Meeting Transcriber...
echo   Transcripts saved to: C:\Transcripts\
echo   Press Ctrl+C to stop
echo ================================================
echo.

python "%~dp0meeting_transcriber.py"

pause
