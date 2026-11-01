import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { html, load, loadPele, model } from "../statechart-report.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixture = (name) => path.join(here, "fixtures", name);

async function page(name) {
  const input = load(fixture(name));
  const m = model(input);
  const { render } = await loadPele();
  return { m, doc: html(m, input.mmd && render(input.mmd, { limit: 1e6, outputLimit: 8e6, maxEdges: 1e4 }).svg) };
}

function jsdom() {
  const cache = process.env.XDG_CACHE_HOME ?? path.join(os.homedir(), ".cache");
  const dir = path.join(cache, "statechart-report", "test-jsdom-30.1.3");
  if (!fs.existsSync(path.join(dir, "node_modules", "jsdom")))
    execFileSync("npm", ["install", "--prefix", dir, "--no-audit", "--no-fund", "--save-exact", "jsdom@30.1.3"]);
  return createRequire(path.join(dir, "package.json"))("jsdom");
}

test("TwoPhase replays report.md's path and never invents a chart step", () => {
  const m = model(load(fixture("TwoPhase")));
  const r = m.rules.find((x) => x.name === "TCConsistent");
  assert.equal(r.status, "breaks");
  assert.deepEqual(
    r.steps.map((s) => s.step ?? "start"),
    ["start", "RMChooseToAbort", "RMPrepare", "TMRcvPrepared", "TMCommit", "RMRcvCommitMsg"],
  );
  assert.deepEqual(r.steps[1].edges, ["edge13"]);
  assert.deepEqual(r.steps[3].edges, [], "TMRcvPrepared stays in one chart state");
  assert.match(r.steps[3].notes.join(" "), /draws no arrow/);
  assert.deepEqual(r.steps[5].nodes, ["s1", "s5", "s8"]);
  assert.match(r.steps.at(-1).notes.join(" "), /TCConsistent breaks here/);
  assert.equal(r.trace.file, "tlc.out");
  assert.equal(r.trace.states[2].action, "TMRcvPrepared");
  assert.equal(r.trace.states[2].source, "TwoPhase.tla:24-27");
});

test("a passing run shows every rule as holding and no replay", async () => {
  const { m, doc } = await page("MediaPlayerFixed");
  assert.deepEqual(new Set(m.rules.map((r) => r.status)), new Set(["holds"]));
  assert.doesNotMatch(doc, /Failure replay/);
  assert.match(doc, /<svg /);
});

test("property counterexamples come from their own tlc-RULE.out", () => {
  const m = model(load(fixture("MediaPlayerProps")));
  const plays = m.rules.find((r) => r.name === "EventuallyPlays");
  assert.equal(plays.trace.file, "tlc-EventuallyPlays.out");
  assert.equal(plays.loopStart, 0);
  assert.match(plays.steps[0].notes.join(" "), /forever/);
  const quiet = m.rules.find((r) => r.name === "QuietWhenStopped");
  assert.equal(quiet.trace.file, "tlc-QuietWhenStopped.out");
  assert.deepEqual(quiet.steps[1].edges, ["edge10"]);
});

test("rules in the config with no result are not shown as passing", () => {
  const input = load(fixture("TwoPhase"));
  input.config = { name: "x.cfg", text: "INVARIANT Ghost", sections: {}, rules: ["Ghost", "TCConsistent"] };
  const ghost = model(input).rules.find((r) => r.name === "Ghost");
  assert.equal(ghost.status, "unavailable");
});

test("Previous and Next walk the checker path on the rendered chart", async () => {
  const { doc } = await page("TwoPhase");
  const { JSDOM } = jsdom();
  const { window } = new JSDOM(doc, { runScripts: "dangerously" });
  const d = window.document;
  const cur = () => [...d.querySelectorAll("g.pele-node.rp-cur")].map((g) => g.dataset.id);
  assert.equal(d.getElementById("controls").hidden, false);
  assert.deepEqual(cur(), ["s0", "s2", "s6"]);
  assert.equal(d.getElementById("prev").disabled, true);
  for (let i = 0; i < 3; i++) d.getElementById("next").click();
  assert.match(d.getElementById("explain").textContent, /TMRcvPrepared.*draws no arrow/s);
  assert.equal(d.querySelectorAll("g.pele-edge.rp-cur").length, 0);
  d.getElementById("next").click();
  assert.deepEqual([...d.querySelectorAll("g.pele-edge.rp-cur")].map((g) => g.dataset.id), ["edge2"]);
  d.getElementById("next").click();
  assert.equal(d.getElementById("next").disabled, true);
  assert.deepEqual([...d.querySelectorAll("g.pele-node.rp-bad")].map((g) => g.dataset.id), ["s1", "s5", "s8"]);
  assert.equal(d.getElementById("pos").textContent, "Step 5 of 5");
});
