// Parsers for the files that t3-pstack's statechart command writes:
// report.md, chart.mmd, tlc.out, tlc-RULE.out. Pure functions, no I/O.

const decode = (s) =>
  s
    .replace(/#(\d+);/g, (_, n) => String.fromCodePoint(Number(n)))
    .replace(/ﬂ°°(\d+)¶ß/g, (_, n) => String.fromCodePoint(Number(n)))
    .replaceAll("⁠", "");

export function parseChart(text) {
  const nodes = new Map();
  const regions = [];
  const edges = [];
  const stack = [];
  let title;
  let edgeCount = 0;
  const lines = text.split("\n");
  const front = text.match(/^---\ntitle: (.*)\n---/);
  if (front) title = decode(JSON.parse(front[1]));
  const top = () => stack.at(-1);
  for (const raw of lines) {
    const line = raw.trim();
    let m;
    if ((m = line.match(/^state "(.*)" as (\w+) \{$/))) {
      const parent = top();
      const box = { id: m[2], label: decode(m[1]), parent };
      if (parent?.id === "all") regions.push(box);
      stack.push(box);
    } else if (line === "}") stack.pop();
    else if ((m = line.match(/^(\[\*\]|\w+) --> (\w+)(?:: (.*))?$/))) {
      edges.push({
        id: `edge${edgeCount++}`,
        from: m[1],
        to: m[2],
        label: m[3] ? decode(m[3]) : "",
      });
    } else if ((m = line.match(/^class (\w+) (\w+)$/))) nodes.get(m[1])?.classes.add(m[2]);
    else if ((m = line.match(/^(\w+): (.*)$/)) && top()?.id !== "legend") {
      const path = [];
      const parents = [];
      let region;
      for (let b = top(); b; b = b.parent) {
        if (b.parent?.id === "all") region = b;
        else if (b.id !== "all" && !region) {
          path.unshift(b.label);
          parents.push(b.id);
        }
      }
      path.push(decode(m[2]));
      nodes.set(m[1], { id: m[1], key: path.join(" / "), region: region?.label, parents, classes: new Set() });
    }
  }
  const byKey = new Map();
  for (const n of nodes.values()) byKey.set(`${n.region ?? ""}\u0000${n.key}`, n.id);
  return { title, nodes, regions: regions.map((r) => r.label), edges, byKey };
}

// report.md writes a state as "Region key, Region key" for a regions chart and
// as the bare key otherwise. Labels can contain ", " so try every split.
export function resolveState(chart, s) {
  if (!chart) return null;
  const find = (region, key) => chart.byKey.get(`${region ?? ""}\u0000${key}`);
  if (!chart.regions.length) {
    // A view with one region still prefixes its name ("Count 1"), but the chart draws no region box.
    const id = find(undefined, s) ?? find(undefined, s.slice(s.indexOf(" ") + 1));
    return id ? [id] : null;
  }
  const walk = (rest, i) => {
    const region = chart.regions[i];
    if (!rest.startsWith(`${region} `)) return null;
    const body = rest.slice(region.length + 1);
    if (i === chart.regions.length - 1) {
      const id = find(region, body);
      return id ? [id] : null;
    }
    const sep = `, ${chart.regions[i + 1]} `;
    for (let at = body.indexOf(sep); at >= 0; at = body.indexOf(sep, at + 1)) {
      const id = find(region, body.slice(0, at));
      const tail = id && walk(body.slice(at + 2), i + 1);
      if (tail) return [id, ...tail];
    }
    return null;
  };
  return walk(s, 0);
}

const splitList = (s) => s.split(/,\s*/).filter(Boolean);

export function parseReport(text) {
  const [head, ...sections] = text.split(/^## /m);
  const headLines = head.split("\n").filter((l) => l.trim());
  const report = {
    module: headLines[0]?.replace(/^# /, "") ?? "",
    notes: headLines.slice(1),
    rules: [],
    stopped: undefined,
  };
  const add = (name, status, extra = {}) => report.rules.push({ name, status, ...extra });
  for (const section of sections) {
    const [title, ...body] = section.split("\n");
    const lines = body.filter((l) => l.trim());
    let m;
    if ((m = title.match(/^(.+) breaks$/))) {
      const steps = [];
      let loop;
      let traceFile;
      for (const l of lines) {
        const s = l.match(/^(\d+)\. (.*)$/);
        if (s) steps.push(s[2]);
        else if (/^The run (stops in|stays in|loops through) .* forever\.$/.test(l)) loop = l;
        const f = l.match(/in (tlc-[^ ]+\.out)\./);
        if (f) traceFile = f[1];
      }
      add(m[1], "breaks", { raw: steps, loop, traceFile, offChart: steps.length === 0 });
    } else if (title === "Rules that hold") {
      for (const n of splitList(lines[0] ?? "")) add(n, "holds");
      for (const l of lines.slice(1)) {
        const only = l.match(/^TLC checked (\S+) only in the initial states/);
        const rule = only && report.rules.find((r) => r.name === only[1]);
        if (rule) rule.initialOnly = l;
        else report.notes.push(l);
      }
    } else if (title === "Rules not checked") {
      for (const n of splitList(lines[0] ?? "")) add(n, "not checked");
      const rest = lines.slice(1).join("\n");
      report.notChecked = rest;
      const fence = rest.match(/TLC stopped with exit (\S+?)[ :][\s\S]*?```\n([\s\S]*?)```/);
      if (fence) report.stopped = { status: fence[1], message: fence[2].trim() };
    } else if (title === "TLC stopped") {
      const fence = body.join("\n").match(/exit (\S+?):\s*```\n([\s\S]*?)```/);
      report.stopped = { status: fence?.[1], message: fence?.[2].trim() ?? lines.join("\n") };
    } else report.notes.push(`${title}: ${lines.join(" ")}`);
  }
  return report;
}

// A raw report line is "STEP: STATE" except line 0. Either side can hold ": ",
// so prefer the split whose state the chart knows.
export function splitStep(chart, line, first) {
  if (first) return { step: undefined, state: line };
  const cuts = [];
  for (let at = line.indexOf(": "); at >= 0; at = line.indexOf(": ", at + 1)) cuts.push(at);
  for (const at of cuts) {
    const state = line.slice(at + 2);
    if (resolveState(chart, state)) return { step: line.slice(0, at), state };
  }
  const at = cuts[0] ?? -1;
  return at < 0 ? { step: "", state: line } : { step: line.slice(0, at), state: line.slice(at + 2) };
}

export function parseTlc(text) {
  const lines = text.split("\n");
  const out = { files: [], facts: [], error: undefined, trace: [] };
  let cur;
  for (const line of lines) {
    let m;
    if ((m = line.match(/^Parsing file (.+)$/))) out.files.push(m[1]);
    else if (/^TLC2 Version/.test(line)) out.version = line;
    else if ((m = line.match(/with (\d+) workers? on/))) out.workers = Number(m[1]);
    else if (
      /states generated|depth of the complete|Finished in|Model checking completed|average outdegree/.test(
        line,
      )
    )
      out.facts.push(line);
    else if ((m = line.match(/^Error: (.*)$/))) {
      if (!out.error && !/behavior|counter-example/.test(m[1])) out.error = m[1];
    } else if ((m = line.match(/^State (\d+): (.*)$/))) {
      cur = { n: Number(m[1]), ...action(m[2]), vars: [] };
      out.trace.push(cur);
    } else if (cur && (m = line.match(/^(?:\/\\ )?(\w+) = (.*)$/)) && (!cur.vars.length || line.startsWith("/\\ ")))
      // A spec with one variable prints "x = 0" without the conjunction prefix.
      cur.vars.push([m[1], m[2]]);
    else if (cur && line.trim() && cur.vars.length) cur.vars.at(-1)[1] += `\n${line}`;
    else if (!line.trim()) cur = undefined;
    else if ((m = line.match(/^Back to state (\d+)/))) {
      out.backTo = Number(m[1]);
      out.trace.push({ n: 0, action: line, vars: [] });
    }
  }
  const rule = out.error?.match(/(?:Invariant|Action property) (\S+) is violated/);
  out.rule = rule?.[1];
  out.deadlock = /Deadlock reached/.test(out.error ?? "");
  return out;
}

function action(text) {
  const m = text.match(/^<(\w+) line (\d+), col \d+ to line (\d+), col \d+ of module (\w+)>$/);
  if (m) return { action: m[1], source: { module: m[4], from: Number(m[2]), to: Number(m[3]) } };
  return { action: text.replace(/^<|>$/g, "") };
}

export function parseConfig(text) {
  const sections = {};
  let key;
  for (const raw of text.replace(/\(\*[\s\S]*?\*\)/g, "").replace(/\\\*.*$/gm, "").split("\n")) {
    const line = raw.trim();
    if (!line) continue;
    const m = line.match(/^([A-Z_]+)\b\s*(.*)$/);
    if (m && /^(CONSTANTS?|INIT|NEXT|SPECIFICATION|INVARIANTS?|PROPERT(Y|IES)|CONSTRAINTS?|ACTION_CONSTRAINTS?|VIEW|SYMMETRY|CHECK_DEADLOCK|ALIAS|POSTCONDITION)$/.test(m[1])) {
      key = m[1].replace(/IES$/, "Y").replace(/S$/, "");
      sections[key] ??= [];
      if (m[2]) sections[key].push(m[2]);
    } else if (key) sections[key].push(line);
  }
  const names = (k) => (sections[k] ?? []).flatMap((l) => l.split(/\s+/)).filter(Boolean);
  return { sections, rules: [...names("INVARIANT"), ...names("PROPERTY")] };
}
