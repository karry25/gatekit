const HDR = {"Content-Type": "application/json", "X-Gatekit-Local": "1"};

// --- tabs ---
document.querySelectorAll(".tab").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
    if (btn.dataset.tab === "ratings") loadRatings();
  });
});

// --- rating modal ---
let rateCtx = null, rateValue = 0;
const modal = document.getElementById("rate-modal");
function openRate(kind, subject) {
  rateCtx = {kind, subject}; rateValue = 0;
  document.getElementById("rate-title").textContent = "Rate: " + subject.slice(0, 60);
  document.getElementById("rate-note").value = "";
  paintStars();
  modal.classList.remove("hidden");
}
function paintStars() {
  const el = document.getElementById("rate-stars");
  el.innerHTML = "";
  for (let i = 1; i <= 5; i++) {
    const s = document.createElement("span");
    s.textContent = "\u2605";
    if (i <= rateValue) s.classList.add("lit");
    s.addEventListener("click", () => { rateValue = i; paintStars(); });
    el.appendChild(s);
  }
}
document.getElementById("rate-cancel").addEventListener("click", () => modal.classList.add("hidden"));
document.getElementById("rate-save").addEventListener("click", async () => {
  if (!rateValue) { alert("Pick 1-5 stars first"); return; }
  await fetch("/api/rate", {method: "POST", headers: HDR, body: JSON.stringify({
    kind: rateCtx.kind, subject: rateCtx.subject, rating: rateValue,
    note: document.getElementById("rate-note").value})});
  modal.classList.add("hidden");
});
function rateButton(kind, subject) {
  const b = document.createElement("button");
  b.className = "ghost rate-btn";
  b.textContent = "Rate this";
  b.addEventListener("click", () => openRate(kind, subject));
  return b;
}

// --- helpers ---
function setStatus(id, msg, isErr) {
  const el = document.getElementById(id);
  el.textContent = msg || "";
  el.className = "status" + (isErr ? " err" : "");
}
function esc(s) {
  return String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
}

function renderPreflight(container, rep, subject) {
  if (rep.error) { setStatus("scan-status", rep.error, true); return; }
  let html = "";
  html += '<div class="verdict ' + (rep.ok ? "ok" : "bad") + '">' +
          (rep.ok ? "CLEAR" : "BLOCKED") + "</div>";
  html += '<div class="meta-grid">';
  html += "<span>preflight " + esc(rep.version || "") + "</span>";
  html += "<span>" + esc(rep.root || "") + "</span>";
  if (rep.git && rep.git.is_repo)
    html += "<span>git: " + esc(rep.git.branch || "?") + ", " +
            (rep.git.uncommitted_files || 0) + " uncommitted</span>";
  else html += "<span>not a git repo</span>";
  if (rep.project && rep.project.length)
    html += "<span>project: " + esc(rep.project.join(", ")) + "</span>";
  html += "</div>";
  if (rep.suggested_checks && rep.suggested_checks.length) {
    html += '<p class="muted" style="margin:12px 0 4px">Suggested checks:</p>';
    rep.suggested_checks.forEach(c => { html += '<div class="finding"><span class="badge note">check</span><span><code>' + esc(c) + "</code></span></div>"; });
  }
  (rep.errors || []).forEach(e => {
    let msg = e.kind === "secret" ? ("secret (" + e.pattern + ") at " + e.file + ":" + e.line)
            : e.kind === "env-tracked" ? (e.file + " is tracked by git")
            : ("check failed: " + (e.command || e.kind));
    html += '<div class="finding"><span class="badge err">error</span><span>' + esc(msg) + "</span></div>";
  });
  (rep.warnings || []).forEach(w => {
    html += '<div class="finding"><span class="badge warn">warn</span><span>' +
            esc(w.kind + " at " + w.file + ":" + w.line) + "</span></div>";
  });
  if (rep.todo_fixme_total)
    html += '<div class="finding"><span class="badge note">note</span><span>' +
            esc(rep.todo_fixme_total + " TODO/FIXME markers") + "</span></div>";
  container.innerHTML = html;
  container.appendChild(rateButton("scan", subject));
}

