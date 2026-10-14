#!/usr/bin/env python3
"""Run steps 5/6 from files, reusing Raspieyes detection, filtering and eyes.

Examples (from the workspace root):
  raspieyes/.venv/bin/python experiments/run_raspieyes.py --mode mouse
  raspieyes/.venv/bin/python experiments/run_raspieyes.py --mode webcam
  raspieyes/.venv/bin/python experiments/run_raspieyes.py --mode benchmark

Run configuration lives in config.json. JSON results contain actual measurements,
not configured FPS. No audio capture, images, or identity recognition are used.
"""

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import random
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from metrics import RunMetrics, write_json_atomic
from raspieyes_adapter import (RaspieyesBackend, TargetSnapshot, baseline_intent,
                               intent_record)


def load_config(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("config.json"))
    parser.add_argument("--mode", choices=["mouse", "idle", "webcam", "video", "benchmark"])
    parser.add_argument("--camera-index", type=int)
    parser.add_argument("--detector", choices=["mediapipe", "dnn", "haar", "auto"])
    parser.add_argument("--detection-fps", type=float)
    parser.add_argument("--renderer-fps", type=int)
    parser.add_argument("--duration", dest="duration_s", type=float)
    parser.add_argument("--warmup", dest="warmup_s", type=float)
    parser.add_argument("--rates", dest="benchmark_rates", type=float, nargs="+")
    parser.add_argument("--headless", action="store_true", default=None)
    parser.add_argument("--perception-only", action="store_true", default=None)
    parser.add_argument("--motion-fallback", action="store_true", default=None)
    parser.add_argument("--video", type=Path, help="Optional recorded input; decoded sequentially at the detection rate")
    parser.add_argument("--output", type=Path, help="One JSON file for the entire session")
    cli = parser.parse_args(argv)
    config = json.loads(cli.config.read_text(encoding="utf-8"))
    for key, value in vars(cli).items():
        if key not in ("config", "video", "output") and value is not None:
            config[key] = value
    if cli.video is not None:
        config["video_path"] = str(cli.video.resolve())
        if config["mode"] != "benchmark":
            config["mode"] = "video"
    if config["mode"] not in ("mouse", "idle", "webcam", "video", "benchmark"):
        parser.error("Invalid mode in config")
    if config["detector"] not in ("mediapipe", "dnn", "haar", "auto"):
        parser.error("Invalid detector in config")
    for key in ("dual_eye", "headless", "perception_only", "motion_fallback"):
        if type(config[key]) is not bool:
            parser.error(f"{key} must be a JSON boolean")
    for key in ("raspieyes_dir", "output_dir"):
        config[key] = str((cli.config.resolve().parent / config[key]).resolve())
    for key in ("capture_width", "capture_height", "capture_fps", "detection_fps",
                "renderer_fps", "eye_size", "duration_s", "startup_timeout_s",
                "sample_interval_s", "checkpoint_interval_s", "presence_timeout_s"):
        if type(config[key]) not in (int, float) or not 0 < config[key] < float("inf"):
            parser.error(f"{key} must be a finite positive number")
    for key in ("capture_width", "capture_height", "renderer_fps", "eye_size", "camera_index", "seed"):
        if type(config[key]) is not int:
            parser.error(f"{key} must be an integer")
    if not isinstance(config["warmup_s"], (int, float)) or not 0 <= config["warmup_s"] < float("inf"):
        parser.error("warmup_s must be finite and non-negative")
    if not config["benchmark_rates"] or any(not isinstance(rate, (int, float)) or not 0 < rate < float("inf") for rate in config["benchmark_rates"]):
        parser.error("benchmark_rates must contain finite positive rates")
    if config["mode"] == "video" and not config.get("video_path"):
        parser.error("video mode requires --video PATH")
    if config["mode"] == "mouse" and (config["headless"] or config["perception_only"]):
        parser.error("mouse mode requires a visible renderer")
    if config["perception_only"] and config["mode"] == "idle":
        parser.error("idle + perception-only has no workload")
    return config, cli.output.resolve() if cli.output else None


