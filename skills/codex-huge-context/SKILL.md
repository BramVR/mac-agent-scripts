---
name: codex-huge-context
description: "Codex 1M context: direct OpenAI Responses API route, safe input window, Keychain auth, preflight."
---

# Codex Huge Context

Use when configuring, repairing, or auditing Codex's one-million-token context setup. Intended topology: a direct API inference route that preserves the normal ChatGPT login for Gmail, Calendar, and other connector OAuth:

```text
Codex inference -> Keychain auth helper -> https://api.openai.com/v1/responses
Codex connectors -> normal ChatGPT login in auth.json
```

Not an HTTP proxy. The API stays authoritative for access, actual model limits, and billing.

Never fast mode on this route: no `--enable fast_mode` flag, no `fast_mode` default in config, on fresh or resumed sessions.

## Safe input window

GPT-5.6 Sol exposes a 1,050,000-token total context window and can produce up to 128,000 output tokens. Codex does not set a smaller output budget on normal Responses API turns, so the catalogue must describe the safe input allowance, not the raw total:

```text
1,050,000 total - 128,000 maximum output = 922,000 safe input
```

Same safe input policy for all three direct-provider catalogue models:

- `gpt-5.6-sol`
- `gpt-5.6-terra`
- `gpt-5.6-luna`

Codex applies its normal 95% effective-window reserve to the 922,000-token allowance, so it reports and guards about 875,900 usable tokens. Set automatic compaction to 820,000 total active tokens. That leaves about 55,900 tokens inside Codex's effective guard and 102,000 before the provider's absolute input ceiling for the next prompt, tool schemas and results, instructions, serialization overhead, and compaction itself. This headroom is intentional: Codex 0.144.6 checks compaction at turn boundaries and after completed responses, so a large incoming prompt or tool result can otherwise cross the provider's real limit before compaction runs.

Requests above 272,000 input tokens use the provider's higher long-context pricing. Do not enable this route accidentally for workloads that do not benefit from it.

## Required files

`~/.codex/models-api-1m.json` must contain these values for all three model slugs while preserving the rest of each model entry:

```json
{
  "context_window": 922000,
  "max_context_window": 922000,
  "auto_compact_token_limit": 820000
}
```

Leave `effective_context_window_percent` absent to use Codex's 95% default, or set it explicitly to the integer `95`. Null, floating-point, or other values are invalid.

Root section of `~/.codex/config.toml`:

```toml
model = "gpt-5.6-sol"
model_provider = "openai_api_direct"
model_context_window = 922000
model_auto_compact_token_limit = 820000
model_auto_compact_token_limit_scope = "total"
model_catalog_json = "/Users/bram/.codex/models-api-1m.json"

[model_providers.openai_api_direct]
name = "OpenAI API direct"
base_url = "https://api.openai.com/v1"
wire_api = "responses"
requires_openai_auth = false

[model_providers.openai_api_direct.auth]
command = "/Users/bram/.codex/bin/fetch-openai-inference-key.zsh"
timeout_ms = 5000
refresh_interval_ms = 300000
```

Replace legacy values such as `model_context_window = 1050000` or `model_auto_compact_token_limit = 233000`; leave no duplicate root keys. Keep the scope at `total`: the budget applies to the complete active request, not only content added after a compaction prefix.

Before modifying config, back up both files to date-stamped sibling files. Do not touch unrelated project, plugin, MCP, notification, approval, model-selection, or reasoning settings.

## API credential delivery

The auth command reads a dedicated Keychain delivery copy, never a value in TOML or an environment variable:

```zsh
#!/bin/zsh
set -euo pipefail
exec /usr/bin/security find-generic-password \
  -a Codex \
  -s "Codex OpenAI inference API" \
  -w
```

Use `$one-password` before handling the API key: service-account path, one named tmux session, no vault/item enumeration. If the OpenAI API key item is not already known, stop and ask Bram which item/field to read instead of probing. Store or update only the Keychain copy. Never print it, copy it over SSH, place it in a profile, or write it to a temporary file.

