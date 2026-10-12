# Models, host routes, and face repair

Use this reference when selecting a generator, diagnosing identity or performance failure, or considering local repair. The observations come from a music-video production on **2026-10-07 through 2026-10-11**, reviewed for this skill on 2026-10-12. They are dated evidence, not current product specifications or universal rankings. Verify current host, displayed model, controls, reference support, account eligibility, output count, export options, and quote before acting. This reference authorizes no installation, model download, upload, purchase, or inference.

Record these states separately: researched, available, installed/downloaded, prepared, submitted, output produced, inspected, selected, and integrated. A current receipt can supersede an earlier failure without erasing it. A model name in a template is not evidence that its weights ran.

## Models that produced project outputs

| Route and recorded model | Dated result | Decision-changing limit |
|---|---|---|
| **Google Flow: Omni 1.1 Flash** | Oct 7–8: Frames and Ingredients modes produced 720p motion; separate Characters and a scene reference were used. Some spans entered draft coverage. | Stable, distinct faces were sometimes stable versions of the wrong faces. A subsequent canonical comparison rejected identity fidelity. Body movement and editorial usefulness did not establish identity approval or singing. |
| **Adobe Firefly: Kling 3.0 Omni** | Oct 7–8: reaction footage, then 1080p performance candidates with saved Elements, first frames, generated audio, and Auto multi-shot. Selected spans were used. | Early takes missed restrained expression; later ones improved motion and angles but had occlusion, smear, polished skin, and timing drift. K06 later words lagged roughly 0.24–0.56 s; K08's second line began about 0.53 s early. These are clip findings, not model latency constants. |
| **Direct Kling web: displayed VIDEO 3.0 Omni** | Oct 11: the project also called this route “o3 Omni.” Structured character Elements plus a wide scene image produced K11/K11B and K12–K14 at 1080p/24 fps. These sources were packaged in the delivered R4 edit. | This is distinct from Google Omni and from Adobe's wrapper. The takes supplied stronger dance, dialogue reactions, and camera variety, but needed phrase-level recutting, role corrections, and defect trims. Final continuous audiovisual and singing approval remained unresolved. |
| **Grok Imagine web: exact backend unexposed** | Oct 7: preserved 720p conducting, sofa movement, and appliance-action clips; selected spans entered drafts. | Do not invent a backend version. A sofa take supplied boot placement/shared dance without establishing the requested strong impact. Fresh-composer audio settings needed rechecking. |
| **Built-in image generation: exact backend unrecorded** | Oct 7–8: concept plates, character/scene anchors, and targeted prop corrections were produced and inspected. | A chat model picker is not an image-model identifier. Accepted stills remained conditioning inputs; temporal identity, choreography, and mouth ownership required actual video tests. |
| **FaceFusion 3.9.1: hyperswap_1a_256** | Oct 8: single-frame and bounded moving face replacements completed on local CPU/CUDA routes. | Identity proportions improved, while freckles, skin texture, smirk, and dimple weakened. Successful selection and encoding did not justify production replacement. |
| **FaceFusion expression restorer: live_portrait** | Oct 8: applied after the swapper; a later serial CPU run completed all 51 frames after earlier resource stops. | Some crooked smile/cheek crease returned, but gaze and texture changed. The completed comparison remained unaccepted for production. See the repair procedure below. |
| **faster-whisper small.en and base.en** | Local diagnostic ASR ran using faster-whisper 1.2.1; CPU/int8 was recorded. | Same-family transcripts can share errors. ASR is neither listening, speaker identification, nor visible phoneme verification. Final-shout passes failed reliable timing and remained negative evidence. |

Direct Kling's useful results were specific, not perfect: K11/K11B delivered different phrase order/timing and sometimes featured the wrong singer; K12 recovered the intended dialogue order but used two setups instead of the requested succession of closeups. K13 developed a brief floor-robot deformation and an unwanted piercing; K14's visible shout did not establish precise phonemes. Inspect the result against the brief, then preserve its useful motion without claiming prompt compliance from submission alone.

## Attempted, prepared, and researched routes

**Attempted without output:** Adobe Veo 3.1 Fast rejected one reference and returned a generic processing refusal for another. Adobe Kling 3.0 Omni also had generic failed jobs, including a manual multi-shot test. Preserve the actual error category; do not infer its cause, prove universal incapability, or treat failed jobs as coverage. A quote is not settled billing.

**Local MiniMax H3 Ref2VA:** the native ComfyUI 0.30.2 graph was installed and validated. One preflight deferred without inference. A later 56-frame, 512×288 reference-conditioned attempt was interrupted at `MiniMaxH3ReferenceToVideo` by a system commit-headroom guard, before diffusion sampling: zero sampling steps, zero output files, no observed OOM exception. It did not establish permanent hardware incompatibility, required additional headroom, or identity quality. This graph performed reference-conditioned regeneration, not pixel-preserving masked repair. Source and output audio were disconnected.

The actual H3 graph used:

- `minimax_h3_ref2va_pruned_int8_convrot.safetensors`
- `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`
- `minimax_h3_video_vae_fp16.safetensors`
- `minimax_h3_audio_vae_fp32.safetensors`

