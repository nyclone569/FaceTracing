"""Process metrics and JSON recording; all clocks use time.monotonic()."""

import json
import math
import os
import platform
import resource
import threading
import time
from pathlib import Path


def distribution(values):
    """Linear interpolation, matching NumPy's default percentile convention."""
    values = sorted(values)
    if not values:
        return {"count": 0, "mean": None, "p50": None, "p95": None, "p99": None}

    def percentile(q):
        position = (len(values) - 1) * q
        low, high = math.floor(position), math.ceil(position)
        return values[low] + (values[high] - values[low]) * (position - low)

    return {"count": len(values), "mean": sum(values) / len(values),
            "p50": percentile(0.5), "p95": percentile(0.95), "p99": percentile(0.99)}


def process_usage():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    peak_bytes = usage.ru_maxrss * (1 if platform.system() == "Darwin" else 1024)
    rss_bytes = None
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                rss_bytes = int(line.split()[1]) * 1024
                break
    except OSError:
        pass
    return {"cpu_s": usage.ru_utime + usage.ru_stime,
            "rss_bytes": rss_bytes, "process_lifetime_peak_rss_bytes": peak_bytes}


def write_json_atomic(path, payload):
    """Checkpoint a complete JSON document. Never expose a truncated document."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    os.replace(temporary, path)


class RunMetrics:
    def __init__(self, config):
        self.config = config
        self.started_s = time.monotonic()
        self.measurement_started_s = None
        self.measurement_ended_s = None
        self.measurement_cpu_started_s = None
        self.measurement_cpu_ended_s = None
        self.ready_s = None
        self.actual_backend = None
        self.capture_info = None
        self.frames = []
        self.render_samples = []
        self.process_samples = []
        self.events = []
        self.last_frame = None
        self.failure = None
        self.source_ended = False
        self._last_usage = None
        self._lock = threading.RLock()

    def event(self, kind, **fields):
        with self._lock:
            self.events.append({"event": kind, "elapsed_s": time.monotonic() - self.started_s,
                                **fields})

    def observe_detection(self, sample):
        with self._lock:
            kind = sample["event"]
            if kind == "frame":
                self.last_frame = sample
                measured = (self.measurement_started_s is not None
                            and sample["capture_received_s"] >= self.measurement_started_s
                            and self.measurement_ended_s is None)
                phase = "measurement" if measured else "shutdown" if self.measurement_ended_s is not None else "warmup"
                self.frames.append({**sample, "phase": phase,
                                    "elapsed_s": sample["monotonic_s"] - self.started_s})
            else:
                self.event(kind, **{k: v for k, v in sample.items()
                                    if k not in ("event", "monotonic_s")})
                if kind == "detector_ready":
                    self.actual_backend = sample["backend"]
                elif kind == "capture_ready":
                    self.ready_s = sample["monotonic_s"]
                elif kind == "error":
                    self.failure = sample["message"]
                elif kind == "source_ended":
                    self.source_ended = True

    def begin_measurement(self):
        with self._lock:
            self.measurement_started_s = time.monotonic()
            self.measurement_cpu_started_s = process_usage()["cpu_s"]
            self._last_usage = None
            self.sample_process(force=True)
            self.event("measurement_started")

    def end_measurement(self):
        with self._lock:
            if self.measurement_started_s is not None and self.measurement_ended_s is None:
                self.sample_process(force=True)
                self.measurement_ended_s = time.monotonic()
                self.measurement_cpu_ended_s = process_usage()["cpu_s"]

    def sample_process(self, force=False):
        with self._lock:
            if self.measurement_started_s is None or self.measurement_ended_s is not None:
                return
            now = time.monotonic()
            if (not force and self._last_usage is not None
                    and now - self._last_usage[0] < self.config["sample_interval_s"]):
                return
            usage = process_usage()
            cpu_percent = None
            if self._last_usage is not None:
                wall = now - self._last_usage[0]
                if wall > 0:
                    cpu_percent = (usage["cpu_s"] - self._last_usage[1]) / wall * 100.0
            self.process_samples.append({"elapsed_s": now - self.started_s,
                                         "cpu_percent_one_core": cpu_percent,
                                         "cpu_percent_machine_capacity": (
                                             cpu_percent / (os.cpu_count() or 1)
                                             if cpu_percent is not None else None), **usage})
            self._last_usage = (now, usage["cpu_s"])

    def record_render(self, started_s, finished_s, frame_interval_ms, intent, observation_age_ms):
        with self._lock:
            measured = (self.measurement_started_s is not None
                        and started_s >= self.measurement_started_s
                        and self.measurement_ended_s is None)
            phase = "measurement" if measured else "shutdown" if self.measurement_ended_s is not None else "warmup"
            self.render_samples.append({"elapsed_s": finished_s - self.started_s,
                                        "phase": phase,
                                        "render_work_ms": (finished_s - started_s) * 1000,
                                        "frame_interval_ms": frame_interval_ms,
                                        "observation_age_ms": observation_age_ms,
                                        "intent": intent})

    def latest_detection(self):
        with self._lock:
            return dict(self.last_frame) if self.last_frame else None

    def export(self, status, stop_reason):
        with self._lock:
            frames = [x for x in self.frames if x["phase"] == "measurement"]
            renders = [x for x in self.render_samples if x["phase"] == "measurement"]
            start = self.measurement_started_s
            end = self.measurement_ended_s or time.monotonic()
            seconds = max(0.0, end - start) if start is not None else 0.0
            cpu_end = self.measurement_cpu_ended_s
            if cpu_end is None:
                cpu_end = process_usage()["cpu_s"]
            cpu_s = max(0.0, cpu_end - self.measurement_cpu_started_s) if start is not None else None
            summary = {
                "measurement_duration_s": seconds,
                "completed_detection_frames": len(frames),
                "actual_detection_fps": len(frames) / seconds if seconds > 0 and frames else None,
                "rendered_frames": len(renders),
                "actual_renderer_fps": len(renders) / seconds if seconds > 0 and renders else None,
                "process_cpu_s": cpu_s,
                "mean_process_cpu_percent_one_core": cpu_s / seconds * 100 if cpu_s is not None and seconds > 0 else None,
                "process_cpu_ms_per_completed_frame": cpu_s * 1000 / len(frames) if cpu_s is not None and frames else None,
                "max_sampled_rss_bytes": max((x["rss_bytes"] for x in self.process_samples if x["rss_bytes"] is not None), default=None),
                "face_detected_frames": sum(x["face_detected"] for x in frames),
                "capture_failures": sum(x["event"] == "capture_failure" for x in self.events),
            }
            for field in ("capture_wait_ms", "preprocessing_ms", "detection_stage_ms",
                          "detection_calling_thread_cpu_ms", "host_frame_to_target_ms", "cycle_work_ms"):
                summary[field] = distribution([x[field] for x in frames])
            for field in ("render_work_ms", "frame_interval_ms", "observation_age_ms"):
                summary[field] = distribution([x[field] for x in renders if x[field] is not None])
            return {"status": status, "stop_reason": stop_reason, "config": dict(self.config),
                    "actual_detector": self.actual_backend, "capture": self.capture_info,
                    "summary": summary, "events": list(self.events),
                    "detection_samples": list(self.frames),
                    "render_samples": list(self.render_samples),
                    "process_samples": list(self.process_samples)}
