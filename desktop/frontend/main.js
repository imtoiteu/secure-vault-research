// Security & Privacy Toolkit — frontend controller.
//
// Talks to the Rust core via Tauri's global `invoke` (enabled by `app.withGlobalTauri` in
// tauri.conf.json, so no npm bundler is required). Every backend error is the coded,
// oracle-safe `ApiError` — we render `error.code` (a stable `SV-…` string) so messages are
// localizable and never leak which secret was wrong. The frontend holds only an opaque
// `SessionHandle`; no key material ever crosses the boundary.

const { invoke } = window.__TAURI__.core;

// Localization. `i18n.js` is loaded first (see index.html) and exposes `window.i18n`. `t(key, params)`
// resolves a string in the active locale (Vietnamese by default), so every user-facing message below
// flows through it. This changes presentation only — no IPC, crypto, or format behavior.
const t = window.i18n.t;

let session = null; // opaque SessionHandle from the core; never holds key material.
let currentVaultPath = null; // path of the open vault, for display only.

const $ = (id) => document.getElementById(id);

// ---- error rendering -----------------------------------------------------

// Map stable error codes → i18n keys. The backend never distinguishes wrong-passphrase from
// wrong-share (both → SV-UNAUTHORIZED), preserving the oracle-safe contract. The keys here MUST stay
// the exact `SV-…` set the backend can emit — the desktop `ui_contract` test parses this very block
// and asserts it matches `ApiError::ALL_CODES` 1:1. The values are i18n keys resolved via `t()`.
const MESSAGES = {
  "SV-NOT-FOUND": "err.notFound",
  "SV-MALFORMED": "err.malformed",
  "SV-INCOMPATIBLE-VERSION": "err.incompatibleVersion",
  "SV-CORRUPTED": "err.corrupted",
  "SV-UNAUTHORIZED": "err.unauthorized",
  "SV-INSUFFICIENT-SHARES": "err.insufficientShares",
  "SV-INVALID-INPUT": "err.invalidInput",
  "SV-IO": "err.io",
  "SV-TOO-LARGE": "err.tooLarge",
  "SV-TIMEOUT": "err.timeout",
  "SV-OUTPUT-EXISTS": "err.outputExists",
  "SV-INTERNAL": "err.internal",
};

function mib(bytes) {
  return `${(bytes / (1024 * 1024)).toFixed(0)} MiB`;
}

function describe(err) {
  // ApiError is serialized as `{ code: "SV-…", ...fields }`.
  const code = err && err.code ? err.code : "SV-INTERNAL";
  let msg = MESSAGES[code] ? t(MESSAGES[code]) : code;
  if (code === "SV-INSUFFICIENT-SHARES" && err.got != null) {
    msg = t("err.insufficientShares.detail", { got: err.got, need: err.need });
  }
  if (code === "SV-INCOMPATIBLE-VERSION" && err.found != null) {
    msg = t("err.incompatibleVersion.detail", { found: err.found, supported: err.supported });
  }
  if (code === "SV-INVALID-INPUT" && err.detail) {
    msg = err.detail; // backend-supplied detail (already specific); not localizable on the frontend
  }
  if (code === "SV-TOO-LARGE" && err.actual_bytes != null) {
    msg = t("err.tooLarge.detail", { actual: mib(err.actual_bytes), limit: mib(err.limit_bytes) });
  }
  if (code === "SV-IO" && err.detail) {
    msg = err.detail; // backend-supplied detail; not localizable on the frontend
  }
  if (code === "SV-OUTPUT-EXISTS") {
    msg = t("err.outputExists.detail");
  }
  return msg;
}

function setStatus(text, kind = "info") {
  const el = $("status");
  el.textContent = text;
  el.className = `status ${kind}`;
}

// Run a backend call with uniform busy/disabled handling and coded-error reporting (legacy
// status-bar path — used where a result card isn't appropriate, e.g. lock/unlock transitions).
async function withButton(btn, fn) {
  if (btn) btn.disabled = true;
  try {
    return await fn();
  } catch (e) {
    setStatus(describe(e), "error");
    return undefined;
  } finally {
    if (btn) btn.disabled = false;
  }
}

// ---- small helpers -------------------------------------------------------

const linesOf = (text) =>
  text
    .split("\n")
    .map((s) => s.trim())
    .filter((s) => s.length > 0);

const shortHash = (hex, n = 12) => (hex ? `${hex.slice(0, n)}…` : "");

function baseName(p) {
  const parts = String(p).split(/[\\/]/);
  return parts[parts.length - 1] || p;
}

function humanSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB", "TB"];
  let v = bytes / 1024;
  let i = 0;
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024;
    i++;
  }
  return `${v.toFixed(v < 10 ? 1 : 0)} ${units[i]}`;
}

function escapeHtml(s) {
  return s.replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c],
  );
}

// Pick a singular/plural i18n form by count and interpolate `{n}`. English inflects (the `.plural`
// key carries the "s" form); Vietnamese has no plural marker, so both keys hold the same template.
function plural(n, baseKey) {
  return t(n === 1 ? baseKey : baseKey + ".plural", { n });
}

// ---- clipboard + reveal/open (graceful fallback to copy) -----------------

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (_) {
    return false;
  }
}

const opener = () => (window.__TAURI__ && window.__TAURI__.opener) || null;

async function revealInFolder(path) {
  const o = opener();
  if (o && o.revealItemInDir) {
    try {
      await o.revealItemInDir(path);
      return;
    } catch (_) {
      /* fall through */
    }
  }
  const ok = await copyText(path);
  setStatus(ok ? t("status.folderOpenCopied") : t("status.folderOpenFailed"), "info");
}

async function openFile(path) {
  const o = opener();
  if (o && o.openPath) {
    try {
      await o.openPath(path);
      return;
    } catch (_) {
      /* fall through */
    }
  }
  const ok = await copyText(path);
  setStatus(ok ? t("status.fileOpenCopied") : t("status.fileOpenFailed"), "info");
}

// Common result-card actions. Labels resolve at call time, so each rendered card matches the
// language active when the action was built.
function revealAction(path) {
  return { label: t("action.showInFolder"), onClick: () => revealInFolder(path) };
}
function openAction(path) {
  return { label: t("action.openFile"), onClick: () => openFile(path) };
}

// ---- result cards --------------------------------------------------------
//
// Replaces status-only feedback for task outcomes. renderResult builds DOM safely
// (textContent for all values → no HTML injection from paths/hashes).

function renderResult(id, opts) {
  const el = $(id);
  if (!el) return;
  el.className = "result " + (opts.ok ? "ok" : "bad");
  el.innerHTML = "";

  const title = document.createElement("div");
  title.className = "result-title";
  title.textContent = (opts.ok ? t("res.ok.prefix") : t("res.bad.prefix")) + opts.title;
  el.appendChild(title);

  if (opts.message) {
    const m = document.createElement("div");
    m.className = "result-msg";
    m.textContent = opts.message;
    el.appendChild(m);
  }

  if (opts.rows && opts.rows.length) {
    const rows = document.createElement("div");
    rows.className = "result-rows";
    for (const r of opts.rows) {
      const row = document.createElement("div");
      row.className = "result-row";
      const lab = document.createElement("span");
      lab.className = "rlabel";
      lab.textContent = r.label;
      const val = document.createElement("span");
      val.className = "rvalue";
      val.textContent = r.value;
      row.appendChild(lab);
      row.appendChild(val);
      if (r.copy) {
        const cp = document.createElement("button");
        cp.className = "secondary btn-mini";
        cp.textContent = t("btn.copy");
        cp.addEventListener("click", async () => {
          const ok = await copyText(r.value);
          setStatus(ok ? t("status.copied") : t("status.copyFailed"), ok ? "ok" : "error");
        });
        row.appendChild(cp);
      }
      rows.appendChild(row);
    }
    el.appendChild(rows);
  }

  if (opts.actions && opts.actions.length) {
    const acts = document.createElement("div");
    acts.className = "result-actions";
    for (const a of opts.actions) {
      const b = document.createElement("button");
      b.className = a.primary ? "" : "secondary";
      b.textContent = a.label;
      b.addEventListener("click", a.onClick);
      acts.appendChild(b);
    }
    el.appendChild(acts);
  }

  el.classList.remove("hidden");
}

