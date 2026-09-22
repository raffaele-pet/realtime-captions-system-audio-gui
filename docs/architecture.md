# Architecture

## Overview

The application is composed of five concurrent subsystems spread across dedicated modules under `src/realtime_captions/`. All subsystems share a small, lock-protected state object managed by `state.py`.

```
┌─────────────────────────────────────────────────────────────────────┐
│                          python main.py                             │
│                                                                     │
│  ┌──────────────┐   feed_audio()   ┌───────────────────────────┐   │
│  │ Audio thread │ ───────────────► │  RealtimeSTT / Whisper    │   │
│  │ (WASAPI      │                  │  (AudioToTextRecorder)    │   │
│  │  loopback)   │                  │                           │   │
│  └──────────────┘                  │  on_realtime_update  ──►  │   │
│                                    │  on_realtime_stabilized ► │   │
│  ┌──────────────┐                  │  on_recording_start  ──►  │   │
│  │ Resource     │                  │  on_recording_stop   ──►  │   │
│  │ monitor      │  writes _res     └───────────┬───────────────┘   │
│  │ (psutil /    │ ──────────────────────────    │ callbacks write   │
│  │  pynvml)     │                        │      │ _live_text        │
│  └──────────────┘                        │      │ _stable_text      │
│                                    ┌─────▼──────▼──────────────┐   │
│  ┌──────────────┐   reads state    │   Shared State (_lock)    │   │
│  │ Refresh      │ ◄──────────────  │   _live_text              │   │
│  │ thread       │                  │   _stable_text            │   │
│  │              │  updates Rich UI │   _status                 │   │
│  │              │ ───────────────► │   _history                │   │
│  │              │  updates overlay │   _res (resources)        │   │
│  └──────────────┘                  └───────────────────────────┘   │
│                                                                     │
│  ┌──────────────┐   recorder.text() blocks until utterance done    │
│  │ Main thread  │ ──────────────────────────────────────────────►  │
│  │              │   appends to _history, writes file (optional)    │
│  └──────────────┘                                                   │
│                                                                     │
│  ┌──────────────┐   Tkinter mainloop (optional)                    │
│  │ Overlay      │   polls shared text every 80 ms                  │
│  │ thread       │   controls alpha for show/hide                   │
│  └──────────────┘                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Threads

| Thread | Name | Blocking call | Role | Module |
|---|---|---|---|---|
| Main | `MainThread` | `recorder.text()` | Collects finalized utterances, writes file | `app.py` |
| Audio capture | `stream_loopback` | `stream.read()` | Reads WASAPI loopback, feeds PCM to recorder | `audio.py` |
| Resource monitor | `resource_monitor` | `time.sleep(1.0)` | Polls CPU/RAM/GPU every second | `resources.py` |
| Refresh | `refresh_loop` | `time.sleep(0.1)` | Redraws terminal UI and overlay at ~10 fps | `ui.py` |
| Caption overlay | `caption-overlay` | `root.mainloop()` | Runs Tkinter event loop for the subtitle window | `overlay.py` |

All background threads are **daemon threads** — they exit automatically when the main thread exits.

---

## Data Flow

### Audio path

```
WASAPI loopback (48 kHz stereo int16)
  → audio.resample_to_mono_16k()   [numpy linear interpolation]
  → 16 kHz mono int16 bytes
  → recorder.feed_audio()
  → RealtimeSTT internal VAD + Whisper
```

### Text path

```
RealtimeSTT callbacks (recorder's internal threads)  [audio.py]
  → on_live()          → state.set_live_text()
  → on_stable()        → state.set_stable_text()
  → on_recording_start / on_recording_stop  → state.set_status()

Main thread (after recorder.text() returns)  [app.py]
  → state.append_history(ts, text)
  → state.clear_live()
  → writes line to output file (if enabled)

Refresh thread (every 100 ms)  [ui.py]
  → state.get_snapshot()  (single lock acquisition)
  → live_display.update(make_ui(cfg))
  → overlay.set_text(stable or live)
```

---

## Shared State

All shared variables live in `src/realtime_captions/state.py` and are protected by a single `threading.Lock`. No caller ever holds the lock directly — the module exposes a clean getter/setter API.

```python
# state.py — public API
set_live_text(text)           # called by audio.on_live()
set_stable_text(text)         # called by audio.on_stable()
set_status(status)            # called by audio.on_recording_start/stop
append_history(ts, text)      # called by app.py main loop
clear_live()                  # called by app.py after final utterance
update_resources(**kwargs)    # called by resources.resource_monitor()
get_snapshot() -> tuple       # called by ui.make_ui() and refresh_loop()
```

Internal variables:

```python
_lock        : threading.Lock
_live_text   : str          # current raw partial
_stable_text : str          # stabilised partial
_history     : deque[(ts, text)]  # completed utterances (max_history entries)
_status      : str          # "Initializing" | "Listening" | "Recording" | "Stopped"
_res         : Resources    # latest CPU/RAM/GPU snapshot
```

---

## Key Design Decisions

### Why a dedicated `state.py` module instead of module globals?

The original single-file implementation used `globals()["_live_text"] = value` to update shared state from callbacks — a valid but opaque pattern. The refactored layout moves all shared state into `state.py` and exposes it through named setter/getter functions. This makes the shared-state contract explicit, easier to test, and prevents accidental shadowing by local variables in any module.

### Why alpha=0 for hide/show instead of `withdraw/deiconify`?

On Windows, `overrideredirect(True)` (borderless mode) breaks Tkinter's `wm_state` management. Calling `deiconify()` on a withdrawn borderless window often fails silently. Toggling `root.attributes("-alpha", 0.0 / 0.88)` is reliable across all Windows versions.

### Why `GetAncestor(GA_ROOT)` for click-through?

`root.winfo_id()` returns the HWND of the inner child frame that Tkinter creates inside the top-level window. Applying `WS_EX_LAYERED` to a child window causes rendering failures. `GetAncestor(hwnd, GA_ROOT=2)` walks up to the actual top-level window where the style must be set.