The Keychain item should allow `/usr/bin/security`. A Keychain read normally produces no prompt. A login Keychain locked after reboot, or a command launched via noninteractive SSH, can fail with error 36 (`User interaction is not allowed`). Do not work around that with a plaintext file or a long-lived secret daemon: unlock from the local graphical session, install the item there, then use Codex from that session.

Before the first fresh or resumed Codex launch on a configured machine, run the secret-safe preflight. It validates the direct-provider config, safe input and compaction values, all three catalogue entries, helper executable, and non-empty helper delivery without printing the credential or helper stderr:

```zsh
ruby ~/.codex/skills/codex-huge-context/scripts/preflight.rb
```

Do not mark setup complete or launch Codex when this fails. With `requires_openai_auth = false`, a missing Keychain delivery copy cannot fall back to the normal Codex login: the direct provider can reach `api.openai.com/v1/responses` without a bearer header and surface an opaque HTTP 401 instead. The preflight fails earlier with the bootstrap action needed. An unset `GITHUB_PAT_TOKEN` warning is independent and non-blocking for inference; it explains a concurrent GitHub MCP startup failure and must not be confused with OpenAI API authentication.

## ChatGPT connector login

`requires_openai_auth = false` applies only to the custom inference provider. The root Codex login must stay ChatGPT-authenticated for ChatGPT-connected plugins:

```zsh
codex login status
```

If it reports API-key login and connectors are needed, `codex logout` then `codex login` from the local user session. Do not copy `auth.json` or OAuth tokens between machines.

## Fresh, resumed, and shared-server sessions

`-m gpt-5.6-sol` selects a model, not a provider. Fresh sessions read the root `model_provider`; session metadata then records the chosen provider. Resuming preserves that recorded provider.

Codex TUI sessions can reuse `~/.codex/app-server-control/app-server-control.sock`. A shared app server keeps the configuration it loaded at startup, so changing files on disk does not update sessions attached to an older server. After changing context or authentication config:

1. let active turns finish;
2. restart the Codex desktop app and any shared CLI app server;
3. start a fresh session for final proof;
4. resume old sessions only when preserving their recorded model/provider is intentional.

A same-value CLI override such as `codex -c 'model_provider="openai_api_direct"'` forces an embedded per-invocation app server; useful for diagnosis without changing provider or service tier, not a permanent fix.

## Verification

Run in the intended local user session:

```zsh
ruby ~/.codex/skills/codex-huge-context/scripts/preflight.rb
codex login status
jq -r '.models[] | select(.slug == "gpt-5.6-sol" or .slug == "gpt-5.6-terra" or .slug == "gpt-5.6-luna") | [.slug, .context_window, .max_context_window, .auto_compact_token_limit] | @tsv' ~/.codex/models-api-1m.json
codex exec --skip-git-repo-check 'Reply with exactly: direct-api-safe-context-ok' </dev/null
```

Expect a successful preflight, `922000`, `922000`, and `820000` for every catalogue model, ChatGPT login when connectors are needed, and the exact probe response. A successful direct API probe does not prove connector OAuth; confirm `codex login status` separately.

For TUI proof, send prompt text and Enter as separate terminal actions. Do not treat echoed input as the model's response.

Script tests: `ruby skills/codex-huge-context/scripts/preflight.test.rb`.

## Failure policy

- API response still clamps or rejects a request: record the server response; do not claim a client catalogue override changed server entitlement.
- Context overflow below 820,000 active tokens: preserve the session file and inspect the last token-accounting events before lowering the threshold further.
- Context overflow above 820,000 without compaction: verify the running app-server version and loaded configuration; an old server can retain the previous threshold.
- HTTP 401 `Missing bearer or basic authentication in header`: rerun the preflight and repair Keychain delivery; do not switch providers or fall back to ordinary Codex authentication.
- Keychain error 36 remotely: leave the safe configuration staged and require a local GUI unlock. Never weaken secret storage.
- Root API-key login but connectors are required: complete the ChatGPT login locally; inference can stay on the direct provider.
- Existing `openai_api_direct` provider differs from this contract: inspect before changing; do not append a duplicate TOML table.
