#!/usr/bin/env python3
"""Tile a sample_video.py run into one labelled PNG that Red can look at in a single read.

Red sees images, not playback. Reading thirty separate frames costs thirty
reads; one labelled grid costs one. This helper reads an existing
sample_video.py output directory, checks every PNG it uses against the
receipt's SHA-256, and writes one new contact-sheet image with each tile
labelled by decoded frame index and actual time.

It changes nothing in the sample directory and decodes no video. A contact
sheet is an overview of sampled stills: it is not evidence of motion,
lip sync or audio.

Requires Pillow (present in Claude's cloud workspace). Python 3.10+.

    python3 contact_sheet.py SAMPLE_DIR --out NEW_SHEET.png [--cols 6] [--tile-width 320]
                             [--start SECONDS] [--end SECONDS] [--max-tiles 48]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - reported at runtime
    Image = ImageDraw = ImageFont = None  # type: ignore[assignment]

LABEL_HEIGHT = 22
PAD = 4
BACKGROUND = (18, 18, 20)
TEXT = (235, 235, 235)
FINAL_TEXT = (255, 196, 92)


class SheetError(Exception):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_samples(sample_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    receipt_path = sample_dir / "receipt.json"
    if not receipt_path.is_file():
        raise SheetError(f"no receipt.json in {sample_dir}")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("status") != "completed":
        raise SheetError(f"sample run status is {receipt.get('status')!r}, not 'completed'")
    samples = receipt.get("samples") or []
    if not samples:
        raise SheetError("receipt lists no samples")
    return receipt, samples


def select(samples: list[dict[str, Any]], start: float | None, end: float | None) -> list[dict[str, Any]]:
    chosen = []
    for sample in samples:
        t = float(sample["actual_time_seconds"])
        if start is not None and t < start:
            continue
        if end is not None and t > end:
            continue
        chosen.append(sample)
    if not chosen:
        raise SheetError("no samples fall inside the requested time range")
    return chosen


def font(size: int):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow < 10.1
        return ImageFont.load_default()


def build(sample_dir: Path, samples: list[dict[str, Any]], cols: int, tile_width: int):
    tiles = []
    for sample in samples:
        path = sample_dir / sample["file"]
        if not path.is_file():
            raise SheetError(f"missing frame file: {sample['file']}")
        if sha256(path) != sample.get("sha256"):
            raise SheetError(f"frame does not match its receipt hash: {sample['file']}")
        with Image.open(path) as image:
            image = image.convert("RGB")
            scale = min(1.0, tile_width / image.width)
            size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
            tiles.append(image.resize(size, Image.LANCZOS) if scale < 1.0 else image.copy())
    cell_w = max(tile.width for tile in tiles)
    cell_h = max(tile.height for tile in tiles) + LABEL_HEIGHT
    cols = max(1, min(cols, len(tiles)))
    rows = math.ceil(len(tiles) / cols)
    sheet = Image.new("RGB", (cols * cell_w + (cols + 1) * PAD, rows * cell_h + (rows + 1) * PAD), BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    label_font = font(13)
    for i, (sample, tile) in enumerate(zip(samples, tiles)):
        x = PAD + (i % cols) * (cell_w + PAD)
        y = PAD + (i // cols) * (cell_h + PAD)
        sheet.paste(tile, (x, y))
        final = "last_frame_requested_time_seconds" in sample
        label = f"#{sample['frame_index']}  {float(sample['actual_time_seconds']):.3f}s" + ("  END" if final else "")
        draw.text((x + 3, y + tile.height + 4), label, fill=FINAL_TEXT if final else TEXT, font=label_font)
    return sheet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("sample_dir", help="an existing sample_video.py output directory")
    parser.add_argument("--out", required=True, help="new PNG path (must not exist; parent must exist)")
    parser.add_argument("--cols", type=int, default=6)
    parser.add_argument("--tile-width", type=int, default=320)
    parser.add_argument("--start", type=float, help="first actual time to include (seconds)")
    parser.add_argument("--end", type=float, help="last actual time to include (seconds)")
    parser.add_argument("--max-tiles", type=int, default=48, help="refuse larger sheets (default 48)")
    args = parser.parse_args(argv)
    try:
        if Image is None:
            raise SheetError("Pillow is required (available in Claude's cloud workspace)")
        if args.cols < 1 or args.tile_width < 32 or args.max_tiles < 1:
            raise SheetError("--cols must be >= 1, --tile-width >= 32, --max-tiles >= 1")
        sample_dir = Path(args.sample_dir).expanduser().resolve()
        out = Path(args.out).expanduser().resolve()
        if out.suffix.lower() != ".png":
            raise SheetError("--out must end in .png")
        if out.exists():
            raise SheetError(f"output exists: {out}")
        if not out.parent.is_dir():
            raise SheetError(f"output parent does not exist: {out.parent}")
        if sample_dir == out.parent or sample_dir in out.parents:
            raise SheetError("write the sheet outside the sample directory; it stays as sampled")
        receipt, samples = load_samples(sample_dir)
        chosen = select(samples, args.start, args.end)
        if len(chosen) > args.max_tiles:
            raise SheetError(f"{len(chosen)} tiles exceeds --max-tiles {args.max_tiles}; narrow --start/--end")
        sheet = build(sample_dir, chosen, args.cols, args.tile_width)
        with out.open("xb") as handle:
            sheet.save(handle, format="PNG")
        print(json.dumps({
            "ok": True,
            "sheet": str(out),
            "size": list(sheet.size),
            "source": receipt.get("source", {}).get("name"),
            "tiles": [{"frame_index": s["frame_index"], "actual_time_seconds": s["actual_time_seconds"]}
                      for s in chosen],
            "label": "sampled stills only; not evidence of motion, lip sync or audio",
        }, indent=2))
    except (SheetError, OSError, ValueError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
