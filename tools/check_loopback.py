"""
Loopback diagnostic script.

Captures system audio via WASAPI loopback for a few seconds and reports:
  - The detected loopback device name and format
  - RMS level per chunk so you can confirm audio is actually flowing
  - Peak amplitude across the entire capture
  - A simple ASCII VU meter so you can see levels at a glance

Run this while playing any audio (music, video, etc.) to verify the
loopback stream is working before using it with RealtimeSTT.
"""

import struct
import math
import time

import pyaudiowpatch as pyaudio

CAPTURE_SECONDS = 10
CHUNK = 512


def rms(data: bytes) -> float:
    """Root-mean-square amplitude of a chunk of int16 PCM bytes."""
    if not data:
        return 0.0
    samples = struct.unpack(f"{len(data) // 2}h", data)
    mean_sq = sum(s * s for s in samples) / len(samples)
    return math.sqrt(mean_sq)


def vu_bar(level: float, max_level: float = 32768.0, width: int = 40) -> str:
    filled = int(width * min(level / max_level, 1.0))
    return f"[{'#' * filled}{' ' * (width - filled)}]"


def find_loopback_device(p: pyaudio.PyAudio) -> dict:
    wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
    default_out = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])

    loopback = next(
        (d for d in p.get_loopback_device_info_generator() if default_out["name"] in d["name"]),
        None,
    )
    if loopback is None:
        raise RuntimeError(
            "No WASAPI loopback device found for the default output.\n"
            "Make sure your audio driver supports WASAPI loopback."
        )
    return loopback


def main() -> None:
    p = pyaudio.PyAudio()
    try:
        loopback = find_loopback_device(p)
        channels: int = loopback["maxInputChannels"]
        src_rate: int = int(loopback["defaultSampleRate"])

        print("=" * 60)
        print("  WASAPI Loopback Diagnostic")
        print("=" * 60)
        print(f"  Device  : {loopback['name']}")
        print(f"  Index   : {loopback['index']}")
        print(f"  Rate    : {src_rate} Hz")
        print(f"  Channels: {channels}")
        print(f"  Capture : {CAPTURE_SECONDS}s  |  Chunk: {CHUNK} frames")
        print("=" * 60)
        print("  Play some audio now...\n")

        stream = p.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=src_rate,
            input=True,
            input_device_index=loopback["index"],
            frames_per_buffer=CHUNK,
        )

        peak = 0.0
        silent_chunks = 0
        total_chunks = 0
        deadline = time.monotonic() + CAPTURE_SECONDS

        while time.monotonic() < deadline:
            raw = stream.read(CHUNK, exception_on_overflow=False)
            level = rms(raw)
            peak = max(peak, level)
            total_chunks += 1
            if level < 10:
                silent_chunks += 1

            bar = vu_bar(level)
            remaining = max(0.0, deadline - time.monotonic())
            print(f"\r  {bar}  RMS: {level:6.1f}  [{remaining:4.1f}s left]", end="", flush=True)

        stream.stop_stream()
        stream.close()

        print("\n")
        print("=" * 60)
        print("  Results")
        print("=" * 60)
        print(f"  Total chunks  : {total_chunks}")
        print(f"  Silent chunks : {silent_chunks}  ({100 * silent_chunks / total_chunks:.1f}%)")
        print(f"  Peak RMS      : {peak:.1f}  (max possible: 32768)")

        if peak < 10:
            print("\n  [WARN]  Peak is near zero — no audio detected.")
            print("          Make sure something is playing on your default output device.")
        elif silent_chunks / total_chunks > 0.9:
            print("\n  [WARN]  Most chunks were silent. Audio may be intermittent.")
        else:
            print("\n  [OK]    Audio stream looks healthy. Loopback is working.")

        print("=" * 60)

    finally:
        p.terminate()


if __name__ == "__main__":
    main()
