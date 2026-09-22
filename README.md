<div align="center">

# 📺 realtime-captions-system-audio

**Live subtitles for everything playing on your computer — no microphone, no cloud, no subscription.**

<p align="center">
  <img src="https://github.com/emidium-science/realtime-captions-system-audio/releases/download/dev/demo.gif" alt="realtime-captions-system-audio demo" width="800">
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.11%2B-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+"></a>
  <a href="https://github.com/openai/whisper"><img src="https://img.shields.io/badge/Powered%20by-Whisper-412991?style=for-the-badge&logo=openai&logoColor=white" alt="Powered by Whisper"></a>
  <img src="https://img.shields.io/badge/Platform-Windows%2011-0078d4?style=for-the-badge&logo=windows&logoColor=white" alt="Windows 11">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge" alt="MIT License"></a>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> ·
  <a href="#-features">Features</a> ·
  <a href="#-use-cases">Use Cases</a> ·
  <a href="#%EF%B8%8F-setup-wizard">Setup Wizard</a> ·
  <a href="#-model-selection-guide">Models</a> ·
  <a href="#-faq">FAQ</a> ·
  <a href="docs/architecture.md">Architecture</a>
</p>

</div>

---

Powered by [OpenAI Whisper](https://github.com/openai/whisper) via [RealtimeSTT](https://github.com/KoljaB/RealtimeSTT).
Captures whatever your computer plays through **WASAPI loopback** — meetings, videos, podcasts, calls — and shows live captions instantly. **Audio never leaves your machine.**

---

## ✨ Features

| Feature | Description |
|---|---|
| **Real-time captions** | Partial text updates as speech is detected, before the sentence is complete |
| **High-accuracy final text** | Stable Whisper transcription committed after each utterance |
| **System audio capture** | WASAPI loopback — no virtual cable, no microphone, no extra software |
| **Floating subtitle overlay** | Borderless always-on-top window over every app, click-through |
| **Full-screen terminal UI** | Rich display with live text, history, and resource panels |
| **GPU / CPU monitor** | Real-time CPU, RAM, GPU load and temperature |
| **Save to file** | Timestamped `.txt` transcripts written to `transcripts/` as you speak |
| **Interactive setup wizard** | Two-step guided setup: pick device, models, and options |
| **CUDA acceleration** | GPU-accelerated inference for ultra-low latency on NVIDIA cards |
| **100% offline** | Fully local after the one-time Whisper model download |

---

## 🎯 Use Cases

> **Not fluent in English yet?** This tool was built for you.

### 🌍 International remote work
Starting a job at a company where meetings happen in English — but you're still building fluency? Real-time captions let you read every word your colleagues say, in the moment, with zero delay. No rewinding, no asking people to repeat themselves.

### 🎓 Language learning
Captions reinforce listening comprehension by mapping sounds to words as you hear them. Watch English content and read along simultaneously — one of the most effective methods for accelerating fluency.

### 🔇 Noisy environments
Working from a busy café or open office? Missed audio translates directly to missed context. Captions keep you in sync even when conditions are poor.

### ♿ Accessibility
Always-on, offline captions for people with hearing difficulties — no account, no subscription, no data leaving your machine.

### 📝 Meeting transcription
Save a timestamped `.txt` transcript of every call, lecture, or video. Searchable, copy-pasteable, and ready for notes or summaries.

### 🎬 Foreign-language video
Watching a video or lecture in a second language without subtitles? Get instant captions without waiting for YouTube's auto-subtitle delay.

---

## 🚀 Quick Start

### Windows graphical installer

Double-click `install.bat`. It creates an isolated Python environment, installs
the dependencies, downloads the requested Icons8 icon and creates a **Realtime
Captions** desktop shortcut. Whisper models (`tiny.en`, `small.en`, and
`medium.en`) can then be downloaded and selected independently from the GUI.

The original terminal interface remains available with `python console.py`.

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** `pyaudiowpatch` is a specialized fork of PyAudio with WASAPI loopback support.
> Do **not** install plain `pyaudio` alongside it — they conflict.

### 2. Run

```bash
python main.py
```

The interactive wizard launches automatically. No config files, no flags — answer the prompts and start reading.

---

## 💻 Platform Support

| Platform | Status |
|---|---|
| **Windows 11** | ✅ Fully supported |
| macOS | 🚧 Not yet implemented |
| Linux | 🚧 Not yet implemented |

> Windows support uses WASAPI loopback, which is built into Windows audio drivers.
> macOS and Linux contributions are welcome.

---

## ⚙️ Setup Wizard

### Step 1 — Choose your audio device

Lists every active output device available for loopback capture:

```
┌───┬───────────────────────────┬───────────┬──────────┐
│ # │ Device                    │      Rate │ Channels │
├───┼───────────────────────────┼───────────┼──────────┤
│ 1 │ Headphones (Zone Vibe)    │ 48000 Hz  │        2 │
│ 2 │ Speakers (Realtek)        │ 48000 Hz  │        2 │
└───┴───────────────────────────┴───────────┴──────────┘
```

Use ↑ / ↓ arrow keys to select, then press **Enter**.

### Step 2 — Configure accuracy and display

| Option | What it controls |
|---|---|
| **Transcription model** | Final accuracy: `tiny.en` → `small.en` ★ → `medium.en` → `large-v2` |
| **Real-time preview model** | Live display speed: `tiny.en` ★ (recommended) |
| **Compute device** | CUDA (GPU, fast) or CPU (no GPU needed) |
| **Language** | English (faster) or auto-detect (multilingual) |
| **Resource monitor** | Show CPU / RAM / GPU panel in terminal |
| **Save to file** | Write transcript to `transcripts/` folder |
| **Caption overlay** | Show floating subtitle window over all apps |

---

## 🖥️ Terminal UI

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ● Listening  │  Headphones  │  model: small.en  │  Ctrl+C to stop
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
╭──── System  RTX 4070 ─────────────────────────────────╮
│  CPU  ████████░░░░  58.0%   RAM  ████░░░░  12/32 GB   │
│  GPU  ███████░░░░░  65.0%  61°C  VRAM  ████░░  5/8 GB │
╰───────────────────────────────────────────────────────╯
╭──── ◉  Live ──────────────────────────────────────────╮
│                                                       │
│   And this is what I wanted to show you today…       │  ← yellow
│                                                       │
╰───────────────────────────────────────────────────────╯
╭──── ≡  History ───────────────────────────────────────╮
│  14:23:01 │ Welcome everyone to today's session.      │
│  14:24:15 │ Let's start with a quick overview.        │
╰───────────────────────────────────────────────────────╯
```

Press **Ctrl+C** at any time to stop cleanly.

---

## 🪟 Caption Overlay

The optional floating overlay renders subtitles **on top of every application** — video calls, browsers, fullscreen apps — exactly like movie subtitles.

| Behaviour | Detail |
|---|---|
| Always on top | Floats above every window |
| Click-through | Mouse clicks reach the app behind it |
| Auto-hides | Invisible when silent, appears instantly on speech |
| Not in taskbar | Hidden from Alt+Tab and the taskbar |
| Position | Centred, 72 px above the Windows taskbar |

---

## 📊 Model Selection Guide

### Transcription model (final accuracy)

| Model | VRAM | Accuracy | Best for |
|---|---|---|---|
| `tiny.en` | ~1 GB | Good | Fast machines, casual use |
| `small.en` ★ | ~2 GB | Very good | **Recommended** — best balance |
| `medium.en` | ~5 GB | Excellent | High-stakes meetings |
| `large-v2` | ~10 GB | Best | Maximum accuracy |

### Real-time preview model

| Model | Latency | Best for |
|---|---|---|
| `tiny.en` ★ | Very low | **Recommended** for live display |
| `base.en` | Low | Slightly better live accuracy |
| `small.en` | Medium | Best quality live display |

`.en` models are English-only and faster than their multilingual equivalents.

---

## 💾 Saving Transcripts

When you enable **Save to file**, every completed sentence is written immediately to:

```
transcripts/transcript_YYYYMMDD_HHMMSS.txt
```

File format:

```
# Transcription started 2026-03-21 14:23:01
# Source : Headphones (Zone Vibe) [Loopback]
# Model  : small.en

[14:23:04] Welcome everyone to today's session.
[14:24:18] Let's start with a quick overview of the agenda.

# Transcription ended 2026-03-21 15:01:00
```

Files are written in **append mode** — safe to re-run with the same filename.

---

## 🔧 Loopback Diagnostic

If you're unsure whether loopback is working, run the diagnostic while playing any audio:

```bash
python tools/check_loopback.py
```

Captures 10 seconds, prints RMS levels per chunk, and confirms if the stream is healthy.

---

## 📋 Requirements

- **Python 3.11+**
- **Windows 11** (WASAPI loopback)
- Audio driver with WASAPI loopback support (most Realtek and USB audio drivers qualify)
- NVIDIA GPU recommended for CUDA acceleration — CPU fallback is available

---

## 🙋 FAQ

<details>
<summary><strong>Can I use this without a GPU?</strong></summary>

Yes. Select CPU at the compute device prompt. `tiny.en` and `small.en` run well on modern CPUs, though with higher latency than CUDA.
</details>

<details>
<summary><strong>Will this work with Bluetooth headphones?</strong></summary>

Yes, as long as your Bluetooth audio device appears as a WASAPI output device (it normally does on Windows 11). Select it in the wizard.
</details>

<details>
<summary><strong>Does it work with Zoom / Teams / Google Meet?</strong></summary>

Yes. It captures whatever your computer plays — including the audio from video call participants. It does not capture your own microphone.
</details>

<details>
<summary><strong>Can I use it with non-English content?</strong></summary>

Yes. Select **Auto-detect** in the language step. The first transcription will be slightly slower while Whisper detects the language, then it continues in that language.
</details>

<details>
<summary><strong>Does it upload audio anywhere?</strong></summary>

No. Everything runs locally. No internet connection is needed after the Whisper model is downloaded once.
</details>

<details>
<summary><strong>How much disk space do the models use?</strong></summary>

`tiny.en`: ~75 MB · `small.en`: ~460 MB · `medium.en`: ~1.5 GB · `large-v2`: ~2.9 GB.
Models are cached in `%USERPROFILE%\.cache\huggingface\hub\` and downloaded automatically on first use.
</details>

<details>
<summary><strong>My audio device is not showing up. What should I do?</strong></summary>

Run `python tools/check_loopback.py` while audio is playing. Ensure the output device is set as active in Windows Sound Settings and that no other app has exclusive control of it.
</details>

---

## 🗂️ Project Structure

```
realtime-captions-system-audio/
├── main.py                          # Entry point — run this
├── requirements.txt
├── .gitignore
├── README.md
│
├── src/
│   └── realtime_captions/
│       ├── __init__.py
│       ├── config.py                # Config dataclass, constants, model choices
│       ├── state.py                 # Thread-safe shared state
│       ├── audio.py                 # WASAPI loopback capture + resampling
│       ├── resources.py             # CPU / RAM / GPU monitor thread
│       ├── ui.py                    # Rich terminal panels + refresh loop
│       ├── overlay.py               # Floating caption overlay (Tkinter)
│       ├── wizard.py                # Interactive setup wizard
│       └── app.py                   # Orchestrator — wires all threads
│
├── tools/
│   └── check_loopback.py           # Loopback diagnostic utility
│
├── transcripts/                     # Saved .txt transcripts (git-ignored)
│
└── docs/
    ├── architecture.md
    ├── configuration.md
    ├── overlay.md
    └── dependencies.md
```

---

## 📖 Documentation

| File | Contents |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | Thread model, data flow, module responsibilities |
| [`docs/configuration.md`](docs/configuration.md) | All Config fields and wizard options explained |
| [`docs/overlay.md`](docs/overlay.md) | Caption overlay design, Windows API details, known limits |
| [`docs/dependencies.md`](docs/dependencies.md) | Full dependency list with version notes |

---

## 🤝 Contributing

Contributions are welcome — especially macOS and Linux audio capture backends.

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/macos-capture`
3. Commit your changes
4. Open a Pull Request

---

## 📄 License

MIT — free to use, modify, and distribute.
