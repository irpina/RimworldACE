/* The laboratory viewer's page (docs/48).  Plain JavaScript, hand-rolled
   SVG charts, no framework.  Everything numeric comes from the server; the
   page arranges it and never computes a model quantity of its own, except
   the differences the compare page exists to show. */
"use strict";

const state = {
  scenarios: [],
  parameters: [],
  runs: {},          // key -> run document
  order: [],         // keys in the order they were made
  current: null,     // key shown on Run and Ledgers
  compare: { a: null, b: null, overlay: false },
  chart: { fields: ["price", "inventory"], commodities: null, region: "both" },
  metrics: { reference: null, current: null, filter: "", sort: "name" },
  sensitivity: { ranking: null, parameter: null, detail: null },
  docs: { list: [], current: null },
};

const COMMODITY_COLORS = {
  yayo: "#7b2cbf", psychoid_leaves: "#2d6a4f", chemfuel: "#e76f51",
  meals: "#d4a017", garments: "#457b9d", herbal_medicine: "#06a77d",
  steel: "#6c757d", wood: "#8d5524", components: "#1d3557",
};
const REGION_COLORS = { "Dust Basin": "#b5651d", "Green River": "#2a9d8f" };
const FIELD_UNITS = {
  price: "silver", inventory: "units", unmet: "units", capacity: "units/day",
  cost_ratio: "ratio", cash: "silver", worker_cash: "silver",
  employment: "worker-days", wage_rate: "silver/worker-day", wage_premium: "fraction",
  habitual_scale: "ratio", premium_over_value: "fraction",
  remaining: "units", marginal_cost: "silver", labor_value: "work-ticks",
};
const PER_COMMODITY_FIELDS = ["price", "inventory", "unmet", "capacity", "cost_ratio"];
const REGIONAL_FIELDS = ["employment", "wage_rate", "wage_premium", "habitual_scale", "premium_over_value", "cash", "worker_cash"];

// ------------------------------------------------------------------ utils
const $ = (selector, root = document) => root.querySelector(selector);
const el = (tag, attrs = {}, children = []) => {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k === "html") node.innerHTML = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else if (v !== null && v !== undefined) node.setAttribute(k, v);
  }
  for (const child of [].concat(children)) {
    if (child === null || child === undefined) continue;
    node.append(child.nodeType ? child : document.createTextNode(String(child)));
  }
  return node;
};
const esc = (text) => String(text).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function fmt(value, digits) {
  if (value === null || value === undefined) return "—";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value !== "number") return String(value);
  if (!isFinite(value)) return value > 0 ? "∞" : "-∞";
  if (Number.isInteger(value) && Math.abs(value) < 1e12) return value.toLocaleString("en-US");
  const magnitude = Math.abs(value);
  if (digits !== undefined) return value.toFixed(digits);
  if (magnitude >= 1e6) return value.toExponential(3);
  if (magnitude >= 1000) return value.toLocaleString("en-US", { maximumFractionDigits: 1 });
  if (magnitude >= 1) return value.toFixed(4);
  if (magnitude >= 1e-4) return value.toPrecision(4);
  if (magnitude === 0) return "0";
  return value.toExponential(2);
}
function fmtPct(a, b) {
  if (a === null || b === null || typeof a !== "number" || typeof b !== "number") return "—";
  if (a === 0) return b === 0 ? "0%" : "n/a";
  const pct = (b - a) / Math.abs(a) * 100;
  return (pct > 0 ? "+" : "") + pct.toFixed(3) + "%";
}
function signed(value) {
  if (value === null || value === undefined) return "—";
  const text = fmt(value);
  return value > 0 ? "+" + text : text;
}
function signClass(value) {
  if (typeof value !== "number" || value === 0) return "";
  return value > 0 ? "pos" : "neg";
}

async function api(path, body) {
  const options = body === undefined ? {} : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  };
  const response = await fetch(path, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || response.statusText);
  return payload;
}

function runLabel(doc) {
  const parts = [doc.scenario];
  for (const [k, v] of Object.entries(doc.options || {})) parts.push(`${k}=${fmt(v)}`);
  for (const [k, v] of Object.entries(doc.overrides || {})) parts.push(`${k}→${fmt(v)}`);
  return parts.join(" · ");
}

// ------------------------------------------------------------------ charts
function niceTicks(lo, hi, count) {
  if (!(hi > lo)) { hi = lo + 1; lo = lo - 1; }
  const span = hi - lo;
  const rough = span / count;
  const power = Math.pow(10, Math.floor(Math.log10(rough)));
  const candidates = [1, 2, 2.5, 5, 10].map((m) => m * power);
  const step = candidates.find((c) => c >= rough) || candidates[candidates.length - 1];
  const start = Math.ceil(lo / step) * step;
  const ticks = [];
  for (let v = start; v <= hi + step * 1e-9; v += step) ticks.push(+v.toFixed(12));
  return ticks;
}

