# Dependencies

## Installation

```bash
pip install RealtimeSTT pyaudiowpatch numpy psutil nvidia-ml-py questionary rich
```

No administrator rights required for installation or runtime.

---

## Package reference

### Runtime dependencies

| Package | Install name | Used for |
|---|---|---|
| `RealtimeSTT` | `RealtimeSTT` | Whisper-based speech-to-text engine and VAD |
| `pyaudiowpatch` | `pyaudiowpatch` | WASAPI loopback audio capture on Windows |
| `numpy` | `numpy` | PCM audio resampling (48 kHz stereo → 16 kHz mono) |
| `psutil` | `psutil` | CPU and RAM usage metrics |
| `pynvml` | `nvidia-ml-py` | NVIDIA GPU usage, VRAM and temperature via NVML |
| `questionary` | `questionary` | Interactive arrow-key prompts for the setup wizard |
| `rich` | `rich` | Full-screen terminal UI (panels, tables, live display) |

### Standard library (no install needed)

| Module | Used for |
|---|---|
| `ctypes` | Windows API calls for the click-through overlay (`WS_EX_TRANSPARENT`) |
| `tkinter` | Caption overlay window (bundled with all official Python distributions) |
| `threading` | Concurrent audio capture, resource monitor, refresh loop, overlay |
| `logging` | Suppressing RealtimeSTT internal log output |
| `os` | Filename sanitisation (`os.path.basename`) |
| `sys` | Clean exit on wizard cancel (`sys.exit`) |
| `time` | Timestamps for history entries and output files |
| `collections.deque` | Bounded history buffer |
| `dataclasses` | `Config` and `_Resources` data containers |

---

## Package notes

### `pyaudiowpatch` vs `pyaudio`

`pyaudiowpatch` is a fork of PyAudio that adds **WASAPI loopback** support on Windows. Standard `pyaudio` cannot open loopback devices. Do not install both; they conflict.

### `nvidia-ml-py` vs `pynvml`

The package on PyPI named **`pynvml`** is a deprecated shim that re-exports `nvidia-ml-py` and prints a deprecation warning. Install `nvidia-ml-py` directly to avoid the warning. Both install the same `pynvml` Python module.

```bash
# Correct
pip install nvidia-ml-py

# Avoid — deprecated wrapper
pip install pynvml
```

### `RealtimeSTT` model download

On first run, Whisper model weights are downloaded from Hugging Face Hub and cached locally. Download sizes:

| Model | Size on disk |
|---|---|
| `tiny.en` | ~75 MB |
| `base.en` | ~145 MB |
| `small.en` | ~460 MB |
| `medium.en` | ~1.5 GB |
| `large-v2` | ~2.9 GB |

Cache location: `~/.cache/huggingface/hub/` (Linux/macOS) or `%USERPROFILE%\.cache\huggingface\hub\` (Windows).

---

## Tested environment

| Component | Version |
|---|---|
| Python | 3.13 |
| Windows | 11 (build 26100) |
| CUDA | optional (CPU fallback available) |
| RealtimeSTT | latest |
| pyaudiowpatch | 0.2.12.8 |
| numpy | 2.x |
| rich | 14.x |
| questionary | 2.x |
| nvidia-ml-py | 13.x |
| psutil | 7.x |
