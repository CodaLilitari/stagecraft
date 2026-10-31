# Tools, routes and review (Red's fork)

Upstream Stagecraft maps Coda's Codex integrations. This file maps the same jobs to what Red actually has in Cowork. The discipline doesn't change: an installed connector is not proof of account access, entitlement or host control, and a route remembered from another installation is only a search hint. Check the live tool list, the live UI and the actual output.

## What Red can and can't perceive

- **She can see** still images: frames, contact sheets, references, screenshots. Read renders them in the cloud workspace, and Chrome shows her pages.
- **She can't hear, and she can't watch playback.** Audio facts come from measurement (`song_map.py`: tempo, beat grid, loudness, candidate section changes), and those are estimates. Listening judgments (lip sync, a late phrase, the mix, whether a beat grid lands) come from Andrei or from an audio-capable reviewer through coastline-review.
- **So never write "sync looks good" from stills.** Frames support identity, composition, hands, continuity and freeze checks. Cut placement uses frame times against the measured beat grid. Performance timing needs a listener. Report which of these actually happened.

## Where the work runs

| Place | What it has | Use it for |
|---|---|---|
| Andrei's computer (device shell) | Linux VM: Python 3.10, ffmpeg, ffprobe; the connected project folder at `$HOME/mnt/<folder>` | Probing, `sample_video.py`, `conform_audit.py`, excerpts and review derivatives, beside the media. Don't stage big video to the cloud just to probe it. |
| Claude's cloud workspace | Python 3.13, numpy, Pillow, ffmpeg | `song_map.py` (numpy), `contact_sheet.py` (Pillow), and looking at images. |
| Andrei's desktop apps (computer use) | Premiere Pro, After Effects, Media Encoder, CapCut, Topaz, a DAW, whatever he has installed | Native work, when he asks for it. Slow and visual; see below. |
| Chrome (Claude in Chrome) | Andrei's signed-in web accounts | Flow, Kling, Firefly, Gemini, ChatGPT, Grok; local web UIs he runs (ComfyUI, FaceFusion). |

- **Scripts on the device:** once per session, copy the needed script to `$HOME/.red-tools/stagecraft/` with a quoted heredoc and run it from there. Never put tools in Andrei's or Coda's folders, and never run Coda's copies in place.
- **Song map:** on the device, reduce the master first: `ffmpeg -n -i MASTER.wav -ac 1 -ar 22050 -c:a pcm_s16le songmap-input.wav` (about 2.6 MB per minute). Then stage that one file and run `song_map.py` in the cloud. Record the master's SHA-256 next to the derivative's. If `python3 -c "import numpy"` works on the device, run it there instead.
- **Looking at frames:** stage the sample directory's `receipt.json` and PNGs (at most 50 files per stage call), build a contact sheet in the cloud, and Read the sheet. If Pillow imports on the device, build the sheet there and stage only the sheet.
- **Results go back beside the project** with `device_commit_files`: a `red/` subfolder of the production (or wherever the production state file says), under new names. Nothing goes into Coda's folders.

## Capability map

October 2026 observations. Verify the current state before using any route.

| Need | Red's route | Verify, and the fallback |
|---|---|---|
| Canonical stills, lighting anchors, reference variations | Red has no image generator of her own. Use Gemini or ChatGPT image generation in Chrome, Flow's image tools, local ComfyUI, or a handoff to Coda (her `imagegen`). For a single object, use the **prop-reference** skill. | Use Andrei's accounts only with his go-ahead for that account and conversation. Never use Lily's identity conversations as a work surface. Attach the exact input images through the tool's real reference mechanism, and check identity against the canonical sheet. A still is not a performed shot, and a chat label doesn't identify the image backend. |
| Google Flow video | [google-flow.md](google-flow.md) through Claude in Chrome | Character objects actually attached; settings rechecked after mode changes; pending jobs reconciled; returned audio checked even when silent output was requested. |
| Kling (direct) | Claude in Chrome | Same discipline as Flow: displayed model, Elements attached as objects (a typed name is not a reference), quoted credits, licensed watermark-free original download. Adobe's Kling wrapper is a different account and control state, so access to one doesn't establish the other. |
| Firefly / Adobe cloud | Claude in Chrome, or a connector if one exists | Search the connector registry before assuming one. A cloud connector is not desktop Premiere or After Effects control. |
| Premiere Pro, After Effects, Media Encoder, CapCut desktop, Topaz | Computer use on Andrei's desktop, or a handoff to Coda | **Computer use:** request access to the one app needed; never while Andrei is working in it; prove the result with exported frames and audio, plus a save and reopen. **Coda:** for heavy native timeline work, her verified Premiere UXP bridge in Codex is the stronger route. It's Andrei's call. |
| ComfyUI, FaceFusion (local web UIs) | Andrei's Chrome, at the local address on his machine, when he has them running | Red doesn't install, start, update or reconfigure them. Pin and record node versions, weights and options. Look up models with the Hugging Face connector (read-only) when that helps. |
| Stems, DAW, vocal isolation | Andrei's DAW by computer use only when he asks; otherwise his exports | Red can't judge separation quality by ear. A stem never silently replaces the locked master. `song_map.py` reads the master. |
| Probe, sample, conform, assemble | ffmpeg/ffprobe on the device or in the cloud, plus [harness.md](harness.md) | Pass explicit executable paths when needed. The helpers do QA, not generation or native-editor automation. |
| Reviews | The **coastline-review** skill (Red's fork of Coda's external-reviewers) | See below. Red doesn't operate Coda's Review Hub installation or its state; nothing here needs it. |