function hideAllResults() {
  document.querySelectorAll('[id$="-result"]').forEach((el) => el.classList.add("hidden"));
}

// Run a task that produces a result card. Shows a "Working…" busy state, renders the returned
// result on success, or an error card (optionally refined by errMap) on failure.
async function runTask(btn, resultId, fn, errMap) {
  const label = btn ? btn.textContent : null;
  if (btn) {
    btn.disabled = true;
    btn.textContent = t("btn.working");
  }
  try {
    const res = await fn();
    if (res) renderResult(resultId, res);
  } catch (e) {
    const extra = errMap ? errMap(e) : null;
    renderResult(resultId, Object.assign({ ok: false, title: describe(e) }, extra || {}));
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = label;
    }
  }
}

// ---- inline field validation ---------------------------------------------

function setFieldError(input, msg) {
  input.classList.add("invalid");
  const host = input.closest("label") || input.parentElement;
  let err = host.querySelector(".field-error");
  if (!err) {
    err = document.createElement("div");
    err.className = "field-error";
    host.appendChild(err);
  }
  err.textContent = msg;
}

function clearFieldError(input) {
  input.classList.remove("invalid");
  const host = input.closest("label") || input.parentElement;
  const err = host && host.querySelector(".field-error");
  if (err) err.remove();
}

function clearAllFieldErrors() {
  document.querySelectorAll(".field-error").forEach((e) => e.remove());
  document.querySelectorAll(".invalid").forEach((e) => e.classList.remove("invalid"));
}

// Validate a list of [inputEl, message]; mark every empty field, focus the first, return ok.
function validate(pairs) {
  let firstBad = null;
  for (const [el, msg] of pairs) {
    if (!el.value || !el.value.trim()) {
      setFieldError(el, msg);
      if (!firstBad) firstBad = el;
    } else {
      clearFieldError(el);
    }
  }
  if (firstBad) firstBad.focus();
  return !firstBad;
}

// Re-open the Save As dialog for a given output field (used by the "file exists" recovery action).
function clickSaveFor(outputId) {
  const b = document.querySelector(`button.browse[data-target="${outputId}"][data-mode="save"]`);
  if (b) b.click();
}

// "A file already exists" → friendly card with a one-click way to pick a new name.
function outputExistsMap(outputId) {
  return (e) =>
    e && e.code === "SV-OUTPUT-EXISTS"
      ? {
          title: t("r.exists.title"),
          message: t("r.exists.msg"),
          actions: [{ label: t("r.exists.pickNew"), primary: true, onClick: () => clickSaveFor(outputId) }],
        }
      : null;
}

// ---- view / tab switching ------------------------------------------------

function showUnlocked(show) {
  $("unlocked-view").classList.toggle("hidden", !show);
  $("locked-view").classList.toggle("hidden", show);
  const badge = $("lock-badge");
  badge.textContent = show ? t("vault.badge.unlocked") : t("vault.badge.locked");
  badge.className = `badge ${show ? "unlocked" : "locked"}`;
}

// (The vault is now a dashboard of stacked cards — no internal tabs. Locked vs unlocked is the
// only sub-state, handled by showUnlocked above.)

// ---- screen router (goal-based sidebar) ----------------------------------

function showScreen(name) {
  document.querySelectorAll("#main .screen").forEach((s) => {
    s.classList.toggle("hidden", s.dataset.screen !== name);
  });
  document.querySelectorAll("#sidebar-nav .navitem").forEach((n) => {
    n.classList.toggle("active", n.dataset.screen === name);
  });
  clearAllFieldErrors();
}

function wireSidebar() {
  document.querySelectorAll("#sidebar-nav .navitem").forEach((item) => {
    item.addEventListener("click", () => showScreen(item.dataset.screen));
  });
}

function initTiles() {
  document.querySelectorAll(".tile[data-goto]").forEach((t) => {
    t.addEventListener("click", () => showScreen(t.dataset.goto));
  });
}

function initAbout() {
  $("btn-about").addEventListener("click", () => $("about-panel").classList.remove("hidden"));
  $("btn-about-close").addEventListener("click", () => $("about-panel").classList.add("hidden"));
  $("about-panel").addEventListener("click", (e) => {
    if (e.target.id === "about-panel") $("about-panel").classList.add("hidden");
  });
}

// ---- native file/folder/save pickers + drag-drop -------------------------

const dialog = () => (window.__TAURI__ && window.__TAURI__.dialog) || null;

async function pickPath(mode, opts = {}) {
  const d = dialog();
  if (!d) {
    setStatus(t("status.pickerUnavailable"), "info");
    return null;
  }
  try {
    if (mode === "save") return await d.save({ defaultPath: opts.defaultPath });
    if (mode === "folder") return await d.open({ directory: true, multiple: false });
    if (mode === "files") return await d.open({ multiple: true });
    return await d.open({ multiple: false });
  } catch (_) {
    return null;
  }
}

// Smart default: when a source file is chosen, pre-fill a linked output path if it's empty.
function autoFillOutputs(input) {
  const fills = input.dataset && input.dataset.fills;
  if (!fills) return;
  const out = $(fills);
  if (!out || out.value.trim()) return; // never clobber a user-set output
  const src = input.value.trim();
  if (!src) return;
  const strip = input.dataset.fillstrip;
  const suffix = input.dataset.fillsuffix || "";
  if (strip) {
    // Reveal: drop a ".stego.<imgext>" tail (any supported cover format) to suggest the original
    // name; otherwise append the suffix.
    const stripped = src.replace(/\.stego\.(png|jpe?g|bmp)$/i, "");
    out.value = stripped !== src ? stripped : src + suffix;
  } else {
    // Hide: the stego output keeps the cover's container format — mirror its extension.
    out.value = src + mirrorStegoExt(src, suffix);
  }
}

// Adjust a default stego suffix (e.g. ".stego.png") so its trailing image extension matches the
// cover's: a JPEG cover produces a JPEG stego file, a BMP cover a BMP, etc. (the carrier re-encodes
// in the cover's own format). Leaves the suffix unchanged for an unrecognized cover extension.
function mirrorStegoExt(src, suffix) {
  const m = src.toLowerCase().match(/\.(jpe?g|bmp|png)$/);
  if (!m) return suffix;
  const ext = m[1] === "jpeg" ? "jpg" : m[1];
  return suffix.replace(/\.(png|jpe?g|bmp)$/i, "." + ext);
}

function initBrowse() {
  document.addEventListener("click", async (e) => {
    const btn = e.target.closest("button.browse");
    if (!btn) return;
    const target = $(btn.dataset.target);
    if (!target) return;
    const mode = btn.dataset.mode || "file";
    let defaultPath;
    if (mode === "save") {
      if (target.value.trim()) {
        defaultPath = target.value.trim();
      } else {
        const from = btn.dataset.from ? ($(btn.dataset.from)?.value || "").trim() : "";
        if (from) defaultPath = from + mirrorStegoExt(from, btn.dataset.suffix || "");
      }
    }
    const res = await pickPath(mode, { defaultPath });
    if (res == null) return;
    if (mode === "files") {
      const arr = Array.isArray(res) ? res : [res];
      const cur = target.value.trim();
      target.value = (cur ? cur + "\n" : "") + arr.join("\n");
    } else {
      target.value = Array.isArray(res) ? res[0] : res;
      clearFieldError(target);
      autoFillOutputs(target);
    }
  });
}

