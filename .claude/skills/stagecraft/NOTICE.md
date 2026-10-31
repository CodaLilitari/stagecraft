# Notice: Stagecraft for Red

This skill is a fork of [Stagecraft](https://gitlab.com/codalilitari/stagecraft) 1.0.0, the music-video production skill Coda built with Andrei in Codex. Stagecraft's helper scripts, tests, templates and workflow documentation are MIT-licensed by the Stagecraft contributors; `LICENSE` is upstream's, unchanged. Third-party applications, models and dependencies keep their own terms and aren't redistributed here.

## What changed

- **Unchanged from upstream:** `production.md`, `models-and-repair.md`, `editing-and-delivery.md`, `sample_video.py`, the upstream tests, and both templates.
- **Modified:**
  - `conform_audit.py`: a chunked SHA-256 replaces `hashlib.file_digest`, for Python 3.10.
  - `check_updates.py`: adds an opt-in `--env-proxy` and a fork note.
  - `skill-version.json`: adds a `fork` block.
  - `smart-home-strike.md`: adds a fork note; its media links point upstream.
- **Rewritten for Claude:** `SKILL.md`, `tooling-and-review.md` and `harness.md`. These are Red's versions, still under MIT.
- **New:** `song_map.py`, `contact_sheet.py` and their tests, by Red, under MIT.
- **Adapted:** `google-flow.md` is adapted, with Andrei's permission, from Coda's local `google-flow-video` skill, which isn't part of the public Stagecraft release. The observations in it are Coda's, dated 7 October 2026.

Coda's own installed copies were read, never modified.

## Example materials

The Smart Home Strike song, lyrics, character sheets and scene images are **not** bundled in this fork. Upstream includes them with the project owner's permission as an educational example, outside the software license. Coda's and Lily's likenesses, and the song, belong to that production. They are not for reuse in other videos, and not something to claim as Red's work. Use Andrei's authorized music and characters for new productions.

The package contains no model weights, credentials, private conversations or paid service access.
