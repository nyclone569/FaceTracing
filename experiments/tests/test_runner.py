"""Integration checks use generated video, never the laptop webcam."""

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "experiments" / "run_raspieyes.py"


class RunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import cv2
        import numpy as np

        cls.temporary = tempfile.TemporaryDirectory()
        cls.directory = Path(cls.temporary.name)
        cls.video = cls.directory / "blank.avi"
        writer = cv2.VideoWriter(str(cls.video), cv2.VideoWriter_fourcc(*"MJPG"), 30, (320, 240))
        if not writer.isOpened():
            raise RuntimeError("MJPG VideoWriter is unavailable")
        try:
            for _ in range(90):
                writer.write(np.zeros((240, 320, 3), dtype=np.uint8))
        finally:
            writer.release()

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def execute(self, name, *arguments, expected_code=0):
        output = self.directory / f"{name}.json"
        command = [sys.executable, str(RUNNER), "--output", str(output),
                   "--headless", "--duration", "0.5", "--warmup", "0", *arguments]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=40, cwd=self.directory)
        self.assertEqual(completed.returncode, expected_code, completed.stdout + completed.stderr)
        return json.loads(output.read_text())

    def test_idle_renderer_records_real_frames(self):
        result = self.execute("idle", "--mode", "idle")
        self.assertEqual(result["status"], "completed")
        summary = result["runs"][0]["summary"]
        self.assertGreater(summary["rendered_frames"], 0)
        self.assertGreater(summary["actual_renderer_fps"], 0)
        self.assertIsNone(summary["actual_detection_fps"])

    def test_dnn_benchmark_records_each_rate_without_rendering(self):
        result = self.execute("benchmark", "--mode", "benchmark", "--video", str(self.video),
                              "--detector", "dnn", "--perception-only", "--rates", "5", "10", "15")
        self.assertEqual(result["status"], "completed")
        self.assertEqual([r["config"]["detection_fps"] for r in result["runs"]], [5, 10, 15])
        for run in result["runs"]:
            self.assertEqual(run["actual_detector"], "dnn")
            self.assertGreater(run["summary"]["completed_detection_frames"], 0)
            self.assertIsNone(run["summary"]["actual_renderer_fps"])
            self.assertEqual(run["summary"]["face_detected_frames"], 0)
            self.assertGreater(run["summary"]["detection_stage_ms"]["p95"], 0)

    def test_mediapipe_model_runs_on_recorded_input(self):
        result = self.execute("mediapipe", "--video", str(self.video), "--perception-only")
        run = result["runs"][0]
        self.assertEqual(run["actual_detector"], "mediapipe")
        self.assertGreater(run["summary"]["completed_detection_frames"], 0)
        self.assertEqual(run["summary"]["face_detected_frames"], 0)

    def test_source_open_error_still_saves_json(self):
        result = self.execute("failure", "--video", str(self.directory / "missing.avi"),
                              "--detector", "haar", "--perception-only", expected_code=1)
        self.assertEqual(result["status"], "failed")
        run = result["runs"][0]
        self.assertTrue(any(e["event"] == "error" for e in run["events"]))
        self.assertIsNone(run["summary"]["actual_detection_fps"])

    @unittest.skipUnless(os.name == "posix", "POSIX signal check")
    def test_sigterm_saves_partial_measurement(self):
        output = self.directory / "interrupted.json"
        config = self.directory / "interrupt-config.json"
        settings = json.loads((ROOT / "experiments" / "config.json").read_text())
        settings.update(raspieyes_dir=str(ROOT / "raspieyes"), output_dir=str(self.directory),
                        checkpoint_interval_s=0.1)
        config.write_text(json.dumps(settings))
        command = [sys.executable, str(RUNNER), "--config", str(config), "--mode", "idle",
                   "--headless", "--output", str(output), "--duration", "10", "--warmup", "0"]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if output.exists():
                    data = json.loads(output.read_text())
                    if data["runs"] and data["runs"][0]["summary"]["rendered_frames"] > 0:
                        break
                if process.poll() is not None:
                    self.fail("Runner exited before the interruption checkpoint")
                time.sleep(0.05)
            else:
                self.fail("Runner did not produce a checkpoint")
            process.send_signal(signal.SIGTERM)
            stdout, stderr = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 0, stdout + stderr)
            result = json.loads(output.read_text())
            self.assertEqual(result["status"], "interrupted")
            self.assertGreater(result["runs"][0]["summary"]["rendered_frames"], 0)
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate()


if __name__ == "__main__":
    unittest.main()