function clearDropHighlight() {
  document.querySelectorAll(".filefield.dropping").forEach((el) => el.classList.remove("dropping"));
}

function dropZoneAt(position) {
  const r = window.devicePixelRatio || 1;
  const el = document.elementFromPoint(position.x / r, position.y / r);
  return el ? el.closest("[data-drop]") : null;
}

function initDragDrop() {
  const ev = window.__TAURI__ && window.__TAURI__.event;
  if (!ev) return;
  ev.listen("tauri://drag-over", (e) => {
    clearDropHighlight();
    const z = dropZoneAt(e.payload.position);
    if (z) z.classList.add("dropping");
  }).catch(() => {});
  ev.listen("tauri://drag-leave", () => clearDropHighlight()).catch(() => {});
  ev.listen("tauri://drag-drop", (e) => {
    clearDropHighlight();
    const paths = e.payload && e.payload.paths;
    if (!paths || !paths.length) return;
    const z = dropZoneAt(e.payload.position);
    if (!z) return;
    const input = $(z.dataset.drop);
    if (!input) return;
    if (input.tagName === "TEXTAREA") {
      const cur = input.value.trim();
      input.value = (cur ? cur + "\n" : "") + paths.join("\n");
    } else {
      input.value = paths[0];
      clearFieldError(input);
      autoFillOutputs(input);
    }
    setStatus(t("status.fileAdded"), "ok");
  }).catch(() => {});
}

// Clear a field's inline error as soon as the user edits it.
document.addEventListener("input", (e) => {
  if (e.target && e.target.classList && e.target.classList.contains("invalid")) {
    clearFieldError(e.target);
  }
});

// ---- vault banner & metadata ---------------------------------------------

let currentMeta = null;

function renderMeta(meta) {
  currentMeta = meta;
  // Plain-language banner: the filename + a short, jargon-free summary.
  $("vault-title").textContent = currentVaultPath ? baseName(currentVaultPath) : t("vault.banner.default");
  const summary = [];
  const tech = [];
  if (meta) {
    summary.push(plural(meta.item_count, "vault.summary.files")); // file count, localized
    summary.push(
      meta.share_policy
        ? t("vault.summary.recovery", { threshold: meta.share_policy.threshold, total: meta.share_policy.shares_total })
        : t("vault.summary.noRecovery"),
    );
    // Technical details live in the collapsed "Vault details" panel, not the banner.
    tech.push(t("vault.tech.vaultId", { id: meta.vault_uuid }));
    tech.push(t("vault.tech.format", { version: meta.format_version }));
    if (meta.kdf) {
      tech.push(
        t("vault.tech.kdf", {
          alg: meta.kdf.algorithm,
          mem: Math.round(meta.kdf.mem_kib / 1024),
          passes: meta.kdf.time_cost,
        }),
      );
    }
  }
  $("vault-summary").textContent = summary.join(" · ");
  const techEl = $("vault-tech");
  if (techEl) {
    techEl.innerHTML = "";
    for (const t of tech) {
      const d = document.createElement("div");
      d.textContent = t;
      techEl.appendChild(d);
    }
  }
  reflectPolicy(meta);
}

function reflectPolicy(meta) {
  const note = $("shares-policy-note");
  if (!note) return;
  if (meta && meta.share_policy) {
    $("split-shares-total").value = meta.share_policy.shares_total;
    $("split-threshold").value = meta.share_policy.threshold;
    note.textContent = t("vault.note.recoveryReady", {
      threshold: meta.share_policy.threshold,
      total: meta.share_policy.shares_total,
    });
  } else if (meta) {
    note.textContent = t("vault.note.noRecovery");
  }
}

async function loadVault() {
  try {
    renderMeta(await invoke("vault_meta", { session }));
  } catch (_) {
    renderMeta(null);
  }
  await refreshItems();
}

// ---- items ---------------------------------------------------------------

async function refreshItems() {
  if (!session) return;
  const list = $("item-list");
  list.innerHTML = "";
  const items = await invoke("item_list", { session });
  $("item-count").textContent = plural(items.length, "vault.itemCount");
  if (currentMeta) {
    currentMeta.item_count = items.length;
    renderMeta(currentMeta);
  }
  if (items.length === 0) {
    const empty = document.createElement("li");
    empty.className = "muted empty";
    empty.textContent = t("vault.files.empty");
    list.appendChild(empty);
    return;
  }
  for (const it of items) {
    const li = document.createElement("li");
    li.innerHTML = `
      <span class="item-name"></span>
      <span class="muted">${humanSize(it.size_bytes)} · ${shortHash(it.content_hash_hex)}</span>
      <button class="extract secondary btn-mini"></button>`;
    li.querySelector("button.extract").textContent = t("vault.files.saveCopy");
    li.querySelector(".item-name").textContent = it.name; // textContent → no HTML injection
    li.querySelector("button.extract").addEventListener("click", () => extractItem(it));
    list.appendChild(li);
  }
}

async function extractItem(it) {
  // Native save dialog instead of a blind prompt(): the user picks a non-colliding name, and the
  // backend still refuses to overwrite (SV-OUTPUT-EXISTS) as a backstop.
  const dest = await pickPath("save", { defaultPath: it.name });
  if (!dest) return;
  await withButton(null, async () => {
    try {
      await invoke("item_extract", { session, itemId: it.item_id, dest });
      setStatus(t("status.savedTo", { name: it.name, dest }), "ok");
    } catch (e) {
      setStatus(describe(e), "error");
    }
  });
}

// ===========================================================================
// Wiring
// ===========================================================================

let appInfo = null; // cached app_info, so the About line can be re-rendered on a language switch.

// Rebuild the localized About version line from the cached app_info.
function updateAboutVersion() {
  if (!appInfo) return;
  $("about-version").textContent = t("about.version", {
    app: appInfo.app_version,
    fmt: appInfo.max_format_version,
    suite: appInfo.suite_version,
    contract: appInfo.contract_version,
  });
}

// Wire the header language selector and persist/apply the choice.
function initLang() {
  const sel = $("lang-select");
  if (!sel) return;
  sel.value = window.i18n.getLang();
  sel.addEventListener("change", () => window.i18n.setLang(sel.value));
}

// Called by i18n.setLang after the static markup is re-translated. Re-render the dynamic, language-
// dependent UI so nothing is left in the previous language. Transient result cards and the status
// line are cleared (a language switch is a deliberate settings action, not mid-task).
window.onLangChange = function () {
  const sel = $("lang-select");
  if (sel) sel.value = window.i18n.getLang();
  updateAboutVersion();
  const badge = $("lock-badge");
  if (badge) badge.textContent = session ? t("vault.badge.unlocked") : t("vault.badge.locked");
  if (session) {
    if (currentMeta) renderMeta(currentMeta);
    refreshItems();
  } else {
    resetPubkey();
  }
  hideAllResults();
  setStatus("", "info");
};

async function init() {
  window.i18n.apply(); // translate static markup up front (Vietnamese by default)
  initLang();
  wireSidebar();
  initTiles();
  initAbout();
  initBrowse();
  initDragDrop();
  try {
    appInfo = await invoke("app_info");
    updateAboutVersion();
  } catch (_) {
    /* non-fatal */
  }
}

// ---- create / unlock -----------------------------------------------------

