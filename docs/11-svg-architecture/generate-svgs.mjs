// Secure Vault — SVG architecture package generator
// Deterministic, dependency-free. Emits the five ARCH-*.svg files next to this script.
// Run: `node generate-svgs.mjs`. The SVGs are the deliverable; this script reproduces them
// so they stay consistent and editable at source. Facts are sourced from the codebase audit
// (see README.md); nothing here is invented.

import { writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const OUT = dirname(fileURLToPath(import.meta.url));

// ---- palette (dark-on-light, print-friendly) -------------------------------
const INK = "#1c2330", SUB = "#5b6675", LINE = "#566072", HAIR = "#aab2bf";
const COL = {
  ui:     { f: "#e9f1fd", s: "#2f6ab0" }, // presentation / webview — blue
  ipc:    { f: "#fdf3e2", s: "#b9791b" }, // IPC boundary — amber
  comp:   { f: "#eef0f6", s: "#46506a" }, // composition root — indigo-gray
  domain: { f: "#eaf3ee", s: "#3c7d4f" }, // domain crates — green
  plat:   { f: "#e7f1f2", s: "#2f7b86" }, // shared platform (ABI/types) — teal
  crit:   { f: "#fbe9e9", s: "#b0413f" }, // security-critical — red
  ext:    { f: "#efeaf8", s: "#6a4f9c" }, // external tools — purple
  fs:     { f: "#eceff3", s: "#5d6b7c" }, // filesystem / OS — slate
  neutral:{ f: "#f4f6f9", s: "#5b6675" },
};
const CRIT_S = COL.crit.s;

// ---- primitives ------------------------------------------------------------
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

function text(x, y, str, { cls = "node", anchor = "middle", fill } = {}) {
  const f = fill ? ` fill="${fill}"` : "";
  return `<text x="${x}" y="${y}" class="${cls}" text-anchor="${anchor}"${f}>${esc(str)}</text>`;
}

// box with centered title + centered sub-lines
function box(x, y, w, h, { title, lines = [], color = COL.neutral, critical = false, titleCls = "node" } = {}) {
  const s = critical ? CRIT_S : color.s;
  const sw = critical ? 2 : 1.3;
  const cx = x + w / 2;
  let out = `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="7" ry="7" fill="${color.f}" stroke="${s}" stroke-width="${sw}"/>`;
  // vertically center the text block
  const lh = 13.5, blockH = 15 + lines.length * lh;
  let ty = y + (h - blockH) / 2 + 13;
  out += text(cx, ty, title, { cls: titleCls });
  let ly = ty + 16;
  for (const ln of lines) { out += text(cx, ly, ln, { cls: "sub" }); ly += lh; }
  if (critical) out += `<circle cx="${x + w - 11}" cy="${y + 11}" r="4.2" fill="${CRIT_S}"/>`;
  return out;
}

// dashed trust/zone container with a label tab
function zone(x, y, w, h, { label, stroke = SUB, fill = "none", labelFill } = {}) {
  let out = `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="9" ry="9" fill="${fill}" stroke="${stroke}" stroke-width="1.4" stroke-dasharray="7 5"/>`;
  const tw = label.length * 6.6 + 16;
  out += `<rect x="${x + 14}" y="${y - 11}" width="${tw}" height="22" rx="5" fill="#ffffff" stroke="${stroke}" stroke-width="1.1"/>`;
  out += text(x + 14 + tw / 2, y + 4, label, { cls: "zone", fill: labelFill || stroke });
  return out;
}

function arrow(x1, y1, x2, y2, { dashed = false, color = LINE, label, width = 1.6 } = {}) {
  const dash = dashed ? ` stroke-dasharray="6 4"` : "";
  let out = `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="${width}"${dash} marker-end="url(#arrow)"/>`;
  if (label) {
    const mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
    const tw = label.length * 6 + 10;
    out += `<rect x="${mx - tw / 2}" y="${my - 9}" width="${tw}" height="16" rx="3" fill="#ffffff" stroke="${HAIR}" stroke-width="0.8"/>`;
    out += text(mx, my + 3, label, { cls: "lbl" });
  }
  return out;
}

function legend(x, y, items, { title = "Legend", cols = 1, colW = 250 } = {}) {
  let out = `<rect x="${x}" y="${y}" width="${items.colW || 286}" height="${items.boxH || (28 + items.length * 19)}" rx="7" fill="#ffffff" stroke="${HAIR}" stroke-width="1"/>`;
  out += text(x + 12, y + 19, title, { cls: "zone", anchor: "start" });
  let ry = y + 40;
  for (const it of items) {
    if (it.swatch) {
      out += `<rect x="${x + 12}" y="${ry - 11}" width="17" height="12" rx="2.5" fill="${it.swatch.f}" stroke="${it.critical ? CRIT_S : it.swatch.s}" stroke-width="${it.critical ? 2 : 1.2}"/>`;
      if (it.critical) out += `<circle cx="${x + 12 + 17 - 4}" cy="${ry - 11 + 3.5}" r="2.4" fill="${CRIT_S}"/>`;
    } else if (it.line) {
      out += `<line x1="${x + 12}" y1="${ry - 5}" x2="${x + 29}" y2="${ry - 5}" stroke="${it.color || LINE}" stroke-width="1.8"${it.dashed ? ' stroke-dasharray="5 3"' : ""} marker-end="url(#arrow)"/>`;
    }
    out += text(x + 38, ry - 1, it.text, { cls: "legend", anchor: "start" });
    ry += 19;
  }
  return out;
}

const STYLE = `
  <style>
    text { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; fill: ${INK}; }
    .title { font-size: 25px; font-weight: 700; }
    .subtitle { font-size: 13px; fill: ${SUB}; }
    .zone { font-size: 12.5px; font-weight: 700; }
    .node { font-size: 13px; font-weight: 600; }
    .nodeb { font-size: 14px; font-weight: 700; }
    .sub { font-size: 10.8px; fill: #45505f; }
    .lbl { font-size: 10.5px; fill: #34404f; }
    .legend { font-size: 11.3px; }
    .foot { font-size: 10.3px; fill: ${SUB}; }
    .gut { font-size: 11px; font-weight: 700; fill: ${SUB}; letter-spacing: 0.4px; }
    .tag { font-size: 10.5px; font-weight: 700; }
  </style>`;

const DEFS = `
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="7.6" refY="3" orient="auto" markerUnits="userSpaceOnUse">
      <path d="M0,0 L8,3 L0,6 Z" fill="${LINE}"/>
    </marker>
  </defs>`;

function doc(w, h, inner, { title, subtitle, footer }) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(title)}">
${STYLE}
${DEFS}
  <rect x="0" y="0" width="${w}" height="${h}" fill="#ffffff"/>
  <text x="40" y="44" class="title">${esc(title)}</text>
  <text x="40" y="66" class="subtitle">${esc(subtitle)}</text>
  <line x1="40" y1="76" x2="${w - 40}" y2="76" stroke="${HAIR}" stroke-width="1"/>
