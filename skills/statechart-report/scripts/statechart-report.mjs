#!/usr/bin/env node
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { parseArgs } from "node:util";
import { parseChart, parseConfig, parseReport, parseTlc, resolveState, splitStep } from "./parse.mjs";

const USAGE = `Usage: statechart-report.mjs OUT_DIR [--config FILE] [--html FILE] [--svg FILE]

Reads report.md, chart.mmd, tlc.out, and tlc-RULE.out from a statechart --out folder.
Writes a self-contained report.html, report.embed.html for T3 html_render, and a themed\nchart.svg (Pele 1.9.0) into OUT_DIR.
  --config FILE  TLC config to show bounds from. Default: SPEC.cfg beside the spec TLC parsed.
  --html FILE    Where to write the HTML. Default: OUT_DIR/report.html
  --svg FILE     Where to write the SVG. Default: OUT_DIR/chart.svg`;

const PELE = "pele@1.9.0";
const PELE_OPTIONS = { limit: 1_000_000, outputLimit: 8_000_000, maxEdges: 10_000 };

export async function loadPele() {
  const cache = process.env.XDG_CACHE_HOME ?? path.join(os.homedir(), ".cache");
  const dir = path.join(cache, "statechart-report", PELE.replace("@", "-"));
  if (!fs.existsSync(path.join(dir, "node_modules", "pele")))
    execFileSync("npm", ["install", "--prefix", dir, "--no-audit", "--no-fund", "--save-exact", PELE], {
      stdio: ["ignore", "ignore", "inherit"],
    });
  const req = createRequire(path.join(dir, "package.json"));
  return import(pathToFileURL(req.resolve("pele")).href);
}

const read = (f) => (fs.existsSync(f) ? fs.readFileSync(f, "utf8") : undefined);

export function load(dir, configFile) {
  const report = parseReport(read(path.join(dir, "report.md")) ?? fail(`${dir} has no report.md`));
  const mmd = read(path.join(dir, "chart.mmd"));
  const traces = new Map();
  for (const f of fs.readdirSync(dir).sort())
    if (/^tlc(-.+)?\.out$/.test(f)) traces.set(f, parseTlc(read(path.join(dir, f))));
  const files = traces.get("tlc.out")?.files ?? [];
  const specs = new Map();
  for (const f of files) {
    const text = read(f);
    if (text) specs.set(path.basename(f), text);
  }
  const main = files.find((f) => path.basename(f, ".tla") === report.module) ?? files[0];
  const cfgPath = configFile ?? (main && main.replace(/\.tla$/, ".cfg"));
  const cfgText = cfgPath && read(cfgPath);
  return {
    report,
    mmd,
    chart: mmd ? parseChart(mmd) : undefined,
    traces,
    specs,
    config: cfgText ? { name: path.basename(cfgPath), text: cfgText, ...parseConfig(cfgText) } : undefined,
  };
}

function fail(msg) {
  throw new Error(msg);
}

function definition(specs, name) {
  const re = new RegExp(`^${name.replace(/\W/g, "\\$&")}\\s*(\\([^)]*\\))?\\s*==`, "m");
  for (const [file, text] of specs) {
    const m = re.exec(text);
    if (m) return `${file}:${text.slice(0, m.index).split("\n").length}`;
  }
}

function traceFor(traces, rule, isDeadlock) {
  const own = traces.get(rule.traceFile ?? `tlc-${rule.name}.out`);
  if (own?.trace.length) return { file: rule.traceFile ?? `tlc-${rule.name}.out`, ...own };
  const main = traces.get("tlc.out");
  if (main?.trace.length && (main.rule === rule.name || (isDeadlock && main.deadlock)))
    return { file: "tlc.out", ...main };
}

