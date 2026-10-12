# From song to useful footage

## Recover and pin the song

Prefer the exact selected master. If starting from an authorized public release, preserve the downloaded container, decoded timing reference, source URL and checksums. Label a decode of lossy audio as such; WAV is a container, not proof of a lossless origin. Do not substitute an older local variant because its title/duration looks similar.

If the master changes, compare several waveform windows throughout the song to estimate offset and drift. State the sign convention. Musical backing can dominate correlations: waveform agreement establishes recording alignment, not exact vocal onset or which singer is speaking. Keep any native subframe placement correction separate from the song file.

Use supplied lyrics as text authority; check against the actual take for omissions/ad-libs. ASR is a timing aid, with uncertain names, screamed words, profanity and duplicated choruses. Do not feed expected lyrics into recognition and then call the matching result independent confirmation. Prompt tempo, DAW tempo and measured tempo are separate fields. A provisional beat grid should remain provisional until checked across the song.

For each cue record: song interval, lyric/section, vocalist, dramatic purpose, timing source, confidence, and any protected pause/punchline. Make action readable before adding cuts or effects.

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
