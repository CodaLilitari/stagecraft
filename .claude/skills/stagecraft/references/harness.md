# Stagecraft local harness (Red's fork)

Five helpers and their tests, all Python 3.10 or later. None of them installs or downloads anything, generates media, or drives an editor.

| Script | Needs | Runs best |
|---|---|---|
| `conform_audit.py` | standard library | device or cloud |
| `sample_video.py` | standard library + `ffmpeg`/`ffprobe` | device, beside the media |
| `contact_sheet.py` | Pillow | cloud (or the device, if Pillow imports there) |
| `song_map.py` | numpy + `ffmpeg` | cloud (or the device, if numpy imports there) |
| `check_updates.py` | standard library | cloud, with `--env-proxy` |
| `test_*.py` | as above | cloud: `python3 -B -m unittest discover -s scripts -p "test_*.py"` |

[tooling-and-review.md](tooling-and-review.md) explains the device/cloud split. On the device, copy a script once per session to `$HOME/.red-tools/stagecraft/` with a quoted heredoc and run it from there. In the cloud, run it from the skill directory. Use a fresh output name for every run, and read the returned status before promoting anything.

Upstream's conform and sampler specifications are kept below nearly verbatim (MIT, Stagecraft contributors). The fork changed `conform_audit.py` only for Python 3.10 compatibility (a chunked SHA-256 in place of `hashlib.file_digest`).

## Map the song

```text
python3 -B scripts/song_map.py SONG.wav --out NEW_DIR [--start-bpm 168] [--click-preview]
```

- **Input:** one exact audio or video file. It's decoded to 22,050 Hz mono, and the receipt records the input's SHA-256. If you analysed a reduced derivative (see tooling-and-review), keep the master's hash beside it.
- **Writes:** `NEW_DIR` must not exist. Outputs are `song-map.json` (schema `red-stagecraft/song-map/v1`), `beats.csv`, and with `--click-preview`, `click-preview.wav`.
- **Exit codes:** `0` ok, `2` refused or failed. Silence and constant signals are reported, not invented around.

What the map contains, and how far to trust it:

- **Tempo.** The global estimate is the least-squares slope of the beat grid, with half and double alternatives listed. Octave choice is ambiguous by construction. The prior is centred on `--start-bpm` (default 120); when the brief states a tempo, pass it, and the prior then picks that octave without forcing it. On synthetic clicks, a prior of 168 still reads an 84 BPM track as 84, and 160/166/170 BPM read exactly.
- **Stability.** Re-estimates tempo over 20 s windows. A window reading 2:3 or 1:2 of the global tempo usually means a half-time, triplet-feel or sparse passage, not a tempo change. Check it by ear.
- **Beats.** A dynamic-programming beat tracker (after Ellis 2007) with a calibrated 33 ms onset latency. Leading and trailing beats in near-silence are trimmed by signal level. `share_within_5pct_of_median` is a regularity check, not accuracy.
- **Energy.** RMS dB of the decoded mono mix every half second. This is not LUFS and not perceived loudness.
- **Sections.** Candidate changes in beat-synchronous timbre (Foote checkerboard novelty, 16-beat kernel), with strengths. These are candidates only. Name sections from the lyric sheet and by listening.
- **Click preview.** The mix with a short tick on every estimated beat, and no downbeats, because none are detected. Red can't hear it. Ask Andrei, or an audio-capable reviewer, to listen to ten seconds at the intro, a strong section candidate and the outro: do the ticks sit on the beat, drift, or land on the off-beat?
- **What it never gives:** lyric timing, vocal onsets, which singer is singing, or lip sync. Supplied lyrics stay supplied text; ASR stays ASR; the map stays a measured estimate.

### Validation on the Smart Home Strike master (26 October 2026)

