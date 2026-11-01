# Stagecraft 1.0.0 validation

## Documentation revision — 2026-11-01 (unreleased)

The code-directed production guide and cue-to-performer/review-evidence guidance are source-branch documentation additions. The latest versioned release remains 1.0.0; its archive and release manifest are not rebuilt by this update.

The packaged skill passed the skill-creator metadata validator using Python 3.13.15 and an isolated PyYAML 6.0.3 dependency outside the checkout. Local Markdown destinations and JSON parsing passed. Updated installed references and entrypoint were checked for byte parity with the package. All three helper scripts and their three test files retain the published manifest's byte counts and SHA-256 values in both the package and installed skill.

Primary documentation and pinned public source were reviewed for the added claims. The Claudia toolkit example is static source analysis at commit `6071aed58a8e00d6a4e496cb9ef5012be188a026`, not an installed or executed Stagecraft integration. A delegated video review informed questions, but its observations and timestamps were not independently confirmed against the final master in this update. No private review transcript is bundled.

These checks establish structure, local link targets, parseability and file parity. They do not establish renderer performance, audiovisual quality, current provider entitlement or production acceptance. The unchanged helper suite was not rerun, and no new renderer, paid generation or full-film decode ran. The 59 tests and media evidence below belong to the dated October release checks.

## Published 1.0.0 checks — 2026-10-12

Executed on 2026-10-12 on Windows with Python 3.13.15 and FFmpeg/ffprobe 7.0.2. The helper code targets Python 3.11+, but this release was not executed on every supported Python version or operating system.

| Check | Observed result | What it establishes |
| --- | --- | --- |
| Conform audit tests | 24 passed | Rational timing, cumulative rounding, gaps/overlaps, bounds, hashes, duplicate JSON and path refusal behavior on the exercised fixtures |
| Frame sampler tests | 19 passed | Generated CFR/VFR and low-rate fixtures, frame selection, last-frame inclusion, extraction and refusal/failure handling |
| Update checker tests | 16 passed | Offline/mock networking, schemas, versions, response bounds, redirect handling and no artifact-fetch behavior |
| Skill metadata validator | Passed | Required metadata and skill structure accepted by the local validator |
| Fresh-agent forward exercise | Completed | Another agent used only the portable skill to reason through a new production scenario and actually ran its conform example |
| Synthetic review fixture | 72 decoded frames; 4 PNG samples; full decode passed | A three-second 320×180, 24 fps test-pattern video with PCM audio was processed end to end; source hash unchanged |
| Example media manifest | Every listed byte count and SHA-256 matched | Included copies agree with the selected authorized source bytes |

The fresh-agent exercise independently preserved successful comedy footage while proposing a bounded performance test, distinguished host-specific entitlement from model names, treated contact sheets as incomplete evidence of audiovisual sync, and did not invent permission to spend or create a Goal. Its metadata-only example reported valid while hash verification correctly reported the two deliberately missing media files. Suggestions from that exercise added dense-passage and synthetic-practice instructions.

The additional synthetic run selected decoded frame indices 0, 24, 48 and 71, at observed timestamps 0, 1, 2 and 2.958 seconds. The last sample was visually inspected: a correctly sized test pattern with frame 71 and 2.958 seconds visible. This does not count as listening or continuous audiovisual review.

No new commercial video generation or face-repair run was performed to validate this reusable package. The model/repair outcomes are a dated synthesis of the source production's records. They are not a reproducibility claim across provider revisions, machines or accounts. Unit tests do not validate a native Adobe import, a performer's identity, a final cut's musical timing or a vendor's current capabilities.

## Repeat the local checks

From the installed skill's `scripts` directory:

```text
python -B -m unittest -v test_conform_audit.py test_check_updates.py
python -B test_sample_video.py --ffmpeg EXACT_FFMPEG --ffprobe EXACT_FFPROBE -v
```

Use the synthetic recipe in `references/harness.md` to inspect a real contact sheet. Keep a project's actual media validation separate from these toolkit checks.