The FP16 video VAE replaced the template's newer INT8 VAE. Optional turbo LoRA, switch branches, and newer Fun ControlNet extras were omitted. Registered filenames and validated graph structure did not prove completed weight execution.

**Prepared only:** Topaz Video 1.7.1.0 recognized **Starlight Precise 2.6** as installed; catalog/package naming retained `slp-2.5`. Device enumeration succeeded. No render was queued. The actual Precise filter JSON, sharpening schema, model-store configuration, and end-frame semantics remained unresolved; generic `tvai_up` help was insufficient. **Starlight Fast 2** was unchecked and its payload was absent in the scoped check. Neither established successful facial-detail restoration.

**Research only:** the shortlist included Dreamina **OmniHuman 1.5 / Avatar Pro / Turbo**, host-specific **Seedance 2.0/Fast and 2.5**, **Wan2.2 Animate 14B / Mix**, **Wan Animate 2**, **Ray3 Modify**, **Runway Aleph 2.0**, and Flow **Veo 3.1 Lite/Quality**. CapCut lip sync, Adobe camera-reference generation, and Adobe translation/lip-sync were separate feature routes. H3 research additionally named FL2VA, hosted H3-Context-IR/H3-Regenerate-2K, Fun ControlNet Union v1/2, and pose/detector extras. Research did not run them. Audio-reference conditioning, generated audio, translation, and a separate lip-sync pass are different capabilities; verify the exact wrapper rather than transferring claims between hosts.

## A bounded identity-repair procedure

1. **Diagnose against canon and the original performance.** Compare face proportions, eyes, expression/gaze, jewelry, texture, mouth action, motion, and surrounding scene separately. Stable hair colors or two distinguishable people are insufficient. Select a frontal frame, an expression apex, and an occlusion/head-turn frame before a moving test. These are useful examples, not a compulsory sample count.

2. **Prove selection before synthesis.** A two-person probe initially selected both faces at one similarity threshold. A narrower threshold isolated the intended face for that frame, but did not qualify tracking. A subsequent single-person clip used explicit count, location, size, and center-movement bounds. Its first version missed late frames; a revised selection policy passed all 48 frames. Derive bounds for each shot; do not reuse numeric thresholds or face positions blindly. Save misses and cross-bindings rather than labeling unchanged frames repaired.

3. **Keep per-stage pixels.** Preserve original, swap-only, and expression-restored frames with exact source indices and hashes. The tested chain was `hyperswap_1a_256 → live_portrait`, factor 80, lower-face expression, box plus occlusion masks, no enhancer. Those settings describe an experiment, not defaults. Expression restoration recovered part of the smile but regenerated the whole crop. “Lower-face” restricted latent expression, not the output pixel mask. Adding upper-face restoration on one frame still failed to recover strong side-eye.

4. **Treat resource stops accurately.** Earlier CPU/CUDA attempts hit chosen private-memory fuses; other attempts hit actual system-headroom guards. Neither automatically meant OOM. Serial CPU processing eventually completed 51 frames without lowering guards. Releasing completed content-analysis sessions after the stock check preserved the comparison frame exactly. That local optimization did not remove checks or prove arbitrary workloads safe. Keep resumable frame manifests and terminate only owned workers.

5. **Preserve performance with a targeted composite when warranted.** The tested eye repair reused original eye pixels over the expression-restored face: opaque iris/sclera cores, exterior feathering, inspected polygon keyframes, and bidirectional pyramidal Lucas–Kanade tracking. No additional neural model ran. All 51 composites completed; five intervals retained strict tracking warnings and needed every-frame mask inspection. The RGB lossless master preserved pixel invariants; a YUV420 review encode did not. Original eye styling/proportions return too, so assess that identity-performance tradeoff. Continuous playback and production acceptance remained separate.

6. **Stop when improvement is too small or changes the performance.** A one-frame non-neural cheek-detail transfer restored only faint freckle contrast; it excluded displaced nose/outline geometry and did not justify a full moving pass. Topaz was not tested as its cure. The next character's prepared runner never reached inference in the recorded checkpoint. Texture processing cannot establish missing singing, fix wrong source geometry, or recover unmeasured lip synchronization.

Auxiliary FaceFusion diagnostic sessions recorded `yoloface_8n`, `fan_68_5`, `2dfan4`, `arcface_w600k_r50`, `fairface`, `nsfw_1/2/3`, and `xseg_1` ONNX models. `bisenet_resnet_34` existed but its parser route was only inspected here; eye/lip retargeter and stitcher weights were absent. A separate **InsightFace/InSwapper** run was not established. Do not relabel the recorded ArcFace recognizer as proof of that separate pipeline.

## Choose the next action from the failure

For wrong identity, test accepted canonical references and host controls before a bounded repair or replacement. For missing bodily energy, specify concrete weight transfer and gestures; a moving camera is insufficient. For poor synchronization, use short phrase mapping and inspect mouths against the chosen song; avoid one global speed change across unequal generated phrases. For softness, compare native source pixels before adding enhancement. Prompted film grain or practical effects are requests, not observed properties. Carry the smallest useful successful test forward; keep unresolved quality gates explicit.
