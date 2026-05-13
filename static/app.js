/* =========================================================
   BTP AI — Frontend Application Logic (v2 + Metadata)
   ========================================================= */

"use strict";

// ── State ────────────────────────────────────────────────
let selectedFiles = [];

// ── DOM Refs ─────────────────────────────────────────────
const dropZone      = document.getElementById("dropZone");
const fileInput     = document.getElementById("fileInput");
const fileList      = document.getElementById("fileList");
const uploadBtn     = document.getElementById("uploadBtn");
const projectInput  = document.getElementById("projectInput");
const lotInput      = document.getElementById("lotInput");
const auteurInput   = document.getElementById("auteurInput");
const progressWrap  = document.getElementById("progressWrap");
const progressFill  = document.getElementById("progressFill");
const progressLabel = document.getElementById("progressLabel");
const uploadResults = document.getElementById("uploadResults");
const uploadResultsList = document.getElementById("uploadResultsList");

const queryInput  = document.getElementById("queryInput");
const queryBtn    = document.getElementById("queryBtn");
const answerCard  = document.getElementById("answerCard");
const answerBody  = document.getElementById("answerBody");
const sourcesList = document.getElementById("sourcesList");
const loadingCard = document.getElementById("loadingCard");
const copyBtn     = document.getElementById("copyBtn");

const statusPill  = document.getElementById("statusPill");
const statusText  = document.getElementById("statusText");
const resetBtn    = document.getElementById("resetBtn");
const toast       = document.getElementById("toast");

// ── Navigation ───────────────────────────────────────────

const pageTitles = {
  ingest: ["Document Upload", "Ingest PDFs, TXT, and DOCX files into the knowledge base"],
  query:  ["AI Query",        "Ask natural language questions about your construction documents"],
  email:  ["Connecteur Email",        "Importer des emails Gmail et Outlook dans la base de connaissances"],
  stats:  ["Knowledge Base",  "Overview of indexed documents and projects"],
};

document.querySelectorAll(".nav-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    const panel = btn.dataset.panel;
    document.getElementById(`panel-${panel}`).classList.add("active");
    const [title, sub] = pageTitles[panel];
    document.getElementById("pageTitle").textContent = title;
    document.getElementById("pageSub").textContent   = sub;
    if (panel === "stats") loadStats();
  });
});

// ── Drag & Drop ──────────────────────────────────────────

dropZone.addEventListener("click", () => fileInput.click());

dropZone.addEventListener("dragover", e => {
  e.preventDefault();
  dropZone.classList.add("drag-over");
});

dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));

dropZone.addEventListener("drop", e => {
  e.preventDefault();
  dropZone.classList.remove("drag-over");
  addFiles([...e.dataTransfer.files]);
});

fileInput.addEventListener("change", () => addFiles([...fileInput.files]));

function addFiles(files) {
  const allowed = ["pdf", "txt", "docx", "png", "jpg", "jpeg"];
  files.forEach(file => {
    const ext = file.name.split(".").pop().toLowerCase();
    if (!allowed.includes(ext)) {
      showToast(`❌ ${file.name}: format non supporté`, "error");
      return;
    }
    if (!selectedFiles.find(f => f.name === file.name)) {
      selectedFiles.push(file);
    }
  });
  renderFileList();
}

function renderFileList() {
  fileList.innerHTML = "";
  selectedFiles.forEach((file, i) => {
    const ext  = file.name.split(".").pop().toUpperCase();
    const size = formatBytes(file.size);
    const item = document.createElement("div");
    item.className = "file-item";
    item.innerHTML = `
      <span class="file-item-icon">
        <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
      </span>
      <span class="file-item-name">${file.name}</span>
      <span class="file-item-size">${ext} · ${size}</span>
      <button class="file-item-rm" data-index="${i}" title="Supprimer">✕</button>
    `;
    fileList.appendChild(item);
  });

  fileList.querySelectorAll(".file-item-rm").forEach(btn => {
    btn.addEventListener("click", () => {
      selectedFiles.splice(parseInt(btn.dataset.index), 1);
      renderFileList();
    });
  });

  uploadBtn.disabled = selectedFiles.length === 0;
}

