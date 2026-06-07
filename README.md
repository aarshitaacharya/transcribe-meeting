# Silent Meeting Transcriber

Automatically transcribes your Microsoft Teams meetings (and any other audio calls) without notifying other participants. No bots. No cloud uploads. Completely free, runs locally on your machine.

Transcripts are saved as plain `.txt` files you can paste into any AI (Claude, ChatGPT, etc.) for summaries, action items, or notes.

---

## How it works

```
You join a Teams meeting
        ↓
Virtual audio driver captures system audio silently
        ↓
Script detects sound → starts recording automatically
        ↓
Meeting goes silent for 60s → recording stops
        ↓
Whisper (local AI) transcribes the audio
        ↓
transcript_2026-06-07_14-30-00.txt saved to ~/Transcripts/
```

**Nothing is sent to any server.** Whisper runs entirely on your machine.

---

## What you need

| Tool | Purpose | Cost |
|------|---------|------|
| BlackHole (Mac) / VB-Cable (Windows) | Virtual audio driver — silently captures system audio | Free |
| OpenAI Whisper | Local speech-to-text AI | Free |
| Python 3 | Runs the script | Free |
| ffmpeg | Audio processing for Whisper | Free |

---

## Quick Start

### Mac

```bash
# 1. Run setup — installs everything and starts listening
chmod +x start_transcriber.sh
./start_transcriber.sh
```

### Windows

```cmd
# 1. Run setup script
setup_windows.bat
```

Then join your meeting. Ctrl+C to stop when done.

Transcripts land in `~/Transcripts/` (Mac) or `C:\Transcripts\` (Windows).

---

## Mac — Full Setup

### Step 1 — Install Homebrew (if not already installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2 — Install BlackHole (virtual audio driver)

```bash
brew install blackhole-2ch
```

**Restart your Mac after this step.** BlackHole won't appear until you do.

### Step 3 — Set up Multi-Output Device (so you still hear the meeting)

1. Open **Audio MIDI Setup** (search in Spotlight)
2. Click **+** at the bottom left → **Create Multi-Output Device**
3. In the device list on the right, check:
   -  **BlackHole 2ch**
   -  **MacBook Pro Speakers** (or your headphones)
4. Leave everything else unchecked

> **If you use headphones:** plug them in first, then they'll appear in the list. Check your headphones instead of MacBook Pro Speakers.

### Step 4 — Set system audio output

1. Go to **System Settings → Sound → Output**
2. Select **Multi-Output Device**

> Do this every time before a meeting, or set it as default. You can create a keyboard shortcut via the menu bar volume icon (hold Option and click it).

### Step 5 — Run the transcriber

```bash
chmod +x start_transcriber.sh
./start_transcriber.sh
```

The first run downloads the Whisper model (~150MB for `base`). Subsequent runs start in seconds.

### Step 6 — Join your meeting

The script listens silently. When it hears audio:

```
Meeting detected at 2:30 PM — recording started
```

When it detects 60 seconds of silence:

```
Meeting ended — 3420s recorded
Transcribing: meeting_2026-06-07_14-30-00.wav ...
Transcript saved: ~/Transcripts/transcript_2026-06-07_14-30-00.txt
```

### Step 7 — Stop when done

Press `Ctrl+C`. Any active recording will be saved and transcribed before exiting.

### Optional — Auto-start on login

If you want the transcriber always running in the background without opening a terminal:

```bash
# Edit the plist with your actual path
sed -i '' "s|REPLACE_WITH_FULL_PATH|$HOME/MeetingTranscriber|g" \
  com.user.meeting-transcriber.plist

# Install as a login item
cp com.user.meeting-transcriber.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.user.meeting-transcriber.plist
```

To stop the auto-start:

```bash
launchctl unload ~/Library/LaunchAgents/com.user.meeting-transcriber.plist
```

Logs are at `/tmp/meeting_transcriber.log`.

---

## Windows — Full Setup

### Step 1 — Install VB-Cable (virtual audio driver)

1. Go to [vb-audio.com/Cable](https://vb-audio.com/Cable/)
2. Download **VBCABLE_Driver_Pack43.zip**
3. Extract it, right-click `VBCABLE_Setup_x64.exe` → **Run as Administrator**
4. Click Install Driver, then **Restart your PC**

### Step 2 — Set up audio routing (so you still hear the meeting)

1. Right-click the speaker icon in the taskbar → **Sound settings**
2. Under **Output**, set to **CABLE Input (VB-Audio Virtual Cable)**
3. Open **Sound Control Panel** (search in Start)
4. Go to **Recording** tab → right-click **CABLE Output** → **Properties**
5. Go to **Listen** tab → check **Listen to this device** → set playback to your speakers/headphones
6. Click OK

> This routes audio through VB-Cable while still playing it to your speakers.

### Step 3 — Install Python

1. Go to [python.org/downloads](https://python.org/downloads)
2. Download Python 3.11 or later
3. **Important:** During install, check **"Add Python to PATH"**

### Step 4 — Install ffmpeg

```cmd
# Option A — with winget (Windows 10/11)
winget install ffmpeg

