"use strict";

const $ = (id) => document.getElementById(id);
const svgNS = "http://www.w3.org/2000/svg";
let snapshot = null;
let snapshotSignature = null;
let selectedAgent = null;
let selectedMilestone = null;
let workFilter = "all";
let workView = "board";
let paused = false;
let fetching = false;
let fetchFailed = false;
let lastReceived = null;
let session = null;
let sessionPromise = null;
let chatRole = null;
let conversationId = null;
let conversations = [];
let sending = false;
let historyLoading = false;
let historyVersion = 0;
let drawerOpener = null;
let changingModelCalls = false;
let chatMode = "assistant";
let inboxFetching = false;
let inquiries = [];
let captureMetadata = null;
let captureMetadataAvailable = false;
let captureMetadataFetching = false;
let captureMetadataReceived = null;

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function svgElement(tag, attributes = {}, text) {
  const node = document.createElementNS(svgNS, tag);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
  if (text !== undefined) node.textContent = text;
  return node;
}
function readable(value) { return String(value ?? "Unknown").replaceAll("_", " "); }
function dateLabel(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Unknown time" : date.toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit" });
}
function ageLabel(seconds) {
  if (seconds < 0) return "Observation is in the future";
  const amount = seconds < 60 ? Math.floor(seconds) : seconds < 3600 ? Math.floor(seconds / 60) : seconds < 86400 ? Math.floor(seconds / 3600) : Math.floor(seconds / 86400);
  const unit = seconds < 60 ? "second" : seconds < 3600 ? "minute" : seconds < 86400 ? "hour" : "day";
  return `${amount} ${unit}${amount === 1 ? "" : "s"} ago`;
}
function money(value) {
  return typeof value !== "number" || !Number.isFinite(value) ? "Unknown" : new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 2, maximumFractionDigits: 4 }).format(value);
}
function state(value) {
  const known = new Set(["running", "active", "in_progress", "complete", "completed", "verified", "done", "blocked", "pending", "failed"]);
  return element("span", `status${known.has(value) ? ` status-${value}` : ""}`, readable(value));
}
function groupFor(status) {
  if (["complete", "completed", "verified", "done"].includes(status)) return "completed";
  if (["running", "active", "in_progress", "blocked", "failed", "reviewing", "paused"].includes(status)) return "active";
  return "planned";
}
function empty(container, message) { container.replaceChildren(element("p", "empty", message)); }

// Each identity gets a local geometric insignia; no third-party image request occurs.
function agentIcon(id, size = 36) {
  let seed = 0;
  for (const char of id) seed = ((seed << 5) - seed + char.charCodeAt(0)) >>> 0;
  const svg = svgElement("svg", { viewBox: "0 0 40 40", width: size, height: size, class: "agent-icon", "aria-hidden": "true" });
  svg.append(svgElement("rect", { x: 1, y: 1, width: 38, height: 38, rx: 10, fill: "#f0f4ff" }));
  const motif = svgElement("g", { transform: `rotate(${seed % 90} 20 20)`, fill: "none", stroke: "#2357e8", "stroke-width": "1.35", "stroke-linecap": "round" });
  const petals = 3 + seed % 5;
  for (let i = 0; i < petals; i += 1) {
    const angle = i * 360 / petals;
    const radius = 7 + (seed >>> 4) % 4;
    motif.append(svgElement("ellipse", { cx: 20, cy: 15, rx: 4 + (seed >>> 7) % 3, ry: radius, transform: `rotate(${angle} 20 20)` }));
  }
  motif.append(svgElement("circle", { cx: 20, cy: 20, r: 2.2, fill: "#2357e8", stroke: "none" }));
  svg.append(motif);
  svg.append(svgElement("circle", { cx: 31, cy: 9, r: 1.2 + (seed % 3) * 0.4, fill: "#889ded" }));
  return svg;
}

