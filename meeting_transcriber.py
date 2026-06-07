#!/usr/bin/env python3
"""
Meeting Transcriber — Auto-records from BlackHole virtual audio, transcribes with Whisper.
Runs silently in the background. No notifications sent to meeting participants.

Usage: python3 meeting_transcriber.py
"""

import sounddevice as sd
import numpy as np
import wave
import whisper
import os
import sys
import time
import threading
import signal
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────
#  CONFIG — edit these if needed
# ─────────────────────────────────────────────
BLACKHOLE_DEVICE_NAME = "BlackHole 2ch"   # name as it appears in Audio MIDI Setup
SAMPLE_RATE           = 48000             # BlackHole default
CHANNELS              = 2                 # stereo
CHUNK_SECONDS         = 0.5              # how often we check audio level
SILENCE_THRESHOLD     = 0.005            # RMS below this = silence
SILENCE_TIMEOUT       = 60              # seconds of silence before stopping recording
MIN_RECORDING_SECONDS = 10              # ignore recordings shorter than this
WHISPER_MODEL         = "base"           # tiny / base / small / medium / large
TRANSCRIPTS_DIR       = Path.home() / "Transcripts"
RECORDINGS_DIR        = Path.home() / "Transcripts" / ".recordings"  # temp audio files
# ─────────────────────────────────────────────

# Globals
recording        = False
audio_chunks     = []
silence_counter  = 0
stop_flag        = False
model            = None


def find_blackhole_device():
    """Find BlackHole device index from sounddevice list."""
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        if BLACKHOLE_DEVICE_NAME.lower() in d['name'].lower() and d['max_input_channels'] > 0:
            return i
    return None


def rms(data):
    """Root mean square of audio chunk — measures volume."""
    return np.sqrt(np.mean(data.astype(np.float32) ** 2))


def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def save_wav(chunks, filepath):
    """Save recorded chunks as a WAV file."""
    audio_data = np.concatenate(chunks, axis=0)
    audio_int16 = (audio_data * 32767).astype(np.int16)
    with wave.open(str(filepath), 'w') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_int16.tobytes())


def transcribe(wav_path, transcript_path):
    """Run Whisper on the WAV file and save transcript."""
    global model
    print(f"\nTranscribing: {wav_path.name} ...")

    if model is None:
        print(f"   Loading Whisper '{WHISPER_MODEL}' model (first time may take ~30s) ...")
        model = whisper.load_model(WHISPER_MODEL)

    result = model.transcribe(str(wav_path), fp16=False, language="en")
    text   = result["text"].strip()

    with open(transcript_path, "w") as f:
        f.write(f"Meeting Transcript\n")
        f.write(f"Date: {datetime.now().strftime('%B %d, %Y %I:%M %p')}\n")
        f.write(f"{'─' * 60}\n\n")
        f.write(text)
        f.write("\n")

    print(f"Transcript saved: {transcript_path}")
    print(f"   Words: {len(text.split())}")

    # Clean up temp WAV
    wav_path.unlink(missing_ok=True)


def finish_recording():
    """Called when silence timeout hits — save + transcribe."""
    global audio_chunks, recording

    if not audio_chunks:
        recording = False
        return

    duration = len(audio_chunks) * CHUNK_SECONDS
    if duration < MIN_RECORDING_SECONDS:
        print(f"   (Recording too short [{duration:.0f}s], discarding)")
        audio_chunks = []
        recording    = False
        return

    ts              = get_timestamp()
    wav_path        = RECORDINGS_DIR / f"meeting_{ts}.wav"
    transcript_path = TRANSCRIPTS_DIR / f"transcript_{ts}.txt"

    print(f"\n⏹  Meeting ended — {duration:.0f}s recorded")
    save_wav(audio_chunks, wav_path)
    audio_chunks = []
    recording    = False

    # Transcribe in background so we're back to listening fast
    t = threading.Thread(target=transcribe, args=(wav_path, transcript_path), daemon=True)
    t.start()


def audio_callback(indata, frames, time_info, status):
    """Called by sounddevice for each audio chunk."""
    global recording, audio_chunks, silence_counter

    if status:
        pass  # ignore overflow warnings silently

    volume = rms(indata)

    if not recording:
        # Listening for meeting to start
        if volume > SILENCE_THRESHOLD:
            recording       = True
            silence_counter = 0
            audio_chunks    = []
            ts              = datetime.now().strftime("%I:%M %p")
            print(f"\nMeeting detected at {ts} — recording started")
            audio_chunks.append(indata.copy())
    else:
        # Currently recording
        audio_chunks.append(indata.copy())

        if volume < SILENCE_THRESHOLD:
            silence_counter += 1
            silence_secs     = silence_counter * CHUNK_SECONDS
            # Show countdown in last 10 seconds
            if silence_secs >= SILENCE_TIMEOUT - 10:
                remaining = SILENCE_TIMEOUT - silence_secs
                print(f"\r   Silence: stopping in {remaining:.0f}s ...   ", end="", flush=True)
            if silence_counter >= (SILENCE_TIMEOUT / CHUNK_SECONDS):
                finish_recording()
        else:
            silence_counter = 0


def signal_handler(sig, frame):
    """Graceful shutdown on Ctrl+C."""
    global stop_flag
    print("\n\nStopping... (transcribing any active recording)")
    stop_flag = True
    if recording and audio_chunks:
        finish_recording()
    time.sleep(3)  # let transcription thread start
    sys.exit(0)


def main():
    global stop_flag

    # Setup dirs
    TRANSCRIPTS_DIR.mkdir(exist_ok=True)
    RECORDINGS_DIR.mkdir(exist_ok=True)

    print("=" * 55)
    print("  🎙  Meeting Transcriber")
    print("=" * 55)

    # Find BlackHole
    device_idx = find_blackhole_device()
    if device_idx is None:
        print(f"\nERROR: '{BLACKHOLE_DEVICE_NAME}' not found.")
        print("   Make sure BlackHole is installed and your Mac has been restarted.")
        print("\n   Available input devices:")
        for i, d in enumerate(sd.query_devices()):
            if d['max_input_channels'] > 0:
                print(f"   [{i}] {d['name']}")
        sys.exit(1)

    print(f"\nBlackHole found (device #{device_idx})")
    print(f"   Whisper model : {WHISPER_MODEL}")
    print(f"   Transcripts   : {TRANSCRIPTS_DIR}")
    print(f"   Silence cutoff: {SILENCE_TIMEOUT}s")
    print(f"\n👂 Listening for meetings... (Ctrl+C to stop)\n")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    chunk_size = int(SAMPLE_RATE * CHUNK_SECONDS)

    with sd.InputStream(
        device=device_idx,
        channels=CHANNELS,
        samplerate=SAMPLE_RATE,
        blocksize=chunk_size,
        dtype='float32',
        callback=audio_callback
    ):
        while not stop_flag:
            time.sleep(0.1)


if __name__ == "__main__":
    main()