function lineChart({ title, unit, days, series, shockDay, zeroLine }) {
  const W = 560, H = 230, L = 58, R = 12, T = 10, B = 28;
  const plotW = W - L - R, plotH = H - T - B;
  const values = [];
  for (const s of series) for (const v of s.values) if (typeof v === "number" && isFinite(v)) values.push(v);
  let lo = values.length ? Math.min(...values) : 0;
  let hi = values.length ? Math.max(...values) : 1;
  if (zeroLine) { lo = Math.min(lo, 0); hi = Math.max(hi, 0); }
  if (hi === lo) { hi = lo + Math.abs(lo || 1) * 0.05; lo = lo - Math.abs(lo || 1) * 0.05; }
  const pad = (hi - lo) * 0.06;
  lo -= pad; hi += pad;
  const dayMin = days[0], dayMax = days[days.length - 1];
  const x = (day) => L + (dayMax === dayMin ? 0 : (day - dayMin) / (dayMax - dayMin) * plotW);
  const y = (v) => T + (hi - v) / (hi - lo) * plotH;

  let svg = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" class="plot">`;
  for (const tick of niceTicks(lo, hi, 5)) {
    const yy = y(tick);
    svg += `<line x1="${L}" x2="${W - R}" y1="${yy}" y2="${yy}" stroke="#eceff3"/>`;
    svg += `<text x="${L - 6}" y="${yy + 3.5}" font-size="10" text-anchor="end" fill="#667085">${esc(fmtTick(tick))}</text>`;
  }
  for (const tick of niceTicks(dayMin, dayMax, 7)) {
    const xx = x(tick);
    svg += `<line x1="${xx}" x2="${xx}" y1="${T}" y2="${H - B}" stroke="#eceff3"/>`;
    svg += `<text x="${xx}" y="${H - B + 14}" font-size="10" text-anchor="middle" fill="#667085">${tick}</text>`;
  }
  if (zeroLine && lo < 0 && hi > 0) svg += `<line x1="${L}" x2="${W - R}" y1="${y(0)}" y2="${y(0)}" stroke="#98a2b3" stroke-dasharray="3 3"/>`;
  if (shockDay !== null && shockDay !== undefined && shockDay >= dayMin && shockDay <= dayMax) {
    svg += `<line x1="${x(shockDay)}" x2="${x(shockDay)}" y1="${T}" y2="${H - B}" stroke="#b42318" stroke-width="1.2" stroke-dasharray="5 3"/>`;
    svg += `<text x="${x(shockDay) + 3}" y="${T + 10}" font-size="10" fill="#b42318">day ${shockDay}</text>`;
  }
  for (const s of series) {
    let d = "", pen = false;
    for (let i = 0; i < days.length; i++) {
      const v = s.values[i];
      if (typeof v !== "number" || !isFinite(v)) { pen = false; continue; }
      d += (pen ? "L" : "M") + x(days[i]).toFixed(2) + " " + y(v).toFixed(2);
      pen = true;
    }
    svg += `<path d="${d}" fill="none" stroke="${s.color}" stroke-width="${s.width || 1.6}" ${s.dashed ? 'stroke-dasharray="4 3"' : ""} vector-effect="non-scaling-stroke"/>`;
  }
  svg += `<line class="cursor" x1="0" x2="0" y1="${T}" y2="${H - B}" stroke="#1f2328" stroke-width="1" visibility="hidden"/>`;
  svg += `<rect class="hit" x="${L}" y="${T}" width="${plotW}" height="${plotH}" fill="transparent"/>`;
  svg += "</svg>";

  const node = el("div", { class: "chart" });
  node.innerHTML = `<div class="title"><span>${esc(title)}</span><span class="unit">${esc(unit || "")}</span></div>${svg}<div class="readout"></div>`;
  const legend = el("div", { class: "legend" });
  for (const s of series) {
    const item = el("span");
    item.innerHTML = `<i class="swatch" style="background:${s.color}"></i>${esc(s.label)}`;
    legend.append(item);
  }
  node.append(legend);

  const svgNode = node.querySelector("svg");
  const cursor = svgNode.querySelector(".cursor");
  const readout = node.querySelector(".readout");
  svgNode.addEventListener("mousemove", (event) => {
    const rect = svgNode.getBoundingClientRect();
    const px = (event.clientX - rect.left) / rect.width * W;
    if (px < L || px > W - R) return;
    const day = dayMin + (px - L) / plotW * (dayMax - dayMin);
    let index = 0, best = Infinity;
    for (let i = 0; i < days.length; i++) { const dd = Math.abs(days[i] - day); if (dd < best) { best = dd; index = i; } }
    const xx = x(days[index]);
    cursor.setAttribute("x1", xx); cursor.setAttribute("x2", xx); cursor.setAttribute("visibility", "visible");
    readout.textContent = `day ${days[index]}: ` + series.map((s) => `${s.label} ${fmt(s.values[index])}`).join("  ");
  });
  svgNode.addEventListener("mouseleave", () => { cursor.setAttribute("visibility", "hidden"); readout.textContent = ""; });
  return node;
}
function fmtTick(v) {
  const a = Math.abs(v);
  if (a >= 1e6) return v.toExponential(1);
  if (a >= 100) return v.toFixed(0);
  if (a >= 1) return +v.toFixed(2);
  return +v.toPrecision(3);
}

// ------------------------------------------------------------------ tables
function table(columns, rows, options = {}) {
  const wrap = el("div", { class: options.scroll ? "tablewrap" : "scroll" });
  const t = el("table", { class: "data" });
  const head = el("tr");
  for (const c of columns) head.append(el("th", { class: c.num ? "num" : "" }, c.label));
  t.append(el("thead", {}, head));
  const body = el("tbody");
  for (const row of rows) {
    const tr = el("tr", { class: row._class || "" });
    for (const c of columns) {
      const value = row[c.key];
      const cell = el("td", { class: (c.num ? "num " : "") + (c.name ? "name " : "") + (c.sign ? signClass(value) : "") });
      cell.textContent = c.format ? c.format(value, row) : (c.num ? fmt(value) : (value ?? "—"));
      tr.append(cell);
    }
    if (row._onclick) { tr.classList.add("clickable"); tr.addEventListener("click", row._onclick); }
    body.append(tr);
  }
  t.append(body);
  wrap.append(t);
  return wrap;
}

function kv(pairs) {
  const dl = el("dl", { class: "kv" });
  for (const [k, v] of pairs) { dl.append(el("dt", {}, k)); dl.append(el("dd", {}, typeof v === "string" ? v : fmt(v))); }
  return dl;
}

function nestedTable(value) {
  if (value === null || typeof value !== "object") return el("span", { class: "mono" }, fmt(value));
  if (Array.isArray(value)) return el("span", { class: "mono" }, value.length ? value.map((v) => fmt(v)).join(", ") : "—");
  const entries = Object.entries(value);
  const scalarRows = entries.filter(([, v]) => v === null || typeof v !== "object");
  const nested = entries.filter(([, v]) => v !== null && typeof v === "object" && !Array.isArray(v));
  const arrays = entries.filter(([, v]) => Array.isArray(v));
  const box = el("div");
  if (scalarRows.length) box.append(kv(scalarRows.map(([k, v]) => [k, v])));
  for (const [k, v] of arrays) box.append(kv([[k, v.length ? v.map((x) => fmt(x)).join(", ") : "—"]]));
  for (const [k, v] of nested) {
    const values = Object.values(v);
    const allObjects = values.length && values.every((x) => x && typeof x === "object" && !Array.isArray(x));
    const uniform = allObjects && values.every((x) => JSON.stringify(Object.keys(x)) === JSON.stringify(Object.keys(values[0])));
    box.append(el("h4", {}, k));
    if (uniform && Object.values(values[0]).every((x) => x === null || typeof x !== "object")) {
      const columns = [{ key: "_name", label: "", name: true }].concat(Object.keys(values[0]).map((c) => ({ key: c, label: c, num: true })));
      box.append(table(columns, Object.entries(v).map(([name, row]) => ({ _name: name, ...row }))));
    } else {
      box.append(el("div", { class: "nested" }, nestedTable(v)));
    }
  }
  return box;
}

// ------------------------------------------------------------------ routing
function route() {
  const hash = location.hash || "#run";
  const [page, arg] = hash.slice(1).split("/");
  const target = page === "doc" ? "docs" : page;
  for (const a of document.querySelectorAll(".tabs a")) a.classList.toggle("active", a.dataset.page === target);
  for (const p of document.querySelectorAll(".page")) p.classList.toggle("active", p.id === "page-" + target);
  if (page === "doc" && arg) showDoc(parseInt(arg, 10));
  if (target === "ledgers") renderLedgers();
  if (target === "compare") renderCompare();
  if (target === "metrics") renderMetrics();
  if (target === "sensitivity") renderSensitivity();
  if (target === "docs") renderDocList();
}
window.addEventListener("hashchange", route);

