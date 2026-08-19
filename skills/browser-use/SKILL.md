---
name: browser-use
description: "Browser automation in cmux or signed-in Chrome; fail-closed relay fallback."
---

# Browser Use

_Source: [steipete/agent-scripts](https://github.com/steipete/agent-scripts), browser-use through `2e320ff0`; combined with Bram's cmux-first routing._

Control a browser without AppleScript or generic GUI scripting. Preserve the user's signed-in state when the task depends on cookies, SSO, device trust, or extensions.

## Route

1. Use `cmux browser` when `cmux browser status` reports `enabled`.
2. Otherwise use the callable Codex `Chrome` or `Chrome [Internal]` plugin when available in the active session. Installed on disk is not enough.
3. Otherwise use the OpenClaw extension-backed Chrome DevTools MCP route through mcporter.
4. Use full-profile direct DevTools attachment only as an explicit last fallback.

Never substitute an isolated browser, Playwright, Puppeteer, AppleScript, `osascript`, generic GUI scripting, or macOS `open` unless the user explicitly asked for a new or isolated browser. Peekaboo is allowed only for Chrome or extension setup, native browser chrome, and visible prompts.

For a rendered-browser bug, prove behavior in the selected real browser. Treat `curl`, source inspection, API checks, and isolated tests as supporting evidence, not live UI proof.

## cmux browser

```bash
cmux browser status
cmux --json browser open https://example.com --focus false
```

Use the returned `surface_ref`:

```bash
cmux browser surface:25 get url
cmux browser surface:25 wait --load-state complete --timeout-ms 15000
cmux browser surface:25 snapshot --interactive
cmux browser surface:25 click e2 --snapshot-after
cmux browser surface:25 fill e1 --text "text" --snapshot-after
cmux browser surface:25 type e1 --text "more text" --snapshot-after
cmux browser surface:25 select e3 --value ship --snapshot-after
cmux browser surface:25 eval 'document.title'
cmux browser surface:25 screenshot --out /tmp/cmux-browser.png
```

Use explicit `--text` and `--value` when a mutating command also has flags. Otherwise trailing flags can be parsed as input text. Run actions sequentially and re-snapshot after DOM changes because older refs can go stale.

Use `cmux identify --json` when caller workspace, window, or surface context matters. If snapshot or evaluation returns `js_error`, fall back to:

```bash
cmux browser surface:25 get text body
cmux browser surface:25 get html body
```

cmux uses WKWebView. Known gaps include viewport and offline emulation, tracing, screencast, network interception, and low-level raw input.

## OpenClaw extension relay

The Chrome DevTools MCP call is the agent-facing interface. The OpenClaw extension is its authenticated transport. Require relay-only routing so a missing relay cannot silently become direct DevTools attachment:

```bash
MCPORTER_CHROME_DEVTOOLS_RELAY_POLICY=require npx -y mcporter call chrome-devtools.<tool>
```

A Chrome "Allow remote debugging?" prompt or relay-policy error means the extension transport was not used.

OpenClaw creates a random per-host relay key. The extension and same-host clients use nonce-bound mutual HMAC proofs. The reusable key must not enter URLs, child process arguments, configuration, command output, chat, logs, or screenshots.

New pairings default to all eligible ordinary tabs except tabs paused in the popup. Existing pairings keep their stored mode. In selected-tabs mode, membership in the Chrome tab group named `OpenClaw` is the sharing boundary. Restricted pages, incognito tabs, other profiles, and ineligible URLs stay excluded.

Direct remote Gateway pairing does not create a local relay for local mcporter. Do not copy remote secrets or create ad-hoc SSH tunnels around that boundary.

### Setup and repair

- Run `openclaw browser extension install` before loading the unpacked extension. It installs a stable copy and registers its deterministic Chrome ID.
- Use `openclaw browser extension status --json`. Require no reported issues and `manualSetupRequired: false`.
- Confirm Settings reports automatic setup ready and the popup reports connected.
- If the extension attempted native messaging before installation, restart Chrome once. Chrome caches the miss for the process lifetime.
- After pairing or route changes, run `npx -y mcporter daemon stop`. A restart can reuse a child with a dead upstream socket; a stop forces a clean child on the next call.
- MCPorter discovers the relay through `openclaw browser extension cdp --json`. A source-checkout launcher may need `MCPORTER_CHROME_DEVTOOLS_RELAY_TIMEOUT_MS=15000` for its freshness build.

Do not run the CDP discovery command or inspect process arguments as routine diagnostics because either can expose relay credentials.

### Fail-closed readiness proof

Require every condition:

1. Extension status reports the stable copy and exact native registrations with no issues.
2. The popup reports connected and the target tab is eligible and not paused.
3. The mcporter daemon was stopped after pairing or route changes.
4. A call with `MCPORTER_CHROME_DEVTOOLS_RELAY_POLICY=require` succeeds.
5. Selection and evaluation both succeed in a known disposable tab.

```bash
MCPORTER_CHROME_DEVTOOLS_RELAY_POLICY=require npx -y mcporter call chrome-devtools.list_pages --args '{}' --output text
MCPORTER_CHROME_DEVTOOLS_RELAY_POLICY=require npx -y mcporter call chrome-devtools.select_page --args '{"pageId":9}' --output text
MCPORTER_CHROME_DEVTOOLS_RELAY_POLICY=require npx -y mcporter call chrome-devtools.evaluate_script --args '{"function":"() => ({title: document.title, href: location.href})"}' --output json
```

A relay-policy error means the extension route is unavailable. Report or repair it instead of retrying without `require`.

## Chrome DevTools flow

Use current snapshot UIDs. Prefer DOM snapshots over screenshots unless layout matters.

```bash
MCPORTER_CHROME_DEVTOOLS_RELAY_POLICY=require npx -y mcporter call chrome-devtools.list_pages --args '{}' --output text
MCPORTER_CHROME_DEVTOOLS_RELAY_POLICY=require npx -y mcporter call chrome-devtools.select_page --args '{"pageId":9}' --output text
MCPORTER_CHROME_DEVTOOLS_RELAY_POLICY=require npx -y mcporter call chrome-devtools.take_snapshot --args '{}' --output text
MCPORTER_CHROME_DEVTOOLS_RELAY_POLICY=require npx -y mcporter call chrome-devtools.click --args '{"uid":"1_38","includeSnapshot":true}' --output text
MCPORTER_CHROME_DEVTOOLS_RELAY_POLICY=require npx -y mcporter call chrome-devtools.fill --args '{"uid":"1_13","value":"text","includeSnapshot":true}' --output text
MCPORTER_CHROME_DEVTOOLS_RELAY_POLICY=require npx -y mcporter call chrome-devtools.evaluate_script --args '{"function":"() => document.title"}' --output json
```

Capture state before the action, perform the requested interaction, then snapshot or evaluate the rendered result. Keep secrets out of DOM, input, network, console, and screenshot output. Return only safe shapes for credential checks, such as present or absent, length, status code, or account name.

If automation is unavailable, report the verification gap instead of switching to prohibited or isolated tooling.

## Argument and output mechanics

`--args` accepts inline JSON only. It does not read `@file`. Flag-style named arguments do:

```bash
MCPORTER_CHROME_DEVTOOLS_RELAY_POLICY=require npx -y mcporter call chrome-devtools.navigate_page url=@/tmp/target-url.txt --output text
MCPORTER_CHROME_DEVTOOLS_RELAY_POLICY=require npx -y mcporter call chrome-devtools.evaluate_script function=@/tmp/probe.js --output json
```

Use a mode-0600 file for sign-in URLs, magic links, callbacks, and multiline scripts so their values do not enter shell history, process arguments, or captured output.

Other mechanics:

- Interactive navigation, snapshots, and consent pages can exceed the short default timeout. Use `--timeout 30000`.
- `take_screenshot` paths are confined to configured workspace roots. When necessary, omit `filePath`, read base64 JSON output, and decode it locally.
- `new_page` can fail for an unavailable or unshared target. Prefer navigating an eligible shared tab.
- Run `npx -y mcporter list chrome-devtools --schema` instead of guessing parameter names.

## Clicks that do not click

A UID click can report success while a page ignores the synthetic event. Verify state after every activation.

When click no-ops, use `press_key` with `Tab`, `Shift+Tab`, or `Enter`, and confirm focus with a screenshot first. Never send blind Enter on a consent screen.

Navigation and re-rendering invalidate UIDs. Re-run `take_snapshot` after each state change.

## Empty relay mid-task

An empty page list usually means there are no eligible tabs, the tab was paused, selected-tabs mode lost its group members, or the extension disconnected. Confirm Chrome is running, check the popup connection and pause state, then check the access mode.

Restarting mcporter cannot repair extension disconnection, tab eligibility, or access policy. Do not switch to full-profile attachment or an isolated browser to hide the gap.

## Legacy full-profile fallback

Use direct attachment only after the callable plugin and authenticated local extension relay are unavailable. It exposes the full real-profile tab set and can show Chrome's blocking remote-debugging prompt.

Approve one visible, unambiguous prompt, then retry `list_pages` once. If the prompt is absent, ambiguous, or the retry fails, stop. Never loop approvals, repeatedly restart Chrome or mcporter, or kill browser processes.

Verify the intended real-profile tabs before acting and label this route as full-profile direct attachment, never extension relay success.