$("btn-create").addEventListener("click", (e) => {
  const path = $("create-path");
  const p1 = $("create-pass");
  const p2 = $("create-pass-2");
  if (!validate([[path, t("v.create.path")], [p1, t("v.create.pass")]])) return;
  if (p1.value !== p2.value) {
    setFieldError(p2, t("v.create.mismatch"));
    p2.focus();
    return;
  }
  clearFieldError(p2);

  let policy = null;
  if ($("create-recovery").checked) {
    const sharesTotal = parseInt($("create-shares-total").value, 10);
    const threshold = parseInt($("create-threshold").value, 10);
    if (!(threshold >= 2 && sharesTotal >= threshold && sharesTotal <= 255)) {
      setStatus(t("status.policyRecovery"), "error");
      return;
    }
    policy = { shares_total: sharesTotal, threshold };
  }

  runTask(e.target, "create-result", async () => {
    const meta = await invoke("vault_create", { path: path.value, passphrase: p1.value, policy });
    p1.value = "";
    p2.value = "";
    return {
      ok: true,
      title: t("r.create.title"),
      message: policy ? t("r.create.msg.recovery") : t("r.create.msg.plain"),
      rows: [{ label: t("r.label.savedTo"), value: path.value, copy: true }],
      actions: [
        revealAction(path.value),
        {
          label: t("r.create.openNow"),
          primary: true,
          onClick: () => {
            $("vault-path").value = path.value;
            $("passphrase").focus();
          },
        },
      ],
    };
  });
});

$("btn-unlock").addEventListener("click", (e) =>
  withButton(e.target, async () => {
    const path = $("vault-path");
    const p1 = $("passphrase");
    if (!validate([[path, t("v.unlock.path")], [p1, t("v.unlock.pass")]])) return;

    session = await invoke("vault_unlock", { path: path.value, passphrase: p1.value });
    p1.value = "";
    currentVaultPath = path.value;
    hideAllResults();
    showUnlocked(true);
    setStatus(t("status.vaultOpened"), "ok");
    await loadVault();
  }),
);

// ---- lock ----------------------------------------------------------------

$("btn-lock").addEventListener("click", async (e) => {
  await withButton(e.target, async () => {
    if (session) await invoke("vault_lock", { session });
  });
  session = null;
  currentVaultPath = null;
  currentMeta = null;
  $("share-list").innerHTML = "";
  hideAllResults();
  resetPubkey();
  showUnlocked(false);
  setStatus(t("status.locked"), "info");
});

// ---- add item ------------------------------------------------------------

$("btn-add").addEventListener("click", (e) =>
  withButton(e.target, async () => {
    const source = $("add-source");
    const name = $("add-name");
    if (!validate([[source, t("v.add.source")], [name, t("v.add.name")]])) return;
    await invoke("item_add", { session, source: source.value, name: name.value });
    source.value = "";
    name.value = "";
    setStatus(t("status.itemAdded"), "ok");
    await refreshItems();
  }),
);

// ---- recovery: split -----------------------------------------------------

$("btn-split").addEventListener("click", (e) => {
  const outDir = $("split-outdir");
  if (!validate([[outDir, t("v.split.outdir")]])) return;
  const sharesTotal = parseInt($("split-shares-total").value, 10);
  const threshold = parseInt($("split-threshold").value, 10);
  if (!(threshold >= 2 && sharesTotal >= threshold && sharesTotal <= 255)) {
    setStatus(t("status.policyShares"), "error");
    return;
  }
  runTask(e.target, "split-result", async () => {
    const infos = await invoke("keys_split", { session, sharesTotal, threshold, outDir: outDir.value });
    const list = $("share-list");
    list.innerHTML = "";
    for (const info of infos) {
      const li = document.createElement("li");
      const name = document.createElement("span");
      name.className = "item-name";
      name.textContent = t("r.share.label", { index: info.share_index, total: info.shares_total });
      const p = document.createElement("span");
      p.className = "muted path";
      p.textContent = info.output_path;
      li.appendChild(name);
      li.appendChild(p);
      list.appendChild(li);
    }
    return {
      ok: true,
      title: plural(infos.length, "r.split.title"),
      message: t("r.split.msg", { threshold }),
      actions: [revealAction(outDir.value)],
    };
  });
});

// ---- recovery: recover ---------------------------------------------------

$("btn-recover").addEventListener("click", (e) =>
  withButton(e.target, async () => {
    const path = $("recover-path");
    const shares = $("recover-shares");
    const sharePaths = linesOf(shares.value);
    if (!validate([[path, t("v.recover.path")]])) return;
    if (sharePaths.length === 0) {
      setFieldError(shares, t("v.recover.shares"));
      shares.focus();
      return;
    }
    clearFieldError(shares);
    session = await invoke("keys_recover", { path: path.value, sharePaths });
    currentVaultPath = path.value;
    hideAllResults();
    showUnlocked(true);
    setStatus(t("status.recoveredOpened"), "ok");
    await loadVault();
  }),
);

// ---- vault: sign ---------------------------------------------------------

$("btn-sign").addEventListener("click", (e) => {
  const file = $("sign-file");
  if (!validate([[file, t("v.sign.file")]])) return;
  runTask(e.target, "sign-result", async () => {
    const sigPath = await invoke("sign_file", { session, path: file.value });
    return {
      ok: true,
      title: t("r.sign.title"),
      rows: [{ label: t("r.label.signature"), value: sigPath, copy: true }],
      actions: [revealAction(sigPath), openAction(sigPath)],
    };
  });
});

// ---- vault: verify & integrity -------------------------------------------

$("btn-verify").addEventListener("click", (e) => {
  const file = $("verify-file");
  const sig = $("verify-sig");
  const pub = $("verify-pub");
  if (
    !validate([
      [file, t("v.verify.file")],
      [sig, t("v.verify.sig")],
      [pub, t("v.verify.pub")],
    ])
  )
    return;
  runTask(e.target, "tools-result", async () => {
    const report = await invoke("verify_file", {
      path: file.value,
      signaturePath: sig.value,
      publicKeyPath: pub.value,
    });
    return report.signature_ok
      ? {
          ok: true,
          title: t("r.verify.ok.title"),
          message: t("r.verify.ok.msg"),
          rows: [{ label: t("r.label.fingerprint"), value: report.computed_hash_hex, copy: true }],
        }
      : {
          ok: false,
          title: t("r.verify.bad.title"),
          message: t("r.verify.bad.msg"),
        };
  });
});

$("btn-integrity").addEventListener("click", (e) => {
  const path = $("integrity-path");
  if (!validate([[path, t("v.integrity.path")]])) return;
  runTask(e.target, "tools-result", async () => {
    const report = await invoke("integrity_check", { path: path.value });
    return report.signature_ok
      ? {
          ok: true,
          title: t("r.integrity.ok.title"),
          message: t("r.integrity.ok.msg"),
          rows: [{ label: t("r.label.fingerprint"), value: report.computed_hash_hex, copy: true }],
        }
      : { ok: false, title: t("r.integrity.bad.title"), message: t("r.integrity.bad.msg") };
  });
});

$("btn-hash").addEventListener("click", (e) => {
  const path = $("integrity-path");
  if (!validate([[path, t("v.integrity.path")]])) return;
  runTask(e.target, "tools-result", async () => {
    const hash = await invoke("integrity_hash", { path: path.value });
    return { ok: true, title: t("r.vaultHash.title"), rows: [{ label: t("r.label.blake3"), value: hash, copy: true }] };
  });
});

// ---- change passphrase ---------------------------------------------------

$("btn-change-pass").addEventListener("click", (e) =>
  withButton(e.target, async () => {
    const a = $("new-passphrase");
    const b = $("new-passphrase-2");
    if (!validate([[a, t("v.changePass.new")]])) return;
    if (a.value !== b.value) {
      setFieldError(b, t("v.changePass.mismatch"));
      b.focus();
      return;
    }
    clearFieldError(b);
    await invoke("vault_change_passphrase", { session, newPassphrase: a.value });
    a.value = "";
    b.value = "";
    setStatus(t("status.passwordChanged"), "ok");
  }),
);

// ---- signing public key (read-only export) -------------------------------