// ── Helpers: get metadata values ─────────────────────────

function getCriticite() {
  const checked = document.querySelector('input[name="criticite"]:checked');
  return checked ? checked.value : "Normale";
}

// ── Upload ───────────────────────────────────────────────

uploadBtn.addEventListener("click", async () => {
  if (selectedFiles.length === 0) return;

  const project   = projectInput.value.trim() || "Projet Général";
  const lot       = lotInput.value.trim() || "";
  const auteur    = auteurInput.value.trim() || "";
  const criticite = getCriticite();

  const formData = new FormData();
  selectedFiles.forEach(f => formData.append("files", f));
  formData.append("project",   project);
  formData.append("lot",       lot);
  formData.append("auteur",    auteur);
  formData.append("criticite", criticite);

  setStatus("busy", "Traitement…");
  uploadBtn.disabled = true;
  progressWrap.classList.remove("hidden");
  uploadResults.style.display = "none";

  let progress = 0;
  const steps = ["Extraction du texte…", "Nettoyage…", "Découpage en chunks…", "Génération embeddings…", "Stockage vecteurs…"];
  let stepIdx = 0;
  const interval = setInterval(() => {
    progress = Math.min(progress + Math.random() * 18, 90);
    progressFill.style.width = progress + "%";
    if (stepIdx < steps.length) progressLabel.textContent = steps[stepIdx++];
  }, 600);

  try {
    const res  = await fetch("/upload", { method: "POST", body: formData });
    const data = await res.json();

    clearInterval(interval);
    progressFill.style.width = "100%";
    progressLabel.textContent = "Terminé !";
    setTimeout(() => progressWrap.classList.add("hidden"), 800);

    if (data.error) throw new Error(data.error);

    renderUploadResults(data.results);
    showToast(`✅ ${data.message}`, "success");
    setStatus("ready", "Système prêt");

    selectedFiles = [];
    renderFileList();
    fileInput.value = "";
  } catch (err) {
    clearInterval(interval);
    progressWrap.classList.add("hidden");
    showToast(`❌ Erreur : ${err.message}`, "error");
    setStatus("error", "Erreur");
  }

  uploadBtn.disabled = selectedFiles.length === 0;
});

function renderUploadResults(results) {
  uploadResults.style.display = "block";
  uploadResultsList.innerHTML = "";
  results.forEach(r => {
    const item = document.createElement("div");
    item.className = "result-item";
    item.innerHTML = `
      <span class="result-name">${r.filename}</span>
      <span class="result-badge ${r.status}">${r.status === "success" ? "✓ OK" : "✗ Erreur"}</span>
      <span class="result-chunks">${r.status === "success" ? `${r.chunks} chunks` : r.message}</span>
    `;
    uploadResultsList.appendChild(item);
  });
}

// ── Query ────────────────────────────────────────────────

document.querySelectorAll(".suggest-pill").forEach(pill => {
  pill.addEventListener("click", () => {
    queryInput.value = pill.dataset.q;
    queryInput.focus();
  });
});

queryInput.addEventListener("keydown", e => {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) runQuery();
});

queryBtn.addEventListener("click", runQuery);