def metadata(config):
    source = Path(config["raspieyes_dir"])
    try:
        commit = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
        diff = subprocess.check_output(["git", "-C", str(source), "diff", "--", "eye_renderer.py", "eye_tracker.py"], text=True)
    except (OSError, subprocess.CalledProcessError):
        commit, diff = None, None
    files = {}
    for name in ("eye_renderer.py", "eye_tracker.py", "blaze_face_short_range.tflite",
                 "deploy.prototxt", "res10_300x300_ssd_iter_140000_fp16.caffemodel"):
        path = source / name
        files[name] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    packages = {}
    for name in ("numpy", "opencv-contrib-python", "mediapipe", "pygame"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    cpu = platform.processor()
    try:
        cpu = next(line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines() if line.startswith("model name"))
    except (OSError, StopIteration):
        pass
    return {"python": sys.version, "executable": sys.executable, "platform": platform.platform(),
            "cpu": cpu, "logical_cpus": os.cpu_count(), "packages": packages,
            "raspieyes_base_commit": commit, "raspieyes_local_patch": diff,
            "source_and_model_sha256": files,
            "display": {key: os.environ.get(key) for key in ("DISPLAY", "WAYLAND_DISPLAY", "SDL_VIDEODRIVER")}}


class CaptureSource:
    """An OpenCV capture with explicit camera index and no saved image frames."""

    def __init__(self, config, metrics):
        import cv2

        self.video = bool(config.get("video_path"))
        source = config["video_path"] if self.video else config["camera_index"]
        api = cv2.CAP_ANY if self.video or platform.system() != "Linux" else cv2.CAP_V4L2
        self.capture = cv2.VideoCapture(source, api)
        if not self.capture.isOpened():
            self.capture.release()
            raise RuntimeError(f"Cannot open capture source: {source}")
        requested_buffer_applied = None
        if not self.video:
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, config["capture_width"])
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, config["capture_height"])
            self.capture.set(cv2.CAP_PROP_FPS, config["capture_fps"])
            requested_buffer_applied = self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        metrics.capture_info = {
            "source": str(source), "kind": "video" if self.video else "webcam",
            "reported_width": self.capture.get(cv2.CAP_PROP_FRAME_WIDTH),
            "reported_height": self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT),
            "reported_fps": self.capture.get(cv2.CAP_PROP_FPS),
            "backend": self.capture.getBackendName(),
            "requested_single_buffer_accepted": requested_buffer_applied,
            "video_playback": "sequential, paced by detection loop" if self.video else None,
        }

    def read(self):
        ok, frame = self.capture.read()
        if not ok and self.video:
            raise EOFError("Recorded video finished")
        return ok, frame

    def release(self):
        self.capture.release()


def run_once(config, app, pygame, session_stop, checkpoint):
    """Background upstream perception; foreground independent intent/render loop."""
    metrics = RunMetrics(config)
    metrics.event("run_started", mode=config["mode"], audio_enabled=False)
    stop = threading.Event()
    worker_done = threading.Event()
    worker = None
    backend = None
    previous_timeout = app.PRESENCE_TIMEOUT
    app.PRESENCE_TIMEOUT = config["presence_timeout_s"]
    status, reason = "completed", "duration_reached"
    camera_mode = config["mode"] in ("webcam", "video", "benchmark")
    random.seed(config["seed"])
    tracking = app.TrackingState()

    def perception_worker(args):
        try:
            app.detection_loop(tracking, args)
        except BaseException as error:
            metrics.observe_detection({"event": "error", "monotonic_s": time.monotonic(),
                                       "message": f"{type(error).__name__}: {error}"})
        finally:
            worker_done.set()

    try:
        if not config["perception_only"]:
            backend = RaspieyesBackend(app, pygame, config)
            metrics.event("renderer_ready", size=list(backend.window_size),
                          sdl_driver=pygame.display.get_driver())
        if camera_mode:
            args = SimpleNamespace(
                test_webcam=True, capture_width=config["capture_width"],
                capture_height=config["capture_height"], detection_fps=config["detection_fps"],
                min_contour_area=300, detector_backend=config["detector"],
                motion_fallback=config["motion_fallback"], stop_event=stop,
                max_failed_reads=3, detection_observer=metrics.observe_detection,
                capture_factory=lambda width, height: CaptureSource(config, metrics),
            )
            worker = threading.Thread(target=perception_worker, args=(args,), daemon=True)
            worker.start()
        else:
            metrics.ready_s = time.monotonic()

        clock = pygame.time.Clock()
        previous_tick = time.monotonic()
        last_checkpoint = previous_tick
        while not session_stop.is_set():
            clock.tick(config["renderer_fps"] if backend else 50)
            now = time.monotonic()
            dt = now - previous_tick
            previous_tick = now
            if backend:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key in (pygame.K_q, pygame.K_ESCAPE)):
                        session_stop.set()
                if session_stop.is_set():
                    break
            if metrics.failure:
                status, reason = "failed", "perception_error"
                break
            if metrics.source_ended:
                reason = "video_finished"
                break
            if camera_mode and worker_done.is_set():
                status, reason = "failed", "perception_stopped_unexpectedly"
                break
            if metrics.ready_s is None:
                if now - metrics.started_s > config["startup_timeout_s"]:
                    raise TimeoutError("Perception startup timed out")
            elif metrics.measurement_started_s is None and now - metrics.ready_s >= config["warmup_s"]:
                metrics.begin_measurement()
                print(f"[measurement] mode={config['mode']}; detection target={config['detection_fps']} FPS; duration={config['duration_s']} s", flush=True)
            if metrics.measurement_started_s is not None and now - metrics.measurement_started_s >= config["duration_s"]:
                break

            if config["mode"] == "mouse":
                mx, my = pygame.mouse.get_pos()
                nx = (mx / backend.window_size[0] - 0.5) * 2
                ny = (my / backend.window_size[1] - 0.5) * 2
                tracking.update("detected", nx, ny, 0.2)

            # This is the explicit future insertion point for Attention + FSM.
            # Perception publishes a filtered snapshot, not display coordinates.
            target = TargetSnapshot.from_tracking(tracking)
            intent = baseline_intent(target)
            if backend:
                started = time.monotonic()
                backend.render(intent, dt)
                finished = time.monotonic()
                latest = metrics.latest_detection()
                age = (started - latest["capture_received_s"]) * 1000 if latest else None
                metrics.record_render(started, finished, dt * 1000, intent_record(intent), age)
            metrics.sample_process()
            if now - last_checkpoint >= config["checkpoint_interval_s"]:
                checkpoint(metrics.export("running", "checkpoint"))
                last_checkpoint = now

        if session_stop.is_set():
            status, reason = "interrupted", "user_stop"
    except Exception as error:
        status, reason = "failed", "runner_error"
        metrics.event("error", message=f"{type(error).__name__}: {error}")
        print(f"[error] {error}", file=sys.stderr, flush=True)
    finally:
        metrics.end_measurement()  # Exclude shutdown time from FPS/CPU statistics.
        stop.set()
        if worker is not None:
            worker.join(timeout=3)
            if worker.is_alive():
                status, reason = "failed", "capture_worker_shutdown_timeout"
                session_stop.set()  # Never start another camera worker over this one.
                metrics.event("error", message="Capture worker did not stop in 3 s; session will exit")
        if backend is not None:
            backend.close()
        else:
            pygame.display.quit()
        app.PRESENCE_TIMEOUT = previous_timeout
    if status == "completed" and (metrics.measurement_started_s is None or (camera_mode and not any(x["phase"] == "measurement" for x in metrics.frames))):
        status = "insufficient_data"
    result = metrics.export(status, reason)
    print(f"[result] {status}: detection={result['summary']['actual_detection_fps']}; render={result['summary']['actual_renderer_fps']}", flush=True)
    return result


