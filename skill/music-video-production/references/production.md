# From song to useful footage

## Recover and pin the song

Prefer the exact selected master. If starting from an authorized public release, preserve the downloaded container, decoded timing reference, source URL and checksums. Label a decode of lossy audio as such; WAV is a container, not proof of a lossless origin. Do not substitute an older local variant because its title/duration looks similar.

If the master changes, compare several waveform windows throughout the song to estimate offset and drift. State the sign convention. Musical backing can dominate correlations: waveform agreement establishes recording alignment, not exact vocal onset or which singer is speaking. Keep any native subframe placement correction separate from the song file.

Use supplied lyrics as text authority; check against the actual take for omissions/ad-libs. ASR is a timing aid, with uncertain names, screamed words, profanity and duplicated choruses. Do not feed expected lyrics into recognition and then call the matching result independent confirmation. Prompt tempo, DAW tempo and measured tempo are separate fields. A provisional beat grid should remain provisional until checked across the song.

For each cue record: song interval, lyric/section, vocalist, dramatic purpose, timing source, confidence, and any protected pause/punchline. Make action readable before adding cuts or effects.

## Assign vocal roles and preserve review evidence

Before generation, make a cue-to-performer record. Keep the intended singer distinct from the performer observed in the selected take. A correct face, recognizable voice or high audio-correlation score does not establish that the right mouth delivers the line.

| Record | What to specify |
| --- | --- |
| Cue and recording | Cue ID, exact master/hash, song interval and adopted lyric or ad-lib |
| Intended ownership | Vocalist and visible singer; duet, offscreen voice or intentional reaction when applicable |
| Other performers | Expected listening, response, dancing or silence; do not force every other mouth closed when the scene calls for a duet |
| Selected evidence | Take/hash, source interval and source-to-song timing; actual observed performer and mouth visibility |
| Separate judgments | Identity, expression/gaze, body motion, role ownership, mouth/phoneme timing and continuity at both joins |
| Decision | Accepted, repair, replace, intentionally offscreen, or not assessable; reviewer and reason |

This is a production record, not an implemented Stagecraft speaker-diarization or face-recognition system. When voice identity is uncertain, retain that uncertainty rather than filling the intended assignment into the observed field. Preserve successful comedy, reactions and restrained expressions while replacing only a demonstrated failure.

For any automated sync measurement, document what it actually compares: audio against audio, transcript word times, visible mouth movement, or an audiovisual learned representation. Record tool/version, input audio, face selection, crop, visibility coverage, window, lag sign and units, threshold, and failure status. Missing dependencies, no suitable face, occlusion and offscreen vocals are not passing scores. A numerical value does not become a calibrated probability merely because it is called confidence. Singing, sustained vowels, rapid syllables, multiple singers, backing vocals and music-dominated waveforms require representative checks against judged examples. Do not transfer a speech threshold to singing without evidence.

Use corrected lyrics for alignment and display as appropriate, but do not call forced alignment independent verification of those words. Caption treatment and cuts on beats are editorial choices. Protect story timing, sustained gestures, reactions, silence and punchlines even when an automatic grid proposes a cut.

For external or delegated review, retain the reviewed file's hash/version, source URL when relevant, resolution, time origin, exact intervals, review method/model if exposed, and whether audio and continuous motion were available. A compressed social upload can reveal useful problems, but its timestamps and identity details must be checked against the chosen master before repairs. Separate reviewer-reported observations from locally confirmed defects. Unknown model identity and an unavailable source hash remain unknown.

Automation that keeps a draft renderable may substitute a still, freeze a final frame, choose a fallback take or cover a missing performance. Record those substitutions visibly and require acceptance before final delivery. A complete render is not evidence that every shot passed its quality gate. See [production driven by code](code-directed-production.md) for rendering and delivery checks.