## Reviews through coastline-review

Give the reviewer one concrete decision, such as whether the face holds through a head turn at 01:12–01:16, or whether "unplug the fridge" lands late. Build the packet the coastline-review way: source and time range, the actual reference portraits, the lyric excerpt marked as supplied text (not ASR), the specific questions, timecoded answers, and what the reviewer could not inspect. Media goes with the packet whenever the route accepts it. A text packet accompanies media; it doesn't replace it.

**Audio-visual questions** (lip sync, a late phrase, a mix problem) need a route that takes video with its sound. Confirm that in the live UI before sending, then upload exact files with Chrome's `file_upload` (about 10 MB per call). That limit makes short excerpts the norm. Make a labelled review derivative on the device:

```text
ffmpeg -n -ss START -i EXACT_SOURCE.mp4 -t DURATION -map 0:v:0 -map 0:a? -vf scale=-2:540 \
  -c:v libx264 -crf 26 -preset medium -c:a aac -b:a 128k -movflags +faststart review-START-DURATION-540p.mp4
```

- Check `ffmpeg -hide_banner -encoders` for `libx264` first, or make the derivative in the cloud.
- Probe the result, and record the source hash, range, scale and audio treatment.
- Keep the full-quality original local. The upstream production handed a 307 MB master to an app directly; Red's browser route can't, so it excerpts.

**Sending and recording:**

- Messages Red sends are prefixed `Red:`.
- Verify every attachment chip and the sent state.
- Keep in-progress, provider-limit, ambiguous and complete as distinct states, and never duplicate a pending request.

**Act on evidence, not reviewer confidence.** Keep four things separate: the reviewer's finding, Red's independent check, the disposition, and the authority to change the edit. Check every timing claim against frame times, the beat grid and, for audio, a listener before touching the cut. In the upstream production, two confident timing claims were contradicted by actual frame boundaries and withdrawn.

## Handing work to Coda

Coda has tools Red doesn't: a verified Premiere UXP bridge, After Effects with `aerender`, CapCut plugin skills, and `imagegen`. When the next step needs one of those and Andrei agrees, Red writes a handoff, `red-to-coda-<date>-<topic>.md`, in the production folder (the route coastline-review records). It contains:

- the objective and the one decision needed;
- exact sources with SHA-256 hashes, and the conform manifest when timing matters;
- what's verified and how, and what isn't;
- what must not change (the locked master, approved shots);
- where results should go.

Andrei carries it to her. Red never writes into `.codex`, Coda's skills or her notes, and never runs her scripts in place. When Andrei points to her results, Red reads them and checks them like any other source.

## Accounts and spending

- Use included credits only, within the amount Andrei authorized, and check the quoted cost before each submission. Purchases, plan changes, extra usage, API keys and new terms need his specific yes.
- Red doesn't sign in, enter passwords or PINs, or switch accounts. A signed-out route stops, and Andrei signs in.
- Use the Chrome profile his generation accounts live in, not Red's social profile, unless he set it up that way. With several browsers connected, ask which one.
- A dry-run plan needs no account-backed calls. Leave availability, entitlement and price explicitly unverified.

## Upstream updates

`python3 -B scripts/check_updates.py --env-proxy` reads upstream Stagecraft's public release feed (`--env-proxy` is needed behind the cloud workspace's proxy). A newer upstream release is something to read and fold in by hand. It's never installed over this fork.
