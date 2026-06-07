#!/bin/bash
# Meeting Transcriber — Setup & Launch Script
# Run this once to install deps, then again anytime to start the transcriber.

set -e

echo ""
echo "================================================"
echo "  Meeting Transcriber — Setup"
echo "================================================"
echo ""

# ── 1. Check Homebrew ──────────────────────────────
if ! command -v brew &>/dev/null; then
  echo "Homebrew not found. Install it first:"
  echo '   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
  exit 1
fi
echo "Homebrew found"

# ── 2. ffmpeg ──────────────────────────────────────
if ! command -v ffmpeg &>/dev/null; then
  echo "Installing ffmpeg..."
  brew install ffmpeg
else
  echo "ffmpeg found"
fi

# ── 3. Python 3 ────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo "Installing Python 3..."
  brew install python
else
  echo "Python 3 found: $(python3 --version)"
fi

# ── 4. pip packages ────────────────────────────────
echo ""
echo "Installing Python packages..."
pip3 install --quiet --upgrade pip
pip3 install --quiet openai-whisper sounddevice numpy

echo "All packages installed"

# ── 5. Check BlackHole ─────────────────────────────
echo ""
python3 - <<'EOF'
import sounddevice as sd
devices = [d['name'] for d in sd.query_devices() if 'blackhole' in d['name'].lower()]
if devices:
    print(f"BlackHole found: {devices[0]}")
else:
    print("BlackHole 2ch not detected.")
    print("   If you just installed it, restart your Mac and run this script again.")
    print("   Install: brew install blackhole-2ch")
EOF

# ── 6. Create Transcripts folder ──────────────────
mkdir -p ~/Transcripts
echo "Transcripts folder: ~/Transcripts"

# ── 7. Launch ─────────────────────────────────────
echo ""
echo "================================================"
echo "  Starting Meeting Transcriber..."
echo "  Transcripts saved to: ~/Transcripts/"
echo "  Press Ctrl+C to stop"
echo "================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/meeting_transcriber.py"