async function runQuery() {
  const question = queryInput.value.trim();
  if (!question) return;

  setStatus("busy", "Recherche…");
  queryBtn.disabled = true;
  answerCard.classList.add("hidden");
  loadingCard.classList.remove("hidden");

  try {
    const res  = await fetch("/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await res.json();

    loadingCard.classList.add("hidden");
    if (data.error) throw new Error(data.error);

    answerBody.textContent = data.answer;
    renderSources(data.sources || []);
    answerCard.classList.remove("hidden");
    setStatus("ready", "Système prêt");
  } catch (err) {
    loadingCard.classList.add("hidden");
    showToast(`❌ Erreur : ${err.message}`, "error");
    setStatus("error", "Erreur");
  }

  queryBtn.disabled = false;
}

function renderSources(sources) {
  sourcesList.innerHTML = "";
  if (!sources.length) {
    sourcesList.innerHTML = `<p style="color:var(--text3);font-size:13px;">Aucune source trouvée.</p>`;
    return;
  }
  sources.forEach(src => {
    const meta = src.metadata || {};
    const criticiteClass = (meta.criticite || "normale").toLowerCase()
      .replace("é", "e").replace("è", "e");

    // Build meta tags
    const tags = [];
    if (meta.lot)       tags.push(`<span class="meta-tag lot">🔧 ${escapeHtml(meta.lot)}</span>`);
    if (meta.auteur)    tags.push(`<span class="meta-tag auteur">👤 ${escapeHtml(meta.auteur)}</span>`);
    if (meta.criticite) tags.push(`<span class="meta-tag crit-${meta.criticite.toLowerCase()}">⚠ ${escapeHtml(meta.criticite)}</span>`);

    const item = document.createElement("div");
    item.className = "source-item";
    item.innerHTML = `
      <div class="source-header">
        <span class="source-name">📄 ${escapeHtml(src.filename)}</span>
        <span class="source-score">score: ${src.relevance_score}</span>
      </div>
      <div class="source-meta">${src.project ? `Projet: ${escapeHtml(src.project)}` : ""} ${src.file_type ? `· ${src.file_type.toUpperCase()}` : ""}</div>
      ${tags.length ? `<div class="meta-tags">${tags.join("")}</div>` : ""}
      <div class="source-excerpt">${escapeHtml(src.excerpt)}</div>
    `;
    sourcesList.appendChild(item);
  });
}

copyBtn.addEventListener("click", () => {
  navigator.clipboard.writeText(answerBody.textContent).then(() => {
    showToast("✅ Réponse copiée", "success");
  });
});

// ── Stats / Knowledge Base ───────────────────────────────

let allDocsData = [];

async function loadStats() {
  try {
    // Fetch stats and knowledge info in parallel
    const [statsRes, knowledgeRes] = await Promise.all([
      fetch("/stats"),
      fetch("/knowledge"),
    ]);
    const stats     = await statsRes.json();
    const knowledge = await knowledgeRes.json();

    // ── Stats counters (user docs only) ──
    const userDocs = (stats.documents || []).filter(d => !d.source.startsWith("[BASE DTU]"));
    const userChunks = (stats.total_chunks || 0) - (knowledge.summary.total || 0);

    document.getElementById("statChunks").textContent   = Math.max(0, userChunks);
    document.getElementById("statDocs").textContent     = userDocs.length;
    document.getElementById("statProjects").textContent = [...new Set(userDocs.map(d => d.project).filter(Boolean))].length;

    // ── DTU Knowledge Grid ──
    renderDtuGrid(knowledge.categories, knowledge.summary.total);

    // ── User docs table ──
    allDocsData = userDocs;
    renderDocsTable(allDocsData);

  } catch (err) {
    showToast("Impossible de charger les stats", "error");
  }
}

function renderDtuGrid(categories, total) {
  const grid = document.getElementById("dtuGrid");
  if (!grid) return;

  const totalCard = `
    <div class="dtu-card" style="border-color:rgba(240,165,0,0.3);background:rgba(240,165,0,0.05)">
      <div class="dtu-card-label">📚 Total Base DTU</div>
      <div class="dtu-card-count">${total}</div>
      <div class="dtu-card-sub">fiches de connaissances</div>
      <span class="dtu-loaded-badge">✓ Chargée</span>
    </div>
  `;

  const categoryCards = categories.map(cat => `
    <div class="dtu-card">
      <div class="dtu-card-label">${cat.label}</div>
      <div class="dtu-card-count">${cat.count}</div>
      <div class="dtu-card-sub">fiches</div>
    </div>
  `).join("");

  grid.innerHTML = totalCard + categoryCards;
}

function renderDocsTable(docs) {
  const tbody = document.getElementById("docsTableBody");
  if (!docs.length) {
    tbody.innerHTML = `<tr><td colspan="7" class="doc-empty">Aucun document utilisateur indexé.<br><span style="font-size:12px;color:var(--text3)">Uploadez des fichiers via l'onglet "Upload Docs"</span></td></tr>`;
    return;
  }

  tbody.innerHTML = docs.map(d => {
    const critKey   = (d.criticite || "normale").toLowerCase().replace("é","e").replace("è","e");
    const critLabel = d.criticite || "Normale";
    const date      = d.ingested_at ? d.ingested_at.substring(0, 10) : "—";

    return `
      <tr>
        <td class="td-filename" title="${escapeHtml(d.source)}">${escapeHtml(d.source)}</td>
        <td>${escapeHtml(d.project || "—")}</td>
        <td class="td-lot" title="${escapeHtml(d.lot || "")}">${escapeHtml(d.lot || "—")}</td>
        <td class="td-auteur">${escapeHtml(d.auteur || "—")}</td>
        <td><span class="crit-pill ${critKey}">${critLabel}</span></td>
        <td class="td-chunks">${d.chunk_count ?? "—"}</td>
        <td class="td-date">${date}</td>
      </tr>
    `;
  }).join("");
}

// Live filter (user docs only)
document.getElementById("docsSearch")?.addEventListener("input", e => {
  const q = e.target.value.toLowerCase();
  const filtered = allDocsData.filter(d =>
    (d.source  || "").toLowerCase().includes(q) ||
    (d.lot     || "").toLowerCase().includes(q) ||
    (d.auteur  || "").toLowerCase().includes(q) ||
    (d.project || "").toLowerCase().includes(q)
  );
  renderDocsTable(filtered);
});

// Reload DTU knowledge button
document.getElementById("reloadKnowledgeBtn")?.addEventListener("click", async () => {
  const btn = document.getElementById("reloadKnowledgeBtn");
  btn.disabled = true;
  btn.textContent = "Rechargement…";
  setStatus("busy", "Rechargement DTU…");

  try {
    const res  = await fetch("/reload-knowledge", { method: "POST" });
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    showToast(`✅ ${data.message}`, "success");
    setStatus("ready", "Système prêt");
    loadStats();
  } catch (err) {
    showToast(`❌ Erreur : ${err.message}`, "error");
    setStatus("error", "Erreur");
  }

  btn.disabled = false;
  btn.innerHTML = `<svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.91"/></svg> Recharger`;
});

// ── Reset ────────────────────────────────────────────────

resetBtn.addEventListener("click", async () => {
  if (!confirm("Confirmer la réinitialisation ? Tous les documents indexés seront supprimés.")) return;

  try {
    const res  = await fetch("/reset", { method: "POST" });
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    showToast("🔄 Système réinitialisé.", "success");
    selectedFiles = [];
    renderFileList();
    answerCard.classList.add("hidden");
  } catch (err) {
    showToast(`❌ Erreur reset : ${err.message}`, "error");
  }
});

// ── Helpers ──────────────────────────────────────────────

function setStatus(type, text) {
  statusPill.className = "status-pill";
  if (type === "busy")  statusPill.classList.add("busy");
  if (type === "error") statusPill.classList.add("error");
  statusText.textContent = text;
}

let toastTimer;
function showToast(msg, type = "") {
  toast.textContent = msg;
  toast.className   = `toast ${type}`;
  toast.classList.remove("hidden");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.add("hidden"), 3500);
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / 1048576).toFixed(1) + " MB";
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ════════════════════════════════════════════════════════
// EMAIL CONNECTOR
// ════════════════════════════════════════════════════════

