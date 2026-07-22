---
name: youtube-to-vault
description: "YouTube video into a vault Source note: transcript, claim extraction, verified quotes, Markdown."
---

# YouTube → Vault Source Note

Convert a YouTube video into a Source note for the `agentic development` vault at `/Users/bram/obsidianVault/agentic development`. Format contract: `~/Projects/agentic-development-blueprint.md` §4–§5. Validated flow, 2026-07-23.

## Pipeline

1. Metadata:

```bash
yt-dlp --skip-download --print "title=%(title)s" --print "upload_date=%(upload_date)s" \
  --print "duration=%(duration_string)s" --print "url=%(webpage_url)s" \
  --print "channel=%(channel)s / %(uploader_id)s" "$URL"
```

Channel browse: `yt-dlp --flat-playlist --print "%(id)s | %(title)s" "https://www.youtube.com/@<handle>/videos" --playlist-items 1-20`.

2. Dedup by video id: `grep -rl "<video-id>" "/Users/bram/obsidianVault/agentic development/Sources/"`. Hit → append new claims to the existing note; do not create a second one.

3. Transcript via `$video-transcript-downloader`:

```bash
cd ~/Projects/agent-scripts/skills/video-transcript-downloader && \
  ./scripts/vtd.js transcript --url "$URL" --lang en > /tmp/<slug>.txt
```

4. Claim extraction. Transcript >1500 words and codex-first gate passes → delegate reading to Codex (temp-file prompt, `-o` file):
   - Summary ≤80 words.
   - 5–8 claims relevant to agentic-development *practice*, one line each, with attribution ([speaker's own view] vs [X's advice, relayed] — name who) + one exact verbatim quote (10–30 words, exact substring, no normalized punctuation).
   - 2–3 verbatim excerpts (1–3 sentences).
   Short transcript: read directly, same output shape.

5. Verify before anything enters the vault: every quote and excerpt `grep -qF` against the transcript file. Drop failures; never paraphrase into a quote.

6. Write `Sources/YYYY-MM-DD <handle> <slug>.md` (date = upload date):

```markdown
---
type: source
url: "<canonical watch URL>"
author: "@<handle> (<Name>)"
published: YYYY-MM-DD
captured: <today>
via: "youtube:@<handle>"
topics: ["[[Topic]]", ...]
tags: []
---

## Excerpt
> <verified excerpts>

## Claims
- <claim> [attribution] — → [[topic]]

## Notes
- Video: "<title>", <duration>. <attribution context>.
- All quotes grep-verified verbatim against the transcript (<date>); transcript not retained (excerpts only, per blueprint).
- Ledger candidates for Bram: <which topic ledgers this should update and how>.
```

7. Roles: create the Source note only. Never edit `Topics/` or `Practices/` — put ledger candidates in Notes and the final report.
8. Transcript stays in `/tmp`; never stored in the vault unless Bram explicitly asks (searchable-essential exception).
9. Commit vault (`feat(agentic): ...`) and push (vault repo sync is standing consent).

## Notes

- Vault-aware `obsidian` CLI needs the vault registered + app running; plain filesystem ops always work.
- Attribution is load-bearing when a video relays someone else's advice (reaction videos): mark relayed claims as such.
- Multi-video batches: one Source note per video, dedup each id first.