function dependencyGraph() {
  const milestones = snapshot?.milestones || [];
  const edges = snapshot?.dependencies;
  if (edges === undefined || (Array.isArray(edges) && !edges.length)) return { empty: true };
  if (!Array.isArray(edges) || !milestones.length || milestones.length > 200 || edges.length > 1000) throw new Error("The dependency map is invalid or exceeds the display limit.");
  const nodes = new Map(milestones.map((item) => [item.id, item]));
  if (nodes.size !== milestones.length) throw new Error("The dependency map contains duplicate milestone identities.");
  const outgoing = new Map(milestones.map((item) => [item.id, []]));
  const degree = new Map(milestones.map((item) => [item.id, 0]));
  const levels = new Map(milestones.map((item) => [item.id, 0]));
  const seen = new Set();
  for (const edge of edges) {
    if (!edge || typeof edge.from !== "string" || typeof edge.to !== "string" || typeof edge.reason !== "string" || !nodes.has(edge.from) || !nodes.has(edge.to) || edge.from === edge.to) throw new Error("The dependency map contains an invalid prerequisite reference.");
    const key = JSON.stringify([edge.from, edge.to]);
    if (seen.has(key)) throw new Error("The dependency map contains a duplicate relationship.");
    seen.add(key); outgoing.get(edge.from).push(edge.to); degree.set(edge.to, degree.get(edge.to) + 1);
  }
  const queue = milestones.filter((item) => degree.get(item.id) === 0).map((item) => item.id);
  let visited = 0;
  for (let index = 0; index < queue.length; index += 1) {
    const id = queue[index]; visited += 1;
    for (const next of outgoing.get(id)) {
      levels.set(next, Math.max(levels.get(next), levels.get(id) + 1));
      degree.set(next, degree.get(next) - 1);
      if (degree.get(next) === 0) queue.push(next);
    }
  }
  if (visited !== milestones.length) throw new Error("The dependency map contains a cycle and cannot be shown as a DAG.");
  return { empty: false, milestones, edges, nodes, levels };
}
function mapTitleLines(title, limit = 27) {
  const words = title.split(/\s+/);
  const lines = [];
  let line = "";
  for (const word of words) {
    if (line && `${line} ${word}`.length > limit) { lines.push(line); line = ""; }
    if (word.length > limit) { if (line) lines.push(line); lines.push(`${word.slice(0, limit - 1)}…`); line = ""; }
    else line = line ? `${line} ${word}` : word;
  }
  if (line) lines.push(line);
  if (lines.length > 3) return [...lines.slice(0, 2), `${lines[2].slice(0, limit - 1)}…`];
  return lines;
}
function renderDependencyMap() {
  const svg = $("dependency-map");
  const canvas = $("dependency-canvas");
  const focused = document.activeElement?.dataset.mapMilestone;
  const scroll = { left: canvas.scrollLeft, top: canvas.scrollTop };
  svg.replaceChildren();
  let graph;
  try { graph = dependencyGraph(); }
  catch (error) { canvas.hidden = true; $("dependency-message").textContent = `${error.message} Use the board or evidence while the snapshot is corrected.`; $("dependency-message").classList.add("map-error"); return; }
  $("dependency-message").classList.remove("map-error");
  if (graph.empty) { canvas.hidden = true; $("dependency-message").textContent = "No prerequisite relationships are recorded in this snapshot. The board and evidence still show the saved milestones."; return; }
  canvas.hidden = false;
  const query = $("agent-search").value.trim().toLocaleLowerCase();
  const columns = new Map();
  for (const milestone of graph.milestones) {
    const level = graph.levels.get(milestone.id);
    if (!columns.has(level)) columns.set(level, []);
    columns.get(level).push(milestone);
  }
  const nodeWidth = 184; const nodeHeight = 106; const gapX = 40; const gapY = 27; const inset = 22;
  const positions = new Map();
  for (const [level, nodes] of columns) nodes.forEach((milestone, row) => positions.set(milestone.id, { x: inset + level * (nodeWidth + gapX), y: inset + row * (nodeHeight + gapY) }));
  const maxLevel = Math.max(...graph.levels.values());
  const maxRows = Math.max(...[...columns.values()].map((nodes) => nodes.length));
  const width = inset * 2 + (maxLevel + 1) * nodeWidth + maxLevel * gapX;
  const height = inset * 2 + maxRows * nodeHeight + (maxRows - 1) * gapY;
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("width", String(width)); svg.setAttribute("height", String(height));
  const defs = svgElement("defs");
  const marker = svgElement("marker", { id: "dependency-arrow", viewBox: "0 0 10 10", refX: 9, refY: 5, markerWidth: 6, markerHeight: 6, orient: "auto-start-reverse" });
  marker.append(svgElement("path", { d: "M0 0L10 5L0 10z", fill: "#9badc9" })); defs.append(marker); svg.append(defs);
  for (const edge of graph.edges) {
    const from = positions.get(edge.from); const to = positions.get(edge.to);
    const start = from.x + nodeWidth; const end = to.x; const startY = from.y + nodeHeight / 2; const endY = to.y + nodeHeight / 2;
    const related = selectedMilestone === edge.from || selectedMilestone === edge.to;
    const path = svgElement("path", { d: `M${start} ${startY}C${start + gapX * 0.6} ${startY} ${end - gapX * 0.6} ${endY} ${end - 3} ${endY}`, class: `dependency-edge${related ? " edge-related" : ""}`, "marker-end": "url(#dependency-arrow)" });
    path.append(svgElement("title", {}, `${graph.nodes.get(edge.from).title} → ${graph.nodes.get(edge.to).title}: ${edge.reason}`)); svg.append(path);
  }
  let matches = 0;
  for (const milestone of graph.milestones) {
    const position = positions.get(milestone.id);
    const match = !query || `${milestone.title} ${milestone.evidence}`.toLocaleLowerCase().includes(query);
    if (match) matches += 1;
    const statusGroup = groupFor(milestone.status);
    const needsAttention = ["blocked", "failed"].includes(milestone.status);
    const node = svgElement("g", { transform: `translate(${position.x} ${position.y})`, class: `dependency-node node-${needsAttention ? "attention" : statusGroup}${selectedMilestone === milestone.id ? " node-selected" : ""}${query && !match ? " node-muted" : ""}`, tabindex: "0", role: "button", "aria-pressed": String(selectedMilestone === milestone.id), "aria-label": `${milestone.title}. State: ${readable(milestone.status)}. Inspect evidence and prerequisites.` });
    node.dataset.mapMilestone = milestone.id;
    node.append(svgElement("title", {}, `${milestone.title}\n${readable(milestone.status)}\n${milestone.evidence}`));
    node.append(svgElement("rect", { width: nodeWidth, height: nodeHeight, rx: 7, class: "dependency-node-box" }));
    const title = svgElement("text", { x: 13, y: 23, class: "dependency-node-title", "aria-hidden": "true" });
    mapTitleLines(milestone.title).forEach((line, index) => title.append(svgElement("tspan", { x: 13, dy: index ? 15 : 0 }, line))); node.append(title);
    node.append(svgElement("circle", { cx: 16, cy: 86, r: 3, class: "dependency-status-dot", "aria-hidden": "true" }));
    node.append(svgElement("text", { x: 25, y: 90, class: "dependency-node-status", "aria-hidden": "true" }, readable(milestone.status)));
    const inspect = () => { selectMilestone(milestone.id); if (window.matchMedia("(max-width:900px)").matches) $("agent-detail").scrollIntoView({ block: "nearest" }); };
    node.addEventListener("click", inspect);
    node.addEventListener("keydown", (event) => { if (["Enter", " "].includes(event.key)) { event.preventDefault(); inspect(); } });
    svg.append(node);
  }
  $("dependency-message").textContent = `${graph.milestones.length} recorded milestones / ${graph.edges.length} prerequisite relationships.${query ? ` ${matches} milestone${matches === 1 ? "" : "s"} match the search; other nodes stay visible for context.` : " Scroll to inspect the full map."}`;
  canvas.scrollLeft = scroll.left; canvas.scrollTop = scroll.top;
  if (focused) [...svg.querySelectorAll("[data-map-milestone]")].find((node) => node.dataset.mapMilestone === focused)?.focus({ preventScroll: true });
}
function switchWorkView(view) {
  workView = view;
  const map = view === "map";
  $("work-board").hidden = map; $("dependency-panel").hidden = !map; $("map-direction").hidden = !map;
  $("board-status-filters").hidden = map;
  $("agent-search").placeholder = map ? "Find milestone…" : "Find work…";
  $("board-view").classList.toggle("selected", !map); $("board-view").setAttribute("aria-pressed", String(!map));
  $("dependency-view").classList.toggle("selected", map); $("dependency-view").setAttribute("aria-pressed", String(map));
  if (map) renderDependencyMap();
}