# Option B — manual
# Download from https://ffmpeg.org/download.html
# Extract, add the bin/ folder to your PATH environment variable
```

### Step 5 — Install Python packages

Open Command Prompt or PowerShell:

```cmd
pip install openai-whisper sounddevice numpy
```

### Step 6 — Edit the script for Windows

Open `meeting_transcriber.py` in Notepad and change line 22:

```python
# Change this:
BLACKHOLE_DEVICE_NAME = "BlackHole 2ch"

# To this:
BLACKHOLE_DEVICE_NAME = "CABLE Output"
```

And change the transcripts path (line 28):

```python
# Change this:
TRANSCRIPTS_DIR = Path.home() / "Transcripts"

# To this (or wherever you want):
TRANSCRIPTS_DIR = Path("C:/Transcripts")
```

### Step 7 — Run the transcriber

```cmd
python meeting_transcriber.py
```

Or double-click `setup_windows.bat` (first run installs everything, subsequent runs just start).

### Optional — Auto-start on Windows login

1. Press `Win + R` → type `shell:startup` → Enter
2. Create a shortcut to `meeting_transcriber.py` in that folder
3. Or create a `.bat` file:

```bat
@echo off
python C:\path\to\meeting_transcriber.py
```

And place it in the Startup folder.

---

## Configuration

All settings are at the top of `meeting_transcriber.py`:

```python
SILENCE_TIMEOUT       = 60      # seconds of silence before stopping
SILENCE_THRESHOLD     = 0.005   # sensitivity (lower = more sensitive)
MIN_RECORDING_SECONDS = 10      # ignore recordings shorter than this
WHISPER_MODEL         = "base"  # accuracy vs speed tradeoff (see below)
TRANSCRIPTS_DIR       = ...     # where transcripts are saved
```

### Whisper model options

| Model | Size | Speed | Accuracy | Recommended for |
|-------|------|-------|----------|-----------------|
| `tiny` | 75MB | Fastest | Good | Quick meetings, fast laptop |
| `base` | 150MB | Fast | Better | **Default — good balance** |
| `small` | 500MB | Medium | Great | Longer meetings, accents |
| `medium` | 1.5GB | Slow | Excellent | Max accuracy, powerful machine |

Change `WHISPER_MODEL = "base"` to whichever you prefer.

---

## Troubleshooting

**BlackHole / CABLE Output not found**
```
Run the script — it will print all available input devices.
Make sure you restarted after installing the driver.
```

**No transcript after meeting**
```
Check that your system audio output is set to the Multi-Output Device (Mac)
or CABLE Input (Windows) — not your regular speakers.
Open System Settings → Sound → Output to verify.
```

**Transcript cuts off early**
```
Increase SILENCE_TIMEOUT in meeting_transcriber.py.
Default is 60 seconds — try 120 if your meetings have long pauses.
```

**Poor transcription accuracy**
```
Switch to a larger Whisper model: WHISPER_MODEL = "small" or "medium"
Make sure your microphone isn't muted in Teams (your own voice is captured too)
```

**Script says "Recording too short, discarding"**
```
The meeting was under 10 seconds of detected audio.
This is normal for short test sounds — join an actual meeting.
```

---

## Privacy

- All processing is local — no audio or transcripts leave your machine
- Whisper model runs fully offline after the initial download
- Transcripts are stored only in `~/Transcripts/` (or `C:\Transcripts\`)
- No meeting participants are notified (no bot joins the call)

---

## Files

```
meeting_transcriber.py              ← main script
start_transcriber.sh                ← Mac: setup + launch
com.user.meeting-transcriber.plist  ← Mac: auto-start on login (optional)
README.md                           ← this file
```

---

## License

MIT — free to use, modify, and distribute.