// Security & Privacy Toolkit — frontend controller.
//
// Talks to the Rust core via Tauri's global `invoke` (enabled by `app.withGlobalTauri` in
// tauri.conf.json, so no npm bundler is required). Every backend error is the coded,
// oracle-safe `ApiError` — we render `error.code` (a stable `SV-…` string) so messages are
// localizable and never leak which secret was wrong. The frontend holds only an opaque
// `SessionHandle`; no key material ever crosses the boundary.

const { invoke } = window.__TAURI__.core;

let session = null; // opaque SessionHandle from the core; never holds key material.
let currentVaultPath = null; // path of the open vault, for display only.

const $ = (id) => document.getElementById(id);

// ---- error rendering -----------------------------------------------------

// Map stable error codes → human strings. The backend never distinguishes wrong-passphrase
// from wrong-share (both → SV-UNAUTHORIZED), preserving the oracle-safe contract.
const MESSAGES = {
  "SV-NOT-FOUND": "That file could not be found.",
  "SV-MALFORMED": "That file is not the expected type.",
  "SV-INCOMPATIBLE-VERSION": "This file needs a newer version of the app.",
  "SV-CORRUPTED": "This file is damaged or has been tampered with.",
  "SV-UNAUTHORIZED": "Wrong password, recovery shares, or tampered data.",
  "SV-INSUFFICIENT-SHARES": "Not enough recovery shares.",
  "SV-INVALID-INPUT": "Something about the input wasn't valid.",
  "SV-IO": "A file could not be read or written.",
  "SV-TOO-LARGE": "That file is too large.",
  "SV-TIMEOUT": "The operation took too long and was stopped.",
  "SV-OUTPUT-EXISTS": "A file already exists at that location.",
  "SV-INTERNAL": "Something went wrong inside the app.",
};

function mib(bytes) {
  return `${(bytes / (1024 * 1024)).toFixed(0)} MiB`;
}

