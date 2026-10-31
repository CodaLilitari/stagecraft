#!/usr/bin/env python3
"""Measured song map: tempo, beat grid, loudness and candidate section changes.

Decodes one exact audio or video file with ffmpeg and estimates, from the
actual recording:

* tempo in BPM, with half/double alternatives and a stability check across the song;
* a beat grid (dynamic-programming beat tracker, after Ellis 2007);
* loudness per half second;
* candidate section boundaries from beat-synchronous timbre novelty (Foote 2000).

Everything here is a MEASURED ESTIMATE, labelled as such. It is not the
prompt's or the DAW's tempo, not lyric timing, and not vocal onsets. It
cannot hear the song: it finds periodicity and change in the signal. Check
octave errors (half/double tempo) and every boundary against the actual track
before cutting to it.

Requires numpy and an ffmpeg executable. Run it in Claude's cloud workspace,
where numpy is available. Python 3.10+.

    python3 song_map.py SONG.wav --out NEW_DIR [--sr 22050] [--start-bpm 120] [--click-preview]

--click-preview also writes click-preview.wav (the mono mix with a tick on every
estimated beat) so someone who can listen can check the grid in seconds.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path
from typing import Any

try:
    import numpy as np
except ImportError:  # pragma: no cover - reported at runtime
    np = None  # type: ignore[assignment]

SCHEMA = "red-stagecraft/song-map/v1"
N_FFT = 2048
HOP = 512
N_MELS = 64
# Centered analysis windows make spectral-flux onsets appear early. Measured on
# synthetic click tracks (90-168 BPM, several phases): -33.2 ms +/- 0.5 ms at
# n_fft=2048, hop=512, 22.05 kHz. Beat times are shifted by this amount.
ONSET_LATENCY_S = 0.033


class SongMapError(Exception):
    pass


# ------------------------------------------------------------------ decoding

def sha256_file(path: Path) -> tuple[str, int]:
    digest, size = hashlib.sha256(), 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def decode(path: Path, sr: int, ffmpeg: str) -> "np.ndarray":
    command = [ffmpeg, "-nostdin", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", str(sr),
               "-f", "f32le", "-"]
    result = subprocess.run(command, capture_output=True, check=False)
    if result.returncode != 0:
        raise SongMapError("ffmpeg could not decode the file: " + result.stderr.decode("utf-8", "replace")[:300])
    audio = np.frombuffer(result.stdout, dtype=np.float32).astype(np.float64)
    if audio.size < sr:
        raise SongMapError("decoded audio is shorter than one second")
    return audio


# ------------------------------------------------------------------ features

def mel_filters(sr: int, n_fft: int, n_mels: int, fmin: float = 30.0, fmax: float | None = None) -> "np.ndarray":
    fmax = fmax or sr / 2.0

    def hz_to_mel(hz):
        return 2595.0 * np.log10(1.0 + np.asarray(hz) / 700.0)

    def mel_to_hz(mel):
        return 700.0 * (10.0 ** (np.asarray(mel) / 2595.0) - 1.0)

    bins = np.linspace(0, sr / 2.0, n_fft // 2 + 1)
    edges = mel_to_hz(np.linspace(hz_to_mel(fmin), hz_to_mel(fmax), n_mels + 2))
    filters = np.zeros((n_mels, bins.size))
    for m in range(n_mels):
        lower, centre, upper = edges[m], edges[m + 1], edges[m + 2]
        rising = (bins - lower) / max(centre - lower, 1e-9)
        falling = (upper - bins) / max(upper - centre, 1e-9)
        filters[m] = np.maximum(0.0, np.minimum(rising, falling))
    return filters


def mel_db(audio: "np.ndarray", sr: int) -> "np.ndarray":
    padded = np.pad(audio, (N_FFT // 2, N_FFT // 2), mode="reflect")
    frames = np.lib.stride_tricks.sliding_window_view(padded, N_FFT)[::HOP]
    spectrum = np.abs(np.fft.rfft(frames * np.hanning(N_FFT), axis=1)) ** 2
    mel = spectrum @ mel_filters(sr, N_FFT, N_MELS).T
    return 10.0 * np.log10(np.maximum(mel, 1e-10))  # frames x mels


def onset_envelope(mel: "np.ndarray") -> "np.ndarray":
    flux = np.maximum(0.0, np.diff(mel, axis=0, prepend=mel[:1]))
    env = flux.mean(axis=1)
    # remove slow trends so loud passages don't dominate periodicity
    width = 64
    kernel = np.ones(width) / width
    env = env - np.convolve(env, kernel, mode="same")
    env = np.maximum(env, 0.0)
    std = env.std()
    return env / std if std > 0 else env


# ------------------------------------------------------------------ tempo

def tempo_curve(env: "np.ndarray", sr: int, start_bpm: float, min_bpm: float = 50.0,
                max_bpm: float = 220.0) -> tuple["np.ndarray", "np.ndarray", "np.ndarray"]:
    n = env.size
    taps = np.arange(-4, 5)
    smooth = np.exp(-0.5 * (taps / 1.5) ** 2)
    env = np.convolve(env, smooth / smooth.sum(), mode="same")
    spectrum = np.fft.rfft(env - env.mean(), n=2 * n)
    acf = np.fft.irfft(np.abs(spectrum) ** 2)[:n]
    if acf[0] <= 0:
        raise SongMapError("no rhythmic energy found (silence or constant signal)")
    acf = acf / acf[0]
    fps = sr / HOP
    lags = np.arange(n)
    with np.errstate(divide="ignore"):
        bpm = 60.0 * fps / lags
    valid = (bpm >= min_bpm) & (bpm <= max_bpm)
    prior = np.exp(-0.5 * (np.log2(np.where(valid, bpm, 1.0) / start_bpm)) ** 2)
    return lags[valid], bpm[valid], (acf[valid], prior[valid])  # type: ignore[return-value]


def estimate_tempo(env: "np.ndarray", sr: int, start_bpm: float) -> dict[str, Any]:
    lags, bpm, (acf, prior) = tempo_curve(env, sr, start_bpm)
    weighted = acf * prior
    best = int(np.argmax(weighted))
    # parabolic refinement on the lag axis
    lag = float(lags[best])
    if 0 < best < weighted.size - 1:
        a, b, c = weighted[best - 1], weighted[best], weighted[best + 1]
        denom = a - 2 * b + c
        if denom != 0:
            lag = lag + 0.5 * (a - c) / denom
    fps = sr / HOP
    tempo = 60.0 * fps / lag
    peaks = [i for i in range(1, acf.size - 1) if acf[i] > acf[i - 1] and acf[i] >= acf[i + 1] and acf[i] > 0]
    peaks.sort(key=lambda i: acf[i], reverse=True)
    candidates = [{"bpm": round(float(bpm[i]), 2), "periodicity": round(float(acf[i]), 3)} for i in peaks[:5]]
    positive = acf[acf > 0]
    confidence = float(weighted[best] / (np.mean(weighted[weighted > 0]) + 1e-9)) if positive.size else 0.0
    return {"bpm": round(tempo, 2), "period_frames": 60.0 * fps / tempo, "candidates": candidates,
            "peak_to_mean": round(confidence, 2),
            "octave_alternatives": [round(tempo / 2, 2), round(tempo * 2, 2)]}


def tempo_stability(env: "np.ndarray", sr: int, global_bpm: float, window_s: float = 20.0,
                    hop_s: float = 10.0) -> dict[str, Any]:
    fps = sr / HOP
    width, step = int(window_s * fps), int(hop_s * fps)
    windows = []
    for start in range(0, max(1, env.size - width + 1), step):
        segment = env[start:start + width]
        if segment.size < width // 2 or segment.std() == 0:
            continue
        try:
            local = estimate_tempo(segment, sr, global_bpm)["bpm"]
        except SongMapError:
            continue
        # fold octave errors toward the global estimate before comparing
        for factor in (0.5, 2.0):
            if abs(local * factor - global_bpm) < abs(local - global_bpm):
                local = local * factor
        windows.append({"start_s": round(start / fps, 2), "bpm": round(local, 2)})
    deviations = [abs(w["bpm"] - global_bpm) / global_bpm * 100 for w in windows]
    return {"window_s": window_s, "windows": windows,
            "max_deviation_pct": round(max(deviations), 2) if deviations else None}


# ------------------------------------------------------------------ beats

def track_beats(env: "np.ndarray", period: float, tightness: float = 100.0) -> "np.ndarray":
    sigma = max(period / 32.0, 1.0)
    taps = np.arange(-int(4 * sigma), int(4 * sigma) + 1)
    window = np.exp(-0.5 * (taps / sigma) ** 2)
    local = np.convolve(env, window / window.sum(), mode="same")
    n = local.size
    cumulative = np.zeros(n)
    backlink = np.full(n, -1, dtype=int)
    low, high = int(round(period / 2)), int(round(2 * period))
    offsets = np.arange(low, high + 1)
    penalty = -tightness * np.log(offsets / period) ** 2
    for t in range(n):
        prev = t - offsets
        ok = prev >= 0
        if not ok.any():
            cumulative[t] = local[t]
            continue
        candidates = cumulative[prev[ok]] + penalty[ok]
        k = int(np.argmax(candidates))
        if candidates[k] > 0:
            cumulative[t] = local[t] + candidates[k]
            backlink[t] = int(prev[ok][k])
        else:
            cumulative[t] = local[t]
    tail = max(int(period), 1)
    end = n - tail + int(np.argmax(cumulative[n - tail:]))
    beats = [end]
    while backlink[beats[-1]] >= 0:
        beats.append(int(backlink[beats[-1]]))
    return np.array(beats[::-1])


def trim_silent_beats(beats: "np.ndarray", audio: "np.ndarray", sr: int, floor_db: float = -50.0) -> "np.ndarray":
    """Drop leading/trailing beats where the recording itself is near-silent.

    Judged on signal level (relative to the loudest frame), not on onset strength,
    so a dense or noisy passage with weak transients keeps its beat grid.
    """
    if beats.size == 0:
        return beats
    padded = np.pad(audio, (N_FFT // 2, N_FFT // 2), mode="reflect")
    frames = np.lib.stride_tricks.sliding_window_view(padded, N_FFT)[::HOP]
    level = 10.0 * np.log10(np.maximum(np.mean(frames ** 2, axis=1), 1e-12))
    loud = level[np.minimum(beats, level.size - 1)] >= level.max() + floor_db
    keep = np.where(loud)[0]
    return beats[keep[0]:keep[-1] + 1] if keep.size else beats


# ------------------------------------------------------------------ energy & sections

def loudness(audio: "np.ndarray", sr: int, hop_s: float = 0.5) -> list[float]:
    step = int(sr * hop_s)
    values = []
    for start in range(0, audio.size, step):
        block = audio[start:start + step]
        rms = float(np.sqrt(np.mean(block ** 2))) if block.size else 0.0
        values.append(round(20.0 * np.log10(max(rms, 1e-6)), 1))
    return values


def section_candidates(mel: "np.ndarray", beats: "np.ndarray", fps: float, kernel_beats: int = 16,
                       min_gap_beats: int = 8) -> list[dict[str, Any]]:
    if beats.size < kernel_beats * 2:
        return []
    feats = np.stack([mel[beats[i]:max(beats[i + 1], beats[i] + 1)].mean(axis=0) for i in range(beats.size - 1)])
    feats = feats - feats.mean(axis=0)
    norms = np.linalg.norm(feats, axis=1, keepdims=True)
    feats = feats / np.maximum(norms, 1e-9)
    similarity = feats @ feats.T
    half = kernel_beats // 2
    idx = np.arange(-half, half)
    gauss = np.exp(-0.5 * ((idx + 0.5) / (half / 2.0)) ** 2)
    sign = np.sign(idx + 0.5)
    kernel = np.outer(sign, sign) * np.outer(gauss, gauss)
    novelty = np.zeros(similarity.shape[0])
    for i in range(half, similarity.shape[0] - half):
        novelty[i] = float(np.sum(kernel * similarity[i - half:i + half, i - half:i + half]))
    novelty = np.maximum(novelty, 0.0)
    if novelty.max() <= 0:
        return []
    threshold = novelty.mean() + 0.5 * novelty.std()
    peaks = [i for i in range(1, novelty.size - 1)
             if novelty[i] >= threshold and novelty[i] >= novelty[i - 1] and novelty[i] > novelty[i + 1]]
    chosen: list[int] = []
    for i in sorted(peaks, key=lambda p: novelty[p], reverse=True):
        if all(abs(i - j) >= min_gap_beats for j in chosen):
            chosen.append(i)
    chosen.sort()
    top = novelty.max()
    return [{"time_s": round(beats[i] / fps + ONSET_LATENCY_S, 3), "beat_index": int(i),
             "strength": round(float(novelty[i] / top), 3)}
            for i in chosen]


# ------------------------------------------------------------------ main analysis

def analyse(path: Path, sr: int = 22050, start_bpm: float = 120.0, ffmpeg: str = "ffmpeg") -> dict[str, Any]:
    return analyse_with_audio(path, sr, start_bpm, ffmpeg)[0]


def analyse_with_audio(path: Path, sr: int = 22050, start_bpm: float = 120.0,
                       ffmpeg: str = "ffmpeg") -> "tuple[dict[str, Any], np.ndarray]":
    if np is None:
        raise SongMapError("numpy is required (available in Claude's cloud workspace)")
    if shutil.which(ffmpeg) is None and not Path(ffmpeg).is_file():
        raise SongMapError(f"ffmpeg not found: {ffmpeg}")
    if not path.is_file():
        raise SongMapError(f"not a file: {path}")
    digest, size = sha256_file(path)
    audio = decode(path, sr, ffmpeg)
    fps = sr / HOP
    mel = mel_db(audio, sr)
    env = onset_envelope(mel)
    tempo = estimate_tempo(env, sr, start_bpm)
    stability = tempo_stability(env, sr, tempo["bpm"])
    beats = trim_silent_beats(track_beats(env, tempo["period_frames"]), audio, sr)
    beat_times = beats / fps + ONSET_LATENCY_S
    intervals = np.diff(beat_times)
    median = float(np.median(intervals)) if intervals.size else None
    if beat_times.size >= 8:
        # least-squares slope of beat time vs index: steadier than one ACF lag
        slope = float(np.polyfit(np.arange(beat_times.size), beat_times, 1)[0])
        tempo["acf_bpm"] = tempo["bpm"]
        tempo["bpm"] = round(60.0 / slope, 2)
        tempo["octave_alternatives"] = [round(tempo["bpm"] / 2, 2), round(tempo["bpm"] * 2, 2)]
    within = float(np.mean(np.abs(intervals - median) <= 0.05 * median)) if intervals.size else None
    energy = loudness(audio, sr)
    order = np.argsort(energy)[::-1][:5]
    tempo.pop("period_frames")
    result = {
        "schema": SCHEMA,
        "source": {"path": str(path), "sha256": digest, "bytes": size},
        "decode": {"sample_rate": sr, "channels": "downmixed to mono", "duration_s": round(audio.size / sr, 3)},
        "tempo": {**tempo, "stability": stability,
                  "label": "measured estimate; check half/double tempo by ear or against the session tempo"},
        "beats": {"count": int(beats.size), "times_s": [round(float(t), 3) for t in beat_times],
                  "median_interval_s": round(median, 4) if median else None,
                  "share_within_5pct_of_median": round(within, 3) if within is not None else None,
                  "label": "estimated beat grid; verify against the track before cutting to it"},
        "energy": {"hop_s": 0.5, "db": energy,
                   "loudest_s": [round(float(i) * 0.5, 1) for i in sorted(order)],
                   "label": "RMS level of the decoded mono mix, not perceived loudness (LUFS)"},
        "sections": {"boundaries": section_candidates(mel, beats, fps),
                     "method": "beat-synchronous mel timbre novelty (Foote checkerboard, 16-beat kernel)",
                     "label": "candidate changes only; name sections by listening or from the lyric sheet"},
        "limits": [
            "No lyric, vocal-onset or singer detection; those need the supplied lyrics and listening.",
            "Tempo octave (half/double) is ambiguous by construction; alternatives are listed.",
            "Swing, rubato, tempo changes and sparse intros reduce beat-grid reliability.",
            "Measured from the decoded file; confirm it is the locked master before timing an edit.",
        ],
    }
    return result, audio


def click_preview(audio: "np.ndarray", sr: int, beat_times: list[float]) -> "np.ndarray":
    """The decoded mix with a short identical tick on every estimated beat.

    Red cannot hear. Andrei (or an audio-capable reviewer) can: a few seconds of
    this file at the intro, a section change and the outro show whether the grid
    lands, drifts or sits on the off-beat. No downbeats are marked because none
    are detected.
    """
    peak = float(np.max(np.abs(audio))) or 1.0
    mix = audio / peak * 0.55
    n = int(0.025 * sr)
    t = np.arange(n) / sr
    tick = 0.45 * np.sin(2 * np.pi * 1760.0 * t) * np.exp(-t * 160.0)
    for bt in beat_times:
        start = int(round(bt * sr))
        if 0 <= start < mix.size:
            stop = min(mix.size, start + n)
            mix[start:stop] += tick[: stop - start]
    return (np.clip(mix, -1.0, 1.0) * 32767).astype("<i2")


def write_wav(path: Path, samples: "np.ndarray", sr: int) -> None:
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sr)
        handle.writeframes(samples.tobytes())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", help="one exact local audio or video file")
    parser.add_argument("--out", help="new directory for song-map.json and beats.csv (must not exist)")
    parser.add_argument("--sr", type=int, default=22050)
    parser.add_argument("--start-bpm", type=float, default=120.0, help="tempo prior centre (default 120)")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--click-preview", action="store_true",
                        help="also write click-preview.wav: the mix with a tick on every estimated beat (needs --out)")
    args = parser.parse_args(argv)
    try:
        if args.click_preview and not args.out:
            raise SongMapError("--click-preview needs --out")
        result, audio = analyse_with_audio(Path(args.input).expanduser().resolve(), args.sr,
                                           args.start_bpm, args.ffmpeg)
        if args.out:
            out = Path(args.out).expanduser().resolve()
            if out.exists():
                raise SongMapError(f"output directory exists: {out}")
            out.mkdir(parents=True)
            (out / "song-map.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            with (out / "beats.csv").open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["beat", "time_s"])
                for i, t in enumerate(result["beats"]["times_s"]):
                    writer.writerow([i, t])
            if args.click_preview:
                write_wav(out / "click-preview.wav", click_preview(audio, args.sr, result["beats"]["times_s"]), args.sr)
            summary = {k: result[k] for k in ("source", "decode")}
            summary["tempo_bpm"] = result["tempo"]["bpm"]
            summary["beats"] = result["beats"]["count"]
            summary["section_candidates_s"] = [b["time_s"] for b in result["sections"]["boundaries"]]
            summary["written"] = str(out)
            if args.click_preview:
                summary["click_preview"] = str(out / "click-preview.wav")
            print(json.dumps({"ok": True, **summary}, indent=2))
        else:
            print(json.dumps({"ok": True, **result}, indent=2))
    except SongMapError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
