# Stagecraft

**A reusable music-video production workflow for Codex, with local tools and a complete learning example.**

Stagecraft takes an existing song from concept and character references through generated performances, shot review, source-preserving editing, native-editor validation and delivery. It was distilled from the production of *Smart Home Strike*, a chaotic duet by Coda and Lilitari in a kitchen full of rebellious appliances.

This is a working skill and inspectable Python toolkit. It does not automatically operate every vendor, guarantee character fidelity or lip synchronization, or include access to anyone's accounts. The practical method is portable; provider availability, capabilities and costs must be checked in the user's own environment.

- [Portfolio: process, example and video](https://richard-pemberton-research.darkahn.chatgpt.site/projects/stagecraft/index.html)
- [GitLab source and releases — primary](https://gitlab.com/codalilitari/stagecraft)
- [Watch Smart Home Strike in 1080p](https://drive.google.com/file/d/1F6DU97Nads5uePAZ32XJo4V0rXuurzis/view)
- [Machine-readable project writeup](stagecraft.json)
- [Release manifest](release.json)

## Install

Download the versioned archive linked in `release.json`, compare its byte count and SHA-256, then inspect its contents. Extract it into a new staging directory. Copy only the `music-video-production` folder into your Codex skills directory: normally `$CODEX_HOME/skills`, or `~/.codex/skills` when `CODEX_HOME` is not set. On Windows the usual location is `%USERPROFILE%\.codex\skills`.

The source repository contains the same folder at `skill/music-video-production`. Keep an existing installation until you have compared any local changes; do not blindly overwrite it. Start a new Codex task if the newly installed skill has not appeared in the current session's skill list.

Use it explicitly:

> Use $music-video-production to plan a music video for this recording. These are my canonical characters, intended visual style, available tools and budget. Inspect the current project first, then propose and validate a representative performance section before generating the whole video.

For longer work, explicitly authorize a Goal if you want one. Stagecraft teaches concrete deliverables, budgets, checkpoints and stop conditions; it does not silently create Goals or scheduled work.

## What is included

- A concise `SKILL.md`, seven detailed production references, and project-state/conform templates.
- A code-directed production guide: deterministic frame timing, selective local tooling, audio/caption handling, resource-aware rendering and final-file QA. These are documented integration options; the package does not yet supply a browser, React or Blender renderer.
- `sample_video.py`: timestamp-aware frame sampling, an HTML review sheet, source hashes and optional full decode checks. Start with one-second samples; inspect dense passages and actual audiovisual playback for motion and sync.
- `conform_audit.py`: exact rational-rate timing, source bounds, coverage, cumulative frame rounding, optional hash verification and explicit unperformed-review states. It does not import a native timeline or inspect image quality.
- `check_updates.py`: a read-only release check with GitLab first and the portfolio as fallback. It does not download or install code.
- The authorized *Smart Home Strike* master WAV, supplied lyrics, provisional cues, canonical Coda/Lilitari sheets, two scene references and a SHA-256 asset manifest.
- Dated findings for Flow Omni, Kling through Adobe and direct Kling, Grok, still generation, local face repair, H3/ComfyUI, Topaz, transcription, native Adobe tooling and CapCut workflows. Completed renders, experiments, setup-only routes and researched alternatives are distinguished.
- Optional Review Hub/external-reviewer discovery and installation guidance, including actual media attachments and independent checking of reviewer advice.

Private conversations, credentials, local account configuration and private conversation references are not included. The worked-example images are generation references; the video method favors actual moving performances and intentional narrative shots.

## Local tools

Python 3.11+ is required for the helpers. The sampler also needs an existing FFmpeg/ffprobe installation. Supply exact executable paths if they are not on PATH. No Python package installation is needed for these three helpers.

```text
python -B scripts/sample_video.py INPUT.mp4 --out NEW_REVIEW_DIRECTORY --interval 1 --decode
python -B scripts/conform_audit.py PROJECT_MANIFEST.json --out NEW_RECEIPT.json --verify-hashes
python -B scripts/check_updates.py
```

Run these from the installed `music-video-production` directory, or pass the full script path. Read [the harness guide](skill/music-video-production/references/harness.md) for schemas, failure behavior, dense sampling and a synthetic practice fixture. The bundled conform template deliberately names nonexistent media: metadata checks can pass while file verification correctly fails.

## Updates and optional reviewers

The primary feed is [GitLab release.json](https://gitlab.com/codalilitari/stagecraft/-/raw/main/release.json); the [portfolio feed](https://richard-pemberton-research.darkahn.chatgpt.site/projects/stagecraft/release.json) is a fallback. GitHub is an optional mirror and is not required for installation, release discovery or Review Hub acquisition. A version in a feed is only a claim until the downloaded archive's hash and contents are checked. The feed is not a cryptographic signature or permission to update.

[Review Hub](https://gitlab.com/codalilitari/review-hub) is optional and separately maintained. See [tooling and review](skill/music-video-production/references/tooling-and-review.md) for the verified GitLab route, portfolio fallback, provider requirements and configuration boundaries. Do not copy someone else's private bridge configuration or infer API credits from a web subscription.

## Read the production lessons

1. [Plan, map the song and direct performances](skill/music-video-production/references/production.md)
2. [Choose models and assess face repair](skill/music-video-production/references/models-and-repair.md)
3. [Edit, conform and verify native delivery](skill/music-video-production/references/editing-and-delivery.md)
4. [Discover tools and collaborate with reviewers](skill/music-video-production/references/tooling-and-review.md)
5. [Use the offline harness](skill/music-video-production/references/harness.md)
6. [Study Smart Home Strike](skill/music-video-production/references/smart-home-strike.md)
7. [Build repeatable production stages with code](skill/music-video-production/references/code-directed-production.md)

The source branch includes documentation additions dated 2026-11-01. The latest versioned release remains 1.0.0; `release.json`, `package-files.json` and the existing versioned ZIP describe that historical release. Install from the current source branch to include these additions. See the Unreleased changelog and current validation addendum.

The model observations describe this production in October 2026. They are not universal rankings. Google Flow Omni produced useful material but drifted from the canonical faces and often missed the required performance energy. Later Kling routes supplied stronger singing/dance coverage. Local repair experiments were measured and retained as lessons; an executed repair was not automatically accepted into the final cut.

## Authorship and reuse

Project direction and example materials: Andrei, with Lilitari/Lily. Workflow synthesis, implementation and verification: Coda in Codex. Collaborator recommendations were checked against artifacts rather than treated as authority. See [NOTICE.md](NOTICE.md) for the distinct terms for code, documentation and example media.

This release is a starting production method with tested local helpers, not a promise that a different account or model will reproduce the example. See [VALIDATION.md](VALIDATION.md) for the actual checks and their limits.
