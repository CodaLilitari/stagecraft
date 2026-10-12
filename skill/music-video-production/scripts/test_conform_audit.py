"""Synthetic, isolated tests. Run: python -B -m unittest -v test_conform_audit.py"""
import copy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from conform_audit import audit_manifest, round_half_up, validate_ordinary_windows_path


SCRIPT = Path(__file__).with_name("conform_audit.py")


UNSAFE_WINDOWS_PATHS = (
    "media/clip.dat:receipt.json", "media/clip.dat::$DATA", "media:stream/clip.dat",
    r"\\?\C:\media\clip.dat", r"\\.\NUL", r"\??\C:\media\clip.dat",
    "//?/C:/media/clip.dat", "//./pipe/clip", "C:drive-relative.json",
    "NUL", "media/nUl.json", "media/CON/clip.dat", "media/PRN.txt", "media/AUX.dat",
    "media/COM1.txt", "media/LPT9", "media/COM¹.json", "media/LPT².dat",
    "media/CONIN$", "media/CONOUT$.txt", "media/NUL .txt",
    "media/clip.dat.", "media/clip.dat ", "media/dir./clip.dat",
    'media/bad"name.dat', "media/bad<name.dat", "media/bad>name.dat", "media/bad|name.dat",
    "media/bad?name.dat", "media/bad*name.dat", "media/bad\x00name.dat", "media/bad\x1fname.dat",
)


def valid_manifest():
    return {
        "schema_version": 1,
        "delivery": {"width": 1920, "height": 1080, "fps": "30/1", "duration_us": 2500000},
        "assets": [
            {"id": "v24", "path": "media/24.dat", "kind": "video", "duration_us": 2000000, "fps": "24/1"},
            {"id": "v30", "path": "media/30.dat", "kind": "video", "duration_us": 2000000, "fps": "30/1"},
            {"id": "song", "path": "media/song.dat", "kind": "audio", "duration_us": 2500000},
        ],
        "clips": [
            {"id": "fast", "asset_id": "v24", "timeline_in_us": 0, "timeline_out_us": 1000000,
             "source_in_us": 0, "source_out_us": 1500000, "speed": "3/2"},
            {"id": "slow", "asset_id": "v30", "timeline_in_us": 1000000, "timeline_out_us": 2500000,
             "source_in_us": 0, "source_out_us": 1000000, "speed": "2/3"},
        ],
        "audio": {"asset_id": "song", "timeline_in_us": 0, "source_in_us": 0, "source_out_us": 2500000},
    }


class ConformAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.manifest = self.root / "manifest.json"

    def save(self, data):
        self.manifest.write_text(json.dumps(data), encoding="utf-8")

    def audit(self, data, verify=False):
        self.save(data)
        return audit_manifest(self.manifest, verify)[0]

    def codes(self, report):
        return {issue["code"] for issue in report["issues"]}

    def cli(self, *extra):
        return subprocess.run([sys.executable, "-B", str(SCRIPT), str(self.manifest), *map(str, extra)],
                              text=True, capture_output=True, check=False)

    def create_assets(self, data):
        for asset in data["assets"]:
            path = self.root / asset["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            content = ("synthetic:" + asset["id"]).encode()
            path.write_bytes(content)
            asset["sha256"] = hashlib.sha256(content).hexdigest()

    def test_mixed_source_rates_and_fractional_speeds_metadata_only(self):
        report = self.audit(valid_manifest())
        self.assertEqual(report["status"], "valid", report["issues"])
        self.assertEqual([c["frame_count"] for c in report["clips"]], [30, 45])
        self.assertEqual(report["clips"][1]["diagnostic_last_consumed_source_us_exact"], "8800000/9")
        self.assertEqual(report["mode"], "supplied_metadata_only")
        self.assertTrue(all(a["existence_status"] == "not_checked" for a in report["assets"]))
        for key in ("native_import_status", "native_reopen_status", "perceptual_review_status"):
            self.assertEqual(report[key], "not_checked")

    def test_fractional_sequence_fps_and_exact_half_up(self):
        data = valid_manifest()
        data["delivery"]["fps"] = "30000/1001"
        report = self.audit(data)
        self.assertEqual(report["status"], "valid")
        self.assertEqual(report["clips"][-1]["exclusive_end_frame"], 75)
        self.assertEqual(round_half_up(Fraction(1, 2)), 1)
        self.assertEqual(round_half_up(Fraction(1499, 1000)), 1)
        self.assertEqual(round_half_up(Fraction(3, 2)), 2)

    def test_duration_tolerance_is_reported_and_does_not_hide_mismatch(self):
        data = valid_manifest()
        data["clips"][0]["source_out_us"] += 1
        report = self.audit(data)
        self.assertEqual(report["status"], "valid")
        row = next(r for r in report["residuals"] if r["kind"] == "duration_consistency")
        self.assertEqual(row["microseconds_exact"], "2/3")
        self.assertTrue(row["tolerated_nonzero"])
        data["settings"] = {"duration_tolerance_us": 0}
        self.assertIn("duration_speed_mismatch", self.codes(self.audit(data)))

    def test_clip_collapse_detected_after_shared_rounding(self):
        data = valid_manifest()
        data["clips"][0].update(timeline_out_us=1000, source_out_us=1500)
        data["clips"][1].update(timeline_in_us=1000, source_out_us=1666000)
        self.assertIn("zero_frame_clip", self.codes(self.audit(data)))

    def test_terminal_source_exhaustion_even_with_tolerated_one_us_residual(self):
        data = valid_manifest()
        data.pop("audio")
        data["delivery"]["duration_us"] = 1050000
        data["assets"][1]["duration_us"] = 33333
        data["clips"][0].update(timeline_out_us=1016666, source_out_us=1016666, speed="1/1")
        data["clips"][1].update(timeline_in_us=1016666, timeline_out_us=1050000,
                                source_out_us=33333, speed="1/1")
        report = self.audit(data)
        self.assertIn("terminal_source_exhaustion", self.codes(report))
        self.assertNotIn("duration_speed_mismatch", self.codes(report))
        self.assertEqual(report["clips"][1]["diagnostic_last_consumed_source_us_exact"], "100000/3")

    def test_gaps_overlaps_and_endpoints_are_strict(self):
        for value, expected in ((1000001, "timeline_gap"), (999999, "timeline_overlap")):
            with self.subTest(value=value):
                data = valid_manifest()
                data["settings"] = {"duration_tolerance_us": 100}
                data["clips"][1]["timeline_in_us"] = value
                self.assertIn(expected, self.codes(self.audit(data)))
        data = valid_manifest()
        data["delivery"]["duration_us"] += 1
        self.assertIn("incomplete_coverage", self.codes(self.audit(data)))

    def test_source_interval_and_timeline_bounds(self):
        for target, expected in (("source", "source_out_of_bounds"), ("timeline", "timeline_out_of_bounds")):
            with self.subTest(target=target):
                data = valid_manifest()
                data["clips"][-1][target + "_out_us"] = 3000000
                self.assertIn(expected, self.codes(self.audit(data)))

    def test_invalid_rationals_rejected_for_fps_speed_and_asset_fps(self):
        for bad in ("0/1", "-1/1", "1/0", "NaN", "Infinity", "1.5", "1//2", 30, True, None):
            for target in ("delivery", "clip", "asset"):
                with self.subTest(bad=bad, target=target):
                    data = valid_manifest()
                    obj, field = {"delivery": (data["delivery"], "fps"), "clip": (data["clips"][0], "speed"),
                                  "asset": (data["assets"][0], "fps")}[target]
                    obj[field] = bad
                    self.assertIn("invalid_rational", self.codes(self.audit(data)))

    def test_exact_integer_times_and_positive_geometry(self):
        for bad in (-1, 1.0, "1", True, None):
            with self.subTest(bad=bad):
                data = valid_manifest()
                data["clips"][0]["source_in_us"] = bad
                self.assertIn("invalid_integer", self.codes(self.audit(data)))
        data = valid_manifest()
        data["delivery"]["width"] = 0
        self.assertIn("invalid_integer", self.codes(self.audit(data)))

    def test_duplicate_ids_unknown_references_and_wrong_types(self):
        mutations = [
            (lambda d: d["assets"].append(copy.deepcopy(d["assets"][0])), "duplicate_id"),
            (lambda d: d["clips"][1].update(id="fast"), "duplicate_id"),
            (lambda d: d["clips"][0].update(asset_id="missing"), "unknown_asset"),
            (lambda d: d["clips"][0].update(asset_id="song"), "asset_type_mismatch"),
            (lambda d: d["audio"].update(asset_id="v24"), "asset_type_mismatch"),
        ]
        for mutation, expected in mutations:
            with self.subTest(expected=expected):
                data = valid_manifest()
                mutation(data)
                self.assertIn(expected, self.codes(self.audit(data)))

    def test_unsafe_paths_rejected_portably(self):
        for bad in ("../outside.dat", "..\\outside.dat", "/absolute.dat", "C:\\absolute.dat",
                    "C:drive-relative.dat", "\\\\server\\share\\file.dat", "bad\x00name"):
            with self.subTest(path=bad):
                data = valid_manifest()
                data["assets"][0]["path"] = bad
                self.assertIn("unsafe_asset_path", self.codes(self.audit(data)))

    def test_windows_stream_device_and_ambiguous_syntax_rejected_on_every_os(self):
        for bad in UNSAFE_WINDOWS_PATHS:
            with self.subTest(path=bad):
                with self.assertRaises(ValueError):
                    validate_ordinary_windows_path(bad)
                data = valid_manifest()
                data["assets"][0]["path"] = bad
                report = self.audit(data, True)
                self.assertIn("unsafe_asset_path", self.codes(report))
                self.assertEqual(report["assets"][0]["existence_status"], "not_checked")
                self.assertEqual(report["assets"][0]["hash_status"], "not_checked")
                self.assertNotIn("observed_sha256", report["assets"][0])

    def test_ordinary_windows_path_syntax_remains_accepted(self):
        for path in ("media/clip.dat", r"media\clip.dat", "./media/clip.dat", ".hidden",
                     "media/revision 2.json", "media/révision.json", "com10.dat", "nulled.dat",
                     r"C:\Review files\receipt.json", r"\\server\share\receipt.json",
                     "/tmp/receipt.json", "../receipt.json"):
            with self.subTest(path=path):
                validate_ordinary_windows_path(path)
        data = valid_manifest()
        data["assets"][0]["path"] = "media/révision 2.dat"
        self.create_assets(data)
        report = self.audit(data, True)
        self.assertEqual(report["status"], "valid", report["issues"])

    def test_hash_checks_only_when_requested(self):
        data = valid_manifest()
        self.assertEqual(self.audit(data)["status"], "valid")
        self.assertIn("asset_read_error", self.codes(self.audit(data, True)))
        self.create_assets(data)
        report = self.audit(data, True)
        self.assertEqual(report["status"], "valid", report["issues"])
        self.assertTrue(all(a["hash_status"] == "matched" for a in report["assets"]))
        (self.root / data["assets"][0]["path"]).write_bytes(b"changed")
        self.assertIn("hash_mismatch", self.codes(self.audit(data, True)))
        self.assertEqual(self.audit(data)["status"], "valid")

    def test_optional_hash_is_observed_without_preservation_claim(self):
        data = valid_manifest()
        self.create_assets(data)
        del data["assets"][0]["sha256"]
        report = self.audit(data, True)
        self.assertEqual(report["assets"][0]["hash_status"], "observed_without_expected")
        data["assets"][0]["sha256"] = "bad-hash"
        self.assertIn("invalid_sha256", self.codes(self.audit(data)))

    def test_malformed_and_nonfinite_json_produce_receipts(self):
        for text in ('{"schema_version":', '{"schema_version": NaN}', '{"schema_version": 1e10000}', '[]'):
            with self.subTest(text=text):
                self.manifest.write_text(text, encoding="utf-8")
                report, _ = audit_manifest(self.manifest)
                self.assertEqual(report["status"], "invalid")
                self.assertTrue(report["issues"])

    def test_duplicate_json_members_rejected_at_any_depth_after_escape_decoding(self):
        original = json.dumps(valid_manifest())
        cases = (
            original.replace('"schema_version": 1', '"schema_version": 0, "schema_version": 1', 1),
            original.replace('"timeline_out_us": 1000000',
                             '"timeline_out_us": 2000000, "timeline_out_us": 1000000', 1),
            original.replace('"path": "media/24.dat"',
                             '"pa\\u0074h": "elsewhere.dat", "path": "media/24.dat"', 1),
            original[:-1] + ', "notes": [{"label": "first", "label": "second"}]}',
        )
        for index, text in enumerate(cases):
            with self.subTest(case=index):
                self.manifest.write_text(text, encoding="utf-8")
                before = self.manifest.read_bytes()
                report, _ = audit_manifest(self.manifest, True)
                self.assertEqual(report["status"], "invalid")
                self.assertEqual(self.codes(report), {"manifest_read_error"})
                self.assertIn("Duplicate JSON member", report["issues"][0]["message"])
                self.assertEqual(report["assets"], [])
                self.assertEqual(self.manifest.read_bytes(), before)
        output = self.root / "duplicate.json"
        result = self.cli("--out", output)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(output.read_text())["status"], "invalid")

    def test_audio_source_bounds_and_delivery_endpoint(self):
        data = valid_manifest()
        data["audio"]["source_out_us"] += 1
        report = self.audit(data)
        self.assertIn("source_out_of_bounds", self.codes(report))
        self.assertIn("audio_out_of_bounds", self.codes(report))

    def test_cli_valid_and_invalid_receipts_and_nonzero_exit(self):
        data = valid_manifest()
        self.save(data)
        before = self.manifest.read_bytes()
        output = self.root / "valid.json"
        result = self.cli("--out", output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(output.read_text())["status"], "valid")
        self.assertEqual(self.manifest.read_bytes(), before)
        data["clips"][0]["speed"] = "NaN"
        self.save(data)
        invalid = self.root / "invalid.json"
        result = self.cli("--out", invalid)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(invalid.read_text())["status"], "invalid")

    def test_output_never_overwrites_manifest_assets_or_receipts(self):
        data = valid_manifest()
        self.create_assets(data)
        self.save(data)
        existing = self.root / "existing.json"
        existing.write_bytes(b"preserve receipt")
        for target in (self.manifest, self.root / data["assets"][0]["path"], existing):
            with self.subTest(target=target.name):
                before = target.read_bytes()
                self.assertEqual(self.cli("--out", target).returncode, 2)
                self.assertEqual(target.read_bytes(), before)
        missing_asset = self.root / data["assets"][1]["path"]
        missing_asset.unlink()
        self.assertEqual(self.cli("--out", missing_asset).returncode, 2)
        self.assertFalse(missing_asset.exists())

    def test_cli_rejects_unsafe_output_syntax_before_creating_anything(self):
        self.save(valid_manifest())
        before = self.manifest.read_bytes()
        for bad in ("receipt.json:stream", "NUL.json", "COM1", "CONIN$", "receipt.json.",
                    "receipt.json ", 'bad"name.json', "bad|name.json", "bad?name.json"):
            with self.subTest(path=bad):
                result = self.cli("--out", str(self.root) + "/" + bad)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("Invalid receipt output path", result.stderr)
                self.assertEqual(self.manifest.read_bytes(), before)
                self.assertEqual(list(self.root.iterdir()), [self.manifest])
        for bad in (r"\\?\C:\receipt.json", r"\\.\NUL", r"\??\C:\receipt.json", "C:receipt.json"):
            with self.subTest(path=bad):
                result = self.cli("--out", bad)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("Invalid receipt output path", result.stderr)

    @unittest.skipUnless(sys.platform == "win32", "Windows alternate-stream regression")
    def test_output_cannot_add_named_streams_to_protected_inputs_on_windows(self):
        data = valid_manifest()
        self.create_assets(data)
        self.save(data)
        for target in (self.manifest, self.root / data["assets"][0]["path"]):
            with self.subTest(target=target.name):
                before = target.read_bytes()
                stream = Path(str(target) + ":audit-receipt.json")
                self.assertFalse(stream.exists())
                result = self.cli("--out", stream, "--verify-hashes")
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("Invalid receipt output path", result.stderr)
                self.assertFalse(stream.exists())
                self.assertEqual(target.read_bytes(), before)

    @unittest.skipUnless(sys.platform == "win32", "Windows alternate-stream regression")
    def test_existing_named_stream_is_not_read_as_listed_media_on_windows(self):
        data = valid_manifest()
        self.create_assets(data)
        ordinary = self.root / data["assets"][0]["path"]
        before = ordinary.read_bytes()
        stream = Path(str(ordinary) + ":synthetic-media")
        stream.write_bytes(b"isolated synthetic stream")
        data["assets"][0]["path"] += ":synthetic-media"
        report = self.audit(data, True)
        self.assertIn("unsafe_asset_path", self.codes(report))
        self.assertEqual(report["assets"][0]["existence_status"], "not_checked")
        self.assertEqual(report["assets"][0]["hash_status"], "not_checked")
        self.assertNotIn("observed_sha256", report["assets"][0])
        self.assertEqual(ordinary.read_bytes(), before)
        self.assertEqual(stream.read_bytes(), b"isolated synthetic stream")

    def test_invalid_top_level_shapes_do_not_crash(self):
        for key, value in (("delivery", []), ("assets", {}), ("clips", {}), ("audio", []), ("settings", [])):
            with self.subTest(key=key):
                data = valid_manifest()
                data[key] = value
                self.assertEqual(self.audit(data)["status"], "invalid")


if __name__ == "__main__":
    unittest.main()