- **Input:** the upstream master, SHA-256 `b42704c2…088b`, 191.0 s.
- **Tempo:** 171.23 BPM (171.27 with `--start-bpm 168`), 543 beats. Per-20-second beat slopes read 169–172 BPM through the body; the intro and outro grids are less regular.
- **Intent vs measurement:** the brief's tempo was 168 BPM. Treat that as composition intent: a 168 grid laid over this recording would slip about a beat every 18 seconds. The click preview is how someone listening confirms which is right.
- **Stability:** two windows around 100–120 s read about 113–116 BPM, a 2:3 relation to 171, in the passage around the provisional "AT-ti" cue. The beat grid itself stays near 171 there.
- **Strongest section candidates:** 7.25, 18.66, 55.06, 57.83, 113.72, 116.50 and 155.89 s. 116.50 sits about 10 ms from the end of the provisional "Lily unfinished AT-ti phrase" cue (116.51). 124.93 and 150.22 sit near the provisional "Coda Cool" (124.83) and "Duet CLICK CLACK" (149.97) cues.
- **Status:** the provisional cues are themselves unverified ASR/editorial landmarks. This is agreement between two estimates, not ground truth.

## Look at sampled frames in one read

```text
python3 -B scripts/contact_sheet.py SAMPLE_DIR --out NEW_SHEET.png [--cols 6] [--tile-width 320] [--start S] [--end S] [--max-tiles 48]
```

- **Input:** a completed `sample_video.py` output directory. Every PNG used is checked against the receipt's SHA-256 first.
- **Output:** one new PNG, outside the sample directory. Each tile is labelled with decoded frame index and actual time, and the final decoded frame is marked END.
- **Large runs:** split them by time range (`--start`/`--end`) instead of shrinking tiles until faces are unreadable. Around 24–30 tiles at 320 px is a comfortable single read.
- **Limits:** a sheet is an overview of stills. It doesn't show motion, mouths in motion, or audio.

## Audit a source conform

```text
python3 -B scripts/conform_audit.py MANIFEST.json --out NEW_RECEIPT.json
python3 -B scripts/conform_audit.py MANIFEST.json --out NEW_RECEIPT.json --verify-hashes
```

The first command validates supplied metadata without checking asset existence or reading asset bytes. The optional `--verify-hashes` checks the exact listed files, computes SHA-256, and compares any supplied expected hashes. An observed hash without an expected hash does not prove preservation. No media probing, decoding, rendering, provider access, or editor operation occurs.

The receipt's parent directory must exist. Output creation refuses an existing path, the input manifest, and listed source paths, including a listed source that does not yet exist. Exit codes are `0` for a valid conform receipt, `1` for an invalid conform with issue details in its receipt, and `2` when output is refused or cannot be created. "Valid" means this helper's checks passed; it is not production approval.

### Manifest version 1

Times are integer microseconds, never floating-point seconds or booleans. Intervals are half-open: the out-point is excluded. FPS and speed values are positive rational strings such as `30/1`, `30000/1001`, or `3/2`. Positive integer strings are also accepted. IDs must be nonempty strings without surrounding whitespace and unique within their asset or clip list.

| Field | Required content |
| --- | --- |
| `schema_version` | Integer `1`. |
| `delivery` | Positive integer `width`, `height`, `duration_us`; positive rational `fps`. |
| `assets` | Array of objects with `id`, relative `path`, `kind` (`video` or `audio`), positive integer `duration_us`; optional rational `fps` and 64-character hexadecimal `sha256`. |
| `clips` | Nonempty array in timeline order. Each object has `id`, `asset_id`, integer `timeline_in_us`, `timeline_out_us`, `source_in_us`, `source_out_us`, and rational `speed`. Sources must reference video assets. |
| `audio` | Optional object with audio `asset_id`, integer `timeline_in_us`, `source_in_us`, and `source_out_us`. Playback speed is unchanged; its derived endpoint must fit the delivery. |
| `settings` | Optional object with nonnegative integer `duration_tolerance_us`, default `1`. |