${inner}
  <line x1="40" y1="${h - 34}" x2="${w - 40}" y2="${h - 34}" stroke="${HAIR}" stroke-width="1"/>
  <text x="40" y="${h - 16}" class="foot">${esc(footer)}</text>
</svg>
`;
}

const FOOT = "Secure Vault — Security & Privacy Toolkit · v0.1.0   |   Source of truth: source code under secure-vault/ (see 11-svg-architecture/README.md)";

// ===========================================================================
// ARCH-01 — Overall system architecture
// ===========================================================================
function arch01() {
  const W = 1240, H = 985, cx = 675, L = 160, R = 1190, CW = R - L;
  let s = "";
  const gut = (y, t) => text(44, y, t, { cls: "gut", anchor: "start" });

  // Row 1 — User
  s += gut(121, "USER");
  s += box(540, 92, 270, 50, { title: "User", lines: ["local · single host · offline"], color: COL.neutral, titleCls: "nodeb" });
  s += arrow(cx, 142, cx, 172);

  // Row 2 — Presentation
  s += gut(212, "PRESENTATION");
  s += box(L, 176, CW, 64, {
    title: "Tauri 2 WebView — static frontend (withGlobalTauri)",
    lines: ["index.html · main.js · i18n.js · styles.css", "22 screen sections (20 routable) · vi/en i18n · CSP: no inline scripts"],
    color: COL.ui, titleCls: "nodeb",
  });
  s += arrow(cx, 240, cx, 270);

  // Row 3 — IPC boundary
  s += gut(301, "IPC BOUNDARY");
  s += box(L, 272, CW, 50, {
    title: "IPC — Tauri invoke · 38 commands · coded oracle-safe ApiError",
    lines: ["IpcPassphrase (zeroizing) · file paths cross the boundary, never secret bytes"],
    color: COL.ipc, titleCls: "node",
  });
  s += arrow(cx, 322, cx, 352);

  // Row 4 — Composition root with 5 managed-state chips
  s += gut(400, "COMPOSITION");
  s += box(L, 354, CW, 92, { title: "sv-app composition root  (desktop/src/lib.rs + src-tauri)", color: COL.comp });
  const chips = [["Backend", "vault"], ["Platform", "crypto/share/QR"], ["Stego", "conceal"], ["Meta", "metadata"], ["Watermark", "tamper-evidence"]];
  const cw = 187, step = 201, cxs = 180, cy = 396;
  chips.forEach((c, i) => {
    const x = cxs + i * step;
    s += box(x, cy, cw, 36, { title: c[0], lines: [c[1]], color: COL.neutral, titleCls: "node" });
  });
  s += text(L + CW - 8, 372, "5 managed states", { cls: "tag", anchor: "end", fill: COL.comp.s });
  s += arrow(cx, 446, cx, 476);

  // Row 5 — Domain crates
  s += gut(520, "DOMAIN CRATES");
  const dom = [
    ["sv-core", "Secure Vault"], ["sv-platform", "File crypto services"], ["sv-stego", "Steganography"],
    ["sv-meta", "Metadata (ExifTool)"], ["sv-qr", "QR transfer"], ["sv-watermark", "Tamper-evidence"],
  ];
  const dw = 160, dstep = 174;
  dom.forEach((d, i) => { s += box(L + i * dstep, 480, dw, 80, { title: d[0], lines: [d[1]], color: COL.domain }); });
  s += arrow(cx, 560, cx, 590);

  // Row 6 — Shared crypto platform
  s += gut(633, "CRYPTO PLATFORM");
  s += box(L, 594, 332, 78, { title: "sv-crypto-traits", lines: ["backend-free crypto ABI", "secret types: Key32 · SecretBytes"], color: COL.plat });
  s += box(509, 594, 332, 78, { title: "sv-crypto (impl adapters)", lines: ["BLAKE3 · Argon2id · secretbox", "Ed25519-minisign · Shamir"], color: COL.crit, critical: true });
  s += box(858, 594, 332, 78, { title: "sv-types", lines: ["DTO + coded error 'island'", "(zero crypto deps)"], color: COL.plat });
  s += arrow(cx, 672, cx, 702);

  // Row 7 — Backends / bundled tools
  s += gut(747, "BACKENDS / TOOLS");
  const be = [
    ["libsodium", ["FFI · secretbox / Ed25519"], COL.crit, true],
    ["Shamir sss", ["vendored FFI (static C)"], COL.crit, true],
    ["age / age-keygen", ["subprocess · BLAKE3-pinned"], COL.crit, true],
    ["ExifTool", ["subprocess · pinned · optional"], COL.ext, false],
  ];
  const bw = 247, bstep = 261;
  be.forEach((b, i) => { s += box(L + i * bstep, 706, bw, 82, { title: b[0], lines: b[1], color: b[2], critical: b[3] }); });

  // Legend
  s += legend(40, 812, [
    { swatch: COL.ui, text: "Presentation (WebView)" },
    { swatch: COL.ipc, text: "IPC boundary" },
    { swatch: COL.comp, text: "Composition root" },
    { swatch: COL.domain, text: "Domain crate (module)" },
    { swatch: COL.plat, text: "Shared crypto platform" },
    { swatch: COL.crit, text: "Security-critical (keys / crypto / FFI)", critical: true },
    { swatch: COL.ext, text: "External bundled tool" },
    { line: true, text: "calls / depends-on (top → down)" },
  ], { });

  // right-side note
  s += `<rect x="360" y="812" width="840" height="${28 + 8 * 19}" rx="7" fill="#ffffff" stroke="${HAIR}"/>`;
  s += text(372, 831, "How to read", { cls: "zone", anchor: "start" });
  const notes = [
    "• A single offline desktop app: the WebView calls the Rust core only through the typed IPC surface;",
    "   no secret value crosses that boundary (the one documented residual is the passphrase string).",
    "• The composition root owns 5 managed states and exposes 38 #[tauri::command]s that dispatch to the",
    "   six domain crates.",
    "• Every domain crate reuses the shared platform; only sv-crypto, the FFI backends and the age",
    "   subprocess are security-critical (red).",
    "• sv-types has no crypto dependencies — a DTO structurally cannot carry a secret.",
    "• No network egress anywhere in the system.",
  ];
  let ny = 851;
  for (const n of notes) { s += text(372, ny, n, { cls: "sub", anchor: "start" }); ny += 19; }

  return doc(W, H, s, {
    title: "ARCH-01 · Overall System Architecture",
    subtitle: "User → Tauri WebView → IPC command surface → composition root → domain crates → shared crypto platform → bundled backends",
    footer: FOOT,
  });
}

// ===========================================================================
// ARCH-02 — Security trust boundaries
// ===========================================================================
function arch02() {
  const W = 1240, H = 1010, L = 70, R = 1170, CW = R - L;
  let s = "";

  // helper: full-width zone band with header + bullet lines
  function band(y, h, { tag, tagColor, title, lines, color, critical = false }) {
    const sCol = critical ? CRIT_S : color.s;
    let o = `<rect x="${L}" y="${y}" width="${CW}" height="${h}" rx="9" fill="${color.f}" stroke="${sCol}" stroke-width="${critical ? 2 : 1.4}"/>`;
    o += `<rect x="${L + 16}" y="${y + 14}" width="142" height="24" rx="5" fill="${sCol}"/>`;
    o += text(L + 16 + 71, y + 31, tag, { cls: "tag", fill: "#ffffff" });
    o += text(L + 174, y + 25, title, { cls: "nodeb", anchor: "start" });
    let ly = y + 47;
    for (const ln of lines) { o += text(L + 174, ly, ln, { cls: "sub", anchor: "start" }); ly += 14; }
    if (critical) o += `<circle cx="${R - 14}" cy="${y + 13}" r="4.5" fill="${CRIT_S}"/>`;
    return o;
  }
  // boundary divider with centered label + annotation
  function boundary(y, label, note) {
    let o = `<line x1="${L}" y1="${y}" x2="${R}" y2="${y}" stroke="${CRIT_S}" stroke-width="1.6" stroke-dasharray="9 5"/>`;
    const tw = label.length * 6.8 + 26;
    o += `<rect x="${(L + R) / 2 - tw / 2}" y="${y - 13}" width="${tw}" height="26" rx="6" fill="#ffffff" stroke="${CRIT_S}" stroke-width="1.3"/>`;
    o += text((L + R) / 2, y + 4, label, { cls: "zone", fill: CRIT_S });
    if (note) o += text(R, y + 22, note, { cls: "lbl", anchor: "end" });
    return o;
  }

  s += band(92, 58, { tag: "UNTRUSTED", color: COL.fs, title: "User input", lines: ["File paths, passphrases, images selected by the user — treated as untrusted input."] });

  s += band(176, 96, {
    tag: "SANDBOXED", color: COL.ui, title: "Frontend — Tauri WebView (static withGlobalTauri)",
    lines: [
      "CSP: default-src 'self'; no inline scripts.   Capability allowlist: core / dialog / opener only — no fs: / shell:.",
      "Renders all values via textContent (no HTML injection).   Password fields zeroed on navigation and after each task.",
    ],
  });

  s += boundary(300, "IPC TRUST BOUNDARY  (JSON)", null);
  s += text(L, 318, "Crosses the boundary: file paths + passphrase (zeroizing) — never secret bytes.", { cls: "sub", anchor: "start" });
  s += text(L, 332, "Documented residual: serde/JSON copies the passphrase into buffers it cannot zeroize (mitigate via OS disk/swap encryption; exclude these commands from arg logging).", { cls: "sub", anchor: "start" });

  s += band(348, 92, {
    tag: "TRUSTED", color: COL.comp, title: "Backend — Rust command surface (sv-app)",
    lines: [
      "38 commands · coded, oracle-safe ApiError (wrong-passphrase = wrong-share = Unauthorized).",
      "IpcPassphrase zeroizing · no secret in any DTO · size + decompression-bomb caps · atomic refuse-overwrite writes.",
    ],
  });
  s += arrow((L + R) / 2, 440, (L + R) / 2, 452);

  s += band(452, 100, {
    tag: "CRITICAL", color: COL.crit, critical: true, title: "Cryptographic services — shared platform + vault key hierarchy",
    lines: [
      "BLAKE3 · Argon2id · libsodium secretbox / Ed25519-minisign · Shamir.   Signature verified BEFORE the credential gate.",
      "Key32 / SecretBytes zeroize-on-drop · vault master key is RAM-only and never written to disk.",
    ],
  });

  s += boundary(580, "PROCESS BOUNDARY", "env_clear · BLAKE3 hash-pin · wall-clock timeout · fail-closed");

  s += band(610, 84, {
    tag: "EXTERNAL", color: COL.ext, title: "Bundled external tools — hardened subprocess",
    lines: [
      "age / age-keygen (file encryption) · ExifTool (metadata).   Spawned with env_clear, a pinned BLAKE3 hash,",
      "a wall-clock timeout, and -config '' for ExifTool (RCE vector closed).   Disabled tool ⇒ fail-closed.",
    ],
  });

  s += boundary(722, "I/O BOUNDARY", "atomic temp → fsync → rename · refuse-overwrite · path-stripped errors");

  s += band(752, 76, {
    tag: "STORAGE", color: COL.fs, title: "File system",
    lines: [".svault · .svenc / .svkey · .minisig · .svshare / .svss · QR PNG · images · keys — all under the user's own paths."],
  });

  // Legend
  s += legend(70, 858, [
    { swatch: COL.fs, text: "Untrusted input / storage" },
    { swatch: COL.ui, text: "Sandboxed WebView" },
    { swatch: COL.comp, text: "Trusted native backend" },
    { swatch: COL.crit, text: "Security-critical crypto", critical: true },
    { swatch: COL.ext, text: "External process (sandboxed)" },
    { line: true, dashed: true, color: CRIT_S, text: "trust / process / I-O boundary" },
  ], {});
  s += `<rect x="372" y="858" width="798" height="${28 + 6 * 19}" rx="7" fill="#ffffff" stroke="${HAIR}"/>`;
  s += text(384, 877, "Boundary controls (defence in depth)", { cls: "zone", anchor: "start" });
  const bl = [
    "1. WebView → backend: typed IPC only; no direct filesystem or shell access is granted to the page.",
    "2. Backend → crypto: secrets stay in zeroizing types; the vault signature is checked before any passphrase test,",
    "    so tampering is reported as Corrupted, never as an authentication oracle.",
    "3. Backend → tools: external binaries run as cleaned, hash-pinned, time-bounded subprocesses and fail closed.",
    "4. Anything → disk: writes are atomic and refuse to overwrite; error details are path-stripped.",
  ];
  let yy = 897;
  for (const b of bl) { s += text(384, yy, b, { cls: "sub", anchor: "start" }); yy += 19; }

  return doc(W, H, s, {
    title: "ARCH-02 · Security & Trust Boundaries",
    subtitle: "Trust zones from untrusted user input through the sandboxed WebView, the trusted native backend and crypto core, to hardened subprocesses and storage",
    footer: FOOT,
  });
}

// ===========================================================================
// ARCH-03 — Secure file lifecycle
// ===========================================================================
function arch03() {
  const W = 1500, H = 880;
  let s = "";

  // stage column headers
  const heads = [
    ["235", "200", "PROTECT / OPERATE"],
    ["505", "200", "STORE · HIDE · TRANSFER"],
    ["775", "200", "RECOVER"],
    ["1045", "200", "DECRYPT / OPEN"],
  ];
  heads.forEach(([x, w, t]) => { s += text(+x + +w / 2, 100, t, { cls: "zone", fill: SUB }); });
  s += text(125, 100, "INPUT", { cls: "zone", fill: SUB });
  s += text(1395, 100, "OUTPUT", { cls: "zone", fill: SUB });

  // shared input / output
  s += box(50, 300, 150, 150, { title: "Plaintext", lines: ["file or secret", "(user input)"], color: COL.neutral, titleCls: "nodeb" });
  s += box(1320, 300, 150, 150, { title: "Recovered", lines: ["plaintext file", "or secret"], color: COL.neutral, titleCls: "nodeb" });

  const SX = [235, 505, 775, 1045], SW = 200, BH = 74;

  // lanes: [yTop, color, [stage1,stage2,stage3,stage4]]
  const lanes = [
    [118, COL.domain, [
      ["Vault seal", ["Argon2id master · age payload", "minisign over binding root"]],
      [".svault container", ["CBOR header + age payload", "+ signature, on disk"]],
      ["Unlock", ["verify signature → derive key", "→ unwrap identity"]],
      ["Decrypt items", ["age payload → item bytes", "(extract to file)"]],
    ]],
    [240, COL.ui, [
      ["Encrypt file", ["Argon2id + secretbox", "(SVENC artifact)"]],
      ["Encrypted file", [".svenc on disk", "move / back up freely"]],
      ["— (same file)", ["no separate recovery step", "ciphertext is portable"]],
      ["Decrypt file", ["verify MAC → plaintext", "pre-auth cost ceilings"]],
    ]],
    [362, COL.plat, [
      ["Hide", ["seal (Argon2id+secretbox)", "+ embed LSB / JPEG-DCT"]],
      ["Carrier image", ["PNG / BMP / JPEG", "(visually unchanged)"]],
      ["Extract", ["read header → re-derive", "embedding schedule"]],
      ["Reveal payload", ["secretbox open", "(wrong key ⇒ AuthFailed)"]],
    ]],
    [500, COL.comp, [
      ["Split", ["Shamir k-of-n", "SVSH (vault key) / SVSS (DEK)"]],
      ["Shares", [".svshare / .svss", "distribute to holders"]],
      ["Recover", ["combine ≥ threshold", "(decode QR first if used)"]],
      ["Reconstruct", ["rebuild key/secret", "→ secretbox open / unlock"]],
    ]],
  ];

  lanes.forEach(([y, color, cells]) => {
    cells.forEach((c, i) => {
      if (c[0].startsWith("—")) s += box(SX[i], y, SW, BH, { title: c[0], lines: c[1], color: COL.neutral, titleCls: "node" });
      else s += box(SX[i], y, SW, BH, { title: c[0], lines: c[1], color, critical: false });
    });
    const yc = y + BH / 2;
    // input -> stage1
    s += arrow(200, 375, SX[0], yc, { width: 1.4 });
    // stage1->2->3->4
    s += arrow(SX[0] + SW, yc, SX[1], yc);
    s += arrow(SX[1] + SW, yc, SX[2], yc);
    s += arrow(SX[2] + SW, yc, SX[3], yc);
    // stage4 -> output
    s += arrow(SX[3] + SW, yc, 1320, 375, { width: 1.4 });
  });

  // QR optional sub-node attached to the Sharing lane (store column)
  const qy = 612;
  s += box(SX[1], qy, SW, 56, { title: "QR transfer  (optional)", lines: ["share strings → QR PNG (EC-H)", "scan elsewhere → decode (rqrr)"], color: COL.ext });
  // shares -> QR (down) and QR -> recover (up-right), both dashed/optional
  s += arrow(SX[1] + SW / 2, 500 + BH, SX[1] + SW / 2, qy, { dashed: true, label: "optional" });
  s += arrow(SX[1] + SW, qy + 28, SX[2], 500 + BH / 2, { dashed: true });

  // Legend
  s += legend(50, 700, [
    { swatch: COL.domain, text: "Vault path (sv-core)" },
    { swatch: COL.ui, text: "File encryption path (sv-platform)" },
    { swatch: COL.plat, text: "Steganography path (sv-stego)" },
    { swatch: COL.comp, text: "Secret-sharing path (sv-platform / sv-core)" },
    { swatch: COL.ext, text: "QR transfer (sv-qr) — carries shares" },
    { line: true, dashed: true, text: "optional / conditional step" },
  ], {});
  s += `<rect x="372" y="700" width="1078" height="${28 + 5 * 19}" rx="7" fill="#ffffff" stroke="${HAIR}"/>`;
  s += text(384, 719, "Notes", { cls: "zone", anchor: "start" });
  const n3 = [
    "• Four independent protection paths share the same input and produce the same recovered output; a user picks one (or composes them).",
    "• Two distinct encryption mechanisms: the Vault payload uses age; standalone file encryption uses Argon2id + secretbox (SVENC). They are not the same pipeline.",
    "• Secret sharing splits a key (the vault master key, or a freshly generated DEK that encrypts the payload) — never the raw passphrase.",
    "• QR transfer is a transport for share strings only; it sits between 'Shares' and 'Recover' and is optional.",
    "• Every recovery is fail-safe: a wrong key, wrong share set, or tampered carrier yields a coded error, not a partial/incorrect result.",
  ];
  let yy = 739;
  for (const n of n3) { s += text(384, yy, n, { cls: "sub", anchor: "start" }); yy += 19; }

  return doc(W, H, s, {
    title: "ARCH-03 · Secure File Lifecycle",
    subtitle: "End-to-end: file/secret → protect → store · hide · transfer → recover → decrypt, across the Vault, Steganography, Secret-Sharing and QR paths",
    footer: FOOT,
  });
}

// ===========================================================================
// ARCH-04 — Component dependency map
// ===========================================================================
function arch04() {
  const W = 1280, H = 1100;
  let s = "";
  const NW = 156, NH = 46;
  // node registry: id -> {cx, cy, title, sub, color, critical, w}
  const N = {};
  function node(id, cx, cy, title, sub, color, critical = false, w = NW) {
    N[id] = { cx, cy, w, h: NH };
    s += box(cx - w / 2, cy - NH / 2, w, NH, { title, lines: sub ? [sub] : [], color, critical, titleCls: "node" });
  }
  // edge from a (top) depends-on b (bottom): arrow a->b
  function dep(a, b, { dashed = false, color = HAIR } = {}) {
    const A = N[a], B = N[b];
    // connect bottom of A to top of B when A above B; else nearest edges
    let x1 = A.cx, y1 = A.cy + A.h / 2, x2 = B.cx, y2 = B.cy - B.h / 2;
    if (B.cy < A.cy) { y1 = A.cy - A.h / 2; y2 = B.cy + B.h / 2; }
    s += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="1.2"${dashed ? ' stroke-dasharray="5 4"' : ""} marker-end="url(#arrow)"/>`;
  }

  // Level F (top) — desktop
  node("desktop", 620, 150, "desktop", "Tauri shell (excluded)", COL.ui);
  // Level E — sv-app
  node("app", 620, 250, "sv-app (src-tauri)", "command surface · 38 cmds", COL.comp, false, 240);
  // Level D — domain crates
  node("core", 175, 380, "sv-core", "vault", COL.crit, true);
  node("plat", 360, 380, "sv-platform", "file services", COL.crit, true);
  node("stego", 545, 380, "sv-stego", "steganography", COL.domain);
  node("wm", 730, 380, "sv-watermark", "tamper-evidence", COL.domain);
  node("meta", 915, 380, "sv-meta", "metadata", COL.domain);
  node("qr", 1100, 380, "sv-qr", "QR codec", COL.domain);
  // Level C — sv-crypto
  node("crypto", 360, 520, "sv-crypto", "impl adapters", COL.crit, true, 180);
  // Level B — sv-age, sv-sys-sss
  node("age", 700, 540, "sv-age", "age subprocess", COL.crit, true);
  node("sss", 235, 640, "sv-sys-sss", "Shamir FFI", COL.crit, true);
  // Level A (bottom) — leaves
  node("traits", 360, 760, "sv-crypto-traits", "backend-free ABI", COL.plat, false, 190);
  node("sodium", 110, 760, "sv-sys-sodium", "libsodium FFI", COL.crit, true);
  node("types", 1000, 690, "sv-types", "DTO / error island", COL.plat, false, 190);

  // external tools (distinct, right column)
  function tool(id, cx, cy, title, sub) {
    N[id] = { cx, cy, w: 150, h: 44 };
    s += `<path d="M${cx - 75},${cy - 22} h150 v44 h-150 z" fill="${COL.ext.f}" stroke="${COL.ext.s}" stroke-width="1.4" stroke-dasharray="2 0"/>`;
    s += `<rect x="${cx - 75}" y="${cy - 22}" width="150" height="44" rx="2" fill="none" stroke="${COL.ext.s}" stroke-width="1.4"/>`;
    s += `<line x1="${cx - 75}" y1="${cy - 14}" x2="${cx + 75}" y2="${cy - 14}" stroke="${COL.ext.s}" stroke-width="0.9"/>`;
    s += text(cx, cy - 1, title, { cls: "node" });
    s += text(cx, cy + 13, sub, { cls: "sub" });
  }
  tool("agebin", 1140, 540, "age / age-keygen", "external binary");
  tool("exiftool", 1140, 440, "ExifTool", "external binary");

  // edges — exact manifest dependencies
  dep("sss", "traits");
  dep("age", "traits");
  dep("crypto", "traits"); dep("crypto", "sss"); dep("crypto", "sodium");
  dep("core", "traits"); dep("core", "types"); dep("core", "crypto", { dashed: true }); // dev-dep
  dep("plat", "traits"); dep("plat", "crypto"); dep("plat", "types");
  dep("stego", "traits"); dep("stego", "crypto"); dep("stego", "types");
  dep("wm", "traits"); dep("wm", "crypto"); dep("wm", "types");
  dep("meta", "types");
  dep("qr", "types");
  // sv-app -> domain crates + age  (direct deps on traits/crypto/types omitted for legibility — see note)
  ["core", "plat", "stego", "wm", "meta", "qr", "age"].forEach((d) => dep("app", d));
  // desktop -> app, meta, age (also sv-types, omitted)
  ["app", "meta", "age"].forEach((d) => dep("desktop", d));
  // external spawns (runtime, not a cargo dep)
  dep("age", "agebin", { dashed: true, color: COL.ext.s });
  dep("meta", "exiftool", { dashed: true, color: COL.ext.s });

  // Legend
  s += legend(40, 880, [
    { swatch: COL.ui, text: "Tauri shell (workspace-excluded)" },
    { swatch: COL.comp, text: "Composition root" },
    { swatch: COL.domain, text: "Domain crate" },
    { swatch: COL.plat, text: "Shared ABI / DTO (leaf)" },
    { swatch: COL.crit, text: "Security-critical component", critical: true },
    { swatch: COL.ext, text: "External binary (runtime spawn)" },
    { line: true, text: "cargo dependency (depends-on)" },
    { line: true, dashed: true, text: "dev-dependency / runtime spawn" },
  ], {});
  s += `<rect x="360" y="880" width="880" height="${28 + 8 * 19}" rx="7" fill="#ffffff" stroke="${HAIR}"/>`;
  s += text(372, 899, "Reading the graph", { cls: "zone", anchor: "start" });
  const n4 = [
    "• Edges are exact internal Cargo path-dependencies (verified from each crate's Cargo.toml). An arrow A → B means \"A depends on B\".",
    "• sv-crypto-traits is the dependency-light ABI root; sv-types is a leaf with zero crypto deps (so DTOs cannot hold secrets).",
    "• sv-core takes sv-crypto only as a dev-dependency (dashed) — the production vault is generic over the ABI and FFI-free.",
    "• For legibility, sv-app's direct edges to sv-crypto-traits / sv-crypto / sv-types and desktop's edge to sv-types are omitted",
    "    (they exist in the manifests). All other edges are drawn.",
    "• Security-critical = handles key material, performs cryptography, links C/FFI, or executes an external binary.",
    "• age / ExifTool edges are runtime subprocess spawns (hash-pinned), not compile-time dependencies.",
  ];
  let yy = 919;
  for (const n of n4) { s += text(372, yy, n, { cls: "sub", anchor: "start" }); yy += 19; }

  return doc(W, H, s, {
    title: "ARCH-04 · Component Dependency Map",
    subtitle: "Workspace crates and their exact internal dependencies, with security-critical components and external tool spawns highlighted",
    footer: FOOT,
  });
}