def main(argv=None):
    config, output = load_config(argv)
    if config["headless"]:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    sys.path.insert(0, config["raspieyes_dir"])
    import eye_renderer as app
    import pygame

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    output = output or Path(config["output_dir"]) / f"{config['mode']}_{stamp}.json"
    document = {
        "schema_version": 1, "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "running", "environment": metadata(config), "runs": [],
        "measurement_notes": [
            "CPU and RSS describe this whole process, including rendering, native worker threads and logging.",
            "detection_stage_ms includes input construction, model call and best-face selection; it is not model-kernel-only time.",
            "detection_calling_thread_cpu_ms excludes CPU time on native inference worker threads.",
            "process_cpu_ms_per_completed_frame includes all process work; it is not isolated inference CPU cost.",
            "capture_received_s is host frame receipt, not camera exposure time. Buffering may add unmeasured delay.",
            "host_frame_to_target_ms and observation_age_ms are software timings, not measured social reaction latency.",
            "headless render metrics do not represent physical display refresh or latency.",
            "Raw images/video and microphone audio are not saved. Native library stderr warnings remain in the terminal.",
            "Camera FPS reported by the driver is not measured independent capture throughput.",
        ],
    }
    write_json_atomic(output, document)
    print(f"[output] {output}", flush=True)
    session_stop = threading.Event()
    previous_handlers = {}
    for sig in (signal.SIGINT, signal.SIGTERM):
        previous_handlers[sig] = signal.signal(sig, lambda *_: session_stop.set())
    rates = config["benchmark_rates"] if config["mode"] == "benchmark" else [config["detection_fps"]]
    try:
        for rate in rates:
            current_config = {**config, "detection_fps": rate}
            def checkpoint(current):
                write_json_atomic(output, {**document, "runs": document["runs"] + [current]})
            result = run_once(current_config, app, pygame, session_stop, checkpoint)
            document["runs"].append(result)
            write_json_atomic(output, document)
            if result["status"] != "completed" or session_stop.is_set():
                break
        statuses = [run["status"] for run in document["runs"]]
        document["status"] = "failed" if "failed" in statuses else "interrupted" if session_stop.is_set() else "completed" if len(statuses) == len(rates) and all(x == "completed" for x in statuses) else "incomplete"
    finally:
        pygame.quit()
        document["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        if document["status"] == "running":
            document["status"] = "incomplete"
        write_json_atomic(output, document)
        for sig, handler in previous_handlers.items():
            signal.signal(sig, handler)
    print(f"[saved] {output}", flush=True)
    return 0 if document["status"] in ("completed", "interrupted") else 1


if __name__ == "__main__":
    raise SystemExit(main())
