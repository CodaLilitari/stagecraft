"""Synthetic tests for song_map.py. Needs numpy and ffmpeg (Claude's cloud workspace)."""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import song_map  # noqa: E402

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

SR = 22050


def run_quiet(argv: list[str]) -> int:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return song_map.main(argv)


def write_wav(path: Path, signal) -> None:
    clipped = np.clip(signal, -1.0, 1.0)
    data = (clipped * 32767).astype("<i2").tobytes()
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes(data)


def click_track(bpm: float, seconds: float, offset: float = 0.25, seed: int = 1):
    rng = np.random.default_rng(seed)
    out = np.zeros(int(SR * seconds))
    burst = rng.standard_normal(int(0.012 * SR)) * np.exp(-np.linspace(0, 6, int(0.012 * SR)))
    period = 60.0 / bpm
    times = np.arange(offset, seconds - 0.05, period)
    for t in times:
        i = int(t * SR)
        out[i:i + burst.size] += 0.8 * burst[: max(0, min(burst.size, out.size - i))]
    return out, times


@unittest.skipIf(np is None or shutil.which("ffmpeg") is None, "needs numpy and ffmpeg")
class SongMapTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def analyse(self, signal, name: str = "s.wav") -> dict:
        path = self.root / name
        write_wav(path, signal)
        return song_map.analyse(path, SR)

    def test_tempo_and_beats_at_120(self) -> None:
        signal, truth = click_track(120, 30)
        result = self.analyse(signal)
        self.assertAlmostEqual(result["tempo"]["bpm"], 120, delta=2.0)
        beats = np.array(result["beats"]["times_s"])
        hits = sum(np.min(np.abs(beats - t)) <= 0.035 for t in truth[2:-2])
        self.assertGreaterEqual(hits / len(truth[2:-2]), 0.9)
        self.assertLessEqual(result["tempo"]["stability"]["max_deviation_pct"], 3.0)

    def test_168_reports_octave_alternatives(self) -> None:
        signal, _ = click_track(168, 30)
        result = self.analyse(signal)
        bpm = result["tempo"]["bpm"]
        self.assertTrue(abs(bpm - 168) <= 3 or abs(bpm - 84) <= 2, bpm)
        self.assertEqual(len(result["tempo"]["octave_alternatives"]), 2)

    def test_prior_picks_octave_without_forcing_it(self) -> None:
        for bpm in (168, 84):
            signal, _ = click_track(bpm, 40, seed=5)
            path = self.root / f"p{bpm}.wav"
            write_wav(path, signal)
            result = song_map.analyse(path, SR, start_bpm=168)
            self.assertAlmostEqual(result["tempo"]["bpm"], bpm, delta=1.0)

    def test_section_change_is_found(self) -> None:
        rng = np.random.default_rng(7)
        seconds = 64
        clicks, _ = click_track(120, seconds)
        t = np.arange(int(SR * seconds)) / SR
        bed = np.where(t < 32, 0.25 * np.sin(2 * np.pi * 110 * t), 0.25 * rng.standard_normal(t.size))
        result = self.analyse(clicks + bed)
        boundaries = [b["time_s"] for b in result["sections"]["boundaries"]]
        self.assertTrue(any(abs(b - 32) <= 3 for b in boundaries), boundaries)

    def test_silence_is_reported_not_invented(self) -> None:
        with self.assertRaises(song_map.SongMapError):
            self.analyse(np.zeros(SR * 5))

    def test_cli_writes_new_directory_only(self) -> None:
        signal, _ = click_track(100, 20)
        source = self.root / "x.wav"
        write_wav(source, signal)
        out = self.root / "map"
        self.assertEqual(run_quiet([str(source), "--out", str(out)]), 0)
        data = json.loads((out / "song-map.json").read_text())
        self.assertEqual(data["schema"], song_map.SCHEMA)
        self.assertTrue((out / "beats.csv").is_file())
        self.assertEqual(run_quiet([str(source), "--out", str(out)]), 2)

    def test_click_preview_ticks_on_beats(self) -> None:
        signal, _ = click_track(110, 20, seed=3)
        source = self.root / "y.wav"
        write_wav(source, 0.3 * signal)
        out = self.root / "map2"
        self.assertEqual(run_quiet([str(source), "--out", str(out), "--click-preview"]), 0)
        data = json.loads((out / "song-map.json").read_text())
        with wave.open(str(out / "click-preview.wav"), "rb") as handle:
            self.assertEqual((handle.getnchannels(), handle.getsampwidth(), handle.getframerate()), (1, 2, SR))
            frames = np.frombuffer(handle.readframes(handle.getnframes()), dtype="<i2").astype(float)
        self.assertAlmostEqual(frames.size / SR, data["decode"]["duration_s"], delta=0.01)
        # a 1760 Hz tick should start at every estimated beat
        n = int(0.02 * SR)
        tone = np.sin(2 * np.pi * 1760.0 * np.arange(n) / SR)
        on = [abs(np.dot(frames[int(t * SR):int(t * SR) + n], tone)) for t in data["beats"]["times_s"][2:-2]]
        off = [abs(np.dot(frames[int((t + 0.2) * SR):int((t + 0.2) * SR) + n], tone)) for t in data["beats"]["times_s"][2:-2]]
        self.assertGreater(np.median(on), 10 * max(1.0, np.median(off)))

    def test_click_preview_needs_out(self) -> None:
        signal, _ = click_track(100, 10)
        source = self.root / "z.wav"
        write_wav(source, signal)
        self.assertEqual(run_quiet([str(source), "--click-preview"]), 2)


if __name__ == "__main__":
    unittest.main()
