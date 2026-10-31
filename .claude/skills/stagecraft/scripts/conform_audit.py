"""Audit an explicit source-conform manifest; never render or operate an editor.

Usage: conform_audit.py MANIFEST --out NEW_RECEIPT [--verify-hashes]
Times are integer microseconds. FPS and speeds are positive rational strings.
The duration tolerance applies only to source-span/speed versus timeline span.
Coverage, source bounds, and finite-frame source exhaustion are always strict.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
import ntpath
from pathlib import Path
import re
import sys


def rational_text(value):
    return f"{value.numerator}/{value.denominator}"


def round_half_up(value):
    """Exact nearest-integer rounding for nonnegative Fraction values."""
    if value < 0:
        raise ValueError("Frame positions must be nonnegative")
    return (2 * value.numerator + value.denominator) // (2 * value.denominator)


def validate_ordinary_windows_path(value, *, relative_only=False):
    """Reject streams, device namespaces/names, and ambiguous Win32 syntax on every OS.

    This is a lexical file-path policy, not a filesystem or race-safety check.
    Ordinary absolute output paths may include a drive or UNC share. Listed assets
    must be relative; their resolved package containment is checked separately.
    """
    if not isinstance(value, str) or not value:
        raise ValueError("Expected a nonempty file path")
    normalized = value.replace("/", "\\")
    if normalized.startswith(("\\\\?\\", "\\\\.\\", "\\??\\", "\\\\??\\")):
        raise ValueError("Windows device and extended path namespaces are forbidden")
    drive, tail = ntpath.splitdrive(normalized)
    if relative_only and (drive or normalized.startswith("\\")):
        raise ValueError("Absolute and drive-qualified paths are forbidden")
    if drive and not drive.startswith("\\\\"):
        if not re.fullmatch(r"[A-Za-z]:", drive) or not tail.startswith("\\"):
            raise ValueError("Drive-relative or malformed drive paths are forbidden")
        components = tail.split("\\")
    else:
        components = normalized.split("\\")
    for component in components:
        if component in ("", ".", ".."):
            continue
        if re.search(r'[<>:"|?*\x00-\x1f]', component):
            raise ValueError("Streams, control characters, and reserved filename characters are forbidden")
        if component.endswith((".", " ")):
            raise ValueError("File path components may not end with a dot or space")
        stem = component.split(".", 1)[0].rstrip(" ").upper()
        if stem in ("CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$") or re.fullmatch(r"(?:COM|LPT)[1-9¹²³]", stem):
            raise ValueError("Windows reserved device names are forbidden")


def unique_json_object(pairs):
    """Reject duplicate decoded member names in every JSON object."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON member: {key!r}")
        result[key] = value
    return result


