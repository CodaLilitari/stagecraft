# Production driven by code

Use this route for repeatable graphics, titles, compositing, captions, sound processing or procedural scenes within a music-video brief. It also works beside generated performance footage and a native editor. Choose the smallest toolchain that expresses the intended shot and preserves the approved recording.

This guide was added on 2026-11-01 after evaluating a user-supplied production-stack post. The useful lesson is to connect a brief, timeline, renderer, sound, review and delivery through explicit data. Claims that fifteen repositories replace every After Effects job or a fixed studio invoice are not established by that list. “No new software purchase” is a possible project budget, not a zero-cost guarantee: hardware, storage, electricity, asset rights, subscriptions, engineering and revisions still matter.

**Implementation status:** Stagecraft currently bundles a conform auditor, a frame sampler and a release checker. This guide adds a production method and optional integration choices; it does not add a Blender, browser, React or audio-rendering adapter. Documentation-verified capability, installed dependency, successful pilot and accepted production output are separate states. No particular assistant model is required or certified by this method.

## Select a lane, then add tools for a reason

| Need | Candidate | Boundary that changes the decision |
| --- | --- | --- |
| Existing footage, overlays, assembly and delivery | [FFmpeg/ffprobe](https://ffmpeg.org/documentation.html) | Start here when existing filters suffice. Record the actual build and enabled codecs; distribution terms depend on its configuration. |
| Static graphics and contact sheets | [Pillow](https://pillow.readthedocs.io/en/stable/handbook/overview.html) | A light choice for image operations. Stagecraft's existing sampler already creates review PNGs/HTML without it; avoid a duplicate dependency just for those outputs. |
| Numerical animation controls or measurements | [NumPy](https://numpy.org/doc/stable/user/whatisnumpy.html), [SciPy signal](https://docs.scipy.org/doc/scipy/reference/signal.html) | Useful for envelopes, arrays, filters, convolution and resampling. They supply calculations, not a complete editor or automatic creative direction. |
| A measured numerical bottleneck | [Numba](https://numba.readthedocs.io/en/stable/user/5minguide.html) | Profile first. JIT compilation and supported-operation limits apply; it does not accelerate arbitrary browser or Python code. |
| Offline 3D scenes, cameras and compositing | [Blender](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html) | Background rendering is supported. Prove the exact scene, renderer, assets and device on a small pilot before scaling. |
| Procedural browser 3D and previews | [Three.js](https://github.com/mrdoob/three.js) | Rendering a canvas is one stage. Export still needs a controlled timeline, asset readiness, capture and encoding. |
| Browser frame capture | [Puppeteer](https://pptr.dev/) | Pin browser, fonts and viewport. Its normal package downloads a browser; `puppeteer-core` requires an explicitly managed browser. Use a dedicated render process, not the user's personal browsing profile. |
| React compositions with a frame model | [Remotion](https://www.remotion.dev/docs/idea) | A deliberate composition architecture, not a required dependency. Verify the package's applicable license before adopting or distributing it. |
| Tween/easing timelines | [GSAP](https://gsap.com/docs/v3/GSAP/Timeline/) | Optional animation authoring, with explicit seeking for export. Its custom license needs a use-case check, especially for visual animation-building products. |
| New procedural music or sound effects | [Tone.js](https://github.com/Tonejs/Tone.js) | Coordinate its audio timeline with video explicitly. Generating sound is not authorization to replace or remix the approved song. |
| Offline audio processing or plugin hosting | [Pedalboard](https://github.com/spotify/pedalboard) | Effects and hosting are available; third-party plugin licenses and automation behavior remain separate. Preserve an unprocessed reference. |
| Loudness measurement and normalization | [pyloudnorm](https://github.com/csteinmetz1/pyloudnorm) | Integrated loudness is one measurement. Add appropriate true-peak checking and listening; it does not make a mix universally platform-safe. |
| Draft captions and timing | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Local inference has compute and model requirements. Check words and timing against the actual recording; music and singing can be difficult. |
| Tracking and image analysis | [OpenCV](https://docs.opencv.org/4.x/d9/df8/tutorial_root.html) | Useful for measured defects and motion analysis. A threshold crossing is a flagged interval, not an automatic judgment that the shot is broken. |

The list is a menu. A footage edit may only need the existing editor, FFmpeg and Stagecraft helpers. A caption-heavy React piece may justify Remotion. A 3D scene may justify Blender. Install neither a second timeline nor a numerical/JIT stack without a concrete benefit.

## One timeline and an explicit frame contract

Keep one authoritative sequence rate as a rational number and one total frame count. For rate `p/q`, frame `n` begins at `n*q/p` seconds. Use half-open shot ranges: frame `in` is included and frame `out` is excluded. For adjacent cuts, the outgoing shot's `out` equals the incoming shot's `in`; transitions and layers may intentionally overlap. Resolve rounding at shared boundaries once, as the existing [conform guide](harness.md) does. That helper audits a continuous single-track conform; it does not validate a layered composition. Keep audio positions at their actual sample rate; do not round audio timing repeatedly through video frames.

A production recipe should identify the chosen master and source hashes, shot spans, dimensions, crop and color decisions, fonts, renderer/tool versions, asset paths, caption text, output profile and randomness policy. Store generated frames, caches, virtual environments and render copies outside Git checkouts; do not link those directories back into the checkout. Source recipes and small validation receipts can remain with source control.

For a browser or procedural renderer, request a specific frame rather than sleep until a wall-clock animation happens to reach it:

1. Load the exact assets and fonts, establish viewport/device scale and color settings, and wait for explicit readiness. Network idleness alone is not proof that fonts, media seeks or GPU work have finished.
2. Derive transforms, visibility and text from the requested frame/time. Seed randomness. If physics or another stateful simulation is needed, bake a deterministic cache or replay from a fixed initial state; random frame seeking cannot simply skip its history.
3. Seek embedded media to the intended source time, await actual decode/readiness and render completion, then capture. Record failed or missing frames rather than silently substituting the previous picture.
4. Re-render selected boundary and mid-shot frames in a different order under the same pinned environment. Compare pixels or hashes when byte identity is appropriate; declare a justified tolerance when nondeterministic GPU output prevents exact equality. Cross-device byte identity is not assumed.

This independent-frame principle follows [Remotion's flicker guidance](https://www.remotion.dev/docs/flickering) but applies to a custom renderer too. Real-time playback and offline export are different tests. If GSAP, Three.js, video elements and an audio transport coexist, explicitly nominate the export clock; do not let four clocks drift independently.

## Pilot, render and assemble

Choose a short representative section that includes the hardest transition, typography, transparency, motion and audio boundary. Save its recipe and actual render duration, memory/storage observations and defects. A successful low-resolution preview does not establish a production-resolution render budget. Use measured peak resources to choose concurrency; more workers are not always faster or safe.

Render numbered frames or bounded shot intermediates into a new output directory. Keep a completion record keyed to the recipe, dependency/asset hashes and render settings. Resume only matching completed work; changed inputs invalidate affected results. Preserve failures and partial outputs for diagnosis instead of silently replacing them. The proposed checkpoint is a workflow contract, not a currently bundled Stagecraft render scheduler.

Assemble from approved originals/intermediates with explicit stream mapping, frame rate, resolution, pixel format, color tags and audio routing. Color tags describe the encoded signal; verify that required color-space, transfer-function and range conversions actually occurred. Use a lossless or appropriate mezzanine intermediate when later processing needs it. Preview proxies are review derivatives. Preserve the selected song, and retain an unchanged reference when gain, effects, compression, limiting or resampling is authorized. Check stream start times, encoder delay, exact duration and final synchronization; an MP4 extension is not evidence of its codec or completeness.

Captions need an editorial pass over the actual audio: names, intentional lyric variants, profanity handling requested by the brief, word timing, line breaks and safe areas. ASR can invent text; the [Whisper model card](https://github.com/openai/whisper/blob/main/model-card.md) documents that limitation. Keep supplied lyrics, machine transcript and adopted captions distinguishable.

For sung performance, use the [cue-to-performer and review-evidence record](production.md). Audio alignment, lyric timing, visible singer ownership and mouth synchronization are different checks. Keep automated placeholders and rejected-take fallbacks visibly marked as draft coverage; require explicit selection before final export. A render that reaches the final frame is not automatically an accepted cut.

## Measure the delivered candidate, then review it

| Check | Evidence to retain | Limit |
| --- | --- | --- |
| Media integrity | Full decode of every intended video/audio stream; probed streams, actual frame count/timestamps, dimensions, duration and audio layout | A successful decode does not establish good choreography, captions or sound. |
| Timeline and boundaries | Conform receipt plus sampled/exported frames at joins and endpoints | Metadata validation alone does not establish what an editor or renderer actually selected. |
| Black, frozen or silent spans | Tool version, thresholds, timestamp ranges and comparison with intended shot/audio design | Deliberate holds, fades and silence are allowed. Flags require interpretation. |
| Audio delivery | Integrated loudness and true-peak measurements on the final encoded file, against the chosen delivery specification | No single loudness value is correct for every platform or artistic brief. Re-encoding can alter peaks. |
| Visual and audio review | Contact sheet, dense samples where needed, actual playback/listening observations and remaining concerns | Static images cannot prove continuous motion, lip sync or listening. |
| Handoff | Final candidate hash, recipe/source references and exact review status | Rendered, technically checked, perceptually reviewed, accepted and published remain distinct. |

[FFmpeg's filters](https://ffmpeg.org/ffmpeg-filters.html) already offer black/freeze/silence detection and loudness analysis. Try those before adding OpenCV or another audio package solely to reproduce an existing measurement. The existing sampler and conform auditor remain useful regardless of renderer. Avoid re-running an expensive full decode after it has passed unless the candidate changed or new evidence warrants it.

## License and cost checks before adoption

The fifteen packages are not all open source, and the open-source packages do not all use permissive licenses. Record the pinned version, applicable license and intended use; Stagecraft's MIT license does not relicense dependencies, fonts, assets, models or plugins.

- [GSAP's standard license](https://gsap.com/community/standard-license/) is a custom no-charge license with restrictions on certain competing visual animation-building tools. Do not label it unrestricted open source. Stagecraft's current workflow documentation does not by itself establish that a future editor's use would qualify.
- [Remotion is source-available under a proprietary license, rather than an OSI open-source license](https://www.remotion.dev/docs/license/faq). Its [core license](https://github.com/remotion-dev/remotion/blob/main/packages/core/LICENSE.md) allows free production for specified individual/small-organization/nonprofit/evaluation cases; other users need company licensing. Restrictions on selling or relicensing a derivative of Remotion also apply. Match the installed release to its terms. The [terms page](https://www.remotion.dev/docs/terms) displayed upcoming version-5 terms during this check; upcoming terms and current-release terms must not be conflated. Recheck eligibility and pricing at adoption instead of copying a stale price into a permanent skill.
- [Blender](https://www.blender.org/about/license/) and [Pedalboard](https://github.com/spotify/pedalboard) have GPL software terms; Blender separately explains ownership of rendered artwork. [FFmpeg's software license](https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/LICENSE.md) depends on build configuration: GPL components change the applicable license, while a binary configured with `--enable-nonfree` is not redistributable. That restriction concerns the built software, not a blanket prohibition on distributing rendered videos. Check the actual distribution and integration, not just a repository name.
- Local models avoid an API requirement, but their weights, dependencies and compute remain part of the inventory. Existing web subscriptions do not imply included API calls. Record actual incremental spending and resource observations rather than promising a free studio replacement.

Use this guide to make execution more repeatable and revisions cheaper. Creative direction, performance, sound and acceptance still have to be judged on the actual work.
