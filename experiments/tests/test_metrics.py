import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from metrics import RunMetrics, distribution, write_json_atomic


class MetricsTests(unittest.TestCase):
    def test_percentiles_and_empty_data(self):
        self.assertEqual(distribution([])["p95"], None)
        values = [4, 1, 3, 2]
        result = distribution(values)
        self.assertEqual(result["mean"], 2.5)
        self.assertEqual(result["p50"], 2.5)
        self.assertAlmostEqual(result["p95"], 3.85)
        self.assertAlmostEqual(result["p99"], 3.97)
        self.assertEqual(values, [4, 1, 3, 2])

    def test_summary_excludes_warmup_and_uses_completed_frames(self):
        metrics = RunMetrics({"sample_interval_s": 1, "detection_fps": 999})
        metrics.started_s = 0
        metrics.measurement_started_s = 10
        metrics.measurement_cpu_started_s = 1
        for captured in (9, 10.2, 11.2):
            metrics.observe_detection({
                "event": "frame", "monotonic_s": captured + 0.1,
                "capture_received_s": captured, "completed_s": captured + 0.1,
                "face_detected": False, "capture_wait_ms": 5,
                "preprocessing_ms": 1, "detection_stage_ms": 20,
                "detection_calling_thread_cpu_ms": 3,
                "host_frame_to_target_ms": 21, "cycle_work_ms": 26,
            })
        metrics.measurement_ended_s = 12
        metrics.measurement_cpu_ended_s = 1.5
        summary = metrics.export("completed", "duration_reached")["summary"]
        self.assertEqual(summary["completed_detection_frames"], 2)
        self.assertEqual(summary["actual_detection_fps"], 1)
        self.assertEqual(summary["mean_process_cpu_percent_one_core"], 25)
        self.assertEqual(summary["process_cpu_ms_per_completed_frame"], 250)
        self.assertIsNone(summary["actual_renderer_fps"])
        self.assertEqual(summary["detection_stage_ms"]["count"], 2)

    def test_atomic_checkpoint_is_valid_json_without_nan(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.json"
            write_json_atomic(path, {"status": "running", "value": None})
            write_json_atomic(path, {"status": "completed", "value": 0})
            self.assertEqual(json.loads(path.read_text())["status"], "completed")
            self.assertFalse(path.with_name(path.name + ".tmp").exists())
            with self.assertRaises(ValueError):
                write_json_atomic(path, {"value": float("nan")})
            self.assertEqual(json.loads(path.read_text())["status"], "completed")


if __name__ == "__main__":
    unittest.main()
