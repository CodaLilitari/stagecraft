# Smart Home Strike: worked example

> **Red's fork note:** this case study is Coda and Lily's production, kept verbatim as a learning example. Its media (master WAV, character sheets, scene stills) is *not* bundled in Red's fork; the links point to the upstream Stagecraft repository. Coda and Lily's likenesses and the song are not for reuse in other productions.

This is an authorized learning example from a completed production-and-revision cycle, distilled on 2026-10-12. It demonstrates choices and their consequences; it is not a required style, cast, prompt or model stack for other songs. No private conversations are included.

## The materials

The [example folder](https://gitlab.com/codalilitari/stagecraft/-/tree/main/skill/music-video-production/assets/smart-home-strike) includes a byte-verified [191-second stereo master](https://gitlab.com/codalilitari/stagecraft/-/blob/main/skill/music-video-production/assets/smart-home-strike/smart-home-strike-master.wav), [lyrics](https://gitlab.com/codalilitari/stagecraft/-/blob/main/skill/music-video-production/assets/smart-home-strike/lyrics.txt), two canonical character sheets, two scene/performance stills, a [manifest with SHA-256 hashes](https://gitlab.com/codalilitari/stagecraft/-/blob/main/skill/music-video-production/assets/smart-home-strike/manifest.json), and explicitly [provisional timing landmarks](https://gitlab.com/codalilitari/stagecraft/-/blob/main/skill/music-video-production/assets/smart-home-strike/provisional-cues.json). The [public song release](https://www.youtube.com/watch?v=OuFaN3ET3eA) is a reference; it is not a substitute for checking which master an edit actually uses.

- **Coda:** adult woman; short black bob with muted violet ends, gray-violet eyes, freckles, dark lips and an eyebrow piercing. The canonical sheet separates facial identity from a black asymmetric outfit with blue-violet accents. Her performance role is smoky contralto, dry clipped rap and deadpan reactions.
- **Lilitari / Lily:** adult woman; long black hair with purple strands, vivid violet eyes, freckles, dark lips and septum jewelry. Lace, straps, chains and a crescent accessory establish the reference wardrobe. Her performance role is bright soprano/shriek-rap, exaggerated mischief and energetic gestures.

Use the actual [Coda sheet](https://gitlab.com/codalilitari/stagecraft/-/blob/main/skill/music-video-production/assets/smart-home-strike/coda-canonical.jpg) and [Lilitari sheet](https://gitlab.com/codalilitari/stagecraft/-/blob/main/skill/music-video-production/assets/smart-home-strike/lilitari-canonical.jpg) to judge faces; the descriptions alone are insufficient. Wardrobe can change intentionally. Small piercing differences were a possible finishing repair, not a reason to approve a fundamentally different face.

The [wide scene reference](https://gitlab.com/codalilitari/stagecraft/-/blob/main/skill/music-video-production/assets/smart-home-strike/wide-performance-reference.png) and [duo motion reference](https://gitlab.com/codalilitari/stagecraft/-/blob/main/skill/music-video-production/assets/smart-home-strike/duo-motion-reference.png) establish magenta/violet practical light, cyan accents, reflective kitchen surfaces, a lived-in party mess and comic appliances with illuminated faces. In this brief, the stills were generation references: the final picture was to contain motion footage rather than displayed still images.

## Translate the song into a film

The supplied music direction called for 168 BPM, 4/4 and two distinct adult female voices. Treat that as composition intent until measured against the recording. Comic story: a party becomes a smart-appliance revolt, with the performers alternately provoking and reacting to it. The sequence needs performance, escalating appliance jokes and reaction pauses, not only dancing or only literal illustrations of nouns.

Useful scene functions included the sofa party, toaster worship, the screaming kettle, a refrigerator joining a union, call-and-response about who started the strike, the collective chant, and the final dental/solidarity joke. The punchline depends on timing and a readable reaction. Successful comedy remained useful when weak performance footage was replaced.

One reusable prompt pattern, adapted from the production approach:

> Use the two attached character Elements and the attached wide kitchen reference. Adult Coda is camera right; adult Lilitari is camera left. Preserve each canonical face and hair silhouette. They perform an energetic rave-rap in a chaotic kitchen among comically rebellious appliances. Coda delivers the quoted short lyric while Lily reacts; switch ownership only at the specified phrase. Independent high-budget music-video photography, tactile practical light, magenta and cyan spill, natural skin texture and restrained film grain. Real weight shifts, quick bootwork and sharp gestures, not slow swaying. Auto multi-shot: a low moving two-shot, a readable singer closeup, then an appliance reaction. Handheld movement with intentional reframing and one quick push-in; retain useful handles and avoid covering the mouth at the lyric onset.

Replace words such as “attached” with actual provider attachment objects. Specify the exact lyric excerpt and clip-relative timing for each attempt; do not paste the entire song into every short clip. This pattern is an editorial intention, not proof that the generator obeyed it. Repeated unbound character tokens, contradictory camera commands and a long choreography wish list add ambiguity.

## Decisions that changed the result

**Test identity independently of image quality.** Google Flow Omni could maintain two distinguishable faces while both departed from canon. Later comparison made that failure clear. The project moved toward Kling performance takes with actual Elements, stronger lighting, body energy and Auto multi-shot, while preserving useful comic concepts. See the [dated model evidence](models-and-repair.md) for the distinction between Google Omni, Adobe Kling and direct Kling.

**A mouth moving is not necessarily this lyric.** Generated singing produced phrase order, ownership and onset differences. Short phrase recuts and restrained retiming were more useful than assuming one speed change could synchronize a whole take. Diagnostic ASR helped find candidates but did not establish what a visible mouth said. The original song remained the soundtrack.

**Repair has a performance cost.** FaceFusion/hyperswap and LivePortrait comparisons restored some identity/expression features while damaging freckles, gaze or smirk. A deterministic original-eye composite tested a narrower correction. Those experiments produced evidence, not an accepted universal face-repair solution. H3 was installed and graph-validated but stopped before sampling; Topaz Precise was prepared without a completed render. Do not promote either into a successful result.

**Use originals for the finish.** Preserve licensed watermark-free 1080p sources and disclose any inherited 720p material. A tiny preview encode was inappropriate as the quality basis for later assembly. Upscaling can fill a canvas; it does not restore missing identity or source detail.

**Prove the native timeline.** The R4 review movie is 1920×1080, 30 fps, 5,734 frames, about 191.133 seconds. The editable Premiere delivery contains 88 motion cuts and the selected stereo master. An initial XML import reported online media but selected wrong source frames. Corrected native timing was checked with actual exported frames, audio and save/reopen evidence. The movie and native project were separate renders/states, not claimed pixel-identical.

The production records distinguish technical and sampled checks from continuous audiovisual inspection and exact lip synchronization; the latter remain separately qualified. This example teaches how to preserve those distinctions while making a watchable, expressive film.

## Try the method on a different song

Bring a chosen recording, authorized cast references, a creative brief and a spending boundary. Make a song map, select one hard representative passage, and judge a small pilot against identity, singing, movement, light and editability before scaling up. Keep only the tooling and record-keeping that help the next creative decision. The [production guide](production.md), [editing guide](editing-and-delivery.md), [tooling guide](tooling-and-review.md) and [local harness](harness.md) contain the transferable steps.
