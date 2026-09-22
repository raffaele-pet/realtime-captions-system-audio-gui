# Realtime Speech Transcription

Real-time speech-to-text from system audio using [Whisper](https://github.com/openai/whisper) via [RealtimeSTT](https://github.com/KoljaB/RealtimeSTT).  
Captures whatever is playing through your speakers (meetings, videos, podcasts) — no microphone needed.

---

## Features

| Feature | Description |
|---|---|
| **System audio capture** | WASAPI loopback — captures speaker output without a virtual cable |
| **Live transcription** | Partial text updates as speech is detected |
| **Stable transcription** | Higher-quality stabilised output before the final result |
| **Full-screen terminal UI** | Rich-powered display with live, history and resource panels |
| **System resource monitor** | CPU, RAM, GPU usage and VRAM in real time |
| **Caption overlay** | Borderless always-on-top subtitle window over all apps |
| **Save to file** | Timestamped `.txt` transcript written on the fly |
| **Interactive wizard** | Two-page setup to choose device and all options |

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

No administrator rights required.

---

## Usage

```
python main.py
```

The wizard launches automatically:

1. **Page 1 – Audio source**: lists all WASAPI loopback devices; pick one with arrow keys.
2. **Page 2 – Options**: model, compute device, language, resource panel, file save, caption overlay.
3. **Summary**: review all choices then confirm to start.

Press **Ctrl+C** at any time to stop cleanly.

---

## Documentation

| File | Contents |
|---|---|
| [`architecture.md`](architecture.md) | Thread model, data flow, module responsibilities |
| [`configuration.md`](configuration.md) | All `Config` fields and wizard options explained |
| [`overlay.md`](overlay.md) | Caption overlay design, Windows API details, known limits |
| [`dependencies.md`](dependencies.md) | Full dependency list with version notes |