function renderWork() {
  const focusedAgent = document.activeElement?.dataset.agentId;
  const focusedMilestone = document.activeElement?.dataset.milestoneId;
  const query = $("agent-search").value.trim().toLocaleLowerCase();
  const agents = snapshot?.agents || [];
  const shown = agents.filter((agent) => `${agent.name} ${agent.role} ${agent.task} ${agent.model}`.toLocaleLowerCase().includes(query));
  const plannedMilestones = (snapshot?.milestones || []).filter((item) => ["pending", "planned", "not_started", "incomplete", "todo"].includes(item.status) && `${item.title} ${item.evidence}`.toLocaleLowerCase().includes(query));
  const groups = [{ id: "planned", label: "Planned" }, { id: "active", label: "Active" }, { id: "completed", label: "Completed" }];
  const board = $("work-board");
  board.replaceChildren();
  board.classList.toggle("single-column", workFilter !== "all");
  for (const group of groups.filter((item) => workFilter === "all" || item.id === workFilter)) {
    const column = element("section", "board-column");
    column.dataset.group = group.id;
    column.setAttribute("aria-label", `${group.label} work`);
    const members = shown.filter((agent) => groupFor(agent.status) === group.id);
    const milestones = group.id === "planned" ? plannedMilestones : [];
    const heading = element("div", "column-heading");
    const title = element("h3");
    const dot = element("span", "column-dot"); dot.setAttribute("aria-hidden", "true");
    title.append(dot, document.createTextNode(group.label));
    heading.append(title, element("span", "column-count", String(members.length + milestones.length)));
    column.append(heading);
    for (const agent of members) {
      const card = element("button", "work-card"); card.type = "button";
      card.dataset.agentId = agent.id;
      card.setAttribute("aria-expanded", String(selectedAgent === agent.id));
      card.setAttribute("aria-controls", "agent-detail");
      const identity = element("span", "card-identity");
      const copy = element("span", "card-identity-copy");
      copy.append(element("span", "card-name", agent.name), element("span", "card-role", agent.role));
      identity.append(agentIcon(agent.id), copy);
      const foot = element("span", "card-foot");
      foot.append(element("span", "card-model", agent.model || "Model not recorded"), state(agent.status));
      card.append(identity, element("span", "card-task", agent.task), foot);
      card.addEventListener("click", () => selectAgent(agent.id));
      column.append(card);
    }
    for (const milestone of milestones) {
      const card = element("button", "work-card milestone-card"); card.type = "button";
      card.dataset.milestoneId = milestone.id;
      card.setAttribute("aria-expanded", String(selectedMilestone === milestone.id));
      card.setAttribute("aria-controls", "agent-detail");
      const identity = element("span", "card-identity");
      const symbol = element("span", "planned-symbol", "◇"); symbol.setAttribute("aria-hidden", "true");
      const copy = element("span", "card-identity-copy");
      copy.append(element("span", "card-name", "Planned milestone"), element("span", "card-role", "No worker assigned"));
      identity.append(symbol, copy);
      const foot = element("span", "card-foot");
      foot.append(element("span", "card-model", "Recorded milestone"), state(milestone.status));
      card.append(identity, element("span", "card-task", milestone.title), foot);
      card.addEventListener("click", () => { selectedAgent = null; selectedMilestone = milestone.id; renderWork(); });
      column.append(card);
    }
    if (!members.length && !milestones.length) column.append(element("p", "column-empty", query ? "No recorded work matches this search." : `No ${group.label.toLowerCase()} work recorded in this snapshot.`));
    board.append(column);
  }
  renderAgentDetail();
  if (workView === "map") renderDependencyMap();
  if (focusedAgent) [...board.querySelectorAll("[data-agent-id]")].find((card) => card.dataset.agentId === focusedAgent)?.focus();
  if (focusedMilestone) [...board.querySelectorAll("[data-milestone-id]")].find((card) => card.dataset.milestoneId === focusedMilestone)?.focus();
}
function selectAgent(id) { selectedAgent = id; selectedMilestone = null; renderWork(); }
function selectMilestone(id) { selectedAgent = null; selectedMilestone = id; renderWork(); }
function milestoneRelationships(milestone) {
  const section = element("section", "milestone-relationships");
  section.append(element("h4", "", "Recorded prerequisites"));
  let graph;
  try { graph = dependencyGraph(); }
  catch { section.append(element("p", "", "Dependency records are invalid; no prerequisite conclusion can be drawn.")); return section; }
  if (graph.empty) { section.append(element("p", "", "No prerequisite relationships recorded in this snapshot.")); return section; }
  const incoming = graph.edges.filter((edge) => edge.to === milestone.id);
  const outgoing = graph.edges.filter((edge) => edge.from === milestone.id);
  const unresolved = incoming.filter((edge) => groupFor(graph.nodes.get(edge.from).status) !== "completed").length;
  section.append(element("p", "", incoming.length ? `${unresolved} of ${incoming.length} prerequisites are not recorded complete.` : "No prerequisites recorded for this milestone."));
  const relationship = (edge, id) => {
    const item = element("div", "milestone-relationship");
    const related = graph.nodes.get(id);
    const button = element("button", "relationship-link", related.title); button.type = "button";
    button.addEventListener("click", () => selectMilestone(id));
    item.append(button, state(related.status), element("p", "", edge.reason || "No reason recorded."));
    return item;
  };
  for (const edge of incoming) section.append(relationship(edge, edge.from));
  if (outgoing.length) {
    section.append(element("h4", "", "Dependent milestones"));
    for (const edge of outgoing) section.append(relationship(edge, edge.to));
  }
  return section;
}
function renderAgentDetail() {
  const detail = $("agent-detail");
  const agent = snapshot?.agents.find((candidate) => candidate.id === selectedAgent);
  const milestone = snapshot?.milestones.find((candidate) => candidate.id === selectedMilestone);
  detail.hidden = !agent && !milestone;
  $("inspector-empty").hidden = Boolean(agent || milestone);
  detail.replaceChildren();
  if (!agent && milestone) {
    const heading = element("div", "detail-heading");
    const title = element("div", "detail-title");
    const copy = element("div");
    copy.append(element("h3", "", milestone.title), element("p", "", groupFor(milestone.status) === "planned" ? "Planned milestone / no worker assigned" : `Recorded milestone / ${readable(milestone.status)}`)); title.append(copy);
    const close = element("button", "icon-button", "×"); close.type = "button"; close.setAttribute("aria-label", "Close milestone details");
    close.addEventListener("click", () => { const id = selectedMilestone; selectedMilestone = null; renderWork(); const target = workView === "map" ? [...$("dependency-map").querySelectorAll("[data-map-milestone]")].find((node) => node.dataset.mapMilestone === id) : [...$("work-board").querySelectorAll("[data-milestone-id]")].find((card) => card.dataset.milestoneId === id); target?.focus(); });
    heading.append(title, close);
    const link = element("a", "text-button", "View recorded milestone evidence ↘"); link.href = "#evidence";
    const footer = element("div", "detail-footer"); footer.append(state(milestone.status), link);
    detail.append(heading, element("p", "detail-body", milestone.evidence || "No evidence recorded."), milestoneRelationships(milestone), footer);
    return;
  }
  if (!agent) return;
  const heading = element("div", "detail-heading");
  const title = element("div", "detail-title");
  const copy = element("div");
  copy.append(element("h3", "", agent.name), element("p", "", agent.role));
  title.append(agentIcon(agent.id), copy);
  const close = element("button", "icon-button", "×"); close.type = "button"; close.setAttribute("aria-label", "Close task details");
  close.addEventListener("click", () => { const id = selectedAgent; selectedAgent = null; renderWork(); [...$("work-board").querySelectorAll("[data-agent-id]")].find((card) => card.dataset.agentId === id)?.focus(); });
  heading.append(title, close);
  const footer = element("div", "detail-footer");
  const metadata = element("div", "detail-metadata");
  metadata.append(element("span", "", `Recorded model: ${agent.model || "Unknown"}`), element("span", "", `Observed ${dateLabel(agent.observed_at)} / ${readable(agent.status)}`));
  const actions = element("div", "detail-actions");
  const ask = element("button", "button button-light button-small", "Open contextual assistant"); ask.type = "button";
  ask.addEventListener("click", async () => { await openChat(agent.id, ask); await switchChatMode("assistant"); });
  const inquiry = element("button", "text-button", "Leave a worker inquiry"); inquiry.type = "button";
  inquiry.addEventListener("click", async () => { await openChat(agent.id, inquiry); await switchChatMode("inbox"); });
  actions.append(ask, inquiry);
  footer.append(metadata, actions);
  detail.append(heading, element("p", "detail-task", agent.task), element("p", "detail-body", agent.detail || "No additional detail recorded."), footer);
}

