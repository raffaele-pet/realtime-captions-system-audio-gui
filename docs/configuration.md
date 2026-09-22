# Configuration

All settings are collected interactively by the setup wizard (`src/realtime_captions/wizard.py`) and stored in the `Config` dataclass (`src/realtime_captions/config.py`).  
There are no config files or environment variables — the wizard runs every time.

---

## Wizard Pages

### Page 1 — Audio source

Lists every WASAPI loopback device available on the system (one entry per active output device).  
Navigate with **↑ / ↓** arrow keys, confirm with **Enter**.

```
┌───┬────────────────────────────┬───────────┬──────────┐
│ # │ Device                     │      Rate │ Channels │
├───┼────────────────────────────┼───────────┼──────────┤
│ 1 │ Zone Vibe 100              │ 48000 Hz  │        2 │
│ 2 │ Alto-falantes (Realtek)    │ 48000 Hz  │        2 │
└───┴────────────────────────────┴───────────┴──────────┘
```

If no devices are found, check that:
- At least one audio output device is active.
- Your audio driver supports WASAPI loopback (most Realtek and USB audio drivers do).

---

### Page 2 — Options

#### Transcription model

Controls the **final** transcription accuracy (returned by `recorder.text()`).

| Choice | Model | Notes |
|---|---|---|
| Fast | `tiny.en` | Fastest, suitable for clear speech |
| **Balanced** ★ | `small.en` | Recommended — good accuracy at reasonable speed |
| Accurate | `medium.en` | Higher accuracy; requires more VRAM (~5 GB) |
| Best | `large-v2` | Best accuracy; requires ~10 GB VRAM |

`.en` suffix = English-only model, slightly faster and more accurate for English than the multilingual equivalent.

---

#### Real-time preview model

Controls the **live partial** text shown in the terminal and overlay while you are still speaking.  
A smaller model is recommended here because it runs continuously.

| Choice | Model | Notes |
|---|---|---|
| **Fastest** ★ | `tiny.en` | Recommended — low latency updates |
| Balanced | `base.en` | Slightly better live accuracy |
| Accurate | `small.en` | Best live quality; higher GPU load |

---

#### Compute device

| Choice | Notes |
|---|---|
| **CUDA** ★ | GPU accelerated. Shown only if an NVIDIA GPU is detected via NVML. |
| CPU | Works without a GPU; significantly slower for medium/large models. |

---

#### Transcription language

| Choice | Value | Notes |
|---|---|---|
| **English** ★ | `en` | Uses the `.en` English-only model branch |
| Auto-detect | `""` | Multilingual; first transcription is slower while language is detected |

---

#### Show resource monitor

Toggles the **System** panel in the terminal UI showing CPU, RAM, GPU, VRAM and temperature.  
Disabled = one less panel, more room for the transcript history.

---

#### Save transcription to file

When enabled, every finalized sentence is appended to a `.txt` file immediately after it is recognised.  
The file is opened in **append mode** — re-running with the same filename adds to the existing file.

**Filename prompt:**
- Default: `transcript_YYYYMMDD_HHMMSS.txt`
- `.txt` is appended automatically if omitted.
- Only the basename is kept (path separators are stripped) to prevent directory traversal.
- Files are saved to the `transcripts/` directory automatically.

**File format:**
```
# Transcription started 2026-03-21 14:23:01
# Source : Zone Vibe 100 [Loopback]
# Model  : small.en

[14:23:04] Thank you very much.
[14:24:18] And one experience, he actually played Hemi-Sync sounds...

# Transcription ended 2026-03-21 14:45:00
```

Transcript files are saved to `transcripts/transcript_YYYYMMDD_HHMMSS.txt` relative to the project root.

---

#### Caption overlay

Floating subtitle window that appears in front of all other applications.  
See [`overlay.md`](overlay.md) for full details.

---

## Config Dataclass Reference

```python
@dataclass
class Config:
    device_name: str      # Full WASAPI loopback device name (includes " [Loopback]")
    model: str            # Whisper model for final transcription
    realtime_model: str   # Whisper model for live preview
    compute: str          # "cuda" or "cpu"
    language: str         # "en" or "" (auto-detect)
    show_resources: bool  # Show/hide the System resource panel
    max_history: int      # Maximum entries kept in the history deque (default: 100)
    save_to_file: bool    # Whether to write transcription to disk
    output_file: str      # Path of the .txt file (empty if save_to_file is False)
    show_overlay: bool    # Whether to launch the caption overlay window
```

---

## Terminal UI Layout

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ● Listening  │  Zone Vibe 100  │  model: small.en  │  saving → meeting.txt  │  Ctrl+C to stop
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
╭──── System  RTX 3080 ──────────────────────────────╮   ← hidden if show_resources=False
│  CPU  ████████░░░░  58.0%   RAM  ████░░░░  12/32 GB│
│  GPU  ███████░░░░░  65.0%  61°C  VRAM  ████░░  6/8 │
╰────────────────────────────────────────────────────╯
╭──── ◉  Live ───────────────────────────────────────╮
│                                                    │
│   Current in-progress sentence…                   │
│                                                    │
╰────────────────────────────────────────────────────╯
╭──── ≡  History ────────────────────────────────────╮
│  14:23:01 │ Completed sentence.                    │
│  14:24:15 │ Another completed sentence.            │
╰────────────────────────────────────────────────────╯
```

### Status indicator colours

| Colour | Meaning |
|---|---|
| Green `●` | Listening — waiting for voice activity |
| Red `●` | Recording — VAD detected speech, Whisper is accumulating audio |
| Dim `○` | Initializing or Stopped |

### Resource bar colour thresholds

| Colour | Threshold |
|---|---|
| Green | < 50 % |
| Yellow | 50 – 79 % |
| Red | ≥ 80 % |

GPU temperature thresholds: green < 65 °C, yellow < 80 °C, red ≥ 80 °C.
