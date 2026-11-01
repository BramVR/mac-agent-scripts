import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { parseConfig } from "../parse.mjs";
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

test("a rule TLC checked only in the initial states is not shown as checked everywhere", async () => {
  const { m, doc } = await page("Shadow");
  const shade = m.rules.find((r) => r.name === "Shade");
  assert.match(shade.initialOnly, /only in the initial states/);
  assert.match(doc, /Holds in initial states<\/span><\/td><td>TLC checked Shade only in the initial states/);
});

test("a user invariant named NoDeadlock is not described as a deadlock", () => {
  const m = model(load(fixture("UserNoDeadlock")));
  const user = m.rules.find((r) => r.name === "NoDeadlock");
  const deadlock = m.rules.find((r) => r.name === "CHECK_DEADLOCK");
  assert.deepEqual(user.steps.at(-1).notes, ["NoDeadlock breaks here."]);
  assert.match(deadlock.steps.at(-1).notes.join(" "), /No step leads out/);
});

test("a looping counterexample starts its loop where TLC goes back to, and keeps single-variable values", () => {
  const r = model(load(fixture("CounterLoopView"))).rules.find((x) => x.name === "ReachesThree");
  assert.equal(r.loopStart, 1);
  assert.match(r.steps[1].notes.join(" "), /From here: The run loops .* So ReachesThree breaks\./);
  assert.deepEqual(r.trace.states.slice(0, 3).map((s) => s.vars), [[["x", "0"]], [["x", "1"]], [["x", "2"]]]);
});

test("an arrow drawn from a parent state is highlighted, not reported as hidden", () => {
  const r = model(load(fixture("LoginReset"))).rules.find((x) => x.name === "NoResetEmail");
  const last = r.steps.at(-1);
  assert.deepEqual(last.edges, ["edge14"]);
  assert.doesNotMatch(last.notes.join(" "), /hides the arrow/);
});

test("block comments in the config do not become rules", () => {
  assert.deepEqual(parseConfig("SPECIFICATION Spec\nINVARIANT\n  TypeOK (* shape *)\n  LoudWhenStopped\n").rules, ["TypeOK", "LoudWhenStopped"]);
});

test("a config the user did not pass is labelled as assumed", () => {
  const m = model(load(fixture("MediaPlayerFixed")));
  m.config = { name: "Spec.cfg", text: "CONSTANT N = 2", sections: { CONSTANT: ["N = 2"] }, assumed: true };
  assert.match(html(m), /Assumed config Spec\.cfg/);
  m.config.assumed = false;
  assert.doesNotMatch(html(m), /Assumed config/);
});

test("a one-region view resolves its prefixed states to chart nodes", () => {
  const r = model(load(fixture("SingleRegion"))).rules.find((x) => x.name === "ReachesThree");
  assert.deepEqual(r.steps.map((s) => s.nodes), [["s0"], ["s1"], ["s2"], ["s1"]]);
  assert.deepEqual(r.steps.map((s) => s.edges), [[], ["edge1"], ["edge2"], ["edge3"]]);
});

test("a step drawn as a self-loop highlights that loop", () => {
  const r = model(load(fixture("CollapsedLoop"))).rules.find((x) => x.name === "ReachesThree");
  assert.deepEqual(r.steps.slice(1).map((s) => s.edges), [["edge1"], ["edge1"], ["edge1"]]);
  assert.doesNotMatch(r.steps.flatMap((s) => s.notes).join(" "), /draws no arrow/);
});

