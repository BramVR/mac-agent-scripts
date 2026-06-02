---
name: browser-use
description: "Browser automation in cmux or Chrome DevTools; no AppleScript."
---

# Browser Use

Use this for browser tasks in cmux or against an existing Chrome session.

Hard rule: use `cmux browser` in cmux; otherwise use `mcporter` `chrome-devtools`. Do not fall back to AppleScript, `osascript`, GUI scripting, or macOS `open` for browser control.

## cmux Browser

Prefer this path when `cmux browser status` prints `enabled`.

```bash
cmux browser status
cmux --json browser open https://example.com --focus false
```

Use the returned `surface_ref` for the task:

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

Use explicit `--text` / `--value` when a mutating command also has flags; otherwise trailing flags can be parsed as input text. Run actions sequentially and re-snapshot after DOM changes; refs from older snapshots can go stale.

Use `cmux identify --json` when you need caller workspace/window/surface context. If a snapshot or eval returns `js_error`, fall back to:

```bash
cmux browser surface:25 get text body
cmux browser surface:25 get html body
```

cmux uses WKWebView. Known gaps: viewport emulation, offline emulation, tracing/screencast, network interception, and low-level raw input.

## Check MCP

Use this path when cmux browser is unavailable and Chrome DevTools MCP is the target.

```bash
npx -y mcporter list chrome-devtools --schema
npx -y mcporter call chrome-devtools.list_pages --args '{}' --output text
```

If `list_pages` fails with `DevToolsActivePort`, restart the mcporter daemon and retry:

```bash
npx -y mcporter daemon restart
npx -y mcporter call chrome-devtools.list_pages --args '{}' --output text
```

If it still fails, stop and say Chrome DevTools MCP is unavailable. Do not use AppleScript.

Avoid noisy recovery loops. Repeated MCP/browser restarts can trigger
reconnect/login prompts and alerts. Try once, then pause and choose a quieter
path.

## Typical Flow

```bash
# pick the page id from list_pages
npx -y mcporter call chrome-devtools.select_page pageId=9 --output text

# inspect page
npx -y mcporter call chrome-devtools.take_snapshot --args '{}' --output text

# navigate selected page
npx -y mcporter call chrome-devtools.navigate_page url=https://example.com --output text

# click an element uid from the latest snapshot
npx -y mcporter call chrome-devtools.click uid=1_38 includeSnapshot=true --output text

# type/fill
npx -y mcporter call chrome-devtools.fill uid=1_13 value='text' includeSnapshot=true --output text

# run JS, keep secrets out of output
npx -y mcporter call chrome-devtools.evaluate_script --args '{"function":"() => document.title"}' --output json
```

Use `take_snapshot` before actions and use current `uid` values only. Avoid `take_screenshot` unless visual layout matters.

## Secret Handling

Never print tokens/passwords from page DOM, network logs, or inputs. For token checks, return shape only: present/absent, length, status code, account/org name.