// ── State ────────────────────────────────────────────────
let activeEmailProvider = "gmail";
const emailProviderStatus = { gmail: false, outlook: false };

// ── Tab switching ─────────────────────────────────────────
document.querySelectorAll(".email-tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".email-tab").forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    activeEmailProvider = tab.dataset.provider;

    document.getElementById("config-gmail").classList.toggle("hidden", activeEmailProvider !== "gmail");
    document.getElementById("config-outlook").classList.toggle("hidden", activeEmailProvider !== "outlook");

    updateFetchBtn();
  });
});

// ── Toggle password visibility ────────────────────────────
document.querySelectorAll(".toggle-pwd").forEach(btn => {
  btn.addEventListener("click", () => {
    const input = document.getElementById(btn.dataset.target);
    input.type = input.type === "password" ? "text" : "password";
    btn.textContent = input.type === "password" ? "👁" : "🙈";
  });
});

// ── Gmail Connect ─────────────────────────────────────────
document.getElementById("gmail-connect-btn")?.addEventListener("click", async () => {
  const emailAddr = document.getElementById("gmail-email").value.trim();
  const password  = document.getElementById("gmail-password").value.trim();
  const statusEl  = document.getElementById("gmail-status");

  if (!emailAddr || !password) {
    showToast("⚠️ Email et mot de passe requis", "error");
    return;
  }

  const btn = document.getElementById("gmail-connect-btn");
  btn.disabled = true;
  btn.textContent = "Connexion en cours…";
  statusEl.className = "connect-status hidden";

  try {
    const res  = await fetch("/email/configure", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider: "gmail", email: emailAddr, password }),
    });
    const data = await res.json();

    statusEl.classList.remove("hidden");
    if (data.ok) {
      statusEl.className = "connect-status success";
      statusEl.innerHTML = `✅ Connecté à <strong>${data.email}</strong><br>
        Dossiers disponibles : ${(data.folders || []).slice(0,5).join(", ")}`;
      emailProviderStatus.gmail = true;
      document.getElementById("dot-gmail").classList.add("connected");
      updateFetchBtn();
      showToast("✅ Gmail connecté avec succès", "success");
    } else {
      statusEl.className = "connect-status error";
      statusEl.textContent = `❌ ${data.error || "Échec de la connexion"}`;
      emailProviderStatus.gmail = false;
    }
  } catch (err) {
    statusEl.className = "connect-status error";
    statusEl.textContent = `❌ Erreur réseau : ${err.message}`;
  }

  btn.disabled = false;
  btn.innerHTML = `<svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/></svg> Tester & Connecter Gmail`;
});