let pubkeyHex = null;

function resetPubkey() {
  pubkeyHex = null;
  $("signing-pubkey").textContent = t("vault.pubkey.placeholder");
  $("signing-pubkey").classList.add("muted");
  $("btn-copy-pubkey").disabled = true;
}

$("btn-show-pubkey").addEventListener("click", (e) =>
  withButton(e.target, async () => {
    pubkeyHex = await invoke("export_signing_public_key", { session });
    const el = $("signing-pubkey");
    el.textContent = pubkeyHex;
    el.classList.remove("muted");
    $("btn-copy-pubkey").disabled = false;
    setStatus(t("status.pubkeyLoaded"), "ok");
  }),
);

$("btn-copy-pubkey").addEventListener("click", async () => {
  if (!pubkeyHex) return;
  const ok = await copyText(pubkeyHex);
  if (ok) {
    setStatus(t("status.pubkeyCopied"), "ok");
  } else {
    const el = $("signing-pubkey");
    const range = document.createRange();
    range.selectNodeContents(el);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
    setStatus(t("status.pubkeySelectAll"), "info");
  }
});

// ---- vault: self integrity check (from the open vault) -------------------

$("btn-vault-check").addEventListener("click", (e) => {
  if (!currentVaultPath) return;
  runTask(e.target, "vault-tech-result", async () => {
    const report = await invoke("integrity_check", { path: currentVaultPath });
    return report.signature_ok
      ? {
          ok: true,
          title: t("r.vaultCheck.ok.title"),
          rows: [{ label: t("r.label.fingerprint"), value: report.computed_hash_hex, copy: true }],
        }
      : { ok: false, title: t("r.vaultCheck.bad.title"), message: t("r.vaultCheck.bad.msg") };
  });
});

// ===========================================================================
// Toolkit — vault-free Integrity + Cryptography commands (no session).
// ===========================================================================

// ---- Fingerprint a file --------------------------------------------------

$("tk-btn-hash").addEventListener("click", (e) => {
  const path = $("tk-hash-path");
  if (!validate([[path, t("v.hash.file")]])) return;
  runTask(e.target, "tk-hash-result", async () => {
    const hash = await invoke("integrity_hash_file", { path: path.value });
    return {
      ok: true,
      title: t("r.hash.title"),
      message: t("r.hash.msg"),
      rows: [{ label: t("r.label.blake3"), value: hash, copy: true }],
    };
  });
});

// ---- Check a signature ---------------------------------------------------

$("tk-btn-verify").addEventListener("click", (e) => {
  const file = $("tk-verify-file");
  const sig = $("tk-verify-sig");
  const pub = $("tk-verify-pub");
  if (
    !validate([
      [file, t("v.tkverify.file")],
      [sig, t("v.tkverify.sig")],
      [pub, t("v.tkverify.pub")],
    ])
  )
    return;
  runTask(e.target, "tk-verify-result", async () => {
    const report = await invoke("integrity_verify_signature", {
      path: file.value,
      signaturePath: sig.value,
      publicKeyPath: pub.value,
    });
    return report.signature_ok
      ? {
          ok: true,
          title: t("r.tkverify.ok.title"),
          message: t("r.tkverify.ok.msg"),
          rows: [{ label: t("r.label.fingerprint"), value: report.computed_hash_hex, copy: true }],
        }
      : {
          ok: false,
          title: t("r.tkverify.bad.title"),
          message: t("r.tkverify.bad.msg"),
        };
  });
});

// ---- Check a file is unchanged (Verify Integrity = Hash File + compare) ---
//
// Generic integrity check, composed entirely in the UI: hash the file with the existing
// `integrity_hash_file` (Hash File) and compare to the fingerprint the user was given.
// No new backend command, no crypto change. (Signature-based integrity is "Check a signature".)

$("tk-btn-intact").addEventListener("click", (e) => {
  const file = $("tk-intact-file");
  const expected = $("tk-intact-hash");
  if (!validate([[file, t("v.intact.file")], [expected, t("v.intact.hash")]])) return;
  runTask(e.target, "tk-intact-result", async () => {
    const actual = await invoke("integrity_hash_file", { path: file.value });
    const norm = (s) => s.trim().toLowerCase().replace(/\s+/g, "");
    const want = norm(expected.value);
    const match = norm(actual) === want;
    return match
      ? {
          ok: true,
          title: t("r.intact.ok.title"),
          message: t("r.intact.ok.msg"),
          rows: [{ label: t("r.label.fingerprint"), value: actual, copy: true }],
        }
      : {
          ok: false,
          title: t("r.intact.bad.title"),
          message: t("r.intact.bad.msg"),
          rows: [
            { label: t("r.intact.thisFile"), value: actual, copy: true },
            { label: t("r.intact.expected"), value: want || t("r.intact.empty") },
          ],
        };
  });
});

// ---- Verify a download (Verify Integrity = hash and/or signature) ---------
//
// The composed Cryptography primitive: ONE backend call (`integrity_verify_integrity`) checks the
// file against an expected BLAKE3 fingerprint and/or a detached signature + public key, returning a
// single verdict. A mismatch / invalid signature is a normal {verified:false} result, not an error;
// a bad fingerprint / missing file surfaces as the usual coded error card.

$("tk-btn-verify-integrity").addEventListener("click", (e) => {
  const file = $("tk-vi-file");
  const hash = $("tk-vi-hash");
  const sig = $("tk-vi-sig");
  const pub = $("tk-vi-pub");
  [hash, sig, pub].forEach(clearFieldError);
  if (!validate([[file, t("v.vi.file")]])) return;

  const wantHash = hash.value.trim() !== "";
  const sigSet = sig.value.trim() !== "";
  const pubSet = pub.value.trim() !== "";
  // A signature check needs BOTH the signature and the public key.
  if (sigSet !== pubSet) {
    setFieldError(pubSet ? sig : pub, t("v.vi.bothSig"));
    return;
  }
  const wantSig = sigSet && pubSet;
  if (!wantHash && !wantSig) {
    setFieldError(hash, t("v.vi.need"));
    return;
  }

  runTask(e.target, "tk-vi-result", async () => {
    const report = await invoke("integrity_verify_integrity", {
      path: file.value,
      expectedHashHex: wantHash ? hash.value : null,
      signaturePath: wantSig ? sig.value : null,
      publicKeyPath: wantSig ? pub.value : null,
    });
    const rows = [{ label: t("r.label.fingerprint"), value: report.computed_hash_hex, copy: true }];
    if (report.hash_checked) {
      rows.push({ label: t("r.vi.fpMatch"), value: report.hash_matched ? t("r.vi.yes") : t("r.vi.no") });
    }
    if (report.signature_checked) {
      rows.push({ label: t("r.vi.sig"), value: report.signature_valid ? t("r.vi.valid") : t("r.vi.invalid") });
    }
    return report.verified
      ? {
          ok: true,
          title: t("r.vi.ok.title"),
          message: t("r.vi.ok.msg"),
          rows,
        }
      : {
          ok: false,
          title: t("r.vi.bad.title"),
          message: t("r.vi.bad.msg"),
          rows,
        };
  });
});

// ---- Lock a file (encrypt) -----------------------------------------------

