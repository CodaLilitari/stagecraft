# Assembly, repair checks and delivery

## Source quality and review quality

Preserve downloaded originals byte-for-byte. Store proxies, frame sheets, repaired comparisons and renders separately. A small browser WebM can be useful for review but should not become the conform source. Re-encoding a degraded proxy at a high bitrate cannot restore its detail. Probe actual codec, dimensions, sample aspect, frame rate, duration, color metadata and audio streams. Compare native-size face/detail crops as well as motion.

Scale and pad deliberately. A source just narrower than the canvas should not be stretched reflexively; inherited lower-resolution material remains lower-resolution. Upscaling/detail recovery and grain are finishing decisions that need comparisons. Synthetic pores or sharpness can change identity. Avoid multiple lossy generations and preserve an unprocessed version.

Use settings suited to the delivery rather than a universal bitrate. The example used a high-quality 1080p review, but 4K, 24/25/30 fps, HDR, vertical formats and animation need their own choices. Confirm the final encode, not merely the renderer arguments. Handle aspect, pixel aspect and orientation explicitly.

## Independent conform plan

Represent every cut with its source asset, source in/out, timeline in/out and speed. Keep continuous time (e.g. integer microseconds), source frame rate, sequence frame rate, and native ticks separate. Quantize shared cumulative boundaries once rather than summing independently rounded durations.

Check gaps/overlaps, zero-frame cuts, missing media, source exhaustion, unexpected repeated end frames, frame-count/duration differences, audio placement and tails. Distinguish an exclusive source endpoint from the actual last consumed sample. Report rounding residuals and legitimate tolerances rather than changing thresholds until a broken conform passes.

The helper in [harness.md](harness.md) validates this authored structure. It deliberately does not certify a native editor's interpretation.

## Native editor interop: the consequential failure

In Smart Home Strike, structurally valid legacy XML imported all media online with plausible item counts and timeline boundaries, yet retimed clips selected the wrong footage. Time-remap graph interpretation and mixed source/sequence rates were involved. XML validation alone missed it.

Build a small diagnostic sequence with ordinary, slow, fast, mixed-FPS and long-source-offset cases. Compare actual native exported frames with the intended original frames and the reference render. Readback metadata alone is not enough. In the tested Premiere 26.5.2 correction, sequence-rate clip coordinates and percentage-only speed worked while each file retained its real FPS. This is a dated tested pattern, not a universal importer recipe; do not blindly transplant the project's original exporter.

Use supported app automation/UXP/MCP when available and inspect its current capability. An installed plugin or successful HTTP/process response does not prove the host executed the requested action. Verify its returned status, saved artifact and native state. Use additive diagnostic sequences and new output paths. After a timeout or scripting failure, inspect the existing task-owned operation before retrying; do not repeatedly launch or mutate the same project on unknown delivery.

Path URLs, long Windows paths, permissions, escaping and host path normalization are separate from filesystem existence. Test exact paths, avoid shell-string interpolation, and relink exact allowlisted media rather than browsing private folders. Preserve the original project before repair.

## Three kinds of audiovisual evidence

1. **Technical:** full decode, frame count, streams, source/hash integrity, waveform timing/routing/gain. These cannot establish aesthetic success or listening.
2. **Sampled visual:** actual frames at one-second intervals plus dense cut/face/mouth boundaries. Exact frame indexes matter. Similar nearly static frames may identify a source without identifying its exact time; keep alternative rankings and confidence limits.
3. **Continuous audiovisual/perceptual:** supported playback/listening or an explicitly attributed human/AI review. A received review is a claim source, not automatic proof of reliable whole-film inspection. Check consequential notes independently.

Two proposed timing fixes in the example were contradicted by actual decoded frame boundaries. Do not implement a reviewer's confident timestamp merely because it sounds precise. If audio input was unavailable, say so instead of treating ASR or numerical checks as personal listening. One-second sheets cannot catch every flash frame or freeze; inspect flagged spans densely and actual movement where supported.

## Audio preservation

For a fixed-song brief, explicitly map the intended master; do not automatically mix generated clip audio. A provider's silent-output setting once returned audible content, so inspect streams and decoded samples. If effects/ad-libs are wanted, keep their authorization and mix plan explicit.

Export actual native audio to verify the native mix, including L/R routing, effective gain, offset, drift, unexplained silence and duration. Timeline objects don't prove what the mixer emits. Preserve subframe audio placement when required. Across sample-rate conversion or lossy encodes, sample identity is usually the wrong test; report appropriate correlations and tolerances. Peak/rail counts alone cannot establish audible clipping, especially with resampling. Never silently normalize or replace the selected master to make a check pass.

## Handoff

Deliver a clearly named review movie, current editable project if requested, required media, a manifest with relative paths and hashes, and short finishing notes. Save and reopen the native project; verify expected sequence/clip/audio counts and media-online state. If portability is promised, test relocation/relinking separately. An XML candidate is not equivalent to a native project containing later fixes.

Keep statuses separate: source package verified; render technically checked; native import sampled; native saved/reopened; continuous AV reviewed; user approved. A later user approval is new evidence, not retroactive proof that an earlier unavailable listening check happened. State what remains, without burying the user in every diagnostic receipt.
