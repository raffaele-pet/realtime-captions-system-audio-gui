"""WASAPI loopback audio capture and PCM resampling.

Recorder callbacks are defined here because they are tightly coupled to the
audio pipeline — they simply forward RealtimeSTT events into shared state.
"""

import threading

import numpy as np
import pyaudiowpatch as pyaudio
from RealtimeSTT import AudioToTextRecorder

from .config import CHUNK, TARGET_RATE
from . import state


# ── recorder event callbacks ──────────────────────────────────────────────────
def on_live(text: str) -> None:
    state.set_live_text(text)


def on_stable(text: str) -> None:
    state.set_stable_text(text)


def on_recording_start() -> None:
    state.set_status("Recording")


def on_recording_stop() -> None:
    state.set_status("Listening")


# ── PCM helpers ───────────────────────────────────────────────────────────────
def resample_to_mono_16k(data: bytes, src_rate: int, channels: int) -> bytes:
    """Downsample arbitrary-rate stereo int16 PCM to 16 kHz mono int16."""
    audio = np.frombuffer(data, dtype=np.int16).reshape(-1, channels)
    mono  = audio.mean(axis=1).astype(np.float32)
    if src_rate != TARGET_RATE:
        n_out = int(len(mono) * TARGET_RATE / src_rate)
        mono  = np.interp(
            np.linspace(0, len(mono), n_out, endpoint=False),
            np.arange(len(mono)),
            mono,
        )
    return mono.astype(np.int16).tobytes()


# ── loopback stream ───────────────────────────────────────────────────────────
def open_loopback(p: pyaudio.PyAudio, device_name: str) -> tuple[object, int, int]:
    device = next(
        (d for d in p.get_loopback_device_info_generator() if d["name"] == device_name),
        None,
    )
    if device is None:
        available = [d["name"] for d in p.get_loopback_device_info_generator()]
        raise RuntimeError(f"Device '{device_name}' not found.\nAvailable: {available}")
    channels: int = device["maxInputChannels"]
    src_rate: int = int(device["defaultSampleRate"])
    stream = p.open(
        format=pyaudio.paInt16,
        channels=channels,
        rate=src_rate,
        input=True,
        input_device_index=device["index"],
        frames_per_buffer=CHUNK,
    )
    return stream, src_rate, channels


def stream_loopback(
    recorder: AudioToTextRecorder,
    device_name: str,
    stop_event: threading.Event,
) -> None:
    """Read WASAPI loopback audio and feed resampled PCM to the recorder."""
    p = pyaudio.PyAudio()
    try:
        stream, src_rate, channels = open_loopback(p, device_name)
        try:
            while not stop_event.is_set():
                raw = stream.read(CHUNK, exception_on_overflow=False)
                recorder.feed_audio(resample_to_mono_16k(raw, src_rate, channels))
        finally:
            stream.stop_stream()
            stream.close()
    finally:
        p.terminate()