function renderEvidence() {
  const list = $("milestone-list"); list.replaceChildren();
  if (!snapshot.milestones.length) empty(list, "No milestones recorded.");
  for (const milestone of snapshot.milestones) {
    const item = element("article", "milestone");
    const completed = groupFor(milestone.status) === "completed";
    const icon = element("span", `milestone-icon${completed ? " done" : ""}`, completed ? "✓" : ""); icon.setAttribute("aria-hidden", "true");
    const copy = element("div");
    copy.append(element("h3", "", milestone.title), element("p", "", milestone.evidence || "No evidence recorded."));
    item.append(icon, copy, state(milestone.status)); list.append(item);
  }
  const decisions = $("decision-list");
  const open = new Set([...decisions.querySelectorAll("details[open]")].map((item) => item.dataset.id));
  decisions.replaceChildren();
  if (!snapshot.decisions.length) empty(decisions, "No decisions recorded.");
  for (const decision of snapshot.decisions) {
    const item = element("details", "decision"); item.dataset.id = decision.id; item.open = open.has(decision.id);
    const summary = element("summary"); summary.append(element("span", "", decision.title), state(decision.status));
    const body = element("div", "decision-body");
    const reason = element("p"); reason.append(element("span", "reason-label", "Reason: "), document.createTextNode(decision.reason));
    body.append(element("p", "", decision.decision), reason); item.append(summary, body); decisions.append(item);
  }
  const blockers = $("blocker-list"); blockers.replaceChildren();
  if (!snapshot.blockers.length) empty(blockers, "No open dependencies recorded in this snapshot.");
  for (const blocker of snapshot.blockers) {
    const item = element("article", "blocker");
    item.append(element("h3", "", blocker.title), element("p", "", blocker.detail), element("span", "blocker-scope", `Affects: ${blocker.scope}`)); blockers.append(item);
  }
  const events = $("event-list"); events.replaceChildren();
  if (!snapshot.events.length) events.append(element("li", "empty", "No events recorded."));
  for (const event of [...snapshot.events].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))) {
    const item = element("li", "event");
    const time = element("time", "event-time", dateLabel(event.timestamp)); time.dateTime = event.timestamp;
    const agent = snapshot.agents.find((candidate) => candidate.id === event.agent_id);
    item.append(time, element("h3", "", event.title), element("p", "", event.detail), element("span", "event-kind", `${readable(event.kind)}${agent ? ` / ${agent.name}` : ""}`)); events.append(item);
  }
}
function renderBudget(budget) {
  if (!budget || typeof budget !== "object") return;
  const value = (name) => typeof budget[`${name}_usd`] === "number" ? budget[`${name}_usd`] : typeof budget[`${name}_micro_usd`] === "number" ? budget[`${name}_micro_usd`] / 1e6 : null;
  $("budget-spent").textContent = money(value("spent"));
  $("budget-reserved").textContent = money(value("reserved"));
  $("budget-limit").textContent = money(value("daily_limit"));
  $("budget-scope").textContent = budget.scope || "Recorded project API usage; total account usage may differ.";
  $("budget-timezone").textContent = budget.timezone ? `Calendar day: ${budget.timezone}` : "Calendar timezone not reported.";
}
function updateFreshness() {
  const connection = $("connection");
  if (!snapshot) { connection.textContent = fetchFailed ? "Progress record unavailable" : "Loading progress…"; connection.className = `connection${fetchFailed ? " failed" : ""}`; return; }
  const age = (Date.now() - new Date(snapshot.observed_at).getTime()) / 1000;
  const stale = age > 90 || age < -5;
  $("snapshot-age").textContent = `${stale ? "Stale · " : ""}${ageLabel(age)}`;
  $("snapshot-age").classList.toggle("stale-label", stale);
  connection.textContent = fetchFailed ? "Progress refresh failed" : paused ? "Work updates paused" : stale ? "Progress record stale" : "Progress record current";
  connection.className = `connection ${fetchFailed ? "failed" : stale || paused ? "stale" : "fresh"}`;
  connection.title = lastReceived ? `Last successful fetch: ${dateLabel(lastReceived)}` : "";
}

