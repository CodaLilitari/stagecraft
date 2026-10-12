# Tooling and multimodal collaboration

Start with what the receiving installation actually has. This skill is useful with a video editor, FFmpeg/ffprobe and ordinary file tools; it does not require every service below. Plugins, MCP servers, CLIs, browser automation and native application extensions are different integration layers. An installed plugin is not proof of account access, an available feature, current entitlement, or successful host control.

## Discover, then add only what is needed

For a dry run that prohibits account access, inspect only available tool descriptions and local documentation. Leave model availability, entitlement, usage and quoted cost explicitly unverified; an account-backed `routes`, usage or catalog call is not necessary to draft a plan. Run only authorized synthetic/local checks.

1. Inspect the current skill/tool catalog and the project's documented tools. Discover deferred tools by their descriptions when supported. Use app metadata and exact project paths, not a search through the user's computer.
2. For the next concrete operation, identify a supported route and read its installed skill/documentation. Check the actual tool schema, host version and model/capability state. A name remembered from another installation is only a search hint.
3. If a missing skill/plugin would help, use the environment's plugin-management or skill-installer workflow, or its official documented setup route. Obtain it from a verified maintainer/user-supplied source; inspect its executable, dependencies, permissions and registration before use. Do not invent a download URL, clone a private installation into a public package, or change billing/security settings under a general filmmaking request.
4. Prefer an existing working integration over building a bridge. If a small bridge is necessary and authorized, isolate it in the project, use least necessary permissions, document how to stop/remove it, and first test on disposable synthetic media. An MCP handshake, advertised ACP capability or a panel saying Loaded proves only that stage.
5. Keep account configuration, API keys, helper pins, conversation IDs and installation paths in local state. Do not include them in deliverables or prompt examples. Reconnect clients after a deliberate server update when required; don't assume an old connection exposes new fields.

## Capability map from the worked production

The execution evidence below is historical (October 2026). Inspect current official documentation and the local catalog before invoking any route.

| Integration | Useful role | What to verify / fallback |
|---|---|---|
| Built-in image generation and optional `imagegen` skill | Canonical stills, scene/lighting anchors, reference variations | Inspect the exact input images, use the tool's supported reference mechanism, and preserve identity. A still is not a performed shot. A chat model label does not identify the image backend. |
| `google-flow-video` skill + supported browser UI | Flow project, Characters/Ingredients/Frames, generation and downloads | Actual character objects must be attached to the prompt. Confirm settings after mode changes, reconcile pending jobs, and check returned audio even when silent generation was requested. No hidden endpoints or credential extraction. |
| Direct Kling browser route | Structured Elements, scene references, Auto multi-shot and licensed original downloads | Verify the displayed model and controls in this host. Adobe's Kling wrapper and direct Kling had different account/control states; access to one did not establish access to the other. |
| Adobe Creative Cloud connector/plugin | Discover documented cloud image/video and asset operations | Read the actual tool descriptions. This connector is not automatically a Premiere or After Effects desktop-control server. Firefly web was a separate generation route. |
| Premiere Pro UXP extension / verified desktop bridge | Read and manipulate actual native sequences, source objects, timing and saved projects | The project progressed from a read-only diagnostic to native timeline validation. Use supported current APIs, inspect returned errors, and prove frame/audio output and save/reopen. The generic XMEML exporter is deliberately not bundled as a universal native adapter. |
| After Effects JSX + `aerender` | Compositions, overlays and deterministic renders | A disposable one-second smoke render succeeded. The actual output template produced MP4 despite an AVI output filename; inspect real output filename and codec. This test did not establish that AE rendered the final music video. |
| Adobe Media Encoder | Optional export queue | Installation was verified; a live queue was not established by that setup check. Do not claim every installed Adobe tool was used in production. |
| CapCut plugin skills | Media upload, generation, draft editing and collaborative cloud drafts | Discover `capcut-upload`, `generate-media`, `video-editing`, `capcut-stdraft-builder`, `web-collaborative-editing`, and `mcp-auth` as needed. Use the installed schemas and exact billing-confirmation capabilities. A cloud STDraft, a desktop project and an exported video are separate artifacts. Template search is optional inspiration, not a prerequisite. |
| Review Hub MCP/CLI + `external-reviewers` skill | Coordinate bounded reviews, stage media, preserve replies and dispositions | Optional; detailed procedure below. A prepared handoff has not uploaded anything. Use a directly supported provider app when that is the appropriate media route. |
| REAPER / TwelveTake MCP, existing DAW or Suno stems | Optional vocal isolation, alignment and diagnostic audio | Inspect the actual exposed tools and their errors. Stem availability does not guarantee separation quality. Inspect bleed, timing and artifacts; a stem is optional for phrase-based generation and must not silently replace the locked song. Prior local DAW work is separate from final-video rendering evidence. |
| ComfyUI local graph/API | Optional reference-conditioned video experiments | Verify graph node versions, exact weights, memory headroom and a bounded executed test. H3 graph validation did not produce video in this project. A CUDA device being listed is not proof every node uses it. |
| FaceFusion local CLI | Bounded face selection, replacement and expression comparisons | Pin tested versions/options, prove target selection through the whole span, retain originals and independently inspect performance. The tested repair was not accepted as a wholesale production replacement. |
| Topaz local application / documented CLI | Optional enhancement after identity/performance decisions | Starlight Precise was installed and device enumeration worked; no successful Precise render was established. Do not copy a generic `tvai_up` command and claim it is a verified Precise configuration. |
| FFmpeg, ffprobe, Python | Probe, frame sampling, conform auditing, offline assembly and delivery checks | Pass explicit executable paths when PATH is unavailable. Probe actual outputs and decoded timestamps. The bundled helpers perform local QA, not generation or native-editor automation. |

