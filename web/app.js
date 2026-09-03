const DATA_URL = "../data/programs.json";
const state = { catalog: null, programs: [] };

const $ = (selector) => document.querySelector(selector);

function make(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function amount(program) {
  if (program.amount_usd_max !== null && program.amount_usd_max !== undefined) {
    return `$${Number(program.amount_usd_max).toLocaleString("en-US")}`;
  }
  return program.amount_display || "Variable";
}

function matches(program) {
  const query = $("#search").value.trim().toLowerCase();
  const kind = $("#kind").value;
  const access = $("#access").value;
  const applications = $("#applications").checked;
  const haystack = [
    program.provider,
    program.name,
    program.benefit,
    ...(program.eligibility || []),
    ...(program.tags || []),
  ].join(" ").toLowerCase();
  return (!query || haystack.includes(query))
    && (!kind || program.kind === kind)
    && (!access || program.access === access)
    && (!applications || program.access === "application");
}

function renderStats(records) {
  const applications = records.filter((program) => program.access === "application").length;
  const gpu = records.filter((program) => program.resource_types.includes("gpu")).length;
  const api = records.filter((program) => program.resource_types.includes("api")).length;
  const values = [
    ["MATCHING", records.length],
    ["API", api],
    ["GPU", gpu],
    ["APPLICATIONS", applications],
  ];
  const stats = $("#stats");
  stats.replaceChildren(...values.map(([label, value]) => {
    const block = make("div", "stat");
    block.append(make("strong", "stat-value", String(value)), make("span", "stat-label", label));
    return block;
  }));
}

function renderCard(program) {
  const card = make("article", "card");
  const top = make("div", "card-top");
  top.append(make("span", `pill pill-${program.kind}`, program.kind.toUpperCase()));
  top.append(make("span", "status", program.status === "active" ? "ACTIVE" : "CONDITIONAL"));
  card.append(top);
  card.append(make("h2", "card-title", program.name));
  card.append(make("p", "provider", program.provider));

  const benefit = make("p", "benefit", program.benefit);
  card.append(benefit);

  const facts = make("dl", "facts");
  for (const [label, value] of [["最大展示", amount(program)], ["入口", program.access], ["交接", program.handoff]]) {
    const term = make("dt", null, label);
    const detail = make("dd", null, value);
    facts.append(term, detail);
  }
  card.append(facts);

  const tags = make("div", "tags");
  for (const tag of program.tags || []) tags.append(make("span", "tag", `#${tag}`));
  card.append(tags);

  const actions = make("div", "actions");
  const apply = make("a", "button primary", "打开官方入口");
  apply.href = program.application_url;
  apply.target = "_blank";
  apply.rel = "noreferrer";
  const evidence = make("a", "button secondary", "看官方证据");
  evidence.href = program.evidence_url;
  evidence.target = "_blank";
  evidence.rel = "noreferrer";
  actions.append(apply, evidence);
  card.append(actions);

  const caution = make("details", "details");
  caution.append(make("summary", null, "资格与风险提示"));
  const notes = make("div", "details-body");
  notes.append(make("p", null, program.caution));
  if (program.payment_note) notes.append(make("p", null, `账单提示：${program.payment_note}`));
  notes.append(make("p", null, `最后核验：${program.last_verified}`));
  caution.append(notes);
  card.append(caution);
  return card;
}

function render() {
  const records = state.programs.filter(matches);
  renderStats(records);
  const list = $("#list");
  list.replaceChildren(...records.map(renderCard));
  if (!records.length) list.append(make("p", "empty", "没有匹配记录，试试更短的关键词或清除筛选。"));
}

async function init() {
  try {
    const response = await fetch(DATA_URL);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.catalog = await response.json();
    state.programs = state.catalog.programs || [];
    $("#review-date").textContent = `Catalog review · ${state.catalog.last_catalog_review}`;
    render();
  } catch (error) {
    $("#review-date").textContent = "Catalog unavailable";
    $("#error").hidden = false;
    $("#error").textContent = `无法加载目录：${error.message}。请从项目根目录启动本地 HTTP server。`;
  }
}

for (const selector of ["#search", "#kind", "#access", "#applications"]) {
  $(selector).addEventListener("input", render);
  $(selector).addEventListener("change", render);
}

init();