$("tk-btn-encrypt").addEventListener("click", (e) => {
  const input = $("tk-enc-input");
  const output = $("tk-enc-output");
  const p1 = $("tk-enc-pass");
  const p2 = $("tk-enc-pass2");
  if (
    !validate([
      [input, t("v.enc.input")],
      [output, t("v.enc.output")],
      [p1, t("v.enc.pass")],
    ])
  )
    return;
  if (p1.value !== p2.value) {
    setFieldError(p2, t("v.enc.mismatch"));
    p2.focus();
    return;
  }
  clearFieldError(p2);
  runTask(
    e.target,
    "tk-enc-result",
    async () => {
      const out = await invoke("crypto_encrypt_file", { input: input.value, output: output.value, passphrase: p1.value });
      p1.value = "";
      p2.value = "";
      return {
        ok: true,
        title: t("r.enc.title"),
        message: t("r.enc.msg"),
        rows: [{ label: t("r.label.savedTo"), value: out, copy: true }],
        actions: [
          revealAction(out),
          {
            label: t("r.enc.another"),
            onClick: () => {
              input.value = "";
              output.value = "";
              $("tk-enc-result").classList.add("hidden");
              input.focus();
            },
          },
        ],
      };
    },
    outputExistsMap("tk-enc-output"),
  );
});

// ---- Unlock a file (decrypt) ---------------------------------------------

$("tk-btn-decrypt").addEventListener("click", (e) => {
  const input = $("tk-dec-input");
  const output = $("tk-dec-output");
  const p1 = $("tk-dec-pass");
  if (
    !validate([
      [input, t("v.dec.input")],
      [output, t("v.dec.output")],
      [p1, t("v.dec.pass")],
    ])
  )
    return;
  runTask(
    e.target,
    "tk-dec-result",
    async () => {
      const out = await invoke("crypto_decrypt_file", { input: input.value, output: output.value, passphrase: p1.value });
      p1.value = "";
      return {
        ok: true,
        title: t("r.dec.title"),
        rows: [{ label: t("r.label.savedTo"), value: out, copy: true }],
        actions: [revealAction(out), openAction(out)],
      };
    },
    (err) => {
      if (err && err.code === "SV-UNAUTHORIZED") {
        return { title: t("r.dec.bad.title"), message: t("r.dec.bad.msg") };
      }
      return outputExistsMap("tk-dec-output")(err);
    },
  );
});

// ---- Hide data in an image (steganography) -------------------------------

$("tk-btn-hide").addEventListener("click", (e) => {
  const cover = $("tk-hide-cover");
  const payload = $("tk-hide-payload");
  const output = $("tk-hide-output");
  const p1 = $("tk-hide-pass");
  const p2 = $("tk-hide-pass2");
  const randomize = $("tk-hide-randomize");
  if (
    !validate([
      [cover, t("v.hide.cover")],
      [payload, t("v.hide.payload")],
      [output, t("v.hide.output")],
      [p1, t("v.hide.pass")],
    ])
  )
    return;
  if (p1.value !== p2.value) {
    setFieldError(p2, t("v.enc.mismatch"));
    p2.focus();
    return;
  }
  clearFieldError(p2);
  runTask(
    e.target,
    "tk-hide-result",
    async () => {
      const rep = await invoke("stego_hide", {
        coverPath: cover.value,
        payloadPath: payload.value,
        outputPath: output.value,
        passphrase: p1.value,
        randomize: randomize.checked,
      });
      p1.value = "";
      p2.value = "";
      return {
        ok: true,
        title: t("r.hide.title"),
        message: t("r.hide.msg"),
        rows: [
          { label: t("r.label.savedTo"), value: rep.output_path, copy: true },
          { label: t("r.hide.size"), value: humanSize(rep.payload_bytes) },
          {
            label: t("r.hide.capacity"),
            value: t("r.hide.capacityVal", { pct: rep.utilization_pct.toFixed(1), capacity: humanSize(rep.capacity_bytes) }),
          },
        ],
        actions: [revealAction(rep.output_path)],
      };
    },
    (err) => {
      if (err && err.code === "SV-TOO-LARGE")
        return {
          title: t("r.hide.tooBig.title"),
          message: t("r.hide.tooBig.msg"),
        };
      if (err && err.code === "SV-MALFORMED")
        return { title: t("r.hide.unsupported.title"), message: t("r.hide.unsupported.msg") };
      return outputExistsMap("tk-hide-output")(err);
    },
  );
});

// ---- Reveal hidden data --------------------------------------------------

$("tk-btn-unhide").addEventListener("click", (e) => {
  const input = $("tk-unhide-input");
  const output = $("tk-unhide-output");
  const p1 = $("tk-unhide-pass");
  if (
    !validate([
      [input, t("v.unhide.input")],
      [output, t("v.unhide.output")],
      [p1, t("v.unhide.pass")],
    ])
  )
    return;
  runTask(
    e.target,
    "tk-unhide-result",
    async () => {
      const rep = await invoke("stego_extract", {
        stegoPath: input.value,
        outputPath: output.value,
        passphrase: p1.value,
      });
      p1.value = "";
      return {
        ok: true,
        title: t("r.unhide.title"),
        rows: [
          { label: t("r.label.savedTo"), value: rep.output_path, copy: true },
          { label: t("r.label.size"), value: humanSize(rep.bytes_written) },
        ],
        actions: [revealAction(rep.output_path), openAction(rep.output_path)],
      };
    },
    (err) => {
      if (err && err.code === "SV-UNAUTHORIZED")
        return {
          title: t("r.unhide.bad.title"),
          message: t("r.unhide.bad.msg"),
        };
      return outputExistsMap("tk-unhide-output")(err);
    },
  );
});

// ---- Detect hidden data (heuristic steganalysis) -------------------------

$("tk-btn-detect").addEventListener("click", (e) => {
  const input = $("tk-detect-input");
  if (!validate([[input, t("v.detect.input")]])) return;
  runTask(
    e.target,
    "tk-detect-result",
    async () => {
      const rep = await invoke("stego_detect", { imagePath: input.value });
      const elevated = rep.suspicion === "High" || rep.suspicion === "Elevated";
      // Backend `suspicion` is a stable enum (NotObserved/Low/Elevated/High); localize via key.
      const verdictKey = "detect.verdict." + rep.suspicion;
      const verdict = t(verdictKey);
      const rows = [{ label: t("r.detect.verdict"), value: verdict === verdictKey ? rep.suspicion : verdict }];
      for (const s of rep.signals)
        rows.push({ label: s.name, value: Math.round(s.score * 100) + "% — " + s.detail });
      rows.push({ label: t("r.detect.note"), value: rep.caveat });
      return {
        ok: !elevated,
        title: t("r.detect.title"),
        message: elevated ? t("r.detect.msg.elevated") : t("r.detect.msg.clean"),
        rows,
      };
    },
    (err) => {
      if (err && err.code === "SV-MALFORMED")
        return { title: t("r.detect.unsupported.title"), message: t("r.detect.unsupported.msg") };
      return null;
    },
  );
});

// ---- Inspect metadata -----------------------------------------------------

$("tk-btn-mi").addEventListener("click", (e) => {
  const file = $("tk-mi-file");
  if (!validate([[file, t("v.mi.file")]])) return;
  runTask(e.target, "tk-mi-result", async () => {
    const rep = await invoke("metadata_inspect", { path: file.value });
    const rows = [];
    for (const g of rep.groups) {
      for (const tag of g.tags) {
        rows.push({ label: `${g.group}:${tag.name}`, value: tag.value });
      }
    }
    const summary = [rep.format || t("r.mi.unknownType")];
    if (rep.mime_type) summary.push(rep.mime_type);
    summary.push(plural(rep.tag_count, "r.mi.fieldCount"));
    return {
      ok: true,
      title: t("r.mi.title"),
      message: t("r.mi.msg", { summary: summary.join(" · ") }),
      rows,
    };
  });
});

// ---- Remove metadata ------------------------------------------------------

