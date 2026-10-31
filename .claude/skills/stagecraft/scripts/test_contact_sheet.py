"""Tests for contact_sheet.py. Needs ffmpeg/ffprobe (for a real sample run) and Pillow."""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import contact_sheet  # noqa: E402

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None


def quiet(func, *args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = func(*args)
    return code, out.getvalue(), err.getvalue()


@unittest.skipIf(Image is None or not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
                 "needs Pillow, ffmpeg and ffprobe")
class ContactSheetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        video = cls.root / "synthetic.mkv"
        subprocess.run(["ffmpeg", "-v", "error", "-n", "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=24",
                        "-t", "3", "-c:v", "ffv1", str(video)], check=True)
        cls.samples = cls.root / "samples"
        subprocess.run([sys.executable, "-B", str(HERE / "sample_video.py"), str(video), "--out", str(cls.samples)],
                       check=True, capture_output=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def setUp(self) -> None:
        self.out_dir = Path(tempfile.mkdtemp(dir=self.root))

    def test_builds_labelled_sheet(self) -> None:
        out = self.out_dir / "sheet.png"
        code, stdout, _ = quiet(contact_sheet.main, [str(self.samples), "--out", str(out), "--tile-width", "160"])
        self.assertEqual(code, 0)
        report = json.loads(stdout)
        self.assertEqual(len(report["tiles"]), 4)
        with Image.open(out) as image:
            self.assertEqual(image.width, 4 * 160 + 5 * contact_sheet.PAD)
            self.assertEqual(image.height, 90 + contact_sheet.LABEL_HEIGHT + 2 * contact_sheet.PAD)

    def test_time_range_selects_subset(self) -> None:
        out = self.out_dir / "range.png"
        code, stdout, _ = quiet(contact_sheet.main, [str(self.samples), "--out", str(out), "--start", "0.5", "--end", "2.1"])
        self.assertEqual(code, 0)
        times = [t["actual_time_seconds"] for t in json.loads(stdout)["tiles"]]
        self.assertEqual(len(times), 2)
        self.assertTrue(all(0.5 <= t <= 2.1 for t in times))

    def test_refuses_existing_output_and_inside_sample_dir(self) -> None:
        out = self.out_dir / "exists.png"
        out.write_bytes(b"")
        self.assertEqual(quiet(contact_sheet.main, [str(self.samples), "--out", str(out)])[0], 2)
        inside = self.samples / "sheet.png"
        self.assertEqual(quiet(contact_sheet.main, [str(self.samples), "--out", str(inside)])[0], 2)
        self.assertFalse(inside.exists())

    def test_tampered_frame_is_refused(self) -> None:
        copy = self.out_dir / "copy"
        shutil.copytree(self.samples, copy)
        frame = sorted(copy.glob("frame_*.png"))[1]
        with Image.open(frame) as image:
            image.rotate(180).save(frame)
        out = self.out_dir / "tampered.png"
        code, _, err = quiet(contact_sheet.main, [str(copy), "--out", str(out)])
        self.assertEqual(code, 2)
        self.assertIn("receipt hash", err)
        self.assertFalse(out.exists())

    def test_max_tiles_guard(self) -> None:
        out = self.out_dir / "big.png"
        code, _, err = quiet(contact_sheet.main, [str(self.samples), "--out", str(out), "--max-tiles", "2"])
        self.assertEqual(code, 2)
        self.assertIn("max-tiles", err)


if __name__ == "__main__":
    unittest.main()