For current setup details, consult [Adobe's Premiere UXP documentation](https://developer.adobe.com/premiere-pro/uxp/), [ComfyUI's official repository](https://github.com/Comfy-Org/ComfyUI), and [FFmpeg's documentation](https://ffmpeg.org/ffmpeg.html). These were reachable on 2026-10-12. The skill's observations describe this production; they are not guarantees about later product versions.

## Optional Review Hub and external-reviewers

Review Hub is a coordinator, not a requirement to finish a video. If the receiving Codex already has `external-reviewers`, read its SKILL.md and relevant provider guide. If the Hub is exposed, inspect its current `routes` and `capabilities`, configured identity, actual provider/model/mode and current usage. Do not overwrite an established shared state directory or create a second real-job store just because the working directory changed.

The recorded local Hub v0.6.0 beta exposed twenty tools, with automated route adapters and separate app handoffs. The neutral public [Review Hub distribution on GitLab](https://gitlab.com/codalilitari/review-hub) was anonymously readable on 2026-10-12; its README includes native image transport and interrupted-review completion tracking. Use GitLab or the [portfolio case study](https://richard-pemberton-research.darkahn.chatgpt.site/projects/review-hub/index.html) as the primary discovery route. GitHub is an optional mirror whose anonymous access returned 404 in the same check. Do not depend on GitHub for installation or updates, and do not substitute a private repository. No Hub code, accounts, identity seeds, reviewer responses or conversations are bundled here.

When acquisition is authorized, inspect the distributable's README, license, entry point and configuration example; install in an isolated environment, run its tests, register its documented MCP command using the receiving user's own state/configuration, and verify tool discovery. Never copy the originating user's credentials or helper configuration. If acquisition is unavailable, use a supported direct provider route or a local independent agent and record that choice.

An authorized optional acquisition can start with `git clone https://gitlab.com/codalilitari/review-hub.git` into a new dedicated directory. Read the downloaded README before installation and use a pinned commit for reproducibility. Its documented Windows setup uses Python 3.11+, a virtual environment, `requirements.lock`, and an editable install. The entry points are `coda-review` and `coda-review-mcp`; check `--help` before registration. Installing the coordinator does not install, authenticate or fund provider clients. This skill does not run that setup automatically.

### A useful review packet

Give the reviewer a concrete decision: for example, whether a candidate preserves the canonical face through a head turn, or whether a particular sung phrase visibly lands late. Include only necessary authorized materials:

- A short video with sound when relevant, its source/timeline time range, and the actual reference portraits.
- The relevant lyric excerpt and known timing uncertainty, without presenting ASR as ground truth.
- The specific questions and required timecoded evidence; ask for uncertainty rather than a universal approval.
- The requested return form: findings with locations, suggested fixes, and any uninspected part.

Use actual images, audio and video when supported. A text packet can accompany media; it must not become a text-only restriction. Keep full-quality originals locally and label any review derivative with its exact scale, crop, duration and audio changes. If a hub file-size guard rejects a file, that is a hub rejection, not proof the provider rejects it. The production used a direct app handoff for a roughly 307 MB MP4 after a local 20 MiB guard blocked staging. Current provider limits must be observed afresh.

Resolve an exact absolute attachment allowlist before opening a picker. Prefer a supported direct chooser API; otherwise use exact path entry without inspecting folders, thumbnails or recents. Verify every attachment chip and sent message. Do not silently omit a file that the adapter cannot transport, convert it to text and claim audiovisual review, or upload to a different service without scope coverage.

Use a dedicated saved project conversation when the route supports it. Identify agent authorship clearly (for this Coda workflow, prefix `Coda:`; another interlocutor should identify itself), acknowledge useful contributions, and keep the actual sent/replied/pending state. An answer in progress, a provider limit, ambiguous delivery and a complete response are different states. Reopen/verify history when needed for continuation; do not duplicate a pending request.

Current subscription access must cover the chosen route and operation. A signed-in app does not establish API/CLI entitlement or included quota. Respect the project's spending boundary and skip unknown/extra-charge routes. Hub usage observations are coordinator records, not a billing cap. Never redeem resets, enable overages or change account settings to make a review work without specific authorization.

### Act on evidence, not reviewer confidence

Keep four fields separate: reviewer finding, coordinator's independent check, disposition, and authority to execute. In the worked production, two confident timing claims were contradicted by actual frame boundaries and withdrawn. A returned review is useful input; it is not native-editor validation, consensus, or permission to alter the production. Record accepted, rejected and unresolved findings without exporting the private conversation.