// ===========================================================================
// ARCH-05 — Deployment architecture
// ===========================================================================
function arch05() {
  const W = 1240, H = 880;
  let s = "";

  // OS outer zone
  s += zone(40, 92, 1160, 690, { label: "Operating System  (macOS · Windows · Linux)", stroke: COL.fs.s });
  s += text(1186, 110, "no network", { cls: "tag", anchor: "end", fill: COL.fs.s });

  // App bundle
  s += `<rect x="70" y="140" width="690" height="600" rx="9" fill="#fbfcfe" stroke="${COL.comp.s}" stroke-width="1.8"/>`;
  s += text(85, 165, "Secure Vault application bundle", { cls: "nodeb", anchor: "start" });
  s += text(85, 182, "productName: Secure Vault · id: org.secure-vault.desktop · v0.1.0 · bundle.targets: all", { cls: "sub", anchor: "start" });

  // runtime + frontend
  s += box(90, 200, 320, 74, { title: "Tauri 2 runtime", lines: ["Rust core (sv-app + crates)", "+ system WebView (WebKit/WebView2/WebKitGTK)"], color: COL.comp });
  s += box(430, 200, 310, 74, { title: "Frontend assets", lines: ["frontendDist: frontend/", "HTML · JS · CSS · icons (withGlobalTauri)"], color: COL.ui });
  s += arrow(410, 237, 430, 237, { });

  // resources
  s += `<rect x="90" y="296" width="650" height="280" rx="8" fill="#ffffff" stroke="${COL.ext.s}" stroke-width="1.5"/>`;
  s += text(104, 320, "Resources  (bundle.resources: \"binaries/**/*\")", { cls: "zone", anchor: "start", fill: COL.ext.s });
  s += box(108, 336, 290, 64, { title: "age", lines: ["BLAKE3-pinned · mandatory", "release fails to build if missing"], color: COL.crit, critical: true });
  s += box(420, 336, 290, 64, { title: "age-keygen", lines: ["BLAKE3-pinned · mandatory", "vault identity generation"], color: COL.crit, critical: true });
  s += box(108, 414, 290, 64, { title: "ExifTool distribution", lines: ["exiftool + lib/  (or windows .exe)", "self-staged + pinned · optional"], color: COL.ext });
  s += box(420, 414, 290, 64, { title: "pins embedded at build", lines: ["build.rs emit_pin → BLAKE3", "into the compiled binary"], color: COL.neutral });
  s += text(104, 502, "Runtime resolution:", { cls: "tag", anchor: "start", fill: COL.comp.s });
  s += text(104, 520, "• Resolved from the bundled app-resource directory — no env var, no repository path in a packaged build.", { cls: "sub", anchor: "start" });
  s += text(104, 538, "• The runtime re-verifies each binary's BLAKE3 pin before use; release refuses to run an unpinned mandatory binary.", { cls: "sub", anchor: "start" });
  s += text(104, 556, "• SV_*_BIN environment overrides are honoured in debug builds only.", { cls: "sub", anchor: "start" });

  // spawned subprocess
  s += box(90, 600, 650, 56, { title: "Spawned as hardened subprocess", lines: ["env_clear · wall-clock timeout · -config '' (ExifTool) · fail-closed when a tool is absent/unpinned"], color: COL.crit, critical: true });
  s += arrow(255, 478, 255, 600, { label: "resolve + verify pin" });
  s += arrow(565, 478, 420, 600, { });

  // OS / user side (right column)
  s += box(800, 200, 360, 120, { title: "User data on filesystem", lines: [".svault  ·  .svenc / .svkey  ·  .minisig", ".svshare / .svss  ·  QR .png  ·  images  ·  keys", "(under the user's own directories)"], color: COL.fs });
  s += box(800, 344, 360, 96, { title: "OS integration", lines: ["File dialogs (tauri-plugin-dialog)", "Open / reveal in folder (tauri-plugin-opener)", "CSPRNG: getrandom / libsodium"], color: COL.fs });
  s += box(800, 464, 360, 92, { title: "Process sandbox surface", lines: ["WebView ↔ Rust via IPC (no fs:/shell: to page)", "atomic temp → fsync → rename writes", "refuse-overwrite · path-stripped errors"], color: COL.comp });

  // arrows app <-> user files / OS
  s += arrow(740, 252, 800, 252, { label: "IPC results" });
  s += arrow(465, 656, 800, 410, { label: "read / atomic write", dashed: false });
  s += arrow(740, 510, 800, 510, {});

  // note on packaging out of scope
  s += `<rect x="800" y="600" width="360" height="140" rx="8" fill="#fff8f8" stroke="${COL.crit.s}" stroke-width="1.2"/>`;
  s += text(818, 622, "Out of scope (internal use)", { cls: "zone", anchor: "start", fill: COL.crit.s });
  s += text(818, 644, "• Code signing / notarization (hardening item H5)", { cls: "sub", anchor: "start" });
  s += text(818, 662, "• Per-OS signed installer for public distribution", { cls: "sub", anchor: "start" });
  s += text(818, 680, "Per-OS bundle internals (.app / .msi / AppImage)", { cls: "sub", anchor: "start" });
  s += text(818, 698, "differ; the logical structure shown is OS-agnostic.", { cls: "sub", anchor: "start" });
  s += text(818, 720, "Bundling itself (active, targets: all) is configured.", { cls: "sub", anchor: "start" });

  // Legend
  s += legend(40, 800, [
    { swatch: COL.comp, text: "Application runtime / native" },
    { swatch: COL.ui, text: "Frontend assets" },
    { swatch: COL.ext, text: "Bundled resources / external tool" },
    { swatch: COL.crit, text: "Security-critical (pinned binary)", critical: true },
    { swatch: COL.fs, text: "OS / user filesystem" },
  ], { colW: 300 });
  return doc(W, H, s, {
    title: "ARCH-05 · Deployment Architecture",
    subtitle: "Runtime deployment: application bundle, bundled+pinned resources, hardened subprocess execution, and OS / user-filesystem interaction",
    footer: FOOT,
  });
}

// ---- emit ------------------------------------------------------------------
const files = {
  "ARCH-01-overall-system-architecture.svg": arch01(),
  "ARCH-02-security-trust-boundaries.svg": arch02(),
  "ARCH-03-secure-file-lifecycle.svg": arch03(),
  "ARCH-04-component-dependency-map.svg": arch04(),
  "ARCH-05-deployment-architecture.svg": arch05(),
};
for (const [name, body] of Object.entries(files)) {
  writeFileSync(join(OUT, name), body, "utf8");
  console.log("wrote", name, body.length, "bytes");
}
