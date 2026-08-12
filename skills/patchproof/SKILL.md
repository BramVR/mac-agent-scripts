---
name: patchproof
description: "Upload screenshots and videos as permanent pull-request proof and return PR-ready Markdown."
---

# PatchProof

Upload review evidence through the shared PatchProof service. Prefer this over
committing screenshots or recordings to the product repository.

## Upload Workflow

1. Resolve the exact image or video requested by the user. Inspect it before
   upload; do not publish credentials, private messages, customer data, or other
   unintended content.
2. Give images concise, meaningful alt text describing the proven state. Give
   videos a short link label.
3. Run the bundled helper using its absolute path resolved from this skill:

   ```bash
   <skill-dir>/scripts/upload /absolute/path/to/proof.png --alt "Settings after saving"
   ```

4. Preserve the emitted Markdown exactly and place it on its own line in the PR
   body or comment.
5. Verify the returned asset URL responds successfully before reporting proof
   complete. For video, also verify a range request succeeds when practical.

Run `<skill-dir>/scripts/upload --check` for a read-only configuration check.

## Credential Routing

The helper resolves credentials in this order:

1. Existing `PATCHPROOF_TOKEN` environment variable.
2. macOS Keychain service `patchproof`, account from
   `PATCHPROOF_MACHINE_ID` (default `brams-macbook-pro`).

If neither exists, use the `one-password` skill and its tmux-only workflow for
`op://Codex Automation/PatchProof/machine_token`. Never print the value, place
it in command arguments, commit it, or call `op` outside that workflow.

Use `PATCHPROOF_REPO` to override the default checkout and `PATCHPROOF_URL` to
override the endpoint. The helper currently defaults to the verified
`workers.dev` deployment while `proof.bramvanrompuy.be` DNS remains pending.

## Stuck Upload Recovery

1. Preserve the helper's output and inspect only task-local process metadata.
   Before stopping anything, verify the exact upload PID, command, parent,
   start time, input file, and that the process was started by this task.
2. Gracefully stop only that verified helper process; force-terminate it only
   if the graceful stop fails. Never terminate a browser, 1Password, Keychain,
   Cloudflare, or other shared application process to recover an upload.
3. Run the helper's read-only `--check`. If authentication is missing or stale,
   use `$one-password` for the exact known PatchProof item/field in its single
   tmux session, then make one task-local upload retry.
4. Never move, delete, rewrite, or reset another application's caches,
   databases, configuration, profiles, sessions, keychains, or credential
   state. If the verified helper retry still fails, preserve diagnostics, stop,
   and ask Bram for the exact next action.

## Constraints

- Supported: PNG, JPEG, WebP, GIF, MP4, MOV, WebM.
- Maximum upload: 95 MiB.
- Assets are public and immutable. Uploads receive unique URLs; do not expect
  replacement or deletion semantics.
- Do not create, rotate, revoke, or expose machine tokens unless explicitly
  requested.
- Images emit embedded Markdown; videos emit Markdown links. Use the service's
  emitted form rather than inventing a URL.
- If writing a public GitHub body with `gh`, use a quoted temporary body file
  and `--body-file`; never interpolate the Markdown through a double-quoted
  shell argument.