$("tk-btn-mc").addEventListener("click", (e) => {
  const input = $("tk-mc-input");
  const output = $("tk-mc-output");
  if (
    !validate([
      [input, t("v.mc.input")],
      [output, t("v.mc.output")],
    ])
  )
    return;
  runTask(
    e.target,
    "tk-mc-result",
    async () => {
      const rep = await invoke("metadata_sanitize", { input: input.value, output: output.value });
      const removed = Math.max(0, rep.tags_before - rep.tags_after);
      const rows = [
        { label: t("r.label.savedTo"), value: rep.output_path, copy: true },
        { label: t("r.mc.format"), value: rep.format },
        { label: t("r.mc.before"), value: String(rep.tags_before) },
        { label: t("r.mc.after"), value: String(rep.tags_after) },
        { label: t("r.mc.removed"), value: String(removed) },
      ];
      return rep.guaranteed
        ? {
            ok: true,
            title: t("r.mc.ok.title"),
            message: t("r.mc.ok.msg"),
            rows,
            actions: [revealAction(rep.output_path)],
          }
        : {
            ok: true,
            title: t("r.mc.best.title"),
            message: t("r.mc.best.msg"),
            rows,
            actions: [revealAction(rep.output_path)],
          };
    },
    outputExistsMap("tk-mc-output"),
  );
});

// ---- Compare metadata -----------------------------------------------------

$("tk-btn-cmp").addEventListener("click", (e) => {
  const a = $("tk-cmp-a");
  const b = $("tk-cmp-b");
  if (
    !validate([
      [a, t("v.cmp.a")],
      [b, t("v.cmp.b")],
    ])
  )
    return;
  runTask(e.target, "tk-cmp-result", async () => {
    const d = await invoke("metadata_diff", { pathA: a.value, pathB: b.value });
    const rows = [];
    for (const c of d.changed)
      rows.push({ label: t("r.cmp.changed", { key: c.key }), value: t("r.cmp.arrow", { a: c.value_a, b: c.value_b }) });
    for (const o of d.only_in_a) rows.push({ label: t("r.cmp.onlyA", { name: o.name }), value: o.value });
    for (const o of d.only_in_b) rows.push({ label: t("r.cmp.onlyB", { name: o.name }), value: o.value });
    const total = d.changed.length + d.only_in_a.length + d.only_in_b.length;
    return {
      ok: true,
      title: total === 0 ? t("r.cmp.same.title") : t("r.cmp.diff.title"),
      message: total === 0 ? t("r.cmp.same.msg") : plural(total, "r.cmp.diff.msg"),
      rows,
    };
  });
});

// ---- Generate signing keypair --------------------------------------------

let lastSignPubPath = null;

$("tk-btn-genkey").addEventListener("click", (e) => {
  const outDir = $("tk-key-dir");
  const name = $("tk-key-name");
  const p1 = $("tk-key-pass");
  const p2 = $("tk-key-pass2");
  if (
    !validate([
      [outDir, t("v.genkey.dir")],
      [name, t("v.genkey.name")],
      [p1, t("v.genkey.pass")],
    ])
  )
    return;
  if (p1.value !== p2.value) {
    setFieldError(p2, t("v.genkey.mismatch"));
    p2.focus();
    return;
  }
  clearFieldError(p2);
  runTask(e.target, "tk-key-result", async () => {
    const info = await invoke("crypto_generate_signing_keypair", { outDir: outDir.value, name: name.value, passphrase: p1.value });
    p1.value = "";
    p2.value = "";
    $("tk-sign-key").value = info.secret_key_path; // pre-fill for signing below
    lastSignPubPath = info.public_key_path;
    return {
      ok: true,
      title: t("r.genkey.title"),
      message: t("r.genkey.msg"),
      rows: [
        { label: t("r.genkey.pub"), value: info.public_key_path, copy: true },
        { label: t("r.genkey.priv"), value: info.secret_key_path, copy: true },
        { label: t("r.genkey.pubHex"), value: info.public_key_hex, copy: true },
      ],
      actions: [revealAction(info.public_key_path)],
    };
  });
});

// ---- Sign a file ---------------------------------------------------------

$("tk-btn-sign").addEventListener("click", (e) => {
  const input = $("tk-sign-input");
  const key = $("tk-sign-key");
  const p1 = $("tk-sign-pass");
  if (
    !validate([
      [input, t("v.sign2.input")],
      [key, t("v.sign2.key")],
      [p1, t("v.sign2.pass")],
    ])
  )
    return;
  runTask(
    e.target,
    "tk-sign-result",
    async () => {
      const sigPath = await invoke("crypto_sign_file", { input: input.value, signingKeyPath: key.value, passphrase: p1.value });
      p1.value = "";
      return {
        ok: true,
        title: t("r.sign2.title"),
        rows: [{ label: t("r.label.signature"), value: sigPath, copy: true }],
        actions: [
          revealAction(sigPath),
          {
            label: t("r.sign2.checkSig"),
            onClick: () => {
              $("tk-verify-file").value = input.value;
              $("tk-verify-sig").value = sigPath;
              if (lastSignPubPath) $("tk-verify-pub").value = lastSignPubPath;
              showScreen("verify");
            },
          },
        ],
      };
    },
    (err) =>
      err && err.code === "SV-UNAUTHORIZED"
        ? { title: t("r.sign2.bad.title"), message: t("r.sign2.bad.msg") }
        : null,
  );
});

// ===========================================================================
// Secret Sharing — vault-free split/recover (no session).
// ===========================================================================

// Render the per-piece list under a split result. For "Split a secret" each piece carries a
// copy-paste code (share_b64); for "Split a file" share_b64 is empty, so only paths are shown.
function renderPieceList(id, rep) {
  const list = $(id);
  if (!list) return;
  list.innerHTML = "";
  rep.share_paths.forEach((p, i) => {
    const li = document.createElement("li");
    const name = document.createElement("span");
    name.className = "item-name";
    name.textContent = t("r.piece.label", { index: i + 1, total: rep.shares_total });
    const path = document.createElement("span");
    path.className = "muted path";
    path.textContent = p;
    li.appendChild(name);
    li.appendChild(path);
    const code = rep.share_b64 && rep.share_b64[i];
    if (code) {
      const cp = document.createElement("button");
      cp.className = "secondary btn-mini";
      cp.textContent = t("btn.copyCode");
      cp.addEventListener("click", async () => {
        const ok = await copyText(code);
        setStatus(ok ? t("status.pieceCopied") : t("status.pieceCopyFailed"), ok ? "ok" : "error");
      });
      li.appendChild(cp);
    }
    list.appendChild(li);
  });
}

// Validate "2 ≤ needed ≤ total ≤ 255" for the two number inputs; returns the parsed pair or null.
function readPolicy(totalId, neededId) {
  const total = parseInt($(totalId).value, 10);
  const needed = parseInt($(neededId).value, 10);
  if (!(needed >= 2 && total >= needed && total <= 255)) {
    setStatus(t("status.policyPieces"), "error");
    return null;
  }
  return { total, needed };
}

// ---- Split a secret ------------------------------------------------------

$("tk-btn-split-secret").addEventListener("click", (e) => {
  const text = $("tk-split-secret-text");
  const outDir = $("tk-split-secret-outdir");
  if (!validate([[text, t("v.ss.text")], [outDir, t("v.ss.outdir")]])) return;
  const pol = readPolicy("tk-split-secret-total", "tk-split-secret-needed");
  if (!pol) return;
  runTask(e.target, "tk-split-secret-result", async () => {
    const rep = await invoke("shares_split_secret", {
      secret: text.value,
      sharesTotal: pol.total,
      threshold: pol.needed,
      outDir: outDir.value,
    });
    text.value = ""; // the secret must not linger in the field
    renderPieceList("tk-split-secret-pieces", rep);
    return {
      ok: true,
      title: t("r.ss.title", { n: rep.shares_total }),
      message: t("r.ss.msg", { threshold: rep.threshold }),
      rows: [{ label: t("r.payload.label"), value: rep.payload_path, copy: true }],
      actions: [revealAction(rep.payload_path)],
    };
  });
});

// ---- Split a file --------------------------------------------------------