function renderBrief(container, text, subject, statusId) {
  // brief --json returns structured data; rebuild readable markdown client-side
  if (text.error) { setStatus(statusId, text.error, true); return; }
  let md = "# Repo brief: " + text.name + "\n\n## Stack\n- " +
    (text.stack && text.stack.length ? text.stack.join(", ") : "unrecognized") + "\n";
  if (text.extensions && text.extensions.length)
    md += "- files by extension: " + text.extensions.slice(0,8).map(e => e[0] + " x" + e[1]).join(", ") + "\n";
  md += "\n## Layout\n" + (text.tree || []).map(l => "    " + l).join("\n") + "\n";
  if (text.key_files && text.key_files.length) {
    md += "\n## Key files\n";
    text.key_files.forEach(k => { md += "- " + k[0] + ": " + k[1] + "\n"; });
  }
  if (text.git && text.git.branch) {
    md += "\n## Git\n- branch: " + text.git.branch + "\n";
    if (text.git.last_commit) md += "- last commit: " + text.git.last_commit + "\n";
    if (text.git.commits) md += "- commits: " + text.git.commits + "\n";
  }
  if (text.suggested_checks && text.suggested_checks.length) {
    md += "\n## Checks that prove this repo works\n";
    text.suggested_checks.forEach(c => { md += "- `" + c + "`\n"; });
  }
  md += "\n## Working agreement\n- Run the checks above before calling any change done.\n" +
        "- Show evidence (test output, real results), not confidence.\n";
  const pre = document.createElement("pre");
  pre.className = "output";
  pre.textContent = md;
  const copy = document.createElement("button");
  copy.className = "ghost rate-btn";
  copy.textContent = "Copy brief";
  copy.addEventListener("click", () => navigator.clipboard.writeText(md));
  container.innerHTML = "";
  container.appendChild(pre);
  const row = document.createElement("div");
  row.className = "row";
  row.appendChild(copy);
  row.appendChild(rateButton("brief", subject));
  container.appendChild(row);
}

// --- scan tab ---
document.getElementById("scan-btn").addEventListener("click", async () => {
  const path = document.getElementById("scan-path").value.trim();
  if (!path) { setStatus("scan-status", "Enter a folder path first", true); return; }
  setStatus("scan-status", "Scanning (read-only)... ");
  document.getElementById("scan-result").innerHTML = "";
  try {
    const r = await fetch("/api/scan", {method: "POST", headers: HDR, body: JSON.stringify({path})});
    const rep = await r.json();
    setStatus("scan-status", "");
    renderPreflight(document.getElementById("scan-result"), rep, path);
  } catch (e) { setStatus("scan-status", "request failed: " + e, true); }
});
document.getElementById("scan-zip").addEventListener("change", async ev => {
  const f = ev.target.files[0];
  if (!f) return;
  setStatus("scan-status", "Uploading and scanning " + f.name + " ...");
  document.getElementById("scan-result").innerHTML = "";
  try {
    const r = await fetch("/api/upload", {method: "POST",
      headers: {"X-Gatekit-Local": "1", "Content-Type": "application/zip"}, body: f});
    const rep = await r.json();
    if (rep.error) { setStatus("scan-status", rep.error, true); return; }
    setStatus("scan-status", "Scanned uploaded zip (temp folder deleted after).");
    renderPreflight(document.getElementById("scan-result"), rep.preflight || {}, f.name);
    if (rep.brief && !rep.brief.error)
      renderBrief(document.getElementById("brief-result"), rep.brief, f.name, "brief-status");
  } catch (e) { setStatus("scan-status", "upload failed: " + e, true); }
  ev.target.value = "";
});

// --- brief tab ---
document.getElementById("brief-btn").addEventListener("click", async () => {
  const path = document.getElementById("brief-path").value.trim();
  if (!path) { setStatus("brief-status", "Enter a folder path first", true); return; }
  setStatus("brief-status", "Building brief (read-only)...");
  document.getElementById("brief-result").innerHTML = "";
  try {
    const r = await fetch("/api/brief", {method: "POST", headers: HDR, body: JSON.stringify({path})});
    const rep = await r.json();
    setStatus("brief-status", "");
    renderBrief(document.getElementById("brief-result"), rep, path, "brief-status");
  } catch (e) { setStatus("brief-status", "request failed: " + e, true); }
});