// ── Outlook Connect ───────────────────────────────────────
document.getElementById("outlook-connect-btn")?.addEventListener("click", async () => {
  const emailAddr   = document.getElementById("outlook-email").value.trim();
  const password    = document.getElementById("outlook-password").value.trim();
  const serverType  = document.getElementById("outlook-server").value;
  const statusEl    = document.getElementById("outlook-status");

  if (!emailAddr || !password) {
    showToast("⚠️ Email et mot de passe requis", "error");
    return;
  }

  const btn = document.getElementById("outlook-connect-btn");
  btn.disabled = true;
  btn.textContent = "Connexion en cours…";
  statusEl.className = "connect-status hidden";

  try {
    const res  = await fetch("/email/configure", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider: "outlook", email: emailAddr, password, server_type: serverType }),
    });
    const data = await res.json();

    statusEl.classList.remove("hidden");
    if (data.ok) {
      statusEl.className = "connect-status success";
      statusEl.innerHTML = `✅ Connecté à <strong>${data.email}</strong><br>Serveur : ${data.host}`;
      emailProviderStatus.outlook = true;
      document.getElementById("dot-outlook").classList.add("connected");
      updateFetchBtn();
      showToast("✅ Outlook connecté avec succès", "success");
    } else {
      statusEl.className = "connect-status error";
      statusEl.textContent = `❌ ${data.error || "Échec de la connexion"}`;
      emailProviderStatus.outlook = false;
    }
  } catch (err) {
    statusEl.className = "connect-status error";
    statusEl.textContent = `❌ Erreur réseau : ${err.message}`;
  }

  btn.disabled = false;
  btn.innerHTML = `<svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/></svg> Tester & Connecter Outlook`;
});

