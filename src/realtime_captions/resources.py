"""Background thread that polls CPU, RAM, and GPU metrics once per second."""

import threading
import time

import psutil
import pynvml

from . import state


def resource_monitor(stop_event: threading.Event) -> None:
    gpu_handle = None
    try:
        pynvml.nvmlInit()
        gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        raw  = pynvml.nvmlDeviceGetName(gpu_handle)
        name = raw.decode() if isinstance(raw, bytes) else raw
        state.update_resources(
            gpu_name=name.replace("NVIDIA GeForce ", "").replace("NVIDIA ", "")
        )
    except pynvml.NVMLError:
        pass

    # Prime psutil's CPU measurement — first call always returns 0.0
    psutil.cpu_percent()
    time.sleep(0.5)

    while not stop_event.is_set():
        ram = psutil.virtual_memory()
        state.update_resources(
            cpu_pct=psutil.cpu_percent(interval=None),
            ram_used_gb=ram.used  / 1e9,
            ram_total_gb=ram.total / 1e9,
            ram_pct=ram.percent,
        )

        if gpu_handle is not None:
            try:
                util = pynvml.nvmlDeviceGetUtilizationRates(gpu_handle)
                mem  = pynvml.nvmlDeviceGetMemoryInfo(gpu_handle)
                temp = pynvml.nvmlDeviceGetTemperature(gpu_handle, pynvml.NVML_TEMPERATURE_GPU)
                state.update_resources(
                    gpu_pct=float(util.gpu),
                    gpu_mem_used_gb=mem.used  / 1e9,
                    gpu_mem_total_gb=mem.total / 1e9,
                    gpu_mem_pct=100 * mem.used / mem.total,
                    gpu_temp=float(temp),
                )
            except pynvml.NVMLError:
                pass

        time.sleep(1.0)

    if gpu_handle is not None:
        try:
            pynvml.nvmlShutdown()
        except pynvml.NVMLError:
            pass