// ------------------------------------------------------------------ run page
function scenarioByName(name) { return state.scenarios.find((s) => s.name === name); }

function renderScenarioForm() {
  const scenario = scenarioByName($("#scenario-select").value);
  $("#scenario-description").textContent = scenario.description;
  const docs = $("#scenario-docs");
  docs.innerHTML = "";
  docs.append("Documents: ");
  for (const n of scenario.docs) docs.append(el("a", { href: `#doc/${n}` }, `docs/${String(n).padStart(2, "0")}`));
  if (scenario.mentioned_in.length) {
    docs.append(el("span", { class: "muted small" }, " also mentioned in "));
    for (const n of scenario.mentioned_in) docs.append(el("a", { href: `#doc/${n}`, class: "small" }, `${n}`), " ");
  }
  const form = $("#scenario-options");
  form.innerHTML = "";
  if (!scenario.options.length) form.append(el("span", { class: "muted small" }, "none"));
  for (const option of scenario.options) {
    form.append(el("label", { title: option.name }, option.name));
    const base = option.type.replace("?", "");
    let input;
    if (base === "bool") {
      input = el("select", { "data-option": option.name });
      input.append(el("option", { value: "false" }, "false"), el("option", { value: "true" }, "true"));
      input.value = option.default ? "true" : "false";
    } else {
      input = el("input", { type: "text", "data-option": option.name, placeholder: option.default === null ? "default" : fmt(option.default) });
    }
    form.append(input);
  }
  const button = $("#run-button");
  button.textContent = scenario.cost === "slow" ? `Run (slow, about ${scenario.seconds.toFixed(0)} s)` : "Run";
  button.classList.toggle("slow", scenario.cost === "slow");
  const status = $("#run-status");
  status.className = "status";
  status.textContent = scenario.cost === "slow"
    ? `${scenario.name} runs ${scenario.name === "capacity_exit" ? "4,000 days" : "several economies"} and is cached once made.`
    : "";
}

function renderParameterForm() {
  const form = $("#parameter-form");
  form.innerHTML = "";
  const groups = new Map();
  for (const p of state.parameters) {
    if (!groups.has(p.group)) groups.set(p.group, []);
    groups.get(p.group).push(p);
  }
  for (const [group, params] of groups) {
    const details = el("details", {}, el("summary", {}, `${group} (${params.length})`));
    for (const p of params) {
      const row = el("div", { class: "row", "data-name": p.name });
      row.append(el("label", { title: `${p.name}: default ${fmt(p.default)} (${p.type})` }, p.name));
      const input = el("input", { type: "text", "data-param": p.name, "data-type": p.type, placeholder: fmt(p.default) });
      input.addEventListener("input", () => row.classList.toggle("set", input.value.trim() !== ""));
      row.append(input);
      details.append(row);
    }
    form.append(details);
  }
}

function filterParameters() {
  const needle = $("#parameter-filter").value.trim().toLowerCase();
  for (const details of document.querySelectorAll("#parameter-form details")) {
    let visible = 0;
    for (const row of details.querySelectorAll(".row")) {
      const show = !needle || row.dataset.name.includes(needle);
      row.classList.toggle("hidden", !show);
      if (show) visible++;
    }
    details.style.display = visible ? "" : "none";
    if (needle) details.open = true;
  }
}

function collectRequest() {
  const scenario = $("#scenario-select").value;
  const options = {};
  for (const input of document.querySelectorAll("#scenario-options [data-option]")) {
    const value = input.value.trim();
    if (value !== "") options[input.dataset.option] = value;
  }
  const overrides = {};
  for (const input of document.querySelectorAll("#parameter-form [data-param]")) {
    const value = input.value.trim();
    if (value !== "") overrides[input.dataset.param] = value;
  }
  return { scenario, options, overrides };
}

