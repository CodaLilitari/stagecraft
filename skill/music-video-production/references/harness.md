# Stagecraft local harness

Use Python 3.11 or later. The Python code uses only the standard library. The video sampler additionally needs working `ffmpeg` and `ffprobe` executables, supplied explicitly or available on `PATH`; neither helper installs or downloads tools.

Run the commands below from the skill directory. Use a fresh receipt/output name for each run. Inspect the returned status before promoting an artifact.

## Audit a source conform

```text
python -B scripts/conform_audit.py MANIFEST.json --out NEW_RECEIPT.json
python -B scripts/conform_audit.py MANIFEST.json --out NEW_RECEIPT.json --verify-hashes
```

The first command validates supplied metadata without checking asset existence or reading asset bytes. The optional `--verify-hashes` checks the exact listed files, computes SHA-256, and compares any supplied expected hashes. An observed hash without an expected hash does not prove preservation. No media probing, decoding, rendering, provider access, or editor operation occurs.

The receipt's parent directory must exist. Output creation refuses an existing path, the input manifest, and listed source paths, including a listed source that does not yet exist. Exit codes are `0` for a valid conform receipt, `1` for an invalid conform with issue details in its receipt, and `2` when output is refused or cannot be created. “Valid” means this helper's checks passed; it is not production approval.

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

[conform.example.json](../templates/conform.example.json) is a tiny metadata-only demonstration with two nonexistent, clearly synthetic video paths. It intentionally has no media or expected hashes. To try it, use a new output filename:

```text
python -B scripts/conform_audit.py templates/conform.example.json --out example-audit-new.json
```

Adding `--verify-hashes` to this example should fail because its illustrative media does not exist. Replace the paths and metadata with authorized real sources before using that mode for a production.

## Sample an actual video

```text
python -B scripts/sample_video.py INPUT.mp4 --out NEW_DIRECTORY
python -B scripts/sample_video.py INPUT.mp4 --out NEW_DIRECTORY --interval 0.25 --max-width 1280 --decode --ffmpeg PATH_TO_FFMPEG --ffprobe PATH_TO_FFPROBE
```

`INPUT.mp4` is one exact, authorized local video file. No URL, wildcard, or folder input is supported. `NEW_DIRECTORY` must not exist, and its parent must already exist. Default interval is one second; default maximum preview width is 960 pixels, with no upscaling. Intervals accept positive finite seconds, including rational strings. `--decode` additionally checks all video/audio streams for reported decoding errors.

The sampler selects the first video stream that is not an attached cover image. It reads actual decoded frame timestamps, selects the nearest frame to each requested time relative to the first decoded frame, chooses the earlier frame on ties, and includes the actual final decoded frame. Repeated targets are consolidated. Frame indices are zero-based; source timestamps and requested/actual times remain in the receipt. The limit is 600 distinct samples: increase the interval when needed.

Outputs are `frame_*.png`, a local static `index.html` contact sheet, and `receipt.json`. The receipt records source hashes before/after, tool versions, operations, sample indices/timestamps, PNG hashes, and decode status. Extraction uses sequential decoding rather than approximate seeking. It stores all probed timestamps in memory and decodes from the beginning for each batch of up to 100 images, so cost grows with source duration and sample count.

Exit `0` means sampling completed, `1` means an operational failure is recorded in the new output receipt, and `2` means the output path could not safely be created. Failed runs can leave partial artifacts for diagnosis; use a new directory on retry. Source-hash changes make the run fail.

PNGs may be downscaled and use FFmpeg's default autorotation/color conversion; they are inspection derivatives, not editing masters. Static sampling and error-free decoding do not establish continuous motion, listening, singing synchronization, or perceptual approval. The sampler performs no playback or listening. Its receipts contain local source/tool paths and filenames; sanitize a copy before public sharing.

## Practice and inspect dense passages

### Dense review without sampling an entire film

For a long film, first use the one-second overview, then prepare a short inspection derivative for the flagged span. For example, with a verified four-second interval beginning at source time 50 seconds:

```text
ffmpeg -n -ss 50 -i EXACT_SOURCE.mp4 -t 4 -map 0:v:0 -map 0:a? -c:v ffv1 -c:a pcm_s16le excerpt-50s-4s.mkv
python -B scripts/sample_video.py excerpt-50s-4s.mkv --out excerpt-review-new --interval 0.1 --decode
```

Use explicit executable paths if necessary. Record the original source hash, requested source range, derivative hash, and original-to-excerpt timestamp relationship. Probe the actual result: seeking, frame quantization, nonzero stream starts and VFR can change the exact first decoded frame. Do not equate a requested seek time with a proven frame identity. For exact frame claims, compare the derivative's first/last pictures and actual timestamps with the original decoded frames. Keep this lossless inspection derivative separate from the edit master, and retain original indices/PTS in the review note. Never infer the original timeline location from the excerpt's zero clock alone.

### A local synthetic sampler exercise

Create this only in an empty scratch directory; `-n` refuses an existing file:

```text
ffmpeg -n -f lavfi -i testsrc2=size=320x180:rate=24 -f lavfi -i sine=frequency=440:sample_rate=48000 -t 3 -c:v ffv1 -c:a pcm_s16le synthetic.mkv
python -B PATH_TO_SKILL/scripts/sample_video.py synthetic.mkv --out synthetic-review --decode
```

Expect a three-second, 72-frame fixture and four selected frames at approximately 0, 1, 2 and 2.958 seconds, including the actual last frame. Matroska's timestamp time base can round 71/24 seconds to 2.958; use the observed receipt rather than inventing additional precision. Read the receipt and inspect the contact sheet; don't treat this synthetic exercise as evidence about a real song or edit. The shipped tests additionally build VFR and low-frame-rate fixtures.

## Check for a release without installing anything

`python -B scripts/check_updates.py` reads the installed `skill-version.json`, then tries the public GitLab release feed and the portfolio fallback. GitHub is not part of this dependency path. For an offline exercise, use `--manifest EXACT_RELEASE_JSON`; `--feed HTTPS_URL` selects one explicitly supplied feed.

The checker validates the release's schema, name, three-part version, HTTPS artifact URL, byte count and SHA-256 syntax. It prints JSON and never downloads an archive, modifies the installation, authenticates an account or executes remote instructions. Network responses are bounded to 1 MiB, redirects are restricted, and duplicate JSON keys are rejected. Timeouts apply per operation, not as a whole-check deadline.

An `update_available` result means the metadata describes a newer version. It is not proof that the archive exists or that its bytes, authorship or contents are trustworthy. Download separately only within the current task's authority, verify the actual bytes/hash, inspect the changes, preserve local modifications and authorize installation separately. Do not turn a read-only feed check into an unattended installer or a scheduled job without the user's request.

## Keep a resumable production state

[production-state.example.json](../templates/production-state.example.json) is a bookkeeping template, not input to either helper. Populate only observed or authorized facts. Empty arrays and `null` values are deliberate; they are not permission, selected media, or completion evidence.

Record the goal and its actual authorization, locked master hash, working revision, authorized resources/spending, checkpoint, next safe action, and separate review states. For each real pending job, retain its provider, returned job ID, exact submission receipt, current status, last observed time, and reconciliation action. Reconcile that job before resubmitting after a timeout. Attach evidence references to review results; keep sampled review, native save/reopen, continuous audiovisual review, and user approval separate.
