# Google Flow through Claude in Chrome

Adapted from Coda's `google-flow-video` skill (observations from 7 October 2026), rewritten for Claude's browser tools. Flow changes often, so re-observe every control before trusting a note here. This is a production route through the visible UI. It is not a Gemini or Vertex API integration, and never a reason to use one.

## Scope and spending

- Before generating, settle: the shot or revision wanted, the exact authorized references, the intended output, and **how many credits Andrei has authorized**. Existing authorization counts, so don't ask again for something he already approved within that scope.
- Before each submission, verify in the live UI:
  - the account and project;
  - remaining credits;
  - the selected model, mode, duration, resolution, aspect ratio and output count (**x1** for a single take);
  - the displayed cost.
  Costs are per generation and multiply with output count. Re-check after adding attachments or changing modes, because Flow may switch to a compatible model on its own.
- Use included Flow credits only, within the authorized amount. Purchases, plan changes, extra usage and API routes need their own authorization. Never substitute an API because browser control was awkward.
- Use the visible UI and Chrome's documented tools. Don't extract credentials, call hidden endpoints, or treat page internals as an API.

## Modes and references

- **Frames:** when an exact first composition, or a first-to-last transition, matters.
- **Ingredients:** when separate character, object or setting references should guide a new shot. Keep identity references distinct from scene references.
- **Characters** (`@CharacterName`): reusable identities. Existing appearance images can be uploaded directly. In the observed run, character drafts needed no image generation and the voice could stay empty. Generating new appearance images is a separate, credit-spending step. The own-likeness `@me` enrolment is unrelated.
- In every character shot, also write the identifying appearance, current wardrobe, screen position and intended action into the prompt. A named reference does not replace scene direction.
- Model support moves. On 7 October 2026, Omni 1.1 Flash supported Ingredients at 4/6/8/10 s, while Veo 3.1 Lite and Fast supported Ingredients at 8 s and Quality did not. Check the current [model features](https://support.google.com/flow/answer/16352836?hl=en), [reference modes](https://support.google.com/flow/answer/16353334) and [credits](https://support.google.com/flow/answer/16526234?hl=en) when they affect the choice.
- When the soundtrack is the fixed song, Flow documents a project-level **Return silent videos** setting. Inspect it before changing it, and still check the downloaded file's audio (below).

## Operating it with Chrome

- Use the tab-context tool, then open Red's own tab on the Flow project. Read with `find` / `read_page`, and take screenshots only when judging composition.
- **Composer and settings:** the observed prompt box was `.base-prompt-box`, and **Settings** opened an overlay with mode (**Video / Frames / Ingredients**), aspect ratio, resolution, duration and output-count radios, plus **Select model family**. Prefer accessible labels; use CSS only to disambiguate.
- **Uploading a start frame or reference:** open the upload control (**Start → Upload media**, or **Characters → Upload**). Locate the hidden file input with `find`, then call Chrome's `file_upload` with the exact absolute path. Files must be in a connected folder or the session outputs, at most about 10 MB per call. Never click the button that opens the native picker, and never browse folders.
- **Rights dialog:** accept **Rights to use this image** only when Andrei's authorization and the known source rights cover that exact file.
- **After upload:** the file is not yet attached. Select the option matching the exact uploaded name (desktop layouts may need **Add to prompt** / **Add ingredients to the prompt box**). Then verify the attached chips: the right files, nothing extra.
- **Narrow layouts:** at about 500 px wide, **Characters** and the desktop navigation were hidden. A temporary 1280×800 viewport exposed them. Restore the previous size afterwards.
- **Character registration:** **Characters → Upload**, upload the exact canonical image, fill **Character name** and **Character personality**, then **Done**.

## Submit, recover, preserve

- Submit **once** per intended attempt. Record a small project-local receipt: reference hashes, prompt, observed settings and quote, submission time, visible result reference, and state. Use one of: prepared, submitted, pending, failed, delivery unknown, downloaded, inspected, accepted.
- **After a timeout:** reopen the same project and reconcile the result tile, its status and the credit balance before any new submission. A missing tile is not proof of failure; Google notes that outputs can appear late. If delivery stays unknown, stop submitting and tell Andrei. A confirmed failure can be retried only within the existing authorization, with the earlier outcome recorded.
- **Download:**
  - Click the generated *thumbnail* (the title opens an info popover) to reach the `edit/<assetID>` route.
  - Use **Download media** (in the narrow layout it sits under **More options**) and choose **720p Original size** or the best licensed original offered.
  - Chrome saves to Andrei's Downloads folder, which is normally not connected. Ask him to move the file into the project folder, or request access to that one folder and check only the **exact expected filename** (`test -f`, `stat`, `sha256sum` on that name). Never list or browse Downloads.
- **Verify the actual file:** type, hash, dimensions, frame rate, duration and full decode (`ffprobe`, `sample_video.py --decode`). Inspect frames covering the requested action and known failure regions. Keep "generated", "technically valid", "visually inspected" and "editorially accepted" separate.
- **Audio in an existing-song edit:** exclude generated clip audio in assembly. In the 7 October run, a verified "silent" toggle still produced an AAC track with substantial signal. Check the streams yourself.
- **Credit observations:** in that run the balance moved from 1,050 to 1,043 after two direct character uploads and one quoted seven-credit generation. That is a dated observation, not a price list.

Flow Agent and Flow Tools are optional in-product helpers that also spend credits. Don't switch their confirmation defaults or share tools as part of an ordinary shot request.