function captureCountdownLabel(value, now = Date.now()) {
  if (typeof value !== "string" || !Number.isFinite(Date.parse(value))) return { text: "Unavailable", state: "unavailable" };
  const remaining = Date.parse(value) - now;
  const format = (seconds) => `${Math.floor(seconds / 60)}m ${String(seconds % 60).padStart(2, "0")}s`;
  if (remaining > 0) return { text: `In ${format(Math.ceil(remaining / 1000))}`, state: "scheduled" };
  if (remaining >= -1000) return { text: "Due now", state: "due" };
  return { text: `Overdue ${format(Math.floor(-remaining / 1000))}`, state: "overdue" };
}
function updateCaptureCountdown() {
  const recent = captureMetadataReceived && Date.now() - captureMetadataReceived < 30000;
  const available = captureMetadataAvailable && recent && !["stopped", "never_started"].includes(captureMetadata?.status);
  const next = available ? captureMetadata?.next_attempt_at : null;
  const label = captureCountdownLabel(next);
  $("capture-next-attempt").textContent = next ? dateLabel(next) : "Unavailable";
  $("capture-next-attempt").title = next || "";
  $("capture-countdown").textContent = label.text;
  $("capture-countdown").className = `capture-countdown capture-${label.state}`;
  if (captureMetadataAvailable && !recent) {
    $("capture-availability").textContent = "Metadata needs refresh";
    $("capture-monitor-note").textContent = "The last received metadata is old; the next attempt is unverified until it refreshes. Capture timing does not establish new agent progress.";
  }
}
function renderCaptureMetadata() {
  const data = captureMetadata;
  if (!data) return;
  const time = (id, value) => { $(id).textContent = value ? dateLabel(value) : "Unavailable"; $(id).title = value || ""; };
  time("capture-last-attempt", data.last_attempt_at);
  time("capture-last-success", data.last_success_at);
  time("capture-source-observed", data.source_observed_at);
  const result = data.last_result === "success" ? "Success" : ["failure", "failed"].includes(data.last_result) ? "Failed" : data.last_result === "pending" ? "Pending" : "Unavailable";
  $("capture-result").textContent = result;
  $("capture-result").className = `capture-result capture-result-${result.toLowerCase()}`;
  $("capture-interval").textContent = data.interval_seconds === 300 ? "Every 5 minutes" : `Every ${data.interval_seconds} seconds`;
  const status = { never_started: "No capture yet", current: "Recorder current", delayed: "Recorder delayed", stopped: "Recorder stopped", error: "Recorder error", capturing: "Attempt claimed" };
  $("capture-availability").textContent = status[data.status] || "Metadata received";
  $("capture-monitor-note").textContent = captureExplanation(data);
  updateCaptureCountdown();
}
function captureExplanation(data) {
  const reasons = {
    monitor_not_started: "No capture attempt has been recorded yet.",
    monitor_missing_or_invalid: "Recorder health is unavailable; the next attempt cannot be confirmed.",
    monitor_stopped: "The local recorder is stopped. No next attempt is confirmed.",
    clock_moved_backwards: "The device clock moved backwards; capture scheduling needs verification.",
    monitor_stale: "The recorder has not checked in recently. No next attempt is confirmed.",
    capture_due: "The recorded capture deadline is due; no newer attempt is recorded yet.",
    attempt_pending_or_interrupted: "A capture attempt was claimed; no completed result is recorded yet.",
    scheduled: "The recorder reports its next scheduled attempt.",
    snapshot_metadata_invalid_or_unavailable: "Capture records are unavailable or invalid; no next attempt is confirmed.",
    metadata_invalid: "Capture records are invalid; no next attempt is confirmed.",
  };
  const errors = {
    source_missing: "The saved agent-progress record is missing.",
    source_invalid: "The saved agent-progress record is invalid.",
    source_unsafe: "The saved agent-progress record could not be read safely.",
    source_oversized: "The saved agent-progress record exceeds the capture limit.",
    service_observation_invalid: "The recorded local health check is invalid.",
    capture_interrupted: "The previous capture was interrupted.",
    capture_storage_unavailable: "Capture storage is unavailable.",
    clock_invalid: "The recorder's clock needs verification.",
  };
  if (data.reason === "last_attempt_failed") return `${errors[data.error] || "The last capture attempt failed."}${data.next_attempt_at ? " A later attempt is scheduled." : " No next attempt is confirmed."}`;
  return reasons[data.reason] || errors[data.error] || "The recorder's capture state needs verification.";
}
async function refreshCaptureMetadata() {
  if (captureMetadataFetching) return;
  captureMetadataFetching = true;
  try {
    const response = await fetch("/api/snapshot-status", { cache: "no-store", signal: AbortSignal.timeout(5000) });
    const data = await responseJson(response, "Snapshot-monitor metadata is unavailable.");
    const fields = ["last_attempt_at", "last_success_at", "next_attempt_at", "source_observed_at"];
    const validTime = (value) => value === null || (typeof value === "string" && /(?:Z|[+-]\d{2}:\d{2})$/i.test(value) && Number.isFinite(Date.parse(value)));
    if (!data || typeof data !== "object" || !fields.every((field) => Object.hasOwn(data, field) && validTime(data[field])) || !Number.isInteger(data.interval_seconds) || data.interval_seconds <= 0 || ![null, "success", "failure", "failed", "unavailable", "pending"].includes(data.last_result)) throw new Error("Snapshot-monitor metadata is incomplete or invalid.");
    captureMetadata = data; captureMetadataAvailable = true; captureMetadataReceived = Date.now();
    renderCaptureMetadata();
  } catch (error) {
    captureMetadataAvailable = false;
    $("capture-availability").textContent = "Metadata unavailable";
    $("capture-monitor-note").textContent = `Snapshot-monitor metadata could not be verified.${captureMetadata ? " Historical fields retain the last received metadata; the next attempt is unverified." : " No capture or next attempt is inferred."}`;
    updateCaptureCountdown();
  } finally { captureMetadataFetching = false; }
}
function renderSnapshot() {
  $("phase").textContent = readable(snapshot.project.phase);
  $("project-summary").textContent = snapshot.project.summary;
  $("snapshot-time").textContent = dateLabel(snapshot.observed_at);
  $("snapshot-time").title = snapshot.observed_at;
  const completed = snapshot.milestones.filter((item) => groupFor(item.status) === "completed").length;
  $("progress-count").textContent = `${completed} of ${snapshot.milestones.length} milestones recorded complete`;
  const repository = $("repository"); repository.hidden = true; repository.removeAttribute("href");
  try { const url = new URL(snapshot.project.repository_url); if (url.protocol === "https:" && !url.username && !url.password) { repository.href = url.href; repository.hidden = false; } } catch { /* Unsafe links stay unavailable. */ }
  if (!snapshot.agents.some((agent) => agent.id === selectedAgent)) selectedAgent = null;
  if (!snapshot.milestones.some((item) => item.id === selectedMilestone)) selectedMilestone = null;
  renderWork(); renderEvidence(); renderBudget(snapshot.budget);
}
async function refresh() {
  if (fetching) return;
  fetching = true; $("refresh").disabled = true;
  try {
    const response = await fetch("/api/status", { cache: "no-store", signal: AbortSignal.timeout(5000) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || "The local status snapshot is unavailable.");
    const signature = JSON.stringify(data); snapshot = data; lastReceived = new Date().toISOString(); fetchFailed = false; $("error").hidden = true;
    if (signature !== snapshotSignature) { renderSnapshot(); snapshotSignature = signature; }
    if (workView === "map") renderDependencyMap();
  } catch (error) {
    fetchFailed = true; $("error").hidden = false;
    $("error").textContent = `${error.message || "The snapshot could not be read."}${snapshot ? " The desk retains the last valid snapshot; it does not show new work." : " No progress is inferred."}`;
  } finally { fetching = false; $("refresh").disabled = false; updateFreshness(); }
}

// Chat and health controls are initialized below. Polling never issues model calls.
function chatStatus(message, isError = false) {
  $("chat-status").textContent = message;
  $("chat-status").classList.toggle("error", isError);
}
function currentRole() { return session?.roles.find((role) => role.id === chatRole); }
function roleLabel(role) { return role?.id === "desk_helper" ? role.name : role ? `Assistant for ${role.name}` : "Contextual assistant"; }
function updateChatControls() {
  const available = Boolean(currentRole() && (chatMode === "inbox" ? session && chatRole !== "desk_helper" : session?.models_enabled && !session?.model_calls_paused));
  $("chat-role").disabled = !session?.roles.length || sending;
  $("conversation-history").disabled = !session?.roles.length || sending || historyLoading;
  $("new-conversation").disabled = !session?.roles.length || sending || historyLoading;
  $("chat-input").disabled = !available || sending || historyLoading;
  $("send-chat").disabled = !available || sending || historyLoading || !$("chat-input").value.trim();
  $("send-chat").textContent = sending ? chatMode === "inbox" ? "Recording inquiry…" : "Waiting for reply…" : chatMode === "inbox" ? "Leave inquiry ↑" : "Send message ↑";
  $("message-count").textContent = `${$("chat-input").value.length} / 4000`;
  $("toggle-model-calls").disabled = !session || sending || changingModelCalls;
  $("toggle-model-calls").textContent = session?.model_calls_paused ? "Resume model calls" : "Pause model calls";
  $("model-call-state").textContent = !session ? "Model-call state unverified" : session.model_calls_paused ? "Project model calls paused" : "Project model calls not paused";
  $("inbox-mode").disabled = !currentRole() || chatRole === "desk_helper" || sending;
  $("assistant-mode").disabled = sending;
}
async function responseJson(response, fallback) {
  let data;
  try { data = await response.json(); } catch { throw new Error(fallback); }
  if (!response.ok) throw new Error(typeof data.message === "string" ? data.message : typeof data.error === "string" ? data.error : fallback);
  return data;
}
async function initializeSession() {
  if (sessionPromise) return sessionPromise;
  sessionPromise = (async () => {
    try {
      const response = await fetch("/api/session", { cache: "no-store", credentials: "same-origin", signal: AbortSignal.timeout(5000) });
      const data = await responseJson(response, "The local assistant service is unavailable.");
      if (!data || typeof data.csrf_token !== "string" || !Array.isArray(data.roles)) throw new Error("The local assistant session is incomplete.");
      data.roles = data.roles.filter((role) => role && typeof role.id === "string" && typeof role.name === "string" && typeof role.model === "string");
      session = data;
      $("chat-role").replaceChildren();
      for (const role of session.roles) $("chat-role").append(new Option(roleLabel(role), role.id));
      if (session.roles.some((role) => role.id === chatRole)) $("chat-role").value = chatRole;
      if (!session.roles.length) $("chat-role").append(new Option("No assistant roles configured", ""));
      renderBudget(session.budget);
      chatStatus(session.model_calls_paused ? "Project model calls are paused. Saved conversations remain available." : session.models_enabled ? "Saved context is loaded per request. Send a message to begin." : "Model access is disabled. Saved conversations remain available; no model request will be sent.", !session.models_enabled);
      updateChatControls();
      return session;
    } catch (error) {
      session = null;
      $("chat-role").replaceChildren(new Option("Assistant service unavailable", ""));
      chatStatus(`${error.message} No assistant reply has been generated.`, true);
      const retry = element("button", "text-button", "Reconnect to local service"); retry.type = "button";
      retry.addEventListener("click", () => openChat(null, retry));
      $("chat-status").append(document.createElement("br"), retry);
      updateChatControls();
      return null;
    } finally { sessionPromise = null; }
  })();
  return sessionPromise;
}
function deskRole() {
  return session?.roles.find((role) => ["desk_helper", "desk-helper", "desk"].includes(role.id)) || session?.roles.find((role) => role.model.toLowerCase().includes("opus")) || session?.roles[0];
}
async function openChat(agentId = null, opener = null) {
  drawerOpener = opener || document.activeElement;
  $("chat-drawer").hidden = false;
  $("chat-launcher").hidden = true;
  $("close-chat").focus();
  if (sending) return;
  if (!session) await initializeSession();
  if (!session) return;
  const role = agentId ? session.roles.find((candidate) => candidate.id === agentId || candidate.worker_agent_id === agentId) : deskRole();
  const chosen = role || deskRole();
  if (chosen && chosen.id !== chatRole) await changeChatRole(chosen.id);
  else if (chosen && !$("chat-messages").childElementCount) showWelcome();
  if (agentId && !role && chatMode === "assistant") {
    const agent = snapshot?.agents.find((candidate) => candidate.id === agentId);
    chatStatus(`A dedicated assistant for ${agent?.name || "this worker"} is not configured. The selected desk assistant can discuss its saved context.`, true);
    if (!$("chat-input").value) $("chat-input").value = `Explain the recorded work of ${agent?.name || agentId}, including its evidence and remaining limitations.`;
  }
  updateChatControls();
}
function closeChat() {
  $("chat-drawer").hidden = true; $("chat-launcher").hidden = false;
  if (drawerOpener?.isConnected) drawerOpener.focus();
}
function showWelcome() {
  const list = $("chat-messages"); list.replaceChildren();
  const welcome = element("div", "chat-welcome");
  welcome.append(element("h3", "", "Bring the context together."), element("p", "", "Ask about the work, the evidence or the next decision. Replies use saved project context and may be incomplete."));
  for (const question of ["What is the project working on now?", "Which next step is blocked, and why?", "What evidence is still missing?"]) {
    const button = element("button", "suggestion", question); button.type = "button";
    button.addEventListener("click", () => { $("chat-input").value = question; updateChatControls(); $("chat-input").focus(); });
    welcome.append(button);
  }
  list.append(welcome);
}
function contextDetails(context, model, cost, createdAt) {
  const details = element("details", "message-context");
  details.append(element("summary", "", "Model, context & cost estimate"));
  if (model) details.append(element("p", "", `Model: ${model}`));
  if (createdAt) details.append(element("p", "", `Recorded: ${dateLabel(createdAt)}`));
  if (context && typeof context === "object") {
    if (context.observed_at) details.append(element("p", "", `Context observed: ${dateLabel(context.observed_at)}`));
    if (context.hash) details.append(element("p", "", `Context identity: ${context.hash}`));
    if (Array.isArray(context.sources) && context.sources.length) {
      const sources = element("ul");
      for (const source of context.sources) if (typeof source === "string") sources.append(element("li", "", source));
      details.append(sources);
    }
  }
  details.append(element("p", "", `Conservative request cost estimate: ${typeof cost === "number" ? money(cost / 1e6) : "Unknown"}`));
  return details;
}
function appendMessage(message) {
  const role = message.role === "user" ? "user" : message.role === "assistant" ? "assistant" : "error";
  const item = element("article", `message message-${role}`);
  const label = role === "user" ? "You" : role === "assistant" ? roleLabel(currentRole()) : "Request state";
  item.append(element("div", "message-label", label), element("div", "message-content", typeof message.content === "string" ? message.content : "No message text recorded."));
  if (role === "assistant") item.append(contextDetails(message.context, message.model, message.cost_micro_usd, message.created_at));
  $("chat-messages").append(item);
  $("chat-messages").scrollTop = $("chat-messages").scrollHeight;
}
function renderConversation(conversation) {
  $("chat-messages").replaceChildren();
  if (!conversation || !Array.isArray(conversation.messages) || !conversation.messages.length) { showWelcome(); return; }
  for (const message of conversation.messages) appendMessage(message);
}
async function loadConversations() {
  const version = ++historyVersion;
  const requestedRole = chatRole;
  if (!requestedRole) return;
  historyLoading = true; updateChatControls();
  try {
    const response = await fetch(`/api/conversations?agent_id=${encodeURIComponent(requestedRole)}`, { cache: "no-store", credentials: "same-origin", signal: AbortSignal.timeout(5000) });
    const data = await responseJson(response, "Saved conversations are unavailable.");
    if (!Array.isArray(data.conversations)) throw new Error("The conversation history response is incomplete.");
    if (version !== historyVersion || requestedRole !== chatRole) return;
    conversations = data.conversations.filter((item) => item && item.agent_id === requestedRole && typeof item.id === "string");
    $("conversation-history").replaceChildren(new Option("New conversation", ""));
    for (const conversation of conversations) {
      const first = conversation.messages?.find((message) => message.role === "user")?.content;
      const title = typeof first === "string" ? first.slice(0, 44) : dateLabel(conversation.updated_at);
      $("conversation-history").append(new Option(title, conversation.id));
    }
    if (conversationId && conversations.some((item) => item.id === conversationId)) $("conversation-history").value = conversationId;
  } catch (error) {
    if (version === historyVersion) chatStatus(`${error.message} No model request was made.`, true);
  } finally { if (version === historyVersion) { historyLoading = false; updateChatControls(); } }
}
async function changeChatRole(id) {
  if (sending) return;
  chatRole = id; conversationId = null; conversations = [];
  if (id === "desk_helper") chatMode = "assistant";
  const role = currentRole();
  $("chat-role").value = id;
  $("chat-title").textContent = chatMode === "inbox" ? `Worker inbox: ${role?.name || "Unknown"}` : roleLabel(role);
  $("chat-model").textContent = chatMode === "inbox" ? "Original worker inquiries / no model call" : role?.model || "Model not reported";
  $("chat-role-description").textContent = role?.description || "Reads saved project context.";
  $("chat-input").value = "";
  renderChatMode();
  if (chatMode === "assistant") chatStatus(session?.model_calls_paused ? "Project model calls are paused. Saved conversations remain available." : session?.models_enabled ? "A new contextual assistant, grounded in saved project records." : "Model access is disabled. No model request will be sent.", !session?.models_enabled);
  if (chatMode === "inbox") await loadInbox(); else await loadConversations();
}
async function sendChat(event) {
  event.preventDefault();
  if (chatMode === "inbox") { await sendInbox(); return; }
  const message = $("chat-input").value.trim();
  if (sending || historyLoading || !session?.models_enabled || session?.model_calls_paused || !currentRole() || !message || message.length > 4000) return;
  const requestId = crypto.randomUUID();
  const roleId = chatRole;
  sending = true; updateChatControls();
  if (!conversationId) $("chat-messages").replaceChildren();
  appendMessage({ role: "user", content: message });
  $("chat-input").value = "";
  chatStatus("The assistant is reading saved context. One model request is in progress.");
  try {
    // No automatic retry or client timeout: a lost connection can leave a paid outcome unknown.
    const response = await fetch("/api/chat", {
      method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json", "X-Quanto-CSRF": session.csrf_token },
      body: JSON.stringify({ agent_id: roleId, conversation_id: conversationId, request_id: requestId, message }),
    });
    const data = await responseJson(response, "The assistant request did not return a valid response.");
    if (data.request_id !== requestId || typeof data.status !== "string") throw new Error("The assistant response could not be matched to this request.");
    if (typeof data.conversation_id === "string") conversationId = data.conversation_id;
    const complete = ["completed", "complete", "ok", "success"].includes(data.status);
    if (typeof data.reply === "string" && data.reply) appendMessage({ role: "assistant", content: data.reply, model: data.model, context: data.context, cost_micro_usd: data.cost_micro_usd });
    if (!complete || !data.reply) {
      const detail = typeof data.error === "string" ? data.error : `The request ended with state: ${readable(data.status)}.`;
      appendMessage({ role: "error", content: `${detail} The output is not a completed assistant reply.` });
      chatStatus("Request incomplete. No retry was made. Inspect saved history before another send.", true);
    } else chatStatus(`Reply recorded. Conservative cost estimate: ${typeof data.cost_micro_usd === "number" ? money(data.cost_micro_usd / 1e6) : "Unknown"}.`);
    if (data.budget) renderBudget(data.budget);
    await loadConversations();
    await refreshBudgetAfterRequest();
  } catch (error) {
    appendMessage({ role: "error", content: `${error.message} Delivery or completion may be unknown. Check saved history before sending again. No automatic retry was made.` });
    chatStatus("Request outcome needs verification. No retry was made.", true);
  } finally { sending = false; updateChatControls(); }
}

async function checkHealth() {
  $("check-health").disabled = true;
  try {
    const response = await fetch("/api/health-details", { cache: "no-store", signal: AbortSignal.timeout(5000) });
    const data = await responseJson(response, "Detailed local health is unavailable.");
    if (!data || typeof data !== "object" || Array.isArray(data)) throw new Error("Local health metadata is invalid.");
    const status = typeof data.status === "string" ? readable(data.status) : "Observed";
    $("health-state").textContent = status;
    $("health-header").textContent = `Health: ${status}`;
    $("health-dot").className = `signal-dot${["ok", "healthy", "running"].includes(data.status) ? " healthy" : ""}`;
    $("health-summary").textContent = typeof data.summary === "string" ? data.summary : "Local health metadata was received. Review the recorded checks below; service reachability alone does not verify continuous monitoring.";
    $("health-details").replaceChildren();
    const add = (label, value) => { const row = element("div"); row.append(element("dt", "", readable(label)), element("dd", "", String(value))); $("health-details").append(row); };
    for (const [key, value] of Object.entries(data)) {
      if (["status", "summary"].includes(key)) continue;
      if (["string", "number", "boolean"].includes(typeof value)) add(key, key.includes("_at") ? dateLabel(value) : value);
    }
    if (Array.isArray(data.checks)) for (const check of data.checks) if (check && typeof check.name === "string") add(check.name, check.status || check.detail || "Unknown");
  } catch (error) {
    $("health-state").textContent = "Unavailable"; $("health-header").textContent = "Health unavailable";
    $("health-dot").className = "signal-dot issue";
    $("health-summary").textContent = `${error.message} Continuous monitoring is not verified by this page.`;
    $("health-details").replaceChildren();
  } finally { $("check-health").disabled = false; }
}

async function toggleModelCalls() {
  if (!session || sending || changingModelCalls) return;
  changingModelCalls = true; updateChatControls();
  const action = session.model_calls_paused ? "resume" : "pause";
  try {
    const response = await fetch(`/api/model-calls/${action}`, { method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json", "X-Quanto-CSRF": session.csrf_token }, body: "{}" });
    await responseJson(response, "The model-call setting could not be confirmed.");
    await initializeSession();
  } catch (error) { chatStatus(`${error.message} The current model-call setting needs verification.`, true); }
  finally { changingModelCalls = false; updateChatControls(); }
}

async function refreshBudgetAfterRequest() {
  try {
    const response = await fetch("/api/session", { cache: "no-store", credentials: "same-origin", signal: AbortSignal.timeout(5000) });
    const data = await responseJson(response, "Budget observation is unavailable.");
    if (!session || typeof data.csrf_token !== "string") throw new Error("Session observation is incomplete.");
    session.csrf_token = data.csrf_token;
    session.models_enabled = data.models_enabled;
    session.model_calls_paused = data.model_calls_paused;
    renderBudget(data.budget);
    updateChatControls();
  } catch {
    $("budget-scope").textContent = "Budget refresh failed after the request. Values above retain the last available observation.";
  }
}

function renderChatMode() {
  const inbox = chatMode === "inbox";
  $("assistant-mode").classList.toggle("selected", !inbox);
  $("assistant-mode").setAttribute("aria-pressed", String(!inbox));
  $("inbox-mode").classList.toggle("selected", inbox);
  $("inbox-mode").setAttribute("aria-pressed", String(inbox));
  document.querySelector(".conversation-controls").hidden = inbox;
  document.querySelector(".model-controls").hidden = inbox;
  $("inbox-toolbar").hidden = !inbox;
  $("chat-title").textContent = inbox ? `Worker inbox: ${currentRole()?.name || "Unknown"}` : roleLabel(currentRole());
  $("chat-model").textContent = inbox ? "Original worker inquiries / no model call" : currentRole()?.model || "Model not reported";
  $("assistant-disclosure").textContent = inbox ? "This inbox records a question for the original worker. The lead must retrieve it and record an actual reply with its source. Submission does not confirm delivery or an answer." : "These are new contextual assistants with saved project context, not the original Codex workers. Messages use the shared outside-model budget.";
  $("chat-input-label").textContent = inbox ? "Leave a question for the recorded worker" : "Message your contextual assistant";
  $("chat-input").placeholder = inbox ? "Leave a question about this worker’s recorded work…" : "Ask about the project, a task or its evidence…";
  $("composer-note").textContent = inbox ? "Records an inquiry without a model call. Actual replies include their recorded source." : "One request per send. Failed paid requests are never retried automatically.";
  if (inbox) { inquiries = []; renderInbox(); chatStatus("Questions wait here until the lead records a real worker response."); }
  else showWelcome();
  updateChatControls();
}
async function switchChatMode(mode) {
  if (sending || !session || (mode === "inbox" && chatRole === "desk_helper") || mode === chatMode) return;
  chatMode = mode; conversationId = null; historyVersion += 1; historyLoading = false;
  $("chat-input").value = "";
  renderChatMode();
  if (mode === "inbox") await loadInbox(); else { chatStatus("A contextual assistant using saved project records; not the original worker."); await loadConversations(); }
}
function renderInbox() {
  const list = $("chat-messages"); list.replaceChildren();
  if (!inquiries.length) {
    const welcome = element("div", "chat-welcome");
    welcome.append(element("h3", "", "A question for the worker."), element("p", "", "No inquiries are recorded for this worker in your session. Leave a question below; pending questions and actual recorded replies will appear here.")); list.append(welcome); return;
  }
  for (const inquiry of inquiries) {
    const item = element("article", "inquiry");
    const heading = element("div", "inquiry-heading");
    heading.append(element("span", "", dateLabel(inquiry.created_at)), state(inquiry.status));
    item.append(heading, element("p", "inquiry-message", inquiry.message));
    if (inquiry.reply && typeof inquiry.reply.content === "string") {
      const reply = element("div", "worker-reply");
      reply.append(element("p", "worker-reply-label", `Recorded reply / ${inquiry.reply.actor || "Actor unreported"}`), element("p", "message-content", inquiry.reply.content));
      const source = element("details", "message-context");
      source.append(element("summary", "", "Reply provenance"), element("p", "", `Source: ${inquiry.reply.source_ref || "Unreported"}`), element("p", "", `Recorded ${dateLabel(inquiry.reply.created_at)}`));
      reply.append(source); item.append(reply);
    } else item.append(element("p", "inquiry-pending", "Pending a recorded worker reply. Delivery is not confirmed."));
    list.append(item);
  }
}
async function loadInbox() {
  if (!session || !chatRole || chatRole === "desk_helper" || chatMode !== "inbox") return;
  const roleId = chatRole;
  const version = ++historyVersion;
  inboxFetching = true; $("refresh-inbox").disabled = true;
  try {
    const response = await fetch(`/api/inbox?agent_id=${encodeURIComponent(roleId)}`, { cache: "no-store", credentials: "same-origin", signal: AbortSignal.timeout(5000) });
    const data = await responseJson(response, "Recorded worker inquiries are unavailable.");
    if (!Array.isArray(data.inquiries)) throw new Error("The worker inbox response is incomplete.");
    if (version !== historyVersion || roleId !== chatRole || chatMode !== "inbox") return;
    inquiries = data.inquiries.filter((item) => item && item.agent_id === roleId && typeof item.message === "string");
    renderInbox();
    chatStatus(`Inbox checked ${dateLabel(new Date().toISOString())}. Replies appear only when actually recorded.`);
  } catch (error) { if (version === historyVersion) chatStatus(`${error.message} No worker answer is inferred.`, true); }
  finally { inboxFetching = false; $("refresh-inbox").disabled = false; }
}
async function sendInbox() {
  const message = $("chat-input").value.trim();
  if (sending || !session || !currentRole() || chatRole === "desk_helper" || !message || message.length > 4000) return;
  const requestId = crypto.randomUUID();
  sending = true; updateChatControls();
  chatStatus("Recording your inquiry in the worker inbox…");
  try {
    const response = await fetch("/api/inbox", { method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json", "X-Quanto-CSRF": session.csrf_token }, body: JSON.stringify({ agent_id: chatRole, request_id: requestId, message }) });
    const data = await responseJson(response, "The inquiry could not be confirmed.");
    if (data.request_id !== requestId || data.status !== "pending") throw new Error("The inquiry receipt could not be verified.");
    $("chat-input").value = "";
    await loadInbox();
    chatStatus("Inquiry recorded as pending. No answer or delivery to a worker is claimed.");
  } catch (error) { chatStatus(`${error.message} Check the inbox before submitting the question again.`, true); }
  finally { sending = false; updateChatControls(); }
}

$("refresh").addEventListener("click", () => { refresh(); refreshCaptureMetadata(); });
$("pause").addEventListener("click", () => { paused = !paused; $("pause").setAttribute("aria-pressed", String(paused)); $("pause").textContent = paused ? "Resume progress refresh" : "Pause progress refresh"; updateFreshness(); if (!paused) refresh(); });
$("agent-search").addEventListener("input", renderWork);
$("board-view").addEventListener("click", () => switchWorkView("board"));
$("dependency-view").addEventListener("click", () => switchWorkView("map"));
for (const button of document.querySelectorAll(".board-filter")) button.addEventListener("click", () => {
  workFilter = button.dataset.filter;
  for (const filter of document.querySelectorAll(".board-filter")) { const selected = filter === button; filter.classList.toggle("selected", selected); filter.setAttribute("aria-pressed", String(selected)); }
  renderWork();
});
for (const button of document.querySelectorAll(".open-helper")) button.addEventListener("click", () => openChat(null, button));
$("close-chat").addEventListener("click", closeChat);
document.addEventListener("keydown", (event) => { if (event.key === "Escape" && !$("chat-drawer").hidden) closeChat(); });
$("chat-role").addEventListener("change", () => changeChatRole($("chat-role").value));
$("conversation-history").addEventListener("change", () => {
  conversationId = $("conversation-history").value || null;
  renderConversation(conversations.find((conversation) => conversation.id === conversationId));
  chatStatus(conversationId ? "Saved conversation loaded. Its context may precede the current snapshot." : "New conversation. No request has been sent.");
});
$("new-conversation").addEventListener("click", () => { conversationId = null; $("conversation-history").value = ""; showWelcome(); chatStatus("New conversation. No request has been sent."); });
$("chat-form").addEventListener("submit", sendChat);
$("chat-input").addEventListener("input", updateChatControls);
$("chat-input").addEventListener("keydown", (event) => { if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) sendChat(event); });
$("check-health").addEventListener("click", checkHealth);
$("toggle-model-calls").addEventListener("click", toggleModelCalls);
$("assistant-mode").addEventListener("click", () => switchChatMode("assistant"));
$("inbox-mode").addEventListener("click", () => switchChatMode("inbox"));
$("refresh-inbox").addEventListener("click", loadInbox);
setInterval(() => { if (!paused) refresh(); }, 2000);
setInterval(updateFreshness, 1000);
setInterval(updateCaptureCountdown, 1000);
setInterval(() => { if (!document.hidden) refreshCaptureMetadata(); }, 10000);
document.addEventListener("visibilitychange", () => { if (!document.hidden) { updateCaptureCountdown(); refreshCaptureMetadata(); } });
setInterval(() => { if (!paused) checkHealth(); }, 30000);
setInterval(() => { if (!$("chat-drawer").hidden && chatMode === "inbox" && !sending && !inboxFetching) loadInbox(); }, 15000);
renderWork(); refresh(); checkHealth(); refreshCaptureMetadata();