def audit_manifest(manifest_path, verify_hashes=False):
    """Return (JSON-serializable receipt, protected input paths)."""
    manifest_path = Path(manifest_path).resolve()
    protected = {manifest_path}
    report = {
        "receipt_schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "manifest": str(manifest_path),
        "mode": "file_and_hash_checks" if verify_hashes else "supplied_metadata_only",
        "metadata_status": "supplied metadata; media properties not independently verified",
        "native_import_status": "not_checked",
        "native_reopen_status": "not_checked",
        "perceptual_review_status": "not_checked",
        "issues": [], "residuals": [], "assets": [], "clips": [],
        "capabilities": [
            "Exact rational timing, cumulative frame rounding, and metadata bounds",
            "Explicit listed paths only; no directory discovery or media decoding",
            "File existence and SHA-256 checks only with --verify-hashes",
            "Receipt creation only; no edits to manifest or media",
        ],
        "limits": [
            "Supplied duration, FPS, channel, geometry, and codec metadata are not probed",
            "Finite-frame mapping is a diagnostic model, not host frame-selection evidence",
            "Source FPS metadata does not prove constant frame rate or decoded frame availability",
            "No native import, relink, save/reopen, rendering, audio routing, or perceptual checks",
            "No expected asset hash means an observed hash alone cannot prove preservation",
            "Duration tolerance never permits timeline gaps, overlaps, or source exhaustion",
            "No lock prevents another process changing sources during or after this audit",
        ],
    }

    def issue(code, location, message):
        report["issues"].append({"code": code, "location": location, "message": message})

    def integer(value, location, minimum=0):
        if type(value) is not int or value < minimum:
            issue("invalid_integer", location, f"Expected integer >= {minimum}; booleans are not times")
            return None
        return value

    def ratio(value, location):
        if not isinstance(value, str) or not re.fullmatch(r"[+-]?\d+(?:/[+-]?\d+)?", value):
            issue("invalid_rational", location, "Expected a positive finite rational string, e.g. 30000/1001")
            return None
        try:
            result = Fraction(value)
        except (ValueError, ZeroDivisionError):
            result = None
        if result is None or result <= 0:
            issue("invalid_rational", location, "Rational must be finite, positive, and have a nonzero denominator")
            return None
        return result

    def identifier(value, location, seen):
        if not isinstance(value, str) or not value or value.strip() != value:
            issue("invalid_id", location, "Expected a nonempty, trimmed string ID")
            return False
        if value in seen:
            issue("duplicate_id", location, f"Duplicate ID: {value}")
            return False
        seen.add(value)
        return True

    def interval(obj, prefix, location):
        start = integer(obj.get(prefix + "_in_us"), location + "." + prefix + "_in_us")
        end = integer(obj.get(prefix + "_out_us"), location + "." + prefix + "_out_us")
        if start is None or end is None:
            return None
        if end <= start:
            issue("invalid_interval", location, f"{prefix} interval must have positive length")
            return None
        return start, end

    def residual(kind, clip_id, value, tolerance=None):
        row = {"kind": kind, "clip_id": clip_id, "microseconds_exact": rational_text(value)}
        if tolerance is not None:
            row.update(tolerance_us=tolerance, within_tolerance=abs(value) <= tolerance,
                       tolerated_nonzero=value != 0 and abs(value) <= tolerance)
        report["residuals"].append(row)

    try:
        payload = manifest_path.read_bytes()
        report["manifest_sha256"] = hashlib.sha256(payload).hexdigest()
        def reject_constant(value):
            raise ValueError(f"Non-finite JSON number: {value}")
        def finite_float(value):
            result = float(value)
            if not math.isfinite(result):
                reject_constant(value)
            return result
        data = json.loads(payload, parse_constant=reject_constant, parse_float=finite_float,
                          object_pairs_hook=unique_json_object)
    except (OSError, ValueError) as error:
        issue("manifest_read_error", "$", str(error))
        report["status"] = "invalid"
        return report, protected
    if not isinstance(data, dict):
        issue("invalid_manifest", "$", "Manifest must be an object")
        report["status"] = "invalid"
        return report, protected
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        issue("unsupported_schema", "schema_version", "Expected integer schema_version 1")

    delivery = data.get("delivery")
    if not isinstance(delivery, dict):
        issue("invalid_delivery", "delivery", "Expected an object")
        delivery = {}
    for key in ("width", "height"):
        integer(delivery.get(key), "delivery." + key, 1)
    fps = ratio(delivery.get("fps"), "delivery.fps")
    duration = integer(delivery.get("duration_us"), "delivery.duration_us", 1)
    settings = data.get("settings", {})
    if not isinstance(settings, dict):
        issue("invalid_settings", "settings", "Expected an object")
        settings = {}
    tolerance = integer(settings.get("duration_tolerance_us", 1), "settings.duration_tolerance_us")
    if tolerance is None:
        tolerance = 0
    report["duration_tolerance_us"] = tolerance
    report["duration_tolerance_scope"] = "source-span/speed minus authored timeline span only"
    report["delivery"] = delivery

    assets = data.get("assets")
    if not isinstance(assets, list):
        issue("invalid_assets", "assets", "Expected an array")
        assets = []
    by_id, asset_ids = {}, set()
    for index, asset in enumerate(assets):
        location = f"assets[{index}]"
        if not isinstance(asset, dict):
            issue("invalid_asset", location, "Expected an object")
            continue
        aid = asset.get("id")
        good_id = identifier(aid, location + ".id", asset_ids)
        kind = asset.get("kind")
        if kind not in ("video", "audio"):
            issue("invalid_kind", location + ".kind", "Expected video or audio")
        asset_duration = integer(asset.get("duration_us"), location + ".duration_us", 1)
        if "fps" in asset:
            ratio(asset["fps"], location + ".fps")
        expected = asset.get("sha256")
        if expected is not None and (not isinstance(expected, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected)):
            issue("invalid_sha256", location + ".sha256", "Expected 64 hexadecimal characters")
            expected = None
        relative = asset.get("path")
        resolved = None
        try:
            validate_ordinary_windows_path(relative, relative_only=True)
            resolved = (manifest_path.parent / Path(relative.replace("\\", "/"))).resolve()
            protected.add(resolved)
            validate_ordinary_windows_path(str(resolved))
            if not resolved.is_relative_to(manifest_path.parent):
                raise ValueError("Asset path escapes the package directory")
        except (OSError, ValueError, RuntimeError) as error:
            issue("unsafe_asset_path", location + ".path", str(error))
            resolved = None
        row = {"id": aid, "path": relative, "existence_status": "not_checked", "hash_status": "not_checked"}
        if verify_hashes and resolved is not None:
            try:
                if not resolved.is_file():
                    raise OSError("Explicit asset path is not a regular file")
                row["existence_status"] = "verified"
                digest = hashlib.sha256()
                with resolved.open("rb") as source:
                    # Chunked loop instead of hashlib.file_digest (3.11+) so the
                    # helper also runs on Andrei's device shell (Python 3.10).
                    for chunk in iter(lambda: source.read(1 << 20), b""):
                        digest.update(chunk)
                actual = digest.hexdigest()
                row["observed_sha256"] = actual
                row["hash_status"] = "observed_without_expected" if expected is None else "matched"
                if expected is not None and actual != expected.lower():
                    row["hash_status"] = "mismatch"
                    issue("hash_mismatch", location + ".sha256", "Asset SHA-256 differs from supplied expected hash")
            except OSError as error:
                row["existence_status"] = "unavailable"
                issue("asset_read_error", location + ".path", str(error))
        report["assets"].append(row)
        if good_id:
            by_id[aid] = {"kind": kind, "duration_us": asset_duration}

    def referenced_asset(obj, location, expected_kind):
        aid = obj.get("asset_id")
        if not isinstance(aid, str) or aid not in by_id:
            issue("unknown_asset", location + ".asset_id", "Referenced asset ID does not exist")
            return None
        asset = by_id[aid]
        if asset["kind"] != expected_kind:
            issue("asset_type_mismatch", location + ".asset_id", f"Expected {expected_kind} source")
        return asset

    def source_bounds(source, asset, location):
        if source and asset and asset["duration_us"] is not None and source[1] > asset["duration_us"]:
            issue("source_out_of_bounds", location, "Source exclusive endpoint exceeds supplied asset duration")

    clips = data.get("clips")
    if not isinstance(clips, list) or not clips:
        issue("invalid_clips", "clips", "Expected a nonempty ordered array")
        clips = []
    clip_ids, cursor = set(), 0
    for index, clip in enumerate(clips):
        location = f"clips[{index}]"
        if not isinstance(clip, dict):
            issue("invalid_clip", location, "Expected an object")
            continue
        cid = clip.get("id")
        identifier(cid, location + ".id", clip_ids)
        asset = referenced_asset(clip, location, "video")
        timeline = interval(clip, "timeline", location)
        source = interval(clip, "source", location)
        speed = ratio(clip.get("speed"), location + ".speed")
        source_bounds(source, asset, location)
        if not timeline:
            continue
        start, end = timeline
        if start != cursor:
            issue("timeline_gap" if start > cursor else "timeline_overlap", location,
                  f"Expected start {cursor}, received {start}")
        cursor = end
        if duration is not None and end > duration:
            issue("timeline_out_of_bounds", location, "Clip exceeds delivery duration")
        row = {"id": cid, "timeline_in_us": start, "timeline_out_us": end}
        if source and speed is not None:
            error = Fraction(source[1] - source[0], 1) / speed - (end - start)
            residual("duration_consistency", cid, error, tolerance)
            if abs(error) > tolerance:
                issue("duration_speed_mismatch", location, "Source-span/speed differs from timeline span beyond tolerance")
        if fps is not None:
            first = round_half_up(Fraction(start, 1000000) * fps)
            stop = round_half_up(Fraction(end, 1000000) * fps)
            row.update(start_frame=first, exclusive_end_frame=stop, frame_count=stop - first)
            residual("timeline_start_rounding", cid, Fraction(first * 1000000, 1) / fps - start)
            residual("timeline_end_rounding", cid, Fraction(stop * 1000000, 1) / fps - end)
            if stop <= first:
                issue("zero_frame_clip", location, "Clip collapses under cumulative boundary rounding")
            elif source and speed is not None:
                last = source[0] + Fraction((stop - first - 1) * 1000000, 1) * speed / fps
                row["diagnostic_last_consumed_source_us_exact"] = rational_text(last)
                row["diagnostic_mapping"] = "source_in + (frame_count - 1) * speed * 1000000 / delivery_fps"
                if asset and asset["duration_us"] is not None and last >= asset["duration_us"]:
                    issue("terminal_source_exhaustion", location, "Diagnostic last sample is at or beyond supplied file duration")
                if last >= source[1]:
                    issue("terminal_selection_exhaustion", location, "Diagnostic last sample is at or beyond source selection's exclusive end")
        report["clips"].append(row)
    if duration is not None and cursor != duration:
        issue("incomplete_coverage", "clips", f"Picture ends at {cursor}; delivery ends at {duration}")

    if "audio" in data:
        audio = data["audio"]
        if not isinstance(audio, dict):
            issue("invalid_audio", "audio", "Expected an object")
        else:
            asset = referenced_asset(audio, "audio", "audio")
            start = integer(audio.get("timeline_in_us"), "audio.timeline_in_us")
            source = interval(audio, "source", "audio")
            source_bounds(source, asset, "audio")
            if start is not None and source:
                end = start + source[1] - source[0]
                report["audio"] = {"timeline_in_us": start, "derived_timeline_out_us": end,
                                   "timing_model": "unchanged playback speed; no sample rate supplied"}
                if duration is not None and end > duration:
                    issue("audio_out_of_bounds", "audio", "Audio endpoint exceeds delivery duration")
    report["status"] = "invalid" if report["issues"] else "valid"
    return report, protected


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--out", required=True)
    parser.add_argument("--verify-hashes", action="store_true")
    args = parser.parse_args(argv)
    try:
        validate_ordinary_windows_path(args.out)
        output_path = Path(args.out)
        output = output_path.resolve()
        validate_ordinary_windows_path(str(output))
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Invalid receipt output path: {error}", file=sys.stderr)
        return 2
    report, protected = audit_manifest(args.manifest, args.verify_hashes)
    if output in protected or output_path.exists() or output_path.is_symlink():
        print("Refusing protected input or existing receipt output", file=sys.stderr)
        return 2
    try:
        with output_path.open("x", encoding="utf-8", newline="\n") as receipt:
            json.dump(report, receipt, indent=2, allow_nan=False)
            receipt.write("\n")
    except (OSError, ValueError) as error:
        print(f"Could not create receipt: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"status": report["status"], "issues": len(report["issues"]), "receipt": str(output)}))
    return 0 if report["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
