"""Isolated standard-library tests with tiny synthetic FFmpeg fixtures.

Run: python -B test_sample_video.py --ffmpeg PATH --ffprobe PATH -v
When paths are omitted, ffmpeg and ffprobe are looked up on PATH. Tests requiring
them are explicitly skipped when either is unavailable. No media is downloaded.
"""

import argparse
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import sample_video


SCRIPT = Path(__file__).with_name("sample_video.py")
FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frames_at(times):
    return [{"index": index, "timestamp": Fraction(str(value)), "timestamp_field": "pts"}
            for index, value in enumerate(times)]


class SelectionTests(unittest.TestCase):
    def test_ties_choose_earlier_frame_and_final_frame_is_always_present(self):
        result = sample_video.choose_samples(frames_at([4, 4.4, 5.6, 6.4]), Fraction(1))
        self.assertEqual([s["frame_index"] for s in result], [0, 1, 2, 3])
        self.assertEqual(result[1]["requested_time_seconds"], 1)
        self.assertEqual(result[1]["actual_time_seconds"], 0.4)
        self.assertEqual(result[1]["actual_timestamp_seconds"], 4.4)
        self.assertEqual(result[-1]["reasons"], ["last_frame"])

    def test_duplicate_timestamps_and_grid_targets_are_deduplicated(self):
        result = sample_video.choose_samples(frames_at([0, 0, 1, 1]), Fraction(1, 1000000000))
        self.assertEqual([s["frame_index"] for s in result], [0, 2, 3])
        self.assertEqual(result[0]["interval_targets"]["count"], 500000001)
        self.assertEqual(result[1]["interval_targets"]["count"], 500000000)
        self.assertEqual(result[2]["reasons"], ["last_frame"])

    def test_frame_limit_includes_explicit_final_frame(self):
        result = sample_video.choose_samples(frames_at(range(600)), Fraction(1))
        self.assertEqual(len(result), 600)
        with self.assertRaisesRegex(sample_video.SamplingError, "600"):
            sample_video.choose_samples(frames_at(range(601)), Fraction(1))
        with self.assertRaisesRegex(sample_video.SamplingError, "including the last frame"):
            sample_video.choose_samples(frames_at([0, 1, 1.1]), Fraction(1), max_samples=2)

    def test_actual_integer_timestamps_take_precedence_over_rounded_text(self):
        frames = sample_video.parse_frames([
            {"best_effort_timestamp": 1001, "best_effort_timestamp_time": "0.033367"},
            {"best_effort_timestamp": 2002, "best_effort_timestamp_time": "0.066733"},
        ], {"time_base": "1/30000"})
        self.assertEqual(frames[0]["timestamp"], Fraction(1001, 30000))
        self.assertEqual(frames[1]["timestamp"], Fraction(1001, 15000))

    def test_missing_or_reversed_timestamps_fail_without_fps_estimates(self):
        with self.assertRaisesRegex(sample_video.SamplingError, "no actual"):
            sample_video.parse_frames([{}], {"time_base": "1/25", "avg_frame_rate": "25/1"})
        with self.assertRaisesRegex(sample_video.SamplingError, "monotonic"):
            sample_video.parse_frames([{"pts": 2}, {"pts": 1}], {"time_base": "1/25"})

    def test_invalid_intervals_are_rejected(self):
        for value in ("0", "-1", "nan", "inf", "-inf", "1e9999", "1e-9999", "junk"):
            with self.subTest(value=value), self.assertRaises(sample_video.SamplingError):
                sample_video.positive_interval(value)


class FailureReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="sample-video-unit-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_existing_directory_and_file_are_never_overwritten(self):
        for kind in ("directory", "file"):
            output = self.root / kind
            if kind == "directory":
                output.mkdir()
                sentinel = output / "receipt.json"
            else:
                sentinel = output
            sentinel.write_bytes(b"keep these exact bytes")
            with self.assertRaisesRegex(sample_video.SamplingError, "already exists"):
                sample_video.sample_video(self.root / "missing.mp4", output)
            self.assertEqual(sentinel.read_bytes(), b"keep these exact bytes")

    def test_invalid_input_preserves_failure_receipt(self):
        for index, input_path in enumerate((self.root / "missing.mp4", self.root, "https://example.invalid/video.mp4")):
            output = self.root / f"invalid-{index}"
            receipt = sample_video.sample_video(input_path, output)
            self.assertEqual(receipt["status"], "failed")
            self.assertIn("exact, existing regular file", receipt["error"]["message"])
            self.assertEqual(json.loads((output / "receipt.json").read_text(encoding="utf-8")), receipt)
            self.assertEqual(receipt["operations"], [])

    def test_invalid_interval_and_width_have_failure_receipts(self):
        for index, kwargs in enumerate(({"interval": "nan"}, {"interval": "0"}, {"max_width": 0}, {"max_width": "1.5"})):
            output = self.root / f"bad-setting-{index}"
            receipt = sample_video.sample_video(self.root / "missing.mp4", output, **kwargs)
            self.assertEqual(receipt["status"], "failed")
            self.assertTrue((output / "receipt.json").is_file())

    def test_missing_executable_preserves_source_hashes(self):
        source = self.root / "source.bin"
        source.write_bytes(b"synthetic input, not a video")
        before = digest(source)
        receipt = sample_video.sample_video(source, self.root / "missing-tool", ffmpeg=self.root / "missing.exe")
        self.assertEqual(receipt["status"], "failed")
        self.assertEqual(receipt["source"]["sha256_before"], before)
        self.assertEqual(receipt["source"]["sha256_after"], before)
        self.assertEqual(receipt["source"]["hash_comparison"], "unchanged")

    def test_source_mutation_is_detected(self):
        source = self.root / "source.bin"
        source.write_bytes(b"before")
        real_hash = sample_video.sha256
        calls = []

        def mutate_after_first_hash(path):
            value = real_hash(path)
            calls.append(path)
            if len(calls) == 1:
                source.write_bytes(b"after")
            return value

        with patch.object(sample_video, "sha256", side_effect=mutate_after_first_hash):
            receipt = sample_video.sample_video(source, self.root / "mutated", ffmpeg=self.root / "missing.exe")
        self.assertEqual(receipt["status"], "failed")
        self.assertEqual(receipt["source"]["hash_comparison"], "changed")
        self.assertEqual(receipt["error"]["type"], "SourceChanged")


class FFmpegFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not FFMPEG or not FFPROBE:
            raise unittest.SkipTest("ffmpeg/ffprobe unavailable; pass --ffmpeg PATH --ffprobe PATH")
        cls.temporary = tempfile.TemporaryDirectory(prefix="sample-video-fixtures-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        cls.cfr = cls.root / "CFR & source.mkv"
        cls.vfr = cls.root / "VFR source.mkv"
        cls.short = cls.root / "single frame.mkv"
        cls.slow = cls.root / "slow frames.mkv"
        cls.make_fixture(["-f", "lavfi", "-i", "testsrc2=size=96x64:rate=4:duration=2.5",
                          "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=8000:duration=2.5",
                          "-c:v", "ffv1", "-c:a", "pcm_s16le", "-shortest", str(cls.cfr)])
        cls.make_fixture(["-f", "lavfi", "-i", "testsrc2=size=96x64:rate=10:duration=2",
                          "-vf", "select='eq(n,0)+eq(n,3)+eq(n,9)+eq(n,15)+eq(n,19)'",
                          "-fps_mode", "vfr", "-c:v", "ffv1", str(cls.vfr)])
        cls.make_fixture(["-f", "lavfi", "-i", "color=c=red:size=32x24:rate=1:duration=1",
                          "-frames:v", "1", "-c:v", "ffv1", str(cls.short)])
        cls.make_fixture(["-f", "lavfi", "-i", "testsrc2=size=32x24:rate=1/2:duration=6",
                          "-c:v", "ffv1", str(cls.slow)])

    @classmethod
    def make_fixture(cls, extra):
        process = subprocess.run([FFMPEG, "-hide_banner", "-nostdin", "-v", "error", "-n", *extra],
                                 capture_output=True, check=False)
        if process.returncode:
            raise AssertionError(process.stderr.decode("utf-8", errors="replace"))

    def setUp(self):
        self.temporary_output = tempfile.TemporaryDirectory(prefix="sample-video-output-")
        self.addCleanup(self.temporary_output.cleanup)
        self.output_parent = Path(self.temporary_output.name)

    def sample(self, source, name="sheet", **kwargs):
        output = self.output_parent / name
        receipt = sample_video.sample_video(source, output, ffmpeg=FFMPEG, ffprobe=FFPROBE, **kwargs)
        self.assertEqual(receipt["status"], "completed", receipt.get("error"))
        persisted = json.loads((output / "receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(persisted, receipt)
        return receipt, output

    def test_cfr_count_exact_times_end_frame_unchanged_source_and_decode(self):
        before = digest(self.cfr)
        receipt, output = self.sample(self.cfr, decode=True)
        self.assertEqual(receipt["decoded_frames"]["count"], 10)
        self.assertEqual([s["frame_index"] for s in receipt["samples"]], [0, 4, 8, 9])
        self.assertEqual([s["actual_time_seconds"] for s in receipt["samples"]], [0, 1, 2, 2.25])
        self.assertEqual(receipt["samples"][-1]["reasons"], ["last_frame"])
        self.assertTrue(all(s["width"] == 96 and s["height"] == 64 for s in receipt["samples"]))
        self.assertEqual(receipt["decode_check"]["status"], "passed")
        self.assertEqual(receipt["source"]["sha256_before"], before)
        self.assertEqual(receipt["source"]["sha256_after"], before)
        self.assertEqual(digest(self.cfr), before)
        self.assertEqual(receipt["source"]["hash_comparison"], "unchanged")
        self.assertEqual(len(list(output.glob("*.png"))), 4)
        document = (output / "index.html").read_text(encoding="utf-8")
        self.assertIn("CFR &amp; source.mkv", document)
        self.assertIn('src="frame_000004.png"', document)
        self.assertNotIn(str(self.cfr), document)
        self.assertIn("does not establish continuous motion", document)
        self.assertIn("No playback or listening was performed", document)
        # Independently decode the actual final frame and compare unscaled pixels.
        expected = subprocess.run([FFMPEG, "-v", "error", "-i", str(self.cfr), "-vf", "select='eq(n,9)'",
                                   "-fps_mode", "vfr", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"],
                                  capture_output=True, check=True).stdout
        actual = subprocess.run([FFMPEG, "-v", "error", "-i", str(output / receipt["samples"][-1]["file"]),
                                 "-pix_fmt", "rgb24", "-f", "rawvideo", "-"],
                                capture_output=True, check=True).stdout
        self.assertEqual(actual, expected)

    def test_vfr_uses_actual_timestamps_and_requested_times_are_separate(self):
        receipt, _ = self.sample(self.vfr)
        self.assertEqual(receipt["decoded_frames"]["count"], 5)
        self.assertEqual([s["frame_index"] for s in receipt["samples"]], [0, 2, 4])
        self.assertEqual([s["actual_time_seconds"] for s in receipt["samples"]], [0, 0.9, 1.9])
        self.assertEqual(receipt["samples"][1]["requested_time_seconds"], 1)
        self.assertEqual(receipt["samples"][1]["actual_timestamp_seconds"], 0.9)
        self.assertEqual(receipt["decode_check"]["status"], "not_requested")

    def test_downscale_only_and_single_frame_deduplication(self):
        receipt, _ = self.sample(self.cfr, max_width=48)
        self.assertTrue(all(s["width"] == 48 and s["height"] == 32 for s in receipt["samples"]))
        single, _ = self.sample(self.short, name="single")
        self.assertEqual(single["sample_count"], 1)
        self.assertEqual(single["samples"][0]["reasons"], ["interval", "last_frame"])
        self.assertEqual(single["samples"][0]["width"], 32)

    def test_extraction_batches_preserve_selection_order(self):
        with patch.object(sample_video, "BATCH_SIZE", 2):
            receipt, _ = self.sample(self.cfr)
        batches = [op for op in receipt["operations"] if op["purpose"].startswith("extract batch")]
        self.assertEqual(len(batches), 2)
        self.assertEqual([s["frame_index"] for s in receipt["samples"]], [0, 4, 8, 9])
        self.assertEqual([s["file"] for s in receipt["samples"]],
                         [f"frame_{number:06d}.png" for number in range(1, 5)])

    def test_low_frame_rate_does_not_drop_selected_frames_at_png_export(self):
        receipt, _ = self.sample(self.slow)
        self.assertEqual(receipt["decoded_frames"]["count"], 3)
        self.assertEqual([s["frame_index"] for s in receipt["samples"]], [0, 1, 2])
        self.assertEqual([s["actual_time_seconds"] for s in receipt["samples"]], [0, 2, 4])

    def test_corrupt_file_retains_failure_receipt_and_hashes(self):
        source = self.output_parent / "invalid.mp4"
        source.write_bytes(b"This is deliberately not a media container.")
        output = self.output_parent / "failed"
        receipt = sample_video.sample_video(source, output, ffmpeg=FFMPEG, ffprobe=FFPROBE)
        self.assertEqual(receipt["status"], "failed")
        self.assertIn("probe streams failed", receipt["error"]["message"])
        self.assertEqual(receipt["source"]["hash_comparison"], "unchanged")
        self.assertTrue((output / "receipt.json").is_file())
        self.assertFalse((output / "index.html").exists())

    def test_cli_explicit_tools_and_refusal_to_overwrite(self):
        output = self.output_parent / "CLI output"
        command = [sys.executable, "-B", str(SCRIPT), str(self.vfr), "--out", str(output),
                   "--interval", "1", "--max-width", "48", "--ffmpeg", FFMPEG, "--ffprobe", FFPROBE]
        first = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(first.returncode, 0, first.stderr)
        before = (output / "receipt.json").read_bytes()
        second = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(second.returncode, 2)
        self.assertIn("already exists", second.stderr)
        self.assertEqual((output / "receipt.json").read_bytes(), before)

    def test_path_fallback(self):
        with patch.dict(os.environ, {"PATH": os.pathsep.join([str(Path(FFMPEG).parent), str(Path(FFPROBE).parent)])}):
            receipt = sample_video.sample_video(self.short, self.output_parent / "from-path")
        self.assertEqual(receipt["status"], "completed", receipt.get("error"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--ffmpeg")
    parser.add_argument("--ffprobe")
    options, unittest_args = parser.parse_known_args()
    FFMPEG = str(Path(options.ffmpeg).resolve()) if options.ffmpeg else FFMPEG
    FFPROBE = str(Path(options.ffprobe).resolve()) if options.ffprobe else FFPROBE
    unittest.main(argv=[sys.argv[0], *unittest_args])