function describe(err) {
  // ApiError is serialized as `{ code: "SV-…", ...fields }`.
  const code = err && err.code ? err.code : "SV-INTERNAL";
  let msg = MESSAGES[code] || code;
  if (code === "SV-INSUFFICIENT-SHARES" && err.got != null) {
    msg = `Not enough recovery shares: you added ${err.got}, but ${err.need} are needed.`;
  }
  if (code === "SV-INCOMPATIBLE-VERSION" && err.found != null) {
    msg = `This file is version ${err.found}; this app supports version ${err.supported}.`;
  }
  if (code === "SV-INVALID-INPUT" && err.detail) {
    msg = err.detail;
  }
  if (code === "SV-TOO-LARGE" && err.actual_bytes != null) {
    msg = `That file is ${mib(err.actual_bytes)}, over the ${mib(err.limit_bytes)} limit.`;
  }
  if (code === "SV-IO" && err.detail) {
    msg = err.detail;
  }
  if (code === "SV-OUTPUT-EXISTS") {
    msg = "A file already exists at that path — choose a different name so nothing is overwritten.";
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
  setStatus(ok ? "Couldn't open the folder here — path copied to clipboard." : "Couldn't open the folder.", "info");
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
  setStatus(ok ? "Couldn't open the file here — path copied to clipboard." : "Couldn't open the file.", "info");
}

// Common result-card actions.
function revealAction(path) {
  return { label: "Show in folder", onClick: () => revealInFolder(path) };
}
function openAction(path) {
  return { label: "Open file", onClick: () => openFile(path) };
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
  title.textContent = (opts.ok ? "✅ " : "❌ ") + opts.title;
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
        cp.textContent = "Copy";
        cp.addEventListener("click", async () => {
          const ok = await copyText(r.value);
          setStatus(ok ? "Copied to clipboard." : "Couldn't copy — select the text manually.", ok ? "ok" : "error");
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
    btn.textContent = "Working…";
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
          title: "A file already exists there",
          message: "Nothing was overwritten. Choose a different name and try again.",
          actions: [{ label: "Pick a new name…", primary: true, onClick: () => clickSaveFor(outputId) }],
        }
      : null;
}

// ---- view / tab switching ------------------------------------------------

function showUnlocked(show) {
  $("unlocked-view").classList.toggle("hidden", !show);
  $("locked-view").classList.toggle("hidden", show);
  const badge = $("lock-badge");
  badge.textContent = show ? "Unlocked" : "Locked";
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
    setStatus("File picker isn't available here — type the path instead.", "info");
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
  out.value = strip && src.endsWith(strip) ? src.slice(0, -strip.length) : src + suffix;
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
        if (from) defaultPath = from + (btn.dataset.suffix || "");
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
    setStatus("File added.", "ok");
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
  $("vault-title").textContent = currentVaultPath ? baseName(currentVaultPath) : "Vault";
  const summary = [];
  const tech = [];
  if (meta) {
    summary.push(`${meta.item_count} file${meta.item_count === 1 ? "" : "s"}`);
    summary.push(
      meta.share_policy
        ? `recovery: any ${meta.share_policy.threshold} of ${meta.share_policy.shares_total}`
        : "no recovery set up",
    );
    // Technical details live in the collapsed "Vault details" panel, not the banner.
    tech.push(`Vault ID: ${meta.vault_uuid}`);
    tech.push(`File format: version ${meta.format_version}`);
    if (meta.kdf) {
      tech.push(
        `Password protection: ${meta.kdf.algorithm}, ${Math.round(meta.kdf.mem_kib / 1024)} MiB, ${meta.kdf.time_cost} passes`,
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
    note.textContent = `This vault is set up for recovery: any ${meta.share_policy.threshold} of ${meta.share_policy.shares_total} pieces can restore it. Make the pieces below and keep each one separate.`;
  } else if (meta) {
    note.textContent =
      "This vault has no recovery set up, so pieces made here can't restore it. To use recovery, create a new vault with recovery enabled.";
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
  $("item-count").textContent = `${items.length} item${items.length === 1 ? "" : "s"}`;
  if (currentMeta) {
    currentMeta.item_count = items.length;
    renderMeta(currentMeta);
  }
  if (items.length === 0) {
    list.innerHTML = '<li class="muted empty">No items yet. Add a file below.</li>';
    return;
  }
  for (const it of items) {
    const li = document.createElement("li");
    li.innerHTML = `
      <span class="item-name"></span>
      <span class="muted">${humanSize(it.size_bytes)} · ${shortHash(it.content_hash_hex)}</span>
      <button class="extract secondary btn-mini">Save a copy…</button>`;
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
      setStatus(`Saved “${it.name}” to ${dest}`, "ok");
    } catch (e) {
      setStatus(describe(e), "error");
    }
  });
}

// ===========================================================================
// Wiring
// ===========================================================================

async function init() {
  wireSidebar();
  initTiles();
  initAbout();
  initBrowse();
  initDragDrop();
  try {
    const info = await invoke("app_info");
    $("about-version").textContent = `Version ${info.app_version} · vault format v${info.max_format_version} · suite v${info.suite_version} · contract v${info.contract_version}`;
  } catch (_) {
    /* non-fatal */
  }
}

// ---- create / unlock -----------------------------------------------------

$("btn-create").addEventListener("click", (e) => {
  const path = $("create-path");
  const p1 = $("create-pass");
  const p2 = $("create-pass-2");
  if (!validate([[path, "Choose where to save the new vault"], [p1, "Set a password"]])) return;
  if (p1.value !== p2.value) {
    setFieldError(p2, "Passwords don't match. A typo here would lock you out permanently.");
    p2.focus();
    return;
  }
  clearFieldError(p2);

  let policy = null;
  if ($("create-recovery").checked) {
    const sharesTotal = parseInt($("create-shares-total").value, 10);
    const threshold = parseInt($("create-threshold").value, 10);
    if (!(threshold >= 2 && sharesTotal >= threshold && sharesTotal <= 255)) {
      setStatus("Recovery must satisfy 2 ≤ needed ≤ total ≤ 255.", "error");
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
      title: "Vault created",
      message: policy
        ? "Recovery is enabled — make the pieces after you open it."
        : "Now open it: pick this file in “Open a vault” and enter your password.",
      rows: [{ label: "Saved to", value: path.value, copy: true }],
      actions: [
        revealAction(path.value),
        {
          label: "Open it now",
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
    if (!validate([[path, "Choose the vault file"], [p1, "Enter your password"]])) return;

    session = await invoke("vault_unlock", { path: path.value, passphrase: p1.value });
    p1.value = "";
    currentVaultPath = path.value;
    hideAllResults();
    showUnlocked(true);
    setStatus("Vault opened.", "ok");
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
  setStatus("Locked.", "info");
});

// ---- add item ------------------------------------------------------------

$("btn-add").addEventListener("click", (e) =>
  withButton(e.target, async () => {
    const source = $("add-source");
    const name = $("add-name");
    if (!validate([[source, "Choose a file to add"], [name, "Give it a name in the vault"]])) return;
    await invoke("item_add", { session, source: source.value, name: name.value });
    source.value = "";
    name.value = "";
    setStatus("Item added.", "ok");
    await refreshItems();
  }),
);

// ---- recovery: split -----------------------------------------------------

$("btn-split").addEventListener("click", (e) => {
  const outDir = $("split-outdir");
  if (!validate([[outDir, "Choose a folder for the share files"]])) return;
  const sharesTotal = parseInt($("split-shares-total").value, 10);
  const threshold = parseInt($("split-threshold").value, 10);
  if (!(threshold >= 2 && sharesTotal >= threshold && sharesTotal <= 255)) {
    setStatus("Shares must satisfy 2 ≤ needed ≤ total ≤ 255.", "error");
    return;
  }
  runTask(e.target, "split-result", async () => {
    const infos = await invoke("keys_split", { session, sharesTotal, threshold, outDir: outDir.value });
    const list = $("share-list");
    list.innerHTML = "";
    for (const info of infos) {
      const li = document.createElement("li");
      li.innerHTML = `<span class="item-name">Share ${info.share_index} / ${info.shares_total}</span>
        <span class="muted path"></span>`;
      li.querySelector(".path").textContent = info.output_path;
      list.appendChild(li);
    }
    return {
      ok: true,
      title: `Created ${infos.length} recovery piece${infos.length === 1 ? "" : "s"}`,
      message: `Any ${threshold} of them together can restore this vault. Store each in a separate trusted place.`,
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
    if (!validate([[path, "Choose the vault file"]])) return;
    if (sharePaths.length === 0) {
      setFieldError(shares, "Add at least one recovery share file.");
      shares.focus();
      return;
    }
    clearFieldError(shares);
    session = await invoke("keys_recover", { path: path.value, sharePaths });
    currentVaultPath = path.value;
    hideAllResults();
    showUnlocked(true);
    setStatus("Recovered and opened.", "ok");
    await loadVault();
  }),
);

// ---- vault: sign ---------------------------------------------------------

$("btn-sign").addEventListener("click", (e) => {
  const file = $("sign-file");
  if (!validate([[file, "Choose a file to sign"]])) return;
  runTask(e.target, "sign-result", async () => {
    const sigPath = await invoke("sign_file", { session, path: file.value });
    return {
      ok: true,
      title: "File signed with the vault key",
      rows: [{ label: "Signature", value: sigPath, copy: true }],
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
      [file, "Choose the signed file"],
      [sig, "Choose the signature file"],
      [pub, "Choose the public key file"],
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
          title: "Signature is valid",
          message: "Signed with this key, and the file is unchanged.",
          rows: [{ label: "Fingerprint", value: report.computed_hash_hex, copy: true }],
        }
      : {
          ok: false,
          title: "Signature does NOT match",
          message: "The file, signature, or public key is wrong, or the file changed.",
        };
  });
});

$("btn-integrity").addEventListener("click", (e) => {
  const path = $("integrity-path");
  if (!validate([[path, "Choose the vault file"]])) return;
  runTask(e.target, "tools-result", async () => {
    const report = await invoke("integrity_check", { path: path.value });
    return report.signature_ok
      ? {
          ok: true,
          title: "Vault is intact",
          message: "Its signature and contents check out.",
          rows: [{ label: "Fingerprint", value: report.computed_hash_hex, copy: true }],
        }
      : { ok: false, title: "Integrity check failed", message: "This vault is damaged or has been tampered with." };
  });
});

$("btn-hash").addEventListener("click", (e) => {
  const path = $("integrity-path");
  if (!validate([[path, "Choose the vault file"]])) return;
  runTask(e.target, "tools-result", async () => {
    const hash = await invoke("integrity_hash", { path: path.value });
    return { ok: true, title: "Vault fingerprint", rows: [{ label: "BLAKE3", value: hash, copy: true }] };
  });
});

// ---- change passphrase ---------------------------------------------------

$("btn-change-pass").addEventListener("click", (e) =>
  withButton(e.target, async () => {
    const a = $("new-passphrase");
    const b = $("new-passphrase-2");
    if (!validate([[a, "Enter a new password"]])) return;
    if (a.value !== b.value) {
      setFieldError(b, "Passwords don't match.");
      b.focus();
      return;
    }
    clearFieldError(b);
    await invoke("vault_change_passphrase", { session, newPassphrase: a.value });
    a.value = "";
    b.value = "";
    setStatus("Password changed.", "ok");
  }),
);

// ---- signing public key (read-only export) -------------------------------

let pubkeyHex = null;

function resetPubkey() {
  pubkeyHex = null;
  $("signing-pubkey").textContent = 'Click "Show public key".';
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
    setStatus("Public key loaded. Save it to a .pub file to let others verify your signatures.", "ok");
  }),
);

$("btn-copy-pubkey").addEventListener("click", async () => {
  if (!pubkeyHex) return;
  const ok = await copyText(pubkeyHex);
  if (ok) {
    setStatus("Public key copied to clipboard.", "ok");
  } else {
    const el = $("signing-pubkey");
    const range = document.createRange();
    range.selectNodeContents(el);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
    setStatus("Select-all applied — press ⌘/Ctrl-C to copy.", "info");
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
          title: "This vault file is intact",
          rows: [{ label: "Fingerprint", value: report.computed_hash_hex, copy: true }],
        }
      : { ok: false, title: "This vault file failed the check", message: "It may be damaged or tampered with." };
  });
});

// ===========================================================================
// Toolkit — vault-free Integrity + Cryptography commands (no session).
// ===========================================================================

// ---- Fingerprint a file --------------------------------------------------

$("tk-btn-hash").addEventListener("click", (e) => {
  const path = $("tk-hash-path");
  if (!validate([[path, "Choose a file"]])) return;
  runTask(e.target, "tk-hash-result", async () => {
    const hash = await invoke("integrity_hash_file", { path: path.value });
    return {
      ok: true,
      title: "Fingerprint ready",
      message: "Two files with the same fingerprint are identical.",
      rows: [{ label: "BLAKE3", value: hash, copy: true }],
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
      [file, "Choose the file"],
      [sig, "Choose the signature file"],
      [pub, "Choose the public key file"],
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
          title: "Genuine",
          message: "Signed with this key, and the file is unchanged.",
          rows: [{ label: "Fingerprint", value: report.computed_hash_hex, copy: true }],
        }
      : {
          ok: false,
          title: "Does NOT match",
          message: "The file, signature, or public key is wrong, or the file changed.",
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
  if (!validate([[file, "Choose a file"], [expected, "Paste the fingerprint you were given"]])) return;
  runTask(e.target, "tk-intact-result", async () => {
    const actual = await invoke("integrity_hash_file", { path: file.value });
    const norm = (s) => s.trim().toLowerCase().replace(/\s+/g, "");
    const want = norm(expected.value);
    const match = norm(actual) === want;
    return match
      ? {
          ok: true,
          title: "Unchanged",
          message: "This file matches the fingerprint — it hasn't been altered.",
          rows: [{ label: "Fingerprint", value: actual, copy: true }],
        }
      : {
          ok: false,
          title: "Does NOT match",
          message: "This file doesn't match the fingerprint you provided — it may have changed, or be a different file.",
          rows: [
            { label: "This file", value: actual, copy: true },
            { label: "Expected", value: want || "(empty)" },
          ],
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
      [input, "Choose a file to lock"],
      [output, "Choose where to save the locked file"],
      [p1, "Set a password"],
    ])
  )
    return;
  if (p1.value !== p2.value) {
    setFieldError(p2, "Passwords don't match. A typo here is unrecoverable.");
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
        title: "File locked",
        message: "Keep your password safe — it's the only way to open this file.",
        rows: [{ label: "Saved to", value: out, copy: true }],
        actions: [
          revealAction(out),
          {
            label: "Lock another file",
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
      [input, "Choose the locked file"],
      [output, "Choose where to save the opened file"],
      [p1, "Enter the password"],
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
        title: "File unlocked",
        rows: [{ label: "Saved to", value: out, copy: true }],
        actions: [revealAction(out), openAction(out)],
      };
    },
    (err) => {
      if (err && err.code === "SV-UNAUTHORIZED") {
        return { title: "Couldn't unlock this file", message: "The password is wrong, or this isn't a valid locked file." };
      }
      return outputExistsMap("tk-dec-output")(err);
    },
  );
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
      [outDir, "Choose a folder for the identity"],
      [name, "Name this identity"],
      [p1, "Set a password"],
    ])
  )
    return;
  if (p1.value !== p2.value) {
    setFieldError(p2, "Passwords don't match.");
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
      title: "Signing identity created",
      message: "Keep the private key (.svkey) and its password safe. Share the public key so others can verify.",
      rows: [
        { label: "Public key", value: info.public_key_path, copy: true },
        { label: "Private key", value: info.secret_key_path, copy: true },
        { label: "Public (hex)", value: info.public_key_hex, copy: true },
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
      [input, "Choose a file to sign"],
      [key, "Choose your private key (.svkey)"],
      [p1, "Enter the key's password"],
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
        title: "File signed",
        rows: [{ label: "Signature", value: sigPath, copy: true }],
        actions: [
          revealAction(sigPath),
          {
            label: "Check this signature",
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
        ? { title: "Couldn't sign", message: "The password for this signing key is wrong." }
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
    name.textContent = `Piece ${i + 1} / ${rep.shares_total}`;
    const path = document.createElement("span");
    path.className = "muted path";
    path.textContent = p;
    li.appendChild(name);
    li.appendChild(path);
    const code = rep.share_b64 && rep.share_b64[i];
    if (code) {
      const cp = document.createElement("button");
      cp.className = "secondary btn-mini";
      cp.textContent = "Copy code";
      cp.addEventListener("click", async () => {
        const ok = await copyText(code);
        setStatus(ok ? "Piece code copied — keep it secret." : "Couldn't copy — open the piece file instead.", ok ? "ok" : "error");
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
    setStatus("Pieces must satisfy 2 ≤ needed ≤ total ≤ 255.", "error");
    return null;
  }
  return { total, needed };
}

// ---- Split a secret ------------------------------------------------------

$("tk-btn-split-secret").addEventListener("click", (e) => {
  const text = $("tk-split-secret-text");
  const outDir = $("tk-split-secret-outdir");
  if (!validate([[text, "Type the secret to split"], [outDir, "Choose a folder for the pieces"]])) return;
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
      title: `Made ${rep.shares_total} pieces`,
      message: `Any ${rep.threshold} together restore the secret. Keep the payload file with them — it's needed to recover. Each code below is secret; store the pieces separately.`,
      rows: [{ label: "Payload file", value: rep.payload_path, copy: true }],
      actions: [revealAction(rep.payload_path)],
    };
  });
});

// ---- Split a file --------------------------------------------------------

$("tk-btn-split-file").addEventListener("click", (e) => {
  const input = $("tk-split-file-input");
  const outDir = $("tk-split-file-outdir");
  if (!validate([[input, "Choose a file to split"], [outDir, "Choose a folder for the pieces"]])) return;
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
      title: `Made ${rep.shares_total} pieces`,
      message: `Any ${rep.threshold} of these piece files plus the payload file can restore your file. Store each piece separately.`,
      rows: [{ label: "Payload file", value: rep.payload_path, copy: true }],
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
  if (!validate([[payload, "Choose the payload file"], [output, "Choose where to save the result"]])) return;
  if (sharePaths.length + shareStrings.length === 0) {
    setFieldError(files, "Add at least one piece — a file or a pasted code.");
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
        title: "Recovered",
        message: "The pieces matched and the secret was rebuilt.",
        rows: [{ label: "Saved to", value: rep.output_path, copy: true }],
        actions: [revealAction(rep.output_path), openAction(rep.output_path)],
      };
    },
    (err) => {
      if (err && err.code === "SV-UNAUTHORIZED") {
        return {
          title: "Couldn't recover",
          message: "These pieces don't match, are from a different split, or the payload is wrong or damaged.",
        };
      }
      return outputExistsMap("tk-recover-output")(err);
    },
  );
});

init();