**Source-audited example (2026-11-01):** [Claudia toolkit 0.3.6, commit `6071aed`, `avsync.py`](https://github.com/anabologyco-maker/claudia-bot/blob/6071aed58a8e00d6a4e496cb9ef5012be188a026/slop/sync/avsync.py) compares a generated soundtrack with its conditioning reference. It can estimate audio lag and divergence; it does not inspect mouths or identify the visible singer. Its transfer to visual singing quality depends on a model-behavior assumption. The [edit selector](https://github.com/anabologyco-maker/claudia-bot/blob/6071aed58a8e00d6a4e496cb9ef5012be188a026/slop/edit/edl.py) can retain otherwise rejected material as a last fallback. These are static source findings, not an executed integration or a review of that toolkit's finished films. Borrow useful architecture with attribution, and preserve a separate final acceptance gate.

## Character and style package

Choose a canonical face sheet and useful close/front/three-quarter/profile views. Keep identity traits separate from allowed wardrobe variation. A whole contact sheet helps comparison but may confuse a generator; test a clean crop or individually generated angle if needed. Inspect the crop before upload and meet the host's current minimum dimensions. Never stretch a face to fill a slot.

Character reference = who. Scene still = composition, light, clothing and setting. Performance reference = how movement and framing behave. Label these roles explicitly. Where supported, create actual provider character objects and verify that those objects, not literal placeholder strings, are attached. Names alone do not carry a face.

Write a short visual bible: palette, practical light sources, lens/framing range, texture, locations, cast, recurring props, and variations allowed. For the Smart Home Strike example, magenta/cyan practical lighting, chrome appliances, vigorous choreography and handheld multi-angle performance mattered more than a generic 'cinematic' label. These are that example's choices, not defaults for a ballad or animation.

## Design a proof section

Choose a representative difficult phrase and a contrasting narrative/comic beat. Generate a bounded number of candidates within the authorized budget. Judge source-scale faces, motion, singing, usable timing and coverage before committing a large batch. A useful pilot can expose whether repair is cheaper or more destructive than replacing the shot.

Coverage can include a wide with genuine body travel, a face-readable medium, a short lyric close-up, a reaction and an appliance/prop insert. Motivate angle and zoom changes. Deliberate handheld movement can add energy, but smear, random cuts and repeated whip pans can conceal rather than solve a bad performance.

## Prompt scaffold

Compile this scaffold to the host's actual limits. Use just the instructions the shot needs.

```text
[ACTUALLY ATTACHED CHARACTER REFERENCES]
[Adult character identity, current wardrobe, screen position]
in [approved scene and practical lighting].

[Singer] visibly sings/raps [short exact authorized lyric phrase]
beginning around [clip-relative onset], followed by [phrase B/onset].
[Other performer] [specific non-singing or response behavior].
Keep the singing mouth readable during [important interval].

Immediate real-time action: [weight transfer / travel / footwork],
[second gesture or interaction], [expression].
[Shot one framing and purposeful camera move].
Cut at [phrase/beat] to [different framing/angle/action].
[Ending reaction or movement with editorial handles].
[Photographic texture / film grain / practical effects if wanted].
[Specific exclusions: e.g. no slow-motion posing or idle opening].
```

Keep provider settings, costs, source intervals and review criteria in the shot record rather than consuming creative prompt space. Word onsets and requested phrase ends must be marked measured or estimated. Where a route truly accepts song audio, distinguish vocal-only conditioning for singing from full-mix conditioning for dance. A stem can contain leakage; first check quality and alignment. Generated audio enabled is not the same capability as accepting the supplied song.

## Singing and synchronization

The inexpensive method tested here was exact short lyric prompting followed by source-span selection, timing adjustment and editorial coverage. It produced useful approximate singing candidates. It did not guarantee phoneme-accurate sync. Judge consonant closures, open vowels, phrase boundaries and visible singer ownership at normal speed.

Measure the generated phrase if it has diagnostic audio, but keep that track separate from the locked release. An audio lag measurement does not prove mouths match either track. Don't hide every vocal line behind backs, hands or appliances merely to improve a sync score.

Use restrained slips/retimes and motivated cutaways when the result remains physically plausible. Heavy speed-up can spoil lips, footwork, camera motion and hair; replacing the take may be better. A dedicated lip-sync pass or video-to-video repair is an optional pilot, not a promised rescue.

## Record enough to resume

For a generation: shot ID; role; master interval; provider/host/model/date; duration/resolution/aspect/FPS; actual character and frame references; exact accepted prompt; audio and multi-shot mode; quote and authorized attempt count; attempt/result ID; download path/hash; technical result; accepted source spans; defects; next action.

For creative decisions: keep the rejected alternative and reason when it affects later choices, but do not build a transcript archive. No private conversations belong in a reusable example bundle. Batch accepted changes before full-film renders; short comparison excerpts are often sufficient between revisions.