Asset paths resolve relative to the manifest's directory. Absolute paths, drive-qualified paths, and paths escaping that directory are rejected. Put the manifest at the root of the intended package; do not use `../` to reach external media. Only explicit listed assets are considered. Extra annotation fields are ignored by the validator.

Duplicate JSON member names are rejected, including nested or escaped duplicates. Listed media and receipt destinations must use ordinary file-path syntax: Windows alternate streams, device names/namespaces and ambiguous trailing dots/spaces are refused. This is a portable path check, not an OS sandbox or a lock against another process changing a path.

The clip list must cover the complete delivery continuously from zero, with no gaps or overlaps. Source intervals must fit the supplied asset durations. The duration tolerance applies only to `source_span / speed - timeline_span`; it never excuses a gap, overlap, or exhausted source.

Shared timeline boundaries are rounded once to sequence frames with exact rational half-up rounding. The receipt records every duration and boundary-rounding residual as exact rational microseconds, including tolerated nonzero duration residuals. A clip that rounds to zero frames fails. The diagnostic last consumed source position is:

```text
source_in_us + (rounded_end_frame - rounded_start_frame - 1)
              * speed * 1000000 / delivery_fps
```

A position at or beyond the source selection's exclusive endpoint or supplied file duration fails. This model is not a claim about an editor's actual frame selection. Supplied FPS does not establish constant frame rate, and supplied geometry/duration is not independently probed. The helper does not quantize audio to samples because this schema does not supply its sample rate.

`native_import_status`, `native_reopen_status`, and `perceptual_review_status` always remain `not_checked`. A valid manifest, matching hashes, and frame coverage cannot certify native imports, effects, routing, audible transparency, storytelling, or lip sync.

[conform.example.json](../templates/conform.example.json) is a tiny metadata-only demonstration with two nonexistent, clearly synthetic video paths. It intentionally has no media or expected hashes:

```text
python3 -B scripts/conform_audit.py templates/conform.example.json --out example-audit-new.json
```

Adding `--verify-hashes` to this example should fail because its illustrative media does not exist.

**Beats in a conform:** to cut on the measured grid, convert `beats.csv` times to integer microseconds for `timeline_in_us`/`timeline_out_us`. Remember the audit rounds boundaries to sequence frames: at 24 fps, a beat lands on the nearest frame, within ±21 ms.

## Sample an actual video

```text
python3 -B scripts/sample_video.py INPUT.mp4 --out NEW_DIRECTORY
python3 -B scripts/sample_video.py INPUT.mp4 --out NEW_DIRECTORY --interval 0.25 --max-width 1280 --decode --ffmpeg PATH_TO_FFMPEG --ffprobe PATH_TO_FFPROBE
```

`INPUT.mp4` is one exact, authorized local video file. No URL, wildcard, or folder input is supported. `NEW_DIRECTORY` must not exist, and its parent must already exist. Default interval is one second; default maximum preview width is 960 pixels, with no upscaling. Intervals accept positive finite seconds, including rational strings. `--decode` additionally checks all video/audio streams for reported decoding errors.

The sampler selects the first video stream that is not an attached cover image. It reads actual decoded frame timestamps, selects the nearest frame to each requested time relative to the first decoded frame, chooses the earlier frame on ties, and includes the actual final decoded frame. Repeated targets are consolidated. Frame indices are zero-based; source timestamps and requested/actual times remain in the receipt. The limit is 600 distinct samples: increase the interval when needed.

Outputs are `frame_*.png`, a local static `index.html` contact sheet, and `receipt.json`. The receipt records source hashes before/after, tool versions, operations, sample indices/timestamps, PNG hashes, and decode status. Extraction uses sequential decoding rather than approximate seeking, so cost grows with source duration and sample count.

Exit `0` means sampling completed, `1` means an operational failure is recorded in the new output receipt, and `2` means the output path could not safely be created. Failed runs can leave partial artifacts for diagnosis; use a new directory on retry. Source-hash changes make the run fail.