// --- workflows tab ---
let workflows = [], currentWf = null;
async function loadWorkflows() {
  const r = await fetch("/api/workflows");
  const data = await r.json();
  workflows = data.workflows || [];
  const list = document.getElementById("workflow-list");
  list.innerHTML = "";
  workflows.forEach(w => {
    const card = document.createElement("div");
    card.className = "wf-card";
    card.innerHTML = "<h3>" + esc(w.title) + "</h3><p>" + esc(w.purpose.slice(0, 150)) +
                     (w.purpose.length > 150 ? "..." : "") + "</p>";
    card.addEventListener("click", () => showWorkflow(w));
    list.appendChild(card);
  });
}
function showWorkflow(w) {
  currentWf = w;
  document.getElementById("wf-detail-card").classList.remove("hidden");
  document.getElementById("wf-output-wrap").classList.add("hidden");
  document.getElementById("wf-title").textContent = w.title;
  document.getElementById("wf-purpose").textContent = w.purpose;
  const box = document.getElementById("wf-inputs");
  box.innerHTML = "";
  if (!w.inputs.length)
    box.innerHTML = '<p class="muted">This workflow has no named inputs - compose to get the full prompt.</p>';
  w.inputs.forEach(inp => {
    const div = document.createElement("div");
    div.className = "wf-input";
    div.innerHTML = "<label><b>" + esc(inp.name) + "</b>" + (inp.optional ? " (optional)" : "") +
      '</label><div class="hint">' + esc(inp.hint) + '</div>';
    const ta = document.createElement("textarea");
    ta.dataset.name = inp.name;
    div.appendChild(ta);
    box.appendChild(div);
  });
  document.getElementById("wf-detail-card").scrollIntoView({behavior: "smooth"});
}
document.getElementById("wf-back").addEventListener("click", () => {
  document.getElementById("wf-detail-card").classList.add("hidden");
});
document.getElementById("wf-render").addEventListener("click", async () => {
  const inputs = {};
  document.querySelectorAll("#wf-inputs textarea").forEach(ta => {
    if (ta.value.trim()) inputs[ta.dataset.name] = ta.value.trim();
  });
  const r = await fetch("/api/render", {method: "POST", headers: HDR,
    body: JSON.stringify({workflow: currentWf.slug, inputs})});
  const data = await r.json();
  if (data.error) { alert(data.error); return; }
  document.getElementById("wf-output").textContent = data.prompt;
  document.getElementById("wf-output-wrap").classList.remove("hidden");
  const wrap = document.getElementById("wf-output-wrap");
  if (!wrap.querySelector(".rate-btn")) wrap.appendChild(rateButton("workflow", currentWf.slug));
});
document.getElementById("wf-copy").addEventListener("click", () => {
  navigator.clipboard.writeText(document.getElementById("wf-output").textContent);
});

// --- ratings tab ---
async function loadRatings() {
  const r = await fetch("/api/ratings");
  const data = await r.json();
  const list = document.getElementById("ratings-list");
  const ratings = (data.ratings || []).slice().reverse();
  if (!ratings.length) {
    list.innerHTML = '<p class="muted">No ratings yet. Rate a scan, brief or workflow prompt and it shows up here.</p>';
    return;
  }
  list.innerHTML = "";
  ratings.forEach(rt => {
    const div = document.createElement("div");
    div.className = "rate-row";
    div.innerHTML = '<span class="stars-sm">' + "\u2605".repeat(rt.rating) + "</span>" +
      "<span><b>" + esc(rt.kind) + "</b> " + esc(rt.subject) + "</span>" +
      '<span class="note">' + esc(rt.note || "") + "</span>" +
      '<span class="when">' + esc(rt.ts) + "</span>";
    list.appendChild(div);
  });
}

loadWorkflows();