async function runScenario() {
  const request = collectRequest();
  const status = $("#run-status");
  const button = $("#run-button");
  status.className = "status busy";
  status.textContent = `Running ${request.scenario}…`;
  button.disabled = true;
  try {
    const doc = await api("/api/run", request);
    if (!state.runs[doc.key]) state.order.push(doc.key);
    state.runs[doc.key] = doc;
    state.current = doc.key;
    status.className = "status";
    status.textContent = `Done in ${doc.elapsed_seconds} s (key ${doc.key}).`;
    renderRunList();
    renderRunView();
  } catch (error) {
    status.className = "status error";
    status.textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

function renderRunList() {
  const list = $("#run-list");
  list.innerHTML = "";
  if (!state.order.length) list.append(el("li", { class: "muted" }, "none yet"));
  for (const key of [...state.order].reverse()) {
    const doc = state.runs[key];
    const item = el("li", { class: key === state.current ? "current" : "" });
    item.append(el("div", {}, runLabel(doc)));
    item.append(el("div", { class: "key" }, `${key}${doc.days ? ` · ${doc.days[doc.days.length - 1]} days` : ""}`));
    item.addEventListener("click", () => { state.current = key; renderRunList(); renderRunView(); });
    list.append(item);
  }
}

function commodityChips(commodities, selected, onChange) {
  const bar = el("div", { class: "toolbar" });
  bar.append(el("span", { class: "muted" }, "commodities:"));
  for (const c of commodities) {
    const box = el("input", { type: "checkbox" });
    box.checked = selected.has(c);
    box.addEventListener("change", () => { if (box.checked) selected.add(c); else selected.delete(c); onChange(); });
    bar.append(el("label", { class: "chip" }, [box, el("span", { class: "sw", style: `background:${COMMODITY_COLORS[c] || "#333"}` }), c]));
  }
  return bar;
}

function renderRunView() {
  const view = $("#run-view");
  view.innerHTML = "";
  const doc = state.runs[state.current];
  if (!doc) { view.append(el("div", { class: "empty" }, "Choose a scenario and press Run.")); return; }
  const scenario = scenarioByName(doc.scenario);

  const head = el("div", { class: "card" });
  head.append(el("div", { class: "head" }, [
    el("h2", {}, doc.scenario),
    el("span", { class: "badge" }, `key ${doc.key}`),
    doc.kind === "run" ? el("span", { class: "badge" }, `${doc.days[doc.days.length - 1]} days`) : null,
    doc.shock_day !== null && doc.shock_day !== undefined ? el("span", { class: "badge" }, `shock day ${doc.shock_day}`) : null,
    el("span", { class: "badge" }, `${doc.elapsed_seconds} s`),
  ]));
  const requestLine = [];
  for (const [k, v] of Object.entries(doc.options)) requestLine.push(`${k} = ${fmt(v)}`);
  for (const [k, v] of Object.entries(doc.overrides)) requestLine.push(`${k} → ${fmt(v)} (override)`);
  head.append(el("p", { class: "note" }, requestLine.length ? requestLine.join("; ") : "defaults throughout"));
  head.append(el("p", { class: "note" }, [
    "Documents: ",
    ...scenario.docs.map((n) => el("a", { href: `#doc/${n}`, style: "margin-right:8px" }, `docs/${String(n).padStart(2, "0")}`)),
    " · ", el("a", { href: "#ledgers" }, "ledgers for this run"),
  ]));
  view.append(head);

  if (doc.kind === "sweep") {
    const card = el("div", { class: "card sweep-table" });
    card.append(el("h2", {}, "Sweep"));
    const columns = doc.sweep.columns.map((c, i) => ({ key: c, label: c, num: i > 0, name: i === 0 }));
    card.append(table(columns, doc.sweep.rows));
    view.append(card);
    return;
  }

  if (!state.chart.commodities) state.chart.commodities = new Set(doc.commodities);
  const selected = state.chart.commodities;
  for (const c of doc.commodities) if (!Object.prototype.hasOwnProperty.call(COMMODITY_COLORS, c)) COMMODITY_COLORS[c] = "#333";

  const controls = el("div", { class: "card" });
  const fieldBar = el("div", { class: "toolbar" });
  fieldBar.append(el("span", { class: "muted" }, "per-commodity fields:"));
  for (const f of PER_COMMODITY_FIELDS) {
    const box = el("input", { type: "checkbox" });
    box.checked = state.chart.fields.includes(f);
    box.addEventListener("change", () => {
      state.chart.fields = PER_COMMODITY_FIELDS.filter((x) => x === f ? box.checked : state.chart.fields.includes(x));
      renderRunView();
    });
    fieldBar.append(el("label", { class: "chip" }, [box, f]));
  }
  const regionSelect = el("select");
  for (const r of ["both", ...doc.region_names]) regionSelect.append(el("option", { value: r }, r));
  regionSelect.value = state.chart.region;
  regionSelect.addEventListener("change", () => { state.chart.region = regionSelect.value; renderRunView(); });
  fieldBar.append(el("label", {}, ["region: ", regionSelect]));
  controls.append(fieldBar);
  controls.append(commodityChips(doc.commodities, selected, renderRunView));
  view.append(controls);

  const regions = state.chart.region === "both" ? doc.region_names : [state.chart.region];
  const charts = el("div", { class: "charts" });
  for (const field of state.chart.fields) {
    for (const region of regions) {
      const series = doc.commodities.filter((c) => selected.has(c)).map((c) => ({
        label: c, color: COMMODITY_COLORS[c], values: doc.regions[region][field][c],
      }));
      charts.append(lineChart({ title: `${field} · ${region}`, unit: FIELD_UNITS[field], days: doc.days, series, shockDay: doc.shock_day }));
    }
  }
  for (const field of REGIONAL_FIELDS) {
    const series = doc.region_names.map((r) => ({ label: r, color: REGION_COLORS[r] || "#333", values: doc.regions[r][field] }));
    charts.append(lineChart({ title: field, unit: FIELD_UNITS[field], days: doc.days, series, shockDay: doc.shock_day, zeroLine: field === "wage_premium" || field === "premium_over_value" }));
  }
  for (const region of doc.region_names) {
    for (const [commodity, reserve] of Object.entries(doc.regions[region].reserves)) {
      for (const part of ["remaining", "marginal_cost"]) {
        charts.append(lineChart({
          title: `reserve ${part} · ${commodity} · ${region}`, unit: FIELD_UNITS[part], days: doc.days,
          series: [{ label: commodity, color: COMMODITY_COLORS[commodity], values: reserve[part] }], shockDay: doc.shock_day,
        }));
      }
    }
  }
  charts.append(lineChart({
    title: "social labor value", unit: "work-ticks per unit", days: doc.days, shockDay: doc.shock_day,
    series: doc.commodities.filter((c) => selected.has(c)).map((c) => ({ label: c, color: COMMODITY_COLORS[c], values: doc.labor_values[c] })),
  }));
  view.append(charts);

  const summary = el("div", { class: "card" });
  summary.append(el("h2", {}, "End-state summary"));
  summary.append(el("p", { class: "note" }, "What `python -m economy_lab` prints, arranged. Residuals are the three closing identities; the value ledger is in work-ticks and the price decomposition in silver."));
  summary.append(nestedTable(doc.summary));
  const raw = el("details", { class: "raw" }, el("summary", {}, "raw JSON"));
  raw.append(el("pre", { class: "json" }, JSON.stringify(doc.summary, null, 2)));
  summary.append(raw);
  view.append(summary);
}

// ------------------------------------------------------------------ ledgers
function ledgerCard(kind, title, unit, rule) {
  const card = el("div", { class: `card ledger ${kind}` });
  card.append(el("div", { class: "head" }, [el("h2", {}, title), el("span", { class: "badge unit" }, unit)]));
  if (rule) card.append(el("p", { class: "rule" }, rule));
  return card;
}

function renderLedgers() {
  const view = $("#ledgers-view");
  view.innerHTML = "";
  const doc = state.runs[state.current];
  if (!doc || doc.kind !== "run") { view.append(el("div", { class: "empty" }, "Run a scenario first; the ledgers page reads the current run.")); return; }
  const L = doc.ledgers;
  view.append(el("div", { class: "card" }, [
    el("div", { class: "head" }, [el("h2", {}, `Ledgers · ${runLabel(doc)}`), el("span", { class: "badge" }, `day ${doc.days[doc.days.length - 1]}`)]),
    el("p", { class: "note" }, "Five concepts, five panels, each in its own unit. Nothing here is a sum across panels: labor value is not price, price of production is a ratio, surplus value is in work-ticks, and the money margin in the price panel is not surplus value."),
  ]));
  const grid = el("div", { class: "ledgers-grid" });

  // --- labor value
  const labor = ledgerCard("labor", "Labor value", L.labor_value.unit, "Socially necessary labor embodied per unit. The social value is output-weighted across regions; each region's individual value is beside it (average versus marginal conditions, HANDOFF). The authored figure is FINDINGS.md's, converted at the model's silver-per-tick scale.");
  const commodities = Object.keys(L.labor_value.social);
  const regions = Object.keys(L.labor_value.individual);
  labor.append(table(
    [{ key: "c", label: "commodity", name: true }, { key: "social", label: "social value", num: true },
      ...regions.map((r) => ({ key: "r:" + r, label: r, num: true })), { key: "authored", label: "authored (FINDINGS)", num: true }],
    commodities.map((c) => {
      const row = { c, social: L.labor_value.social[c], authored: L.labor_value.authored_silver[c] / L.labor_value.silver_per_tick };
      for (const r of regions) row["r:" + r] = L.labor_value.individual[r][c] ?? null;
      if (L.labor_value.stale.includes(c)) row._class = "moved";
      return row;
    }),
  ));
  if (L.labor_value.stale.length) labor.append(el("p", { class: "warn" }, `Stale (the solve did not converge for): ${L.labor_value.stale.join(", ")}`));
  grid.append(labor);

  // --- market price
  const price = ledgerCard("price", "Market price", L.market_price.unit, "The current regional price and what the model can attribute of it. The margin is the wedge between RimWorld's authored level and inputs + wages + capital consumed (docs/23); it is reported, not explained, and it is money, not surplus value.");
  for (const r of regions) {
    const entry = L.market_price.regions[r];
    price.append(el("h4", {}, r));
    price.append(table(
      [{ key: "c", label: "commodity", name: true }, { key: "price", label: "price", num: true }, { key: "inputs", label: "inputs", num: true },
        { key: "wages", label: "wages", num: true }, { key: "capital_consumed", label: "capital consumed", num: true },
        { key: "margin", label: "unattributed margin", num: true }, { key: "surplus_if_margin_is_cost", label: "money surplus if margin is cost", num: true },
        { key: "surplus_if_margin_is_surplus", label: "money surplus if margin is surplus", num: true }],
      commodities.map((c) => ({ c, price: entry.prices[c], ...(entry.decomposition[c] || {}) })),
    ));
    price.append(kv([["wages paid", entry.wages_paid], ["of which premium over the basket", entry.wage_premium_paid], ["workers' basket spending", entry.worker_spending],
      ["fixed capital consumed (silver)", entry.fixed_capital_money], ["unattributed margin accumulated", entry.unattributed_margin]]));
  }
  price.append(kv([["investment spending", L.market_price.investment_spending], ["freight paid", L.market_price.transport_cash]]));
  grid.append(price);

  // --- prices of production
  const P = L.price_of_production;
  const production = ledgerCard("production", "Price of production", P.unit, "The classical price system (docs/26): every sector earns the same rate on its advances, with the basket folded into the input matrix and fixed capital inside since docs/37. Computed beside the authored prices and never adopted by them. The eigenvector fixes ratios only, so the table is relative to meals.");
  if (!P.report) production.append(el("p", { class: "note" }, "Undefined for this run."));
  else {
    production.append(kv([["profit rate (per day, on advances)", P.report.profit_rate], ["gross markup", P.labor_value_numeraire.gross_markup],
      ["fixed capital share of the advance", P.labor_value_numeraire.fixed_capital_share], ["basics", P.report.basics.join(", ") || "none"],
      ["wage per tick (meals numeraire)", P.report.wage_per_tick], ["iterations", P.report.iterations],
      ["total profit / total surplus (labor-value normalization)", P.report.profit_over_surplus]]));
    production.append(table(
      [{ key: "c", label: "commodity", name: true }, { key: "labor_value", label: "labor value", num: true }, { key: "price_of_production", label: "price of production", num: true },
        { key: "authored_price", label: "authored price", num: true }, { key: "turnover", label: "turnover days", num: true }],
      Object.entries(P.report.relative_to_meals).map(([c, row]) => ({ c, ...row, turnover: P.labor_value_numeraire.turnover_days[c] })),
    ));
    production.append(el("h4", {}, "aggregates (labor-value normalization, work-ticks)"));
    production.append(kv(Object.entries(P.report.aggregates)));
  }
  grid.append(production);

  // --- surplus value
  const S = L.surplus_value;
  const surplus = ledgerCard("surplus", "Surplus value", S.unit, "Living labor beyond the value of labor-power, in work-ticks (docs/17, docs/23). c is inputs at their social values plus plant worn out; v is the basket at value; s is what remains of the living labor. The realized rate reads wages as paid (docs/46). None of these is money.");
  surplus.append(kv([["constant capital c", S.total.constant_capital], ["  circulating", S.total.circulating_capital], ["  fixed, consumed", S.total.fixed_capital_consumed],
    ["variable capital v", S.total.variable_capital], ["surplus labor s", S.total.surplus_labor], ["organic composition c/v", S.total.organic_composition],
    ["value rate of profit s/(c+v)", S.total.value_rate_of_profit], ["rate of profit on advances (per day)", S.rate_of_profit_on_advances], ["realized turnover (days)", S.realized_turnover_days]]));
  surplus.append(table(
    [{ key: "r", label: "region", name: true }, { key: "living_labor", label: "living", num: true }, { key: "necessary_labor", label: "necessary v", num: true },
      { key: "surplus_labor", label: "surplus s", num: true }, { key: "wage_deviation_labor", label: "wage deviation", num: true },
      { key: "value_of_labor_power", label: "value of labor-power / day", num: true }, { key: "habitual_scale", label: "habitual scale", num: true },
      { key: "rate_of_surplus_value", label: "s/v", num: true }, { key: "realized_rate_of_surplus_value", label: "realized s/v", num: true },
      { key: "organic_composition", label: "c/v", num: true }, { key: "value_rate_of_profit", label: "s/(c+v)", num: true }],
    regions.map((r) => ({ r, ...S.regions[r] })),
  ));
  surplus.append(el("h4", {}, "capital advanced (work-ticks)"));
  surplus.append(kv(Object.entries(S.capital_advanced)));
  surplus.append(el("h4", {}, "per sector"));
  surplus.append(table(
    [{ key: "c", label: "commodity", name: true }, { key: "occ", label: "organic composition c/v", num: true }, { key: "dev", label: "price of production − value (labor-value numeraire)", num: true, sign: true }],
    commodities.map((c) => ({ c, occ: S.sector_organic_composition[c] ?? null, dev: S.price_value_deviation ? S.price_value_deviation[c] ?? null : null })),
  ));
  grid.append(surplus);

  // --- rent
  const Rn = L.rent;
  const rent = ledgerCard("rent", "Rent", "silver · work-ticks per day", "Differential rent is the cost advantage of infra-marginal extractors over the most expensive active one, accumulated in silver (docs/15). The absolute rent bound is the most landed property could withhold per day, in work-ticks: value minus price of production where positive, and only where a reserve gives a landlord (docs/42). A bound, not a payment.");
  rent.append(el("h4", {}, "differential rent, accumulated (silver)"));
  rent.append(kv(Object.entries(Rn.differential_rent.by_commodity).length ? Object.entries(Rn.differential_rent.by_commodity) : [["none", "—"]]));
  rent.append(el("h4", {}, "absolute rent bound, per day (work-ticks)"));
  rent.append(kv(Rn.absolute_rent_bound.by_commodity ? Object.entries(Rn.absolute_rent_bound.by_commodity) : [["undefined", "—"]]));
  rent.append(el("h4", {}, "reserves"));
  for (const r of regions) {
    for (const [c, reserve] of Object.entries(Rn.reserves[r])) {
      rent.append(el("p", { class: "note" }, `${r} · ${c}: remaining ${fmt(reserve.remaining)} units, marginal cost ${fmt(reserve.marginal_cost)} silver; grades ${reserve.grades.map((g) => `${fmt(g.quantity)} @ ${fmt(g.extraction_cost)}`).join(", ")}`));
    }
  }
  grid.append(rent);
  view.append(grid);
}

// ------------------------------------------------------------------ compare
function runSelect(which) {
  const select = el("select");
  select.append(el("option", { value: "" }, "— choose a run —"));
  for (const key of state.order) {
    const doc = state.runs[key];
    if (doc.kind !== "run") continue;
    select.append(el("option", { value: key }, `${runLabel(doc)} [${key}]`));
  }
  select.value = state.compare[which] || "";
  select.addEventListener("change", () => { state.compare[which] = select.value || null; renderCompare(); });
  return select;
}

function diffRows(labels, a, b) {
  return labels.map(([label, va, vb]) => {
    const delta = (typeof va === "number" && typeof vb === "number") ? vb - va : null;
    const pct = (typeof va === "number" && va !== 0 && delta !== null) ? delta / Math.abs(va) * 100 : null;
    return { label, a: va, b: vb, delta, pct: fmtPct(va, vb), _class: pct === null ? (delta ? "moved" : "") : Math.abs(pct) >= 1 ? "big" : Math.abs(pct) >= 0.01 ? "moved" : "" };
  });
}
const DIFF_COLUMNS = [{ key: "label", label: "", name: true }, { key: "a", label: "A", num: true }, { key: "b", label: "B", num: true }, { key: "delta", label: "B − A", num: true, sign: true, format: (v) => signed(v) }, { key: "pct", label: "Δ %", num: true }];

function renderCompare() {
  const view = $("#compare-view");
  view.innerHTML = "";
  const head = el("div", { class: "card" });
  head.append(el("h2", {}, "Compare two runs"));
  head.append(el("p", { class: "note" }, "Differences, not overlays: every series is B − A and every figure is a row of A, B, delta. Rows that moved by 0.01% or more are shaded; by 1% or more, red. Make the runs on the Run page first."));
  const bar = el("div", { class: "toolbar" });
  bar.append(el("label", {}, ["A: ", runSelect("a")]), el("label", {}, ["B: ", runSelect("b")]));
  const overlay = el("input", { type: "checkbox" });
  overlay.checked = state.compare.overlay;
  overlay.addEventListener("change", () => { state.compare.overlay = overlay.checked; renderCompare(); });
  bar.append(el("label", { class: "chip" }, [overlay, "overlay A (dashed) and B instead of the difference"]));
  head.append(bar);
  view.append(head);

  const A = state.runs[state.compare.a], B = state.runs[state.compare.b];
  if (!A || !B) { view.append(el("div", { class: "empty" }, "Choose runs A and B.")); return; }
  if (A.scenario !== B.scenario) view.append(el("p", { class: "warn" }, `A is ${A.scenario} and B is ${B.scenario}; the comparison is meaningful only where they share a shock and a day count.`));

  const commodities = A.commodities.filter((c) => B.commodities.includes(c));
  const dayIndex = new Map(B.days.map((d, i) => [d, i]));
  const days = A.days.filter((d) => dayIndex.has(d));
  const aIndex = new Map(A.days.map((d, i) => [d, i]));
  const align = (seriesA, seriesB) => ({
    a: days.map((d) => seriesA[aIndex.get(d)]),
    b: days.map((d) => seriesB[dayIndex.get(d)]),
  });
  const diff = (sa, sb) => { const { a, b } = align(sa, sb); return a.map((v, i) => (typeof v === "number" && typeof b[i] === "number") ? b[i] - v : null); };
  if (!state.chart.commodities) state.chart.commodities = new Set(commodities);
  const selected = state.chart.commodities;
  const controls = el("div", { class: "card" });
  controls.append(commodityChips(commodities, selected, renderCompare));
  view.append(controls);

  const charts = el("div", { class: "charts" });
  const shock = A.shock_day ?? B.shock_day;
  for (const field of PER_COMMODITY_FIELDS) {
    for (const region of A.region_names.filter((r) => B.region_names.includes(r))) {
      const series = [];
      for (const c of commodities) {
        if (!selected.has(c)) continue;
        if (state.compare.overlay) {
          const { a, b } = align(A.regions[region][field][c], B.regions[region][field][c]);
          series.push({ label: `${c} A`, color: COMMODITY_COLORS[c], values: a, dashed: true, width: 1.2 });
          series.push({ label: `${c} B`, color: COMMODITY_COLORS[c], values: b });
        } else {
          series.push({ label: c, color: COMMODITY_COLORS[c], values: diff(A.regions[region][field][c], B.regions[region][field][c]) });
        }
      }
      charts.append(lineChart({ title: `${state.compare.overlay ? "" : "Δ "}${field} · ${region}`, unit: FIELD_UNITS[field], days, series, shockDay: shock, zeroLine: !state.compare.overlay }));
    }
  }
  for (const field of REGIONAL_FIELDS) {
    const series = [];
    for (const r of A.region_names.filter((x) => B.region_names.includes(x))) {
      if (state.compare.overlay) {
        const { a, b } = align(A.regions[r][field], B.regions[r][field]);
        series.push({ label: `${r} A`, color: REGION_COLORS[r], values: a, dashed: true, width: 1.2 });
        series.push({ label: `${r} B`, color: REGION_COLORS[r], values: b });
      } else series.push({ label: r, color: REGION_COLORS[r], values: diff(A.regions[r][field], B.regions[r][field]) });
    }
    charts.append(lineChart({ title: `${state.compare.overlay ? "" : "Δ "}${field}`, unit: FIELD_UNITS[field], days, series, shockDay: shock, zeroLine: !state.compare.overlay }));
  }
  view.append(charts);

  // --- end-state tables
  const tables = el("div", { class: "card" });
  tables.append(el("h2", {}, "End state, A against B"));
  for (const region of A.region_names.filter((r) => B.region_names.includes(r))) {
    tables.append(el("h4", {}, region));
    const rows = [];
    for (const field of ["price", "inventory", "capacity", "unmet"]) {
      rows.push({ label: field, _class: "section" });
      const last = (doc, c) => { const s = doc.regions[region][field][c]; return s[s.length - 1]; };
      rows.push(...diffRows(commodities.map((c) => [`  ${c}`, last(A, c), last(B, c)])));
    }
    rows.push({ label: "region", _class: "section" });
    rows.push(...diffRows(REGIONAL_FIELDS.map((f) => { const sa = A.regions[region][f], sb = B.regions[region][f]; return [`  ${f}`, sa[sa.length - 1], sb[sb.length - 1]]; })));
    tables.append(table(DIFF_COLUMNS, rows));
  }
  const la = A.ledgers, lb = B.ledgers;
  tables.append(el("h4", {}, "labor value (work-ticks)"));
  tables.append(table(DIFF_COLUMNS, diffRows(commodities.map((c) => [c, la.labor_value.social[c], lb.labor_value.social[c]]))));
  tables.append(el("h4", {}, "surplus value (work-ticks) and its ratios"));
  const sv = ["constant_capital", "variable_capital", "surplus_labor", "organic_composition", "value_rate_of_profit"];
  const svRows = diffRows(sv.map((k) => [k, la.surplus_value.total[k], lb.surplus_value.total[k]]));
  for (const r of A.region_names) for (const k of ["rate_of_surplus_value", "realized_rate_of_surplus_value", "wage_deviation_labor"]) svRows.push(...diffRows([[`${r} · ${k}`, la.surplus_value.regions[r]?.[k] ?? null, lb.surplus_value.regions[r]?.[k] ?? null]]));
  svRows.push(...diffRows([["rate_of_profit_on_advances", la.surplus_value.rate_of_profit_on_advances, lb.surplus_value.rate_of_profit_on_advances]]));
  tables.append(table(DIFF_COLUMNS, svRows));
  if (la.price_of_production.report && lb.price_of_production.report) {
    tables.append(el("h4", {}, "prices of production (ratio to meals) and the profit rate"));
    const rows = diffRows([["profit_rate", la.price_of_production.report.profit_rate, lb.price_of_production.report.profit_rate]]);
    for (const c of commodities) rows.push(...diffRows([[c, la.price_of_production.report.relative_to_meals[c]?.price_of_production ?? null, lb.price_of_production.report.relative_to_meals[c]?.price_of_production ?? null]]));
    tables.append(table(DIFF_COLUMNS, rows));
  }
  tables.append(el("h4", {}, "money (silver): margin and wages, per region"));
  const money = [];
  for (const r of A.region_names) for (const k of ["wages_paid", "wage_premium_paid", "unattributed_margin"]) money.push(...diffRows([[`${r} · ${k}`, la.market_price.regions[r]?.[k] ?? null, lb.market_price.regions[r]?.[k] ?? null]]));
  tables.append(table(DIFF_COLUMNS, money));
  tables.append(el("h4", {}, "rent"));
  const rentRows = [];
  for (const c of new Set([...Object.keys(la.rent.differential_rent.by_commodity), ...Object.keys(lb.rent.differential_rent.by_commodity)])) rentRows.push(...diffRows([[`differential rent · ${c} (silver)`, la.rent.differential_rent.by_commodity[c] ?? null, lb.rent.differential_rent.by_commodity[c] ?? null]]));
  for (const c of new Set([...Object.keys(la.rent.absolute_rent_bound.by_commodity || {}), ...Object.keys(lb.rent.absolute_rent_bound.by_commodity || {})])) rentRows.push(...diffRows([[`absolute rent bound · ${c} (work-ticks/day)`, la.rent.absolute_rent_bound.by_commodity?.[c] ?? null, lb.rent.absolute_rent_bound.by_commodity?.[c] ?? null]]));
  tables.append(table(DIFF_COLUMNS, rentRows));
  view.append(tables);
}

// ------------------------------------------------------------------ metrics
async function renderMetrics() {
  const view = $("#metrics-view");
  view.innerHTML = "";
  if (!state.metrics.reference) {
    try { state.metrics.reference = await api("/api/metrics"); } catch (e) { view.append(el("p", { class: "status error" }, e.message)); return; }
  }
  const reference = state.metrics.reference.metrics;
  const current = state.metrics.current;
  const head = el("div", { class: "card" });
  head.append(el("h2", {}, "Frozen behavioral metrics"));
  head.append(el("p", { class: "note" }, `${Object.keys(reference).length} metrics in behavior_baseline.json: ${state.metrics.reference.description}. Collecting the current values runs every scenario the reference reads, about twelve seconds, and is cached for the session.`));
  const bar = el("div", { class: "filterbar" });
  const filter = el("input", { type: "search", placeholder: "filter by name", value: state.metrics.filter });
  filter.addEventListener("input", () => { state.metrics.filter = filter.value; renderMetricTable(); });
  const sort = el("select");
  for (const [v, label] of [["name", "sort by name"], ["delta", "sort by |delta %|"]]) sort.append(el("option", { value: v }, label));
  sort.value = state.metrics.sort;
  sort.addEventListener("change", () => { state.metrics.sort = sort.value; renderMetricTable(); });
  const button = el("button", { class: "primary" }, current ? "Current metrics collected" : "Collect current metrics (about 12 s)");
  const status = el("span", { class: "status" });
  if (current) button.disabled = true;
  button.addEventListener("click", async () => {
    button.disabled = true; status.className = "status busy"; status.textContent = "Collecting…";
    try { state.metrics.current = (await api("/api/metrics/collect", {})).metrics; status.textContent = ""; renderMetrics(); }
    catch (e) { status.className = "status error"; status.textContent = e.message; button.disabled = false; }
  });
  bar.append(filter, sort, button, status);
  head.append(bar);
  view.append(head);
  const holder = el("div", { class: "card" });
  view.append(holder);

  function renderMetricTable() {
    holder.innerHTML = "";
    const needle = state.metrics.filter.trim().toLowerCase();
    let rows = Object.entries(reference).filter(([name]) => !needle || name.toLowerCase().includes(needle)).map(([name, entry]) => {
      const cur = current ? current[name] : null;
      const value = entry.value, now = cur ? cur.value : null;
      const delta = (current && typeof now === "number") ? now - value : null;
      const pct = delta === null ? null : value === 0 ? (delta === 0 ? 0 : null) : delta / Math.abs(value) * 100;
      return { name, unit: entry.unit, reference: value, current: now, delta, pct: current ? (pct === null ? (delta === 0 ? "0%" : "n/a") : (pct > 0 ? "+" : "") + pct.toFixed(3) + "%") : "—", _pct: pct, _class: delta === null ? "" : Math.abs(delta) < 5e-7 ? "" : "moved" };
    });
    if (current) for (const name of Object.keys(current)) if (!(name in reference)) rows.push({ name, unit: current[name].unit, reference: null, current: current[name].value, delta: null, pct: "new", _class: "moved" });
    if (state.metrics.sort === "delta") rows.sort((x, y) => (Math.abs(y._pct ?? 0) - Math.abs(x._pct ?? 0)) || x.name.localeCompare(y.name));
    const moved = current ? rows.filter((r) => r._class === "moved").length : null;
    holder.append(el("p", { class: "note" }, current ? `${rows.length} shown · ${moved} moved beyond rounding (1e-6)` : `${rows.length} shown`));
    holder.append(table([
      { key: "name", label: "metric", name: true }, { key: "unit", label: "unit" }, { key: "reference", label: "reference", num: true },
      { key: "current", label: "current", num: true }, { key: "delta", label: "delta", num: true, sign: true, format: (v) => v === null ? "—" : signed(v) }, { key: "pct", label: "delta %", num: true },
    ], rows, { scroll: true }));
  }
  renderMetricTable();
}

// ------------------------------------------------------------------ sensitivity
async function renderSensitivity() {
  const view = $("#sensitivity-view");
  view.innerHTML = "";
  if (!state.sensitivity.ranking) {
    try { state.sensitivity.ranking = await api("/api/sensitivity"); } catch (e) { view.append(el("p", { class: "status error" }, e.message)); return; }
  }
  const R = state.sensitivity.ranking;
  const head = el("div", { class: "card" });
  head.append(el("h2", {}, "Parameter sensitivity, one at a time"));
  if (!R.available) { head.append(el("p", { class: "note" }, "No sweep output found. The sweep is run from the terminal (python -m economy_lab.sensitivity, about thirty minutes) and never from here.")); view.append(head); return; }
  head.append(el("p", { class: "note" }, `Read from sensitivity_results.csv, which the sweep wrote; the viewer never launches the sweep. Ranked by reach — how many of the ${R.readings} metric readings (every metric, both directions, nominally ±10%) a parameter moves at all — because elasticity divides by the metric's baseline and a near-zero baseline turns any movement into a large number (docs/45 §2). Elasticity is beside it for where the baseline is a real magnitude. Click a parameter for every reading it moved.`));
  view.append(head);
  const two = el("div", { class: "two" });
  const left = el("div", { class: "card" });
  left.append(table([
    { key: "rank", label: "#", num: true }, { key: "parameter", label: "parameter", name: true }, { key: "reach", label: "reach", num: true },
    { key: "elasticity", label: "elasticity", num: true }, { key: "strongest", label: "strongest output" },
  ], R.ranking.map((row) => ({
    ...row, strongest: `${row.strongest_metric} (${signed(row.strongest_delta)} ${row.strongest_unit})`,
    _class: row.parameter === state.sensitivity.parameter ? "moved" : "",
    _onclick: async () => { state.sensitivity.parameter = row.parameter; state.sensitivity.detail = await api(`/api/sensitivity/${encodeURIComponent(row.parameter)}`); renderSensitivity(); },
  })), { scroll: true }));
  const inert = R.ranking.filter((r) => r.reach === 0).map((r) => r.parameter);
  left.append(el("p", { class: "note" }, `No measured effect on the captured outputs (${inert.length}): ${inert.join(", ") || "none"}`));
  left.append(el("p", { class: "note" }, `Not swept: ${Object.entries(R.excluded).map(([k, v]) => `${k} (${v})`).join("; ")}`));
  if (R.refused.length) left.append(el("p", { class: "warn" }, `Refused to seed: ${R.refused.map((r) => `${r.parameter} ${r.direction}: ${r.note}`).join("; ")}`));
  two.append(left);
  const right = el("div", { class: "card" });
  const detail = state.sensitivity.detail;
  if (!detail) right.append(el("p", { class: "note" }, "Choose a parameter."));
  else {
    right.append(el("h2", {}, detail.parameter));
    const moved = detail.readings.filter((r) => Math.abs(r.absolute_delta || 0) > 0);
    right.append(el("p", { class: "note" }, `${moved.length} of ${detail.readings.length} readings moved. Sorted by |elasticity|.`));
    right.append(table([
      { key: "metric", label: "metric", name: true }, { key: "direction", label: "dir" }, { key: "parameter_change_pct", label: "param %", num: true, format: (v) => v === null ? "—" : v.toFixed(2) },
      { key: "baseline_output", label: "baseline", num: true }, { key: "perturbed_output", label: "perturbed", num: true },
      { key: "absolute_delta", label: "delta", num: true, sign: true, format: (v) => signed(v) }, { key: "relative_delta_pct", label: "delta %", num: true, format: (v) => v === null ? "—" : (v > 0 ? "+" : "") + v.toFixed(3) + "%" },
      { key: "elasticity", label: "elasticity", num: true }, { key: "unit", label: "unit" },
    ], moved.map((r) => ({ ...r, _class: Math.abs(r.relative_delta_pct || 0) >= 1 ? "big" : "" })), { scroll: true }));
  }
  two.append(right);
  view.append(two);
}

// ------------------------------------------------------------------ docs
async function renderDocList() {
  if (!state.docs.list.length) state.docs.list = await api("/api/docs");
  const list = $("#doc-list");
  list.innerHTML = "";
  for (const doc of state.docs.list) {
    const item = el("li", { class: doc.number === state.docs.current ? "current" : "" });
    item.append(el("span", { class: "num" }, String(doc.number).padStart(2, "0")), doc.title);
    item.addEventListener("click", () => { location.hash = `#doc/${doc.number}`; });
    list.append(item);
  }
  if (state.docs.current === null && !$("#doc-view").innerHTML) {
    $("#doc-view").innerHTML = '<p class="muted">Choose a document. Design documents were written before the code they describe; results documents score the predictions afterwards.</p>';
  }
}
async function showDoc(number) {
  state.docs.current = number;
  const view = $("#doc-view");
  view.innerHTML = '<p class="muted">Loading…</p>';
  try {
    const doc = await api(`/api/docs/${number}`);
    view.innerHTML = `<div class="docmeta">docs/${doc.file}</div>` + doc.html;
    view.scrollIntoView({ block: "start" });
    window.scrollTo(0, 0);
  } catch (e) { view.innerHTML = `<p class="status error">${esc(e.message)}</p>`; }
  renderDocList();
}

// ------------------------------------------------------------------ boot
async function boot() {
  [state.scenarios, state.parameters] = await Promise.all([api("/api/scenarios"), api("/api/parameters")]);
  const select = $("#scenario-select");
  for (const s of state.scenarios) select.append(el("option", { value: s.name }, `${s.name}${s.cost === "slow" ? " (slow)" : ""}${s.kind === "sweep" ? " (sweep)" : ""}`));
  select.addEventListener("change", renderScenarioForm);
  renderScenarioForm();
  renderParameterForm();
  $("#parameter-filter").addEventListener("input", filterParameters);
  $("#run-button").addEventListener("click", runScenario);
  $("#clear-overrides").addEventListener("click", () => { for (const input of document.querySelectorAll("#parameter-form [data-param]")) { input.value = ""; input.closest(".row").classList.remove("set"); } });
  renderRunList();
  renderRunView();
  const existing = await api("/api/runs");
  for (const row of existing) {
    if (state.runs[row.key]) continue;
    state.runs[row.key] = await api(`/api/runs/${row.key}`);
    state.order.push(row.key);
  }
  if (existing.length && !state.current) state.current = state.order[state.order.length - 1];
  renderRunList();
  renderRunView();
  route();
}
boot().catch((e) => { $("#run-status").className = "status error"; $("#run-status").textContent = e.message; });