$("tk-btn-split-file").addEventListener("click", (e) => {
  const input = $("tk-split-file-input");
  const outDir = $("tk-split-file-outdir");
  if (!validate([[input, t("v.sf.input")], [outDir, t("v.sf.outdir")]])) return;
  const pol = readPolicy("tk-split-file-total", "tk-split-file-needed");
  if (!pol) return;
  runTask(e.target, "tk-split-file-result", async () => {
    const rep = await invoke("shares_split_file", {
      input: input.value,
      sharesTotal: pol.total,
      threshold: pol.needed,
      outDir: outDir.value,
    });
    renderPieceList("tk-split-file-list", rep);
    return {
      ok: true,
      title: t("r.sf.title", { n: rep.shares_total }),
      message: t("r.sf.msg", { threshold: rep.threshold }),
      rows: [{ label: t("r.payload.label"), value: rep.payload_path, copy: true }],
      actions: [revealAction(rep.payload_path)],
    };
  });
});

// ---- Recover from pieces -------------------------------------------------

$("tk-btn-recover-pieces").addEventListener("click", (e) => {
  const files = $("tk-recover-files");
  const codes = $("tk-recover-codes");
  const payload = $("tk-recover-payload");
  const output = $("tk-recover-output");
  const sharePaths = linesOf(files.value);
  const shareStrings = linesOf(codes.value);
  if (!validate([[payload, t("v.rp.payload")], [output, t("v.rp.output")]])) return;
  if (sharePaths.length + shareStrings.length === 0) {
    setFieldError(files, t("v.rp.pieces"));
    files.focus();
    return;
  }
  clearFieldError(files);
  runTask(
    e.target,
    "tk-recover-result",
    async () => {
      const rep = await invoke("shares_recover_secret", {
        sharePaths,
        shareStrings,
        payloadPath: payload.value,
        outPath: output.value,
      });
      return {
        ok: true,
        title: t("r.recover.title"),
        message: t("r.recover.msg"),
        rows: [{ label: t("r.label.savedTo"), value: rep.output_path, copy: true }],
        actions: [revealAction(rep.output_path), openAction(rep.output_path)],
      };
    },
    (err) => {
      if (err && err.code === "SV-UNAUTHORIZED") {
        return {
          title: t("r.recover.bad.title"),
          message: t("r.recover.bad.msg"),
        };
      }
      return outputExistsMap("tk-recover-output")(err);
    },
  );
});

// ---- Secure QR transfer: make QR images from piece codes ------------------

$("tk-btn-qr-make").addEventListener("click", (e) => {
  const codes = $("tk-qr-codes");
  const outDir = $("tk-qr-outdir");
  const shareB64 = linesOf(codes.value);
  if (!validate([[outDir, t("v.qr.outdir")]])) return;
  if (shareB64.length === 0) {
    setFieldError(codes, t("v.qr.codes"));
    codes.focus();
    return;
  }
  clearFieldError(codes);
  runTask(
    e.target,
    "tk-qr-make-result",
    async () => {
      const rep = await invoke("shares_export_qr", { shareB64, outDir: outDir.value });
      const rows = rep.image_paths.map((p, i) => ({ label: t("r.qr.pieceLabel", { n: i + 1 }), value: p, copy: true }));
      return {
        ok: true,
        title: plural(rep.image_paths.length, "r.qrmake.title"),
        message: t("r.qrmake.msg"),
        rows,
        actions: rep.image_paths.length ? [revealAction(rep.image_paths[0])] : [],
      };
    },
    outputExistsMap("tk-qr-outdir"),
  );
});

// ---- Secure QR transfer: recover from QR images ---------------------------

$("tk-btn-qr-recover").addEventListener("click", (e) => {
  const images = $("tk-qr-images");
  const payload = $("tk-qr-payload");
  const output = $("tk-qr-out");
  const qrPaths = linesOf(images.value);
  if (!validate([[payload, t("v.qr.payload")], [output, t("v.qr.output")]])) return;
  if (qrPaths.length === 0) {
    setFieldError(images, t("v.qr.images"));
    images.focus();
    return;
  }
  clearFieldError(images);
  runTask(
    e.target,
    "tk-qr-recover-result",
    async () => {
      const rep = await invoke("shares_recover_from_qr", {
        qrPaths,
        payloadPath: payload.value,
        outPath: output.value,
      });
      return {
        ok: true,
        title: t("r.qrrecover.title"),
        message: t("r.qrrecover.msg"),
        rows: [{ label: t("r.label.savedTo"), value: rep.output_path, copy: true }],
        actions: [revealAction(rep.output_path), openAction(rep.output_path)],
      };
    },
    (err) => {
      if (err && err.code === "SV-UNAUTHORIZED") {
        return {
          title: t("r.recover.bad.title"),
          message: t("r.recover.bad.msg"),
        };
      }
      if (err && err.code === "SV-MALFORMED") {
        return {
          title: t("r.qr.badRead.title"),
          message: t("r.qr.badRead.msg"),
        };
      }
      return outputExistsMap("tk-qr-out")(err);
    },
  );
});

// ---- Watermark: embed a fragile tamper-evident mark -----------------------

$("tk-btn-wm-embed").addEventListener("click", (e) => {
  const input = $("tk-wm-input");
  const output = $("tk-wm-output");
  const pass = $("tk-wm-pass");
  if (
    !validate([
      [input, t("v.wm.input")],
      [output, t("v.wm.output")],
      [pass, t("v.wm.pass")],
    ])
  )
    return;
  runTask(
    e.target,
    "tk-wm-embed-result",
    async () => {
      const rep = await invoke("watermark_embed", {
        input: input.value,
        output: output.value,
        passphrase: pass.value,
      });
      pass.value = "";
      return {
        ok: true,
        title: t("r.wm.title"),
        message: t("r.wm.msg"),
        rows: [
          { label: t("r.label.savedTo"), value: rep.output_path, copy: true },
          { label: t("r.label.size"), value: `${rep.width} × ${rep.height}` },
          { label: t("r.wm.regions"), value: String(rep.blocks) },
        ],
        actions: [revealAction(rep.output_path)],
      };
    },
    (err) => {
      if (err && err.code === "SV-INVALID-INPUT") return { title: t("r.wm.bad.title"), message: describe(err) };
      return outputExistsMap("tk-wm-output")(err);
    },
  );
});

// ---- Watermark: verify / detect tampering ---------------------------------

$("tk-btn-wm-verify").addEventListener("click", (e) => {
  const input = $("tk-wmv-input");
  const pass = $("tk-wmv-pass");
  if (!validate([[input, t("v.wmv.input")], [pass, t("v.wmv.pass")]])) return;
  runTask(e.target, "tk-wmv-result", async () => {
    const rep = await invoke("watermark_verify", { input: input.value, passphrase: pass.value });
    pass.value = "";
    if (rep.verdict === "Intact") {
      return {
        ok: true,
        title: t("r.wmv.intact.title"),
        message: t("r.wmv.intact.msg"),
        rows: [{ label: t("r.wmv.regionsChecked"), value: String(rep.total_blocks) }],
      };
    }
    if (rep.verdict === "Tampered") {
      return {
        ok: false,
        title: t("r.wmv.tampered.title"),
        message: t("r.wmv.tampered.msg", { tampered: rep.tampered_blocks, total: rep.total_blocks }),
        rows: [
          { label: t("r.wmv.altered"), value: t("r.wmv.alteredVal", { tampered: rep.tampered_blocks, total: rep.total_blocks }) },
        ],
      };
    }
    return {
      ok: false,
      title: t("r.wmv.none.title"),
      message: t("r.wmv.none.msg"),
      rows: [{ label: t("r.wmv.regionsChecked"), value: String(rep.total_blocks) }],
    };
  });
});

init();