// ── Fetch emails ──────────────────────────────────────────
document.getElementById("email-fetch-btn")?.addEventListener("click", async () => {
  const provider  = activeEmailProvider;
  const folder    = document.getElementById("email-folder").value;
  const daysBack  = parseInt(document.getElementById("email-days").value);
  const maxEmails = parseInt(document.getElementById("email-max").value);
  const btpOnly   = document.getElementById("email-btp-only").checked;
  const project   = document.getElementById("email-project").value.trim();
  const lot       = document.getElementById("email-lot").value;
  const criticite = document.getElementById("email-criticite").value;

  const btn       = document.getElementById("email-fetch-btn");
  const progressW = document.getElementById("email-progress-wrap");
  const progressF = document.getElementById("email-progress-fill");
  const progressL = document.getElementById("email-progress-label");
  const resultEl  = document.getElementById("email-result");

  btn.disabled = true;
  progressW.classList.remove("hidden");
  resultEl.classList.add("hidden");
  setStatus("busy", "Import emails…");

  // Animated progress
  let pct = 0;
  const steps = ["Connexion IMAP…", "Récupération des emails…", "Analyse contenu BTP…", "Génération embeddings…", "Indexation…"];
  let si = 0;
  const iv = setInterval(() => {
    pct = Math.min(pct + Math.random() * 20, 88);
    progressF.style.width = pct + "%";
    if (si < steps.length) progressL.textContent = steps[si++];
  }, 700);

  try {
    const res  = await fetch("/email/fetch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider, folder, days_back: daysBack, max_emails: maxEmails, btp_only: btpOnly, project, lot, criticite }),
    });
    const data = await res.json();

    clearInterval(iv);
    progressF.style.width = "100%";
    progressL.textContent = "Terminé !";
    setTimeout(() => progressW.classList.add("hidden"), 800);

    resultEl.classList.remove("hidden");
    if (data.error) {
      resultEl.className = "email-result error";
      resultEl.innerHTML = `❌ ${data.error}`;
      setStatus("error", "Erreur");
    } else {
      const s = data.stats;
      resultEl.className = "email-result success";
      resultEl.innerHTML = `
        ✅ <strong>${s.indexed} emails indexés</strong><br>
        📬 Récupérés : ${s.fetched} &nbsp;|&nbsp;
        🏗️ Indexés : ${s.indexed} &nbsp;|&nbsp;
        ⏭ Non-BTP ignorés : ${s.skipped_non_btp} &nbsp;|&nbsp;
        ⚠️ Erreurs : ${s.errors}
      `;
      setStatus("ready", "Système prêt");
      showToast(`✅ ${s.indexed} emails indexés depuis ${provider}`, "success");
      loadEmailIndex();
    }
  } catch (err) {
    clearInterval(iv);
    progressW.classList.add("hidden");
    resultEl.className = "email-result error";
    resultEl.innerHTML = `❌ Erreur : ${err.message}`;
    resultEl.classList.remove("hidden");
    setStatus("error", "Erreur");
  }

  btn.disabled = false;
  updateFetchBtn();
});

// ── Load email index summary ──────────────────────────────
async function loadEmailIndex() {
  try {
    const res  = await fetch("/stats");
    const data = await res.json();
    const emails = (data.documents || []).filter(d => d.file_type === "email");

    const container = document.getElementById("email-index-list");
    if (!emails.length) {
      container.innerHTML = `<p class="doc-empty">Aucun email indexé pour l'instant.</p>`;
      return;
    }

    container.innerHTML = emails.map(e => `
      <div class="email-index-item">
        <div class="email-index-icon">${e.provider === "Gmail" ? "📧" : "📨"}</div>
        <div class="email-index-info">
          <div class="email-index-subject">${escapeHtml(e.source || "Email")}</div>
          <div class="email-index-meta">
            ${e.project ? escapeHtml(e.project) + " · " : ""}
            ${e.auteur ? escapeHtml(e.auteur) + " · " : ""}
            ${e.chunk_count ?? 1} chunk(s) · ${(e.ingested_at || "").substring(0,10)}
          </div>
        </div>
      </div>
    `).join("");
  } catch (_) {}
}

// ── Helpers ───────────────────────────────────────────────
function updateFetchBtn() {
  const btn = document.getElementById("email-fetch-btn");
  if (btn) btn.disabled = !emailProviderStatus[activeEmailProvider];
}

// Check initial email status on page load
(async () => {
  try {
    const res  = await fetch("/email/status");
    const data = await res.json();
    emailProviderStatus.gmail   = data.gmail;
    emailProviderStatus.outlook = data.outlook;
    if (data.gmail)   document.getElementById("dot-gmail")?.classList.add("connected");
    if (data.outlook) document.getElementById("dot-outlook")?.classList.add("connected");
    updateFetchBtn();
    if (data.gmail || data.outlook) loadEmailIndex();
  } catch (_) {}
})();
