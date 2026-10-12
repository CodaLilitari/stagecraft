#!/usr/bin/env python3
"""Create an auditable, static video contact sheet using ffmpeg and ffprobe.

Only the Python standard library is required. Executables are supplied explicitly
or found on PATH; this helper never installs or downloads anything. The output
directory must not exist, and its parent must already exist.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import html
import json
import math
import os
from pathlib import Path
import shutil
import stat
import struct
import subprocess
import sys
import time


MAX_SAMPLES = 600
BATCH_SIZE = 100
STDERR_LIMIT = 16000
LIMITATIONS = [
    "Only the first video stream that is not an attached picture is sampled.",
    "Sampling times are relative to the first decoded video frame; source timestamps are recorded separately.",
    "The nearest timestamp wins; ties choose the earlier decoded frame. The actual final decoded frame is always included.",
    "Static samples do not establish continuous motion, lip sync, audiovisual quality, or completed perceptual review.",
    "An optional full video/audio decode check detects reported decoding errors only; no playback or listening is performed.",
    "PNG previews use FFmpeg's default autorotation and colour conversion and may be downscaled. They are not editing masters.",
    "After frame selection, export timestamps are reset to sequential seconds only to prevent PNG muxing from dropping duplicate source timestamps; the receipt retains original times.",
    "Probing reads all frame timestamps into memory, and each extraction batch decodes the video from the beginning to the end.",
]


class SamplingError(ValueError):
    """An input or operation could not meet the sampling contract."""


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def positive_interval(value):
    try:
        result = Fraction(str(value))
        numeric = float(result)
        finite = math.isfinite(numeric) and numeric > 0
    except (ValueError, TypeError, ZeroDivisionError, OverflowError) as exc:
        raise SamplingError("interval must be a positive finite number of seconds") from exc
    if result <= 0 or not finite:
        raise SamplingError("interval must be a positive finite number of seconds")
    return result


def seconds(value):
    result = float(value)
    if not math.isfinite(result):
        raise SamplingError("a frame timestamp cannot be represented as finite seconds")
    return result


def resolve_tool(explicit, name):
    candidate = str(explicit) if explicit is not None else shutil.which(name)
    if not candidate:
        raise SamplingError(f"{name} was not found on PATH; provide --{name} PATH")
    try:
        path = Path(candidate).expanduser().resolve(strict=True)
        if not stat.S_ISREG(path.stat().st_mode):
            raise SamplingError(f"{name} executable is not a regular file: {path}")
    except OSError as exc:
        raise SamplingError(f"cannot find {name} executable: {candidate}") from exc
    return str(path)


def run_command(argv, purpose, receipt, *, reject_stderr=True):
    operation = {"purpose": purpose, "argv": list(map(str, argv)), "started_at": utc_now()}
    receipt["operations"].append(operation)
    started = time.monotonic()
    try:
        process = subprocess.run(operation["argv"], stdin=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 check=False)
    except OSError as exc:
        operation.update({"error": str(exc), "duration_seconds": time.monotonic() - started})
        raise SamplingError(f"could not execute {purpose}: {exc}") from exc
    stderr = process.stderr.decode("utf-8", errors="replace")
    operation.update({"return_code": process.returncode,
                      "duration_seconds": time.monotonic() - started,
                      "stdout_bytes": len(process.stdout),
                      "stderr_tail": stderr[-STDERR_LIMIT:],
                      "stderr_truncated": len(stderr) > STDERR_LIMIT})
    if process.returncode or (reject_stderr and stderr.strip()):
        reason = stderr.strip()[-2000:] or f"exit code {process.returncode}"
        raise SamplingError(f"{purpose} failed: {reason}")
    return process.stdout


def probe_json(argv, purpose, receipt):
    data = run_command(argv, purpose, receipt)
    try:
        value = json.loads(data)
    except (UnicodeError, ValueError) as exc:
        raise SamplingError(f"{purpose} did not return valid JSON") from exc
    if not isinstance(value, dict):
        raise SamplingError(f"{purpose} did not return a JSON object")
    return value


def parse_frames(raw_frames, stream):
    """Use actual decoded timestamps; never manufacture them from a frame rate."""
    try:
        time_base = Fraction(stream["time_base"])
        if time_base <= 0:
            raise ValueError()
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        raise SamplingError("selected video stream has no valid time base") from exc
    if not isinstance(raw_frames, list) or not raw_frames:
        raise SamplingError("selected video stream has no decoded frames")
    frames = []
    for index, raw in enumerate(raw_frames):
        timestamp = None
        timestamp_field = None
        for field in ("best_effort_timestamp", "pts"):
            if raw.get(field) not in (None, "N/A"):
                try:
                    timestamp = Fraction(str(raw[field])) * time_base
                except (TypeError, ValueError, ZeroDivisionError) as exc:
                    raise SamplingError(f"frame {index} has an invalid {field}") from exc
                timestamp_field = field
                break
        if timestamp is None:
            for field in ("best_effort_timestamp_time", "pts_time"):
                if raw.get(field) not in (None, "N/A"):
                    try:
                        timestamp = Fraction(str(raw[field]))
                    except (TypeError, ValueError, ZeroDivisionError) as exc:
                        raise SamplingError(f"frame {index} has an invalid {field}") from exc
                    timestamp_field = field
                    break
        if timestamp is None:
            raise SamplingError(f"frame {index} has no actual presentation timestamp")
        seconds(timestamp)
        if frames and timestamp < frames[-1]["timestamp"]:
            raise SamplingError("decoded frame timestamps are not monotonic; cannot make a reliable time grid")
        frames.append({"index": index, "timestamp": timestamp, "timestamp_field": timestamp_field})
    return frames


def choose_samples(frames, interval, max_samples=MAX_SAMPLES):
    """Select nearest frames without expanding arbitrarily many repeated targets.

    Each distinct timestamp owns grid targets between neighbouring midpoints.
    A midpoint belongs to the earlier frame. Duplicate timestamps likewise choose
    the first decoded frame, except that the final frame is always added explicitly.
    """
    origin = frames[0]["timestamp"]
    last = frames[-1]["timestamp"] - origin
    last_grid_index = last // interval
    distinct = []
    for frame in frames:
        if not distinct or frame["timestamp"] != distinct[-1]["timestamp"]:
            distinct.append(frame)
    chosen = {}
    for position, frame in enumerate(distinct):
        relative = frame["timestamp"] - origin
        if position == 0:
            first_k = 0
        else:
            lower = (distinct[position - 1]["timestamp"] - origin + relative) / 2
            first_k = lower // interval + 1
        if position + 1 == len(distinct):
            last_k = last_grid_index
        else:
            upper = (relative + distinct[position + 1]["timestamp"] - origin) / 2
            last_k = min(upper // interval, last_grid_index)
        if first_k <= last_k:
            chosen[frame["index"]] = {
                "frame_index": frame["index"],
                "requested_time_seconds": seconds(first_k * interval),
                "requested_time_exact": str(first_k * interval),
                "reasons": ["interval"],
                "interval_targets": {
                    "first_grid_index": first_k, "last_grid_index": last_k,
                    "count": last_k - first_k + 1,
                    "first_time_seconds": seconds(first_k * interval),
                    "last_time_seconds": seconds(last_k * interval),
                },
            }
        if len(chosen) > max_samples:
            raise SamplingError(f"sampling would exceed {max_samples} distinct frames; increase --interval")
    final_index = frames[-1]["index"]
    if final_index not in chosen:
        chosen[final_index] = {"frame_index": final_index,
                               "requested_time_seconds": seconds(last),
                               "requested_time_exact": str(last), "reasons": []}
    chosen[final_index]["reasons"].append("last_frame")
    chosen[final_index]["last_frame_requested_time_seconds"] = seconds(last)
    if len(chosen) > max_samples:
        raise SamplingError(f"sampling would exceed {max_samples} distinct frames including the last frame; increase --interval")
    result = []
    for ordinal, index in enumerate(sorted(chosen), 1):
        sample = chosen[index]
        frame = frames[index]
        sample.update({"ordinal": ordinal, "file": f"frame_{ordinal:06d}.png",
                       "actual_time_seconds": seconds(frame["timestamp"] - origin),
                       "actual_time_exact": str(frame["timestamp"] - origin),
                       "actual_timestamp_seconds": seconds(frame["timestamp"]),
                       "actual_timestamp_exact": str(frame["timestamp"]),
                       "timestamp_field": frame["timestamp_field"]})
        result.append(sample)
    return result


def inspect_png(path):
    with path.open("rb") as image:
        header = image.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise SamplingError(f"expected PNG was not produced correctly: {path.name}")
    width, height = struct.unpack(">II", header[16:24])
    if not width or not height:
        raise SamplingError(f"PNG has invalid dimensions: {path.name}")
    return {"width": width, "height": height, "bytes": path.stat().st_size, "sha256": sha256(path)}


def write_html(output, receipt):
    source_name = html.escape(receipt["source"]["name"])
    cards = []
    for sample in receipt["samples"]:
        requested = f'{sample["requested_time_seconds"]:.6f} s'
        targets = sample.get("interval_targets")
        if targets and targets["count"] > 1:
            requested = (f'{targets["first_time_seconds"]:.6f}–{targets["last_time_seconds"]:.6f} s '
                         f'({targets["count"]} grid targets)')
        actual = f'{sample["actual_time_seconds"]:.6f} s'
        final = " · actual last frame" if "last_frame" in sample["reasons"] else ""
        label = (f'Frame {sample["frame_index"]} · actual {actual}{final}; requested {requested}')
        filename = html.escape(sample["file"], quote=True)
        cards.append(f'<figure><a href="{filename}"><img src="{filename}" loading="lazy" '
                     f'width="{sample["width"]}" height="{sample["height"]}" '
                     f'alt="{html.escape(label, quote=True)}"></a>'
                     f'<figcaption><strong>Frame {sample["frame_index"]} · actual {actual}{final}</strong>'
                     f'<br>Requested: {requested}<br>Source timestamp: '
                     f'{sample["actual_timestamp_seconds"]:.6f} s</figcaption></figure>')
    decode = receipt["decode_check"]["status"]
    decode_text = ("All video and audio streams completed a technical decode check without reported errors."
                   if decode == "passed" else "A full video/audio decode check was not requested.")
    document = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">'
                '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
                'img-src \'self\'; style-src \'unsafe-inline\'">'
                f'<title>Video samples — {source_name}</title><style>'
                'body{margin:2rem;background:#16191f;color:#f1f3f5;font:16px/1.5 system-ui,sans-serif}'
                'h1{font-size:1.5rem;overflow-wrap:anywhere}a{color:#9fd8ff}'
                '.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr));gap:1rem}'
                'figure{margin:0;background:#252a33;border-radius:8px;overflow:hidden}'
                'img{display:block;max-width:100%;height:auto;margin:auto}figcaption{padding:.8rem;font-size:.85rem}'
                '.notice{max-width:90ch}code{overflow-wrap:anywhere}</style></head><body>'
                f'<h1>Video samples: {source_name}</h1><p class="notice">'
                'Sampled stills only: this sheet does not establish continuous motion, lip sync, audio quality, '
                f'or perceptual review. {decode_text} No playback or listening was performed.</p>'
                '<p>Times are relative to the first decoded frame. Frame indices are zero based. '
                'PNG previews retain FFmpeg’s default autorotation and may be downscaled.</p>'
                f'<p>{len(cards)} distinct frames · interval {receipt["settings"]["interval_seconds"]:g} s · '
                f'<a href="receipt.json">Provenance and limits</a></p><main class="grid">'
                + "\n".join(cards) + '</main></body></html>\n')
    target = output / "index.html"
    with target.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(document)
    return {"file": "index.html", "sha256": sha256(target)}


def write_receipt(output, receipt, *, initial=False):
    payload = json.dumps(receipt, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if initial:
        with (output / "receipt.json").open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
    else:
        temporary = output / "receipt.json.tmp"
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
        os.replace(temporary, output / "receipt.json")


def sample_video(input_path, output_dir, *, interval="1", max_width=960,
                 decode=False, ffmpeg=None, ffprobe=None):
    """Return a receipt; operational failures are preserved in the new output.

    A pre-existing output path raises before any writes. Other failures return a
    failed receipt. Creation errors cannot leave a receipt in an unowned directory.
    """
    output = Path(output_dir).expanduser().absolute()
    if os.path.lexists(output):
        raise SamplingError(f"output path already exists; refusing to overwrite: {output}")
    try:
        output.mkdir()
    except OSError as exc:
        raise SamplingError(f"cannot create new output directory: {output}: {exc}") from exc
    output = output.resolve()
    receipt = {"schema_version": 1, "status": "in_progress", "started_at": utc_now(),
               "input_argument": str(input_path), "output_directory": str(output),
               "settings": {"interval_argument": str(interval), "max_width_argument": str(max_width),
                            "decode_requested": bool(decode), "max_samples": MAX_SAMPLES,
                            "batch_size": BATCH_SIZE},
               "sampling_policy": {"grid_origin": "first decoded frame", "nearest_tie": "earlier decoded frame",
                                   "include_actual_last_frame": True,
                                   "frame_index_basis": "zero-based sequential decoded frame order",
                                   "extraction": "full sequential decode with select(n), no seeking"},
               "source": {"hash_comparison": "unavailable"}, "samples": [], "operations": [],
               "decode_check": {"status": "not_started" if decode else "not_requested"},
               "perceptual_review": "not_performed", "limitations": LIMITATIONS}
    write_receipt(output, receipt, initial=True)
    source = None
    try:
        step = positive_interval(interval)
        try:
            width = int(max_width)
        except (TypeError, ValueError, OverflowError) as exc:
            raise SamplingError("max-width must be a positive integer") from exc
        if width <= 0 or str(width) != str(max_width).strip():
            raise SamplingError("max-width must be a positive integer")
        receipt["settings"].update({"interval_seconds": seconds(step), "interval_exact": str(step),
                                    "max_width": width})
        try:
            source = Path(input_path).expanduser().resolve(strict=True)
            source_stat = source.stat()
            if not stat.S_ISREG(source_stat.st_mode):
                source = None
                raise SamplingError("input must be one exact, existing regular file")
        except OSError as exc:
            source = None
            raise SamplingError("input must be one exact, existing regular file") from exc
        receipt["source"].update({"path": str(source), "name": source.name,
                                   "bytes_before": source_stat.st_size,
                                   "mtime_ns_before": source_stat.st_mtime_ns,
                                   "sha256_before": sha256(source)})
        ffmpeg_path, ffprobe_path = resolve_tool(ffmpeg, "ffmpeg"), resolve_tool(ffprobe, "ffprobe")
        receipt["tools"] = {}
        for name, path in (("ffmpeg", ffmpeg_path), ("ffprobe", ffprobe_path)):
            version = run_command([path, "-version"], f"{name} version", receipt, reject_stderr=False)
            receipt["tools"][name] = {"path": path, "version": version.decode("utf-8", errors="replace").splitlines()[0]}
        base_probe = [ffprobe_path, "-v", "error", "-protocol_whitelist", "file"]
        metadata = probe_json(base_probe + ["-show_streams", "-show_format", "-of", "json", str(source)],
                              "probe streams", receipt)
        receipt["probe"] = metadata
        candidates = [stream for stream in metadata.get("streams", [])
                      if stream.get("codec_type") == "video" and not stream.get("disposition", {}).get("attached_pic")]
        if not candidates:
            raise SamplingError("input has no video stream other than attached pictures")
        stream = candidates[0]
        stream_index = int(stream["index"])
        receipt["selected_video_stream_index"] = stream_index
        frame_data = probe_json(base_probe + ["-select_streams", str(stream_index), "-show_frames", "-show_entries",
                                              "frame=best_effort_timestamp,best_effort_timestamp_time,pts,pts_time",
                                              "-of", "json", str(source)], "probe decoded frames", receipt)
        frames = parse_frames(frame_data.get("frames"), stream)
        receipt["decoded_frames"] = {"count": len(frames), "first_frame_index": 0,
                                      "last_frame_index": len(frames) - 1,
                                      "first_timestamp_seconds": seconds(frames[0]["timestamp"]),
                                      "last_timestamp_seconds": seconds(frames[-1]["timestamp"]),
                                      "first_timestamp_exact": str(frames[0]["timestamp"]),
                                      "last_timestamp_exact": str(frames[-1]["timestamp"]),
                                      "timestamp_source": "ffprobe -show_frames; stream time_base for integer timestamps"}
        samples = choose_samples(frames, step)
        receipt["samples"] = samples
        receipt["sample_count"] = len(samples)
        for offset in range(0, len(samples), BATCH_SIZE):
            batch = samples[offset:offset + BATCH_SIZE]
            expression = "+".join(f'eq(n,{sample["frame_index"]})' for sample in batch)
            video_filter = f"select='{expression}',setpts=N/TB,scale=w='min(iw,{width})':h=-1"
            argv = [ffmpeg_path, "-hide_banner", "-nostdin", "-v", "error", "-xerror", "-n",
                    "-protocol_whitelist", "file", "-i", str(source), "-map", f"0:{stream_index}",
                    "-an", "-sn", "-dn", "-vf", video_filter, "-filter_threads", "1", "-fps_mode", "vfr",
                    "-compression_level", "3", "-start_number", str(offset + 1), "-f", "image2",
                    str(output / "frame_%06d.png")]
            run_command(argv, f"extract batch {offset // BATCH_SIZE + 1}", receipt)
        expected = {sample["file"] for sample in samples}
        actual = {path.name for path in output.glob("frame_*.png")}
        if expected != actual:
            raise SamplingError("extracted PNG count or filenames do not match the selected decoded frame indices")
        for sample in samples:
            sample.update(inspect_png(output / sample["file"]))
            if sample["width"] > width:
                raise SamplingError("extracted PNG exceeds the requested maximum width")
        if decode:
            receipt["decode_check"]["status"] = "running"
            run_command([ffmpeg_path, "-hide_banner", "-nostdin", "-v", "error", "-xerror",
                         "-err_detect", "explode", "-protocol_whitelist", "file", "-i", str(source),
                         "-map", "0:v?", "-map", "0:a?", "-sn", "-dn", "-f", "null", "-"],
                        "full video and audio decode", receipt)
            receipt["decode_check"].update({"status": "passed", "scope": "all video and audio streams",
                                             "perceptual_review": "not_performed"})
        receipt["contact_sheet"] = write_html(output, receipt)
        receipt["status"] = "completed"
    except (Exception, KeyboardInterrupt) as exc:
        receipt["status"] = "failed"
        receipt["error"] = {"type": type(exc).__name__, "message": str(exc) or "interrupted"}
        if receipt["decode_check"]["status"] == "running":
            receipt["decode_check"]["status"] = "failed"
    finally:
        if source is not None and "sha256_before" in receipt["source"]:
            try:
                after_stat = source.stat()
                after_hash = sha256(source)
                unchanged = after_hash == receipt["source"]["sha256_before"]
                receipt["source"].update({"sha256_after": after_hash, "bytes_after": after_stat.st_size,
                                           "mtime_ns_after": after_stat.st_mtime_ns,
                                           "hash_comparison": "unchanged" if unchanged else "changed"})
                if not unchanged:
                    receipt["status"] = "failed"
                    receipt["error"] = {"type": "SourceChanged", "message": "source hash changed during sampling"}
            except OSError as exc:
                receipt["source"]["hash_comparison"] = "unavailable_after"
                receipt["status"] = "failed"
                receipt["error"] = {"type": "SourceVerificationFailed", "message": str(exc)}
        receipt["finished_at"] = utc_now()
        write_receipt(output, receipt)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="one exact local video file (no URL or wildcard expansion)")
    parser.add_argument("--out", required=True, help="new output directory; its parent must exist")
    parser.add_argument("--interval", default="1", help="positive finite seconds between requested grid targets (default: 1)")
    parser.add_argument("--max-width", default="960", help="positive maximum preview width; never upscales (default: 960)")
    parser.add_argument("--decode", action="store_true", help="also decode all video/audio streams to check reported errors")
    parser.add_argument("--ffmpeg", help="explicit ffmpeg executable path; otherwise search PATH")
    parser.add_argument("--ffprobe", help="explicit ffprobe executable path; otherwise search PATH")
    args = parser.parse_args(argv)
    try:
        receipt = sample_video(args.input, args.out, interval=args.interval, max_width=args.max_width,
                               decode=args.decode, ffmpeg=args.ffmpeg, ffprobe=args.ffprobe)
    except (SamplingError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(str(Path(receipt["output_directory"]) / "receipt.json"))
    if receipt["status"] != "completed":
        print(f'error: {receipt["error"]["message"]}', file=sys.stderr)
        return 1
    print(str(Path(receipt["output_directory"]) / "index.html"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