test("a property counterexample is labelled as TLC's counterexample, not a shortest path", async () => {
  const { doc } = await page("CounterLoopView");
  assert.match(doc, /TLC&#39;s counterexample in tlc-ReachesThree\.out: 3 steps\./);
  const { doc: invariant } = await page("TwoPhase");
  assert.match(invariant, /Shortest path in TLC&#39;s state graph: 5 steps\./);
});

test("a step label with a colon keeps its colon when the chart is flat", () => {
  const r = model(load(fixture("R2Colon"))).rules.find((x) => x.name === "ReachesThree");
  assert.equal(r.steps[1].step, "User: Up");
  assert.equal(r.steps[1].state, "1");
});

test("a one-region view with a multiword name resolves to chart nodes", () => {
  const r = model(load(fixture("R2Multiword"))).rules.find((x) => x.name === "ReachesThree");
  assert.deepEqual(r.steps.map((s) => s.nodes), [["s0"], ["s1"], ["s2"], ["s1"]]);
});

test("NoDeadlock listed as an invariant is not a deadlock when deadlock checking is off", () => {
  const m = model(load(fixture("R2Disabled"), fixture("R2Disabled/checked.cfg")));
  assert.deepEqual(m.rules.find((r) => r.name === "NoDeadlock").steps.at(-1).notes, ["NoDeadlock breaks here."]);
});

test("nested config comments do not become rules", () => {
  const m = model(load(fixture("R2Nested"), fixture("R2Nested/checked.cfg")));
  assert.deepEqual(m.rules.filter((r) => r.status === "unavailable"), []);
});

test("summary chips count initial-state-only rules apart from rules that hold everywhere", async () => {
  const { m, doc } = await page("Shadow");
  assert.deepEqual(m.rules.map((r) => [r.name, r.status]), [["Shadow", "holds"], ["Shade", "holds initially"], ["Hold", "holds initially"]]);
  assert.match(doc, /1 holds<\/span><span class="chip s-holds-initially">2 holds in initial states</);
});

test("a --config path that does not exist is an error, not a missing default", () => {
  assert.throws(() => load(fixture("TwoPhase"), fixture("TwoPhase/missing.cfg")), /--config .*missing\.cfg does not exist/);
});

test("a self-loop whose own label contains ' or ' is highlighted", () => {
  const r = model(load(fixture("OrLabel"))).rules.find((x) => x.name === "ReachesThree");
  assert.deepEqual(r.steps[1].edges, ["edge1"]);
  assert.doesNotMatch(r.steps[1].notes.join(" "), /draws no arrow/);
});

test("the initial-states caveat is kept when report.md ends with a Rules not checked section", () => {
  const m = model(load(fixture("InitOnlyUnchecked")));
  assert.equal(m.rules.find((r) => r.name === "Shade").status, "holds initially");
});

test("a one-region name is learned from the whole path even when the start label collides with a chart label", () => {
  const r = model(load(fixture("PrefixCollision"))).rules.find((x) => x.status === "breaks");
  assert.deepEqual(r.steps.map((s) => s.nodes), [["s0"], ["s1"], ["s2"], ["s1"]]);
  assert.deepEqual(r.steps.slice(1).map((s) => s.step), ["you advance: now", "you advance: now", "you advance: now"]);
});

test("a merged self-loop whose labels contain ' or ' still highlights for each label", () => {
  const r = model(load(fixture("OrMergedLoop"))).rules.find((x) => x.status === "breaks");
  assert.deepEqual(r.steps.slice(1).map((s) => s.edges), [["edge1"], ["edge1"]]);
});

test("TLC's deadlock report outweighs an assumed config that lists NoDeadlock", () => {
  const input = load(fixture("DeadlockAssumed"));
  input.config = { name: "Dl.cfg", text: "INVARIANT NoDeadlock", sections: {}, rules: ["NoDeadlock"], assumed: true };
  const r = model(input).rules.find((x) => x.name === "NoDeadlock");
  assert.equal(r.trace.file, "tlc.out");
  assert.match(r.steps.at(-1).notes.join(" "), /No step leads out/);
});

test("a merged self-loop matches each label even when both labels contain ' or '", () => {
  const r = model(load(fixture("OrMergedLoop2"))).rules.find((x) => x.name === "NotTwo");
  assert.deepEqual(r.steps.slice(1).map((s) => s.edges), [["edge1"], ["edge1"]]);
});

test("a NoDeadlock the spec defines is the user's rule when TLC reports no deadlock", () => {
  const input = load(fixture("UserNoDeadlockNoConfig"));
  input.specs = new Map([["UserND.tla", "---- MODULE UserND ----\nVARIABLE x\nNoDeadlock == x < 2\n===="]]);
  assert.deepEqual(model(input).rules.find((r) => r.name === "NoDeadlock").steps.at(-1).notes, ["NoDeadlock breaks here."]);
});

test("the initial-states caveat appears once, in its own rule's row", async () => {
  const { doc } = await page("InitOnlyUnchecked");
  assert.equal(doc.match(/TLC checked Shade only in the initial states/g).length, 1);
});

test("the replay still steps through when Pele could not draw the chart", () => {
  const input = load(fixture("TwoPhase"));
  const { JSDOM, VirtualConsole } = jsdom();
  const errors = [];
  const virtualConsole = new VirtualConsole();
  virtualConsole.on("jsdomError", (e) => errors.push(e.message));
  const { window } = new JSDOM(html(model(input), undefined, { message: "PeleError", mmd: input.mmd }), { runScripts: "dangerously", virtualConsole });
  const d = window.document;
  d.getElementById("next").click();
  assert.deepEqual(errors, []);
  assert.equal(d.getElementById("pos").textContent, "Step 1 of 5");
});