PNGs may be downscaled and use FFmpeg's default autorotation/color conversion; they are inspection derivatives, not editing masters. Static sampling and error-free decoding do not establish continuous motion, listening, singing synchronization, or perceptual approval. Receipts contain local paths and filenames; sanitize a copy before public sharing.

Red reads the PNGs (or a `contact_sheet.py` grid of them) after staging them to the cloud. The `index.html` contact sheet is for Andrei's browser, not for her.

## Inspect dense passages

Use the one-second overview first, then make a short lossless inspection derivative for the flagged span. For example, a four-second span from source time 50 s:

```text
ffmpeg -n -ss 50 -i EXACT_SOURCE.mp4 -t 4 -map 0:v:0 -map 0:a? -c:v ffv1 -c:a pcm_s16le excerpt-50s-4s.mkv
python3 -B scripts/sample_video.py excerpt-50s-4s.mkv --out excerpt-review-new --interval 0.1 --decode
```

Record the original source hash, requested range, derivative hash and the original-to-excerpt timestamp relationship. Probe the actual result: seeking, frame quantization, nonzero stream starts and VFR can change the first decoded frame. For exact frame claims, compare the derivative's first and last pictures and timestamps with the original's decoded frames. Never infer the original timeline location from the excerpt's zero clock alone. Keep this derivative separate from the edit master and from any compressed review derivative sent to a reviewer.

## A synthetic exercise

In an empty scratch directory (`-n` refuses an existing file):

```text
ffmpeg -n -f lavfi -i testsrc2=size=320x180:rate=24 -f lavfi -i sine=frequency=440:sample_rate=48000 -t 3 -c:v ffv1 -c:a pcm_s16le synthetic.mkv
python3 -B PATH_TO_SKILL/scripts/sample_video.py synthetic.mkv --out synthetic-review --decode
python3 -B PATH_TO_SKILL/scripts/contact_sheet.py synthetic-review --out synthetic-sheet.png
```

- **Expected:** a three-second, 72-frame fixture with four selected frames at about 0, 1, 2 and 2.958 s, including the actual last frame. Matroska's time base can round 71/24 s to 2.958.
- **Self-check:** `testsrc2` burns the frame number into each picture, so the sheet's labels can be checked against the pixels.
- **Scope:** this is an exercise, not evidence about any real song or edit.

## Check for an upstream release

```text
python3 -B scripts/check_updates.py --env-proxy
```

This reads `skill-version.json` (upstream version 1.0.0 plus a `fork` block), then the public GitLab release feed, with the portfolio as fallback. GitHub is not on the path. For offline use, `--manifest EXACT_RELEASE_JSON`; `--feed HTTPS_URL` selects one explicit feed. `--env-proxy` routes through the environment's HTTPS proxy, which the cloud workspace requires.

- **What it checks:** the release's schema, name, three-part version, HTTPS artifact URL, byte count and SHA-256 syntax. It prints JSON and never downloads, installs, authenticates or executes anything remote. Responses are bounded to 1 MiB, and duplicate JSON keys are rejected.
- **`update_available`** means upstream metadata describes a newer version. For this fork, that means: read upstream's changelog and fold useful findings in by hand. Never overwrite the fork with an upstream archive.

## Keep a resumable production state

[production-state.example.json](../templates/production-state.example.json) is a bookkeeping template, not input to any helper. Populate only observed or authorized facts. Empty arrays and `null` values are deliberate: they are not permission, selected media, or completion evidence.

- **Record:** the goal and its actual authorization, the locked master hash, the song-map path, the working revision, authorized resources and spending, the checkpoint, the next safe action, and separate review states.
- **For each real pending job:** keep its provider, returned job ID, exact submission receipt, current status, last observed time and reconciliation action. Reconcile the job before resubmitting after a timeout.
- **Keep apart:** sampled review, measured timing, native save/reopen, listening review and Andrei's approval.