function transitions(chart, from, to, label) {
  const changes = [];
  const edges = [];
  for (const [i, a] of from.entries()) {
    const b = to[i];
    if (a === b) continue;
    changes.push({ region: chart.regions[i], from: chart.nodes.get(a).key, to: chart.nodes.get(b).key });
    const all = chart.edges.filter((e) => e.from === a && e.to === b);
    const named = all.filter((e) =>
      e.label
        .replace(/ \[[^\]]*\]$/, "")
        .split(" or ")
        .includes(label.replace(/ \[[^\]]*\]$/, "")),
    );
    edges.push(...(named.length ? named : all).map((e) => e.id));
  }
  return { changes, edges };
}

export function model({ report, chart, traces, specs, config }) {
  const deadlockNames = new Set(["NoDeadlock", "CHECK_DEADLOCK"]);
  const known = new Set(report.rules.map((r) => r.name));
  const rules = report.rules.map((r) => ({ ...r }));
  for (const name of config?.rules ?? [])
    if (!known.has(name)) rules.push({ name, status: "unavailable" });
  for (const r of rules) {
    r.source = definition(specs, r.name);
    if (r.status !== "breaks") continue;
    const trace = traceFor(traces, r, deadlockNames.has(r.name));
    if (trace)
      r.trace = {
        file: trace.file,
        error: trace.error,
        states: trace.trace.map((s) => ({
          n: s.n,
          action: s.action,
          source: s.source && `${s.source.module}.tla:${s.source.from}${s.source.to !== s.source.from ? `-${s.source.to}` : ""}`,
          vars: s.vars,
        })),
      };
    const quoted = new Set([...(r.loop ?? "").matchAll(/"([^"]+)"/g)].map((m) => m[1]));
    const steps = (r.raw ?? []).map((line, i) => splitStep(chart, line, i === 0));
    let loopStart;
    if (r.loop)
      for (let i = steps.length - 1; i >= 0 && quoted.has(steps[i].state); i--) loopStart = i;
    r.loopStart = loopStart;
    r.steps = steps.map((s, i) => {
      const nodes = resolveState(chart, s.state);
      const prev = i > 0 ? resolveState(chart, steps[i - 1].state) : null;
      const t = nodes && prev ? transitions(chart, prev, nodes, s.step) : { changes: [], edges: [] };
      const notes = [];
      if (!chart) notes.push("No chart.mmd, so this step has no chart position.");
      else if (!nodes) notes.push("This state is not in the chart.");
      else if (i > 0 && prev && !t.changes.length)
        notes.push("No chart label changes in this step, so the chart draws no arrow for it.");
      else if (t.changes.length && !t.edges.length) notes.push("The chart hides the arrow for this step.");
      if (loopStart !== undefined && i === loopStart)
        notes.push(steps.length - 1 === i && r.loop?.includes("stops in") ? r.loop : `From here: ${r.loop}`);
      if (i === steps.length - 1 && loopStart === undefined)
        notes.push(deadlockNames.has(r.name) ? `No step leads out of this state, so ${r.name} breaks.` : `${r.name} breaks here.`);
      return { ...s, nodes: nodes ?? [], edges: t.edges, changes: t.changes, notes };
    });
    delete r.raw;
  }
  const main = traces.get("tlc.out");
  return {
    module: report.module,
    title: chart?.title,
    notes: report.notes,
    notChecked: report.notChecked,
    stopped: report.stopped,
    rules,
    tlc: main && { version: main.version, workers: main.workers, facts: main.facts },
    config: config && { name: config.name, text: config.text, sections: config.sections },
  };
}

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

const STATUS = {
  breaks: ["Breaks", "TLC found a counterexample."],
  holds: ["Holds", "TLC checked every reachable state of this bounded model."],
  "not checked": ["Not checked", "TLC did not finish checking this rule. It can hold or break."],
  unavailable: ["No result", "The config lists this rule, but report.md gives no result for it."],
};

// Field Notes theme: Flexoki paper (https://pele.run/theming), ink-blue path, brick-red failure.
const LIGHT_DARK_SVG_THEME = `.pele{--pele-bg:#fffcf0;--pele-fg:#100f0f;--pele-muted:#6f6e69;--pele-line:#6f6e69;--pele-surface:#f2f0e5;--pele-surface-alt:#f7f5ea;--pele-border:#cecdc3;--pele-accent:#205ea6;--pele-critical:#af3029}
.pele .blue rect{fill:#dde6f0}.pele .orange rect{fill:#f6e2d4}.pele .purple rect{fill:#e6e0f0}.pele .yellow rect{fill:#f3ead0}.pele .teal rect{fill:#dbeae6}.pele .tan rect{fill:#ece5d8}.pele .pink rect{fill:#f5dfe8}
.pele .breaks rect{fill:#ffe1d5!important;stroke:#af3029!important;stroke-width:2.5px!important}.pele .breaks text{fill:#af3029!important}
.pele .mayBreak rect{fill:#ffe7ce!important;stroke:#bc5215!important;stroke-width:2.5px!important}.pele .mayBreak text{fill:#9c4310!important}
.pele .bugPath rect{stroke:#205ea6!important;stroke-width:2.5px!important}
.pele .repeats rect{stroke:#5e409d!important;stroke-width:2.5px!important;stroke-dasharray:6 3}
@media (prefers-color-scheme:dark){.pele{--pele-bg:#100f0f;--pele-fg:#cecdc3;--pele-muted:#878580;--pele-line:#878580;--pele-surface:#1c1b1a;--pele-surface-alt:#282726;--pele-border:#403e3c;--pele-accent:#4385be;--pele-critical:#d14d41}
.pele .blue rect{fill:#1a2b3d}.pele .orange rect{fill:#3a2414}.pele .purple rect{fill:#2a2238}.pele .yellow rect{fill:#353016}.pele .teal rect{fill:#16302d}.pele .tan rect{fill:#2e2821}.pele .pink rect{fill:#3a1d2a}
.pele .breaks rect{fill:#3a1714!important;stroke:#d14d41!important}.pele .breaks text{fill:#e8705f!important}
.pele .mayBreak rect{fill:#3a2414!important;stroke:#da702c!important}.pele .mayBreak text{fill:#ec8b49!important}
.pele .bugPath rect{stroke:#4385be!important}.pele .repeats rect{stroke:#8b7ec8!important}}`;

const PAGE_CSS = `:root{--bg:#fffcf0;--fg:#100f0f;--mute:#6f6e69;--panel:#f2f0e5;--line:#e6e4d9;--edge:#cecdc3;--bad:#af3029;--bad-bg:#ffe1d5;--ok:#66800b;--ok-bg:#edeecf;--warn:#ad8301;--warn-bg:#faeec6;--na:#6f6e69;--path:#205ea6;--cur:#100f0f;--serif:"Iowan Old Style",Palatino,Georgia,serif;--sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 var(--serif)}
main{max-width:1200px;margin:0 auto;padding:24px 20px 48px;background:var(--bg);color:var(--fg)}h1{font-size:24px;font-weight:600;margin:0 0 4px}h2{font-size:17px;font-weight:600;margin:30px 0 10px;border-bottom:1px solid var(--line);padding-bottom:6px}h3{font-size:15px;font-weight:600}
.sub{color:var(--mute);margin:0 0 12px}code,pre,.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:13px}pre{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:10px;overflow:auto;white-space:pre-wrap}
.chips{display:flex;flex-wrap:wrap;gap:8px}.chip{border-radius:3px;padding:1px 9px;font:13px/1.6 var(--sans);background:var(--panel);color:var(--na)}
.s-breaks{background:var(--bad-bg);color:var(--bad)}.s-holds{background:var(--ok-bg);color:var(--ok)}.s-not-checked{background:var(--warn-bg);color:var(--warn)}.s-unavailable{background:transparent;color:var(--na);outline:1px dashed var(--edge)}
table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}th{color:var(--mute);font:500 13px var(--sans)}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:16px}
.chart{overflow:auto;background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:16px;margin:10px 0}
.controls{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:10px 0}button{background:var(--panel);color:var(--fg);border:1px solid var(--edge);border-radius:4px;padding:5px 12px;font:14px var(--sans);cursor:pointer}button:hover{border-color:var(--mute)}button[aria-selected=true]{border-color:var(--bad);color:var(--bad);background:var(--bg)}button:disabled{opacity:.4;cursor:default}
.explain{min-height:3.2em;border-left:3px solid var(--bad)}.explain b{color:var(--fg)}.explain .chg{color:var(--mute)}
ol.steps{margin:8px 0 0;padding-left:28px}ol.steps li{padding:3px 6px;border-radius:4px;cursor:default}ol.steps li.cur{background:var(--panel)}ol.steps .act{color:var(--path);font-style:italic}ol.steps .note{color:var(--mute);font-size:13px}
.js ol.steps li{cursor:pointer}.js .failure[hidden]{display:none}
details{margin:8px 0}summary{cursor:pointer;color:var(--mute)}.changed{color:var(--path);font-weight:600}
.pele{--pele-bg:#fffcf0;--pele-fg:#100f0f;--pele-muted:#6f6e69;--pele-line:#6f6e69;--pele-surface:#f2f0e5;--pele-surface-alt:#f7f5ea;--pele-border:#cecdc3;--pele-font:var(--sans)}
.pele rect{rx:6px}
.pele .blue rect{fill:#dde6f0}.pele .orange rect{fill:#f6e2d4}.pele .purple rect{fill:#e6e0f0}.pele .yellow rect{fill:#f3ead0}.pele .teal rect{fill:#dbeae6}.pele .tan rect{fill:#ece5d8}.pele .pink rect{fill:#f5dfe8}
.pele .breaks rect{fill:#ffe1d5!important;stroke:#af3029!important;stroke-width:2px!important}.pele .breaks text{fill:#af3029!important}
.pele .mayBreak rect{fill:#ffe7ce!important;stroke:#bc5215!important;stroke-width:2px!important}.pele .mayBreak text{fill:#9c4310!important}
.pele .bugPath rect{stroke:#cecdc3!important;stroke-width:1px!important}.pele .repeats rect{stroke:#5e409d!important;stroke-width:2px!important;stroke-dasharray:6 3}
.pele g.rp-off{opacity:.25}.pele g.pele-edge.rp-off,.pele g.pele-edge-label.rp-off{opacity:.2}
.pele g.pele-node.rp-path rect{stroke:var(--path)!important;stroke-width:2px!important}.pele g.pele-edge.rp-path path{stroke:var(--path);stroke-width:2px}.pele g.pele-edge.rp-path .pele-marker{fill:var(--path)}.pele g.pele-edge-label.rp-path text{fill:var(--path)}
.pele g.pele-node.rp-cur rect{stroke:var(--cur)!important;stroke-width:3px!important}.pele g.pele-node.rp-cur text{font-weight:700}
.pele g.pele-edge.rp-cur path{stroke:var(--cur);stroke-width:3px}.pele g.pele-edge.rp-cur .pele-marker{fill:var(--cur)}.pele g.pele-edge-label.rp-cur text{fill:var(--cur);font-weight:700}
.pele g.pele-node.rp-bad rect{stroke:var(--bad)!important;stroke-width:3px!important;fill:var(--bad-bg)!important}.pele g.pele-node.rp-bad text{fill:var(--bad)!important}`;

// T3 html_render supplies the page background; the paper becomes one rounded card.
const EMBED_CSS = "body{background:none}main{max-width:none;padding:16px;border-radius:var(--radius,8px)}";

const SCRIPT = `(function(){
var data=JSON.parse(document.getElementById('replay-data').textContent);
document.documentElement.classList.add('js');
var svg=document.querySelector('#replay .chart svg');
var fails=data.rules.filter(function(r){return r.status==='breaks'&&r.steps&&r.steps.length});
if(!fails.length)return;
var sel=0,cur=0;
var tabs=document.querySelectorAll('#replay [data-rule]');
var lists=document.querySelectorAll('#replay .failure');
var prev=document.getElementById('prev'),next=document.getElementById('next');
var pos=document.getElementById('pos'),ex=document.getElementById('explain');
function all(q){return svg?Array.prototype.slice.call(svg.querySelectorAll(q)):[]}
function mark(ids,cls){ids.forEach(function(id){all('[data-id="'+id+'"]').forEach(function(g){g.classList.add(cls)})})}
function txt(s){var d=document.createElement('span');d.textContent=s;return d}
function show(){
var r=fails[sel],s=r.steps[cur];
tabs.forEach(function(t,i){t.setAttribute('aria-selected',String(i===sel))});
lists.forEach(function(l,i){l.hidden=i!==sel});
lists[sel].querySelectorAll('li').forEach(function(li,i){li.classList.toggle('cur',i===cur)});
all('g.pele-node,g.pele-edge,g.pele-edge-label').forEach(function(g){g.classList.remove('rp-off','rp-path','rp-cur','rp-bad')});
var pn=[],pe=[];r.steps.slice(0,cur+1).forEach(function(x){pn=pn.concat(x.nodes);pe=pe.concat(x.edges)});
if(s.nodes.length){all('g.pele-node:not([data-id^="lg"]),g.pele-edge,g.pele-edge-label').forEach(function(g){g.classList.add('rp-off')});
mark(pn,'rp-path');mark(pe,'rp-path');pn.concat(pe).forEach(function(id){all('[data-id="'+id+'"]').forEach(function(g){g.classList.remove('rp-off')})});
mark(s.nodes,'rp-cur');mark(s.edges,'rp-cur');if(cur===r.steps.length-1)mark(s.nodes,'rp-bad');
var box=svg.parentNode,g=svg.querySelector('g.pele-node.rp-cur');if(g&&box.scrollWidth>box.clientWidth){var b=g.getBoundingClientRect(),c=box.getBoundingClientRect();box.scrollLeft+=b.left+b.width/2-(c.left+c.width/2)}}
pos.textContent='Step '+cur+' of '+(r.steps.length-1);
prev.disabled=cur===0;next.disabled=cur===r.steps.length-1;
ex.textContent='';var h=document.createElement('b');h.textContent=cur===0?'Start':s.step;ex.appendChild(h);
ex.appendChild(txt(cur===0?': '+s.state:'. Now: '+s.state));
s.changes.forEach(function(c){var d=document.createElement('div');d.className='chg';d.textContent=(c.region?c.region+': ':'')+c.from+' \\u2192 '+c.to;ex.appendChild(d)});
s.notes.forEach(function(n){var d=document.createElement('div');d.textContent=n;ex.appendChild(d)});
}
tabs.forEach(function(t,i){t.addEventListener('click',function(){sel=i;cur=0;show()})});
lists.forEach(function(l){l.querySelectorAll('li').forEach(function(li,i){li.addEventListener('click',function(){cur=i;show()})})});
prev.addEventListener('click',function(){if(cur>0){cur--;show()}});
next.addEventListener('click',function(){if(cur<fails[sel].steps.length-1){cur++;show()}});
document.addEventListener('keydown',function(e){if(e.key==='ArrowRight')next.click();if(e.key==='ArrowLeft')prev.click()});
document.getElementById('controls').hidden=false;show();
})();`;

function rulesTable(m) {
  const rows = m.rules.map((r) => {
    const [label, meaning] = STATUS[r.status];
    const detail =
      r.status === "breaks"
        ? r.offChart
          ? `Counterexample in ${r.traceFile ?? "a tlc-RULE.out file"}; report.md gives no chart path.`
          : `Shortest path: ${r.steps.length - 1} step${r.steps.length === 2 ? "" : "s"}.${r.loop ? ` ${r.loop}` : ""}`
        : meaning;
    return `<tr><td class="mono">${esc(r.name)}</td><td><span class="chip s-${r.status.replace(" ", "-")}">${label}</span></td><td>${esc(detail)}</td><td class="mono">${esc(r.source ?? "")}</td></tr>`;
  });
  return `<table><thead><tr><th>Rule</th><th>Result</th><th>Meaning</th><th>Defined at</th></tr></thead><tbody>${rows.join("")}</tbody></table>`;
}

function stepList(r) {
  return r.steps
    .map((s, i) => {
      const { notes } = s;
      return `<li value="${i}">${i ? `<span class="act">${esc(s.step)}</span>: ` : ""}${esc(s.state)}${notes.length ? `<div class="note">${esc(notes.join(" "))}</div>` : ""}</li>`;
    })
    .join("");
}

function rawTrace(r) {
  if (!r.trace) return `<p class="sub">No TLC trace file for ${esc(r.name)} in this folder.</p>`;
  let before = new Map();
  const rows = r.trace.states.map((s) => {
    const vars = s.vars
      .map(([k, v]) => `<span class="${before.has(k) && before.get(k) !== v ? "changed" : ""}">${esc(k)} = ${esc(v)}</span>`)
      .join("<br>");
    before = new Map(s.vars);
    return `<tr><td>${s.n || ""}</td><td class="mono">${esc(s.action)}</td><td class="mono">${esc(s.source ?? "")}</td><td class="mono">${vars}</td></tr>`;
  });
  return `<details><summary>TLC's printed counterexample for ${esc(r.name)} (${esc(r.trace.file)}: ${esc(r.trace.error ?? "")})</summary>
<p class="sub">Raw TLC output. When this differs from the replay above, both are shortest paths that TLC found. The replay follows report.md, the path the chart marks.</p>
<table><thead><tr><th>#</th><th>Action</th><th>Source</th><th>Values (changes in bold blue)</th></tr></thead><tbody>${rows.join("")}</tbody></table></details>`;
}

export function html(m, svg, chartError, embed = false) {
  const fails = m.rules.filter((r) => r.status === "breaks" && r.steps?.length);
  const count = (s) => m.rules.filter((r) => r.status === s).length;
  const chips = Object.keys(STATUS)
    .filter((s) => count(s))
    .map((s) => `<span class="chip s-${s.replace(" ", "-")}">${count(s)} ${STATUS[s][0].toLowerCase()}</span>`)
    .join("");
  // Shrink wide charts to fit, but stop at 60% so labels stay readable; past that the box scrolls.
  const natural = Number(svg?.match(/viewBox="[\d.]+ [\d.]+ ([\d.]+)/)?.[1] ?? 0);
  const chart = svg
    ? `<div class="chart">${svg.replace('style="', `style="min-width:${Math.round(natural * 0.6)}px;`)}</div>`
    : `<div class="panel">${chartError ? `Pele could not render chart.mmd: <code>${esc(chartError.message)}</code><pre>${esc(chartError.mmd)}</pre>` : "No chart.mmd in this folder. The statechart command writes none above 500 states when every rule holds."}</div>`;
  const replay = fails.length
    ? `<section id="replay"><h2>Failure replay</h2>
<p class="sub">Each step is one step of the shortest path that the statechart command took from TLC's state graph. The chart groups model states under one label, so a step can stay in one chart state.</p>
<div id="controls" class="controls" hidden><span role="tablist">${fails.map((r) => `<button role="tab" data-rule="${esc(r.name)}">${esc(r.name)}</button>`).join(" ")}</span>
<button id="prev" type="button">Previous</button><button id="next" type="button">Next</button><span id="pos" class="mono"></span></div>
<div id="explain" class="panel explain" aria-live="polite"></div>
${chart}
${fails.map((r) => `<div class="failure"><h3>${esc(r.name)} breaks</h3><ol class="steps" start="0">${stepList(r)}</ol></div>`).join("")}
</section>`
    : `<section id="replay"><h2>Chart</h2>${chart}</section>`;
  const offChart = m.rules.filter((r) => r.status === "breaks" && !r.steps?.length);
  const traced = m.rules.filter((r) => r.status === "breaks");
  const cfg = m.config
    ? `<p class="sub">Config ${esc(m.config.name)}. ${["CONSTANT", "CONSTRAINT", "ACTION_CONSTRAINT", "VIEW", "SYMMETRY"].some((k) => m.config.sections[k]) ? "" : "No CONSTANT, CONSTRAINT, VIEW, or SYMMETRY lines."}</p><pre>${esc(m.config.text.trim())}</pre>`
    : `<p class="sub">No config found next to the spec, so bounds come only from report.md and tlc.out.</p>`;
  const tlc = m.tlc
    ? `<ul>${[m.tlc.version, m.tlc.workers && `${m.tlc.workers} worker`, ...m.tlc.facts].filter(Boolean).map((f) => `<li>${esc(f)}</li>`).join("")}</ul>`
    : "<p class='sub'>No tlc.out in this folder.</p>";
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(m.module)} statechart report</title><style>${PAGE_CSS}${embed ? EMBED_CSS : ""}</style></head><body><main>
<h1>${esc(m.title ?? m.module)}</h1><p class="sub">TLC model ${esc(m.module)}. Results hold only for the bounded model below.</p>
<div class="chips">${chips}</div>
<h2>Rules</h2>${rulesTable(m)}
${m.notChecked ? `<p class="sub">${esc(m.notChecked.replace(/```[\s\S]*?```/g, "").trim())}</p>` : ""}
${m.stopped ? `<div class="panel"><b>TLC stopped</b> with exit ${esc(m.stopped.status)}.<pre>${esc(m.stopped.message)}</pre></div>` : ""}
${replay}
${offChart.length ? `<p class="sub">${offChart.map((r) => esc(r.name)).join(", ")} broke off the chart. See the TLC counterexample below.</p>` : ""}
${traced.length ? `<h2>TLC traces</h2>${traced.map(rawTrace).join("")}` : ""}
<h2>Bounds and assumptions</h2>${cfg}
<h3>Checker notes</h3><ul>${m.notes.map((n) => `<li>${esc(n)}</li>`).join("")}</ul>
<h3>TLC on the config as written (tlc.out)</h3><p class="sub">TLC stops this run at the first break, so its counts can be lower than the full graph in report.md.</p>${tlc}
</main><script type="application/json" id="replay-data">${JSON.stringify({ rules: fails.map(({ name, status, steps }) => ({ name, status, steps })) }).replace(/</g, "\\u003c")}</script><script>${SCRIPT}</script></body></html>`;
}

async function main() {
  const { values, positionals } = parseArgs({
    allowPositionals: true,
    options: { config: { type: "string" }, html: { type: "string" }, svg: { type: "string" }, help: { type: "boolean", short: "h" } },
  });
  if (values.help || positionals.length !== 1) {
    console.log(USAGE);
    process.exit(values.help ? 0 : 2);
  }
  const dir = path.resolve(positionals[0]);
  const input = load(dir, values.config);
  const m = model(input);
  let svg;
  let chartError;
  if (input.mmd) {
    try {
      const { render } = await loadPele();
      svg = render(input.mmd, PELE_OPTIONS).svg;
    } catch (e) {
      chartError = { message: e.message, mmd: input.mmd };
      console.error(`Pele failed: ${e.message}`);
    }
  }
  const htmlFile = values.html ?? path.join(dir, "report.html");
  fs.writeFileSync(htmlFile, html(m, svg, chartError));
  const embedFile = htmlFile.replace(/(\.html)?$/, ".embed.html");
  fs.writeFileSync(embedFile, html(m, svg, chartError, true));
  console.log(htmlFile);
  console.log(embedFile);
  if (svg) {
    const svgFile = values.svg ?? path.join(dir, "chart.svg");
    fs.writeFileSync(svgFile, svg.replace(/^(<svg[^>]*>)/, `$1<style>${LIGHT_DARK_SVG_THEME}</style>`));
    console.log(svgFile);
  }
  const by = (s) => m.rules.filter((r) => r.status === s).map((r) => r.name);
  console.error(
    `breaks: ${by("breaks").join(", ") || "none"}; holds: ${by("holds").join(", ") || "none"}; not checked: ${by("not checked").join(", ") || "none"}; no result: ${by("unavailable").join(", ") || "none"}`,
  );
}

if (process.argv[1] && import.meta.url === pathToFileURL(fs.realpathSync(process.argv[1])).href) await main();
