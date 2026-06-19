#!/usr/bin/env python3
"""Secure Vault — Draw.io architecture package generator.

Deterministic, dependency-free (Python 3 stdlib only). Emits five native, editable
``ARCH-*.drawio`` files next to this script. Every shape is a real ``mxCell`` (vertex /
edge / swimlane / container) so the diagrams open and edit natively in diagrams.net /
the Draw.io VS Code extension — they are NOT exported SVG/PNG.

The .drawio files are the deliverable; this script reproduces them so typography, palette
and spacing stay consistent and the figures remain editable at source (mirroring the sibling
``docs/11-svg-architecture/generate-svgs.mjs`` convention).

Source of truth: the architecture documents under ``docs/architecture/`` (01..10). The
``docs/11-svg-architecture/*.svg`` figures were used as a visual-layout reference only; where
the prose and the SVGs differed, the architecture documents won. See README.md for the
per-file source mapping. Nothing here is invented.

Run:  python3 generate-drawio.py
"""

from pathlib import Path

OUT = Path(__file__).resolve().parent

# ---- palette (mirrors docs/11-svg-architecture/generate-svgs.mjs) ------------
INK = "#1c2330"
SUB = "#5b6675"
LINE = "#566072"
HAIR = "#aab2bf"
COL = {
    "ui":      {"f": "#e9f1fd", "s": "#2f6ab0"},  # presentation / webview — blue
    "ipc":     {"f": "#fdf3e2", "s": "#b9791b"},  # IPC boundary — amber
    "comp":    {"f": "#eef0f6", "s": "#46506a"},  # composition root — indigo-gray
    "domain":  {"f": "#eaf3ee", "s": "#3c7d4f"},  # domain crates — green
    "plat":    {"f": "#e7f1f2", "s": "#2f7b86"},  # shared platform (ABI/types) — teal
    "crit":    {"f": "#fbe9e9", "s": "#b0413f"},  # security-critical — red
    "ext":     {"f": "#efeaf8", "s": "#6a4f9c"},  # external tools — purple
    "fs":      {"f": "#eceff3", "s": "#5d6b7c"},  # filesystem / OS — slate
    "neutral": {"f": "#f4f6f9", "s": "#5b6675"},
}
CRIT_S = COL["crit"]["s"]


def esc(s):
    """XML-escape a label/string for placement inside an attribute value.

    Labels are composed as raw HTML (``<b>``/``<br>``/``<span>``) and escaped once here.
    With ``html=1`` Draw.io re-parses the un-escaped value as HTML, so ``<b>`` renders bold.
    Use the unicode forms (≤ ≥ → ‖) in text, never literal ``<``/``>``.
    """
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def boxlabel(title, lines=(), tsize=13, ssize=10.5, tcolor=None):
    parts = []
    tc = f';color:{tcolor}' if tcolor else ''
    parts.append(f'<b style="font-size:{tsize}px{tc}">{title}</b>')
    for ln in lines:
        parts.append(f'<span style="font-size:{ssize}px;color:#45505f">{ln}</span>')
    return "<br>".join(parts)


# ---- box / container / edge styles ------------------------------------------
def box_style(key, critical=False, dashed=False):
    c = COL[key]
    stroke = CRIT_S if critical else c["s"]
    sw = 2 if critical else 1.3
    st = (f"rounded=1;whiteSpace=wrap;html=1;arcSize=8;fillColor={c['f']};"
          f"strokeColor={stroke};strokeWidth={sw};fontColor={INK};"
          f"verticalAlign=middle;align=center;spacingLeft=4;spacingRight=4;")
    if dashed:
        st += "dashed=1;dashPattern=6 4;"
    return st


EDGE = (f"edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;"
        f"strokeColor={LINE};strokeWidth=1.4;jettySize=auto;")
EDGE_DASH = EDGE + "dashed=1;dashPattern=6 4;"


class Diagram:
    def __init__(self, pid, name, w, h):
        self.pid = pid
        self.name = name
        self.w = w
        self.h = h
        self.cells = []
        self.n = 0
        self.origin = {"0": (0, 0), "1": (0, 0)}

    def _id(self):
        self.n += 1
        return f"{self.pid}-{self.n}"

    def vertex(self, x, y, w, h, label, style, parent="1", cid=None):
        cid = cid or self._id()
        ox, oy = self.origin.get(parent, (0, 0))
        rx, ry = x - ox, y - oy
        self.origin[cid] = (x, y)
        self.cells.append(
            f'<mxCell id="{cid}" value="{esc(label)}" style="{style}" vertex="1" parent="{parent}">'
            f'<mxGeometry x="{rx:g}" y="{ry:g}" width="{w:g}" height="{h:g}" as="geometry"/></mxCell>')
        return cid

    def text(self, x, y, w, h, label, align="center", size=11, bold=False, color=INK,
             valign="middle", parent="1"):
        fs = ";fontStyle=1" if bold else ""
        style = (f"text;html=1;strokeColor=none;fillColor=none;align={align};"
                 f"verticalAlign={valign};fontColor={color};fontSize={size}{fs};whiteSpace=wrap;")
        return self.vertex(x, y, w, h, label, style, parent=parent)

    def edge(self, source, target, label="", style=EDGE, parent="1", extra="", points=None):
        cid = self._id()
        pts = ""
        if points:
            inner = "".join(f'<mxPoint x="{px:g}" y="{py:g}"/>' for px, py in points)
            pts = f'<Array as="points">{inner}</Array>'
        self.cells.append(
            f'<mxCell id="{cid}" value="{esc(label)}" style="{style}{extra}" edge="1" '
            f'parent="{parent}" source="{source}" target="{target}">'
            f'<mxGeometry relative="1" as="geometry">{pts}</mxGeometry></mxCell>')
        return cid

    def seg(self, x1, y1, x2, y2, style, parent="1", label=""):
        cid = self._id()
        self.cells.append(
            f'<mxCell id="{cid}" value="{esc(label)}" style="{style}" edge="1" parent="{parent}">'
            f'<mxGeometry relative="1" as="geometry">'
            f'<mxPoint x="{x1:g}" y="{y1:g}" as="sourcePoint"/>'
            f'<mxPoint x="{x2:g}" y="{y2:g}" as="targetPoint"/>'
            f'</mxGeometry></mxCell>')
        return cid

    def header(self, title, subtitle):
        self.text(40, 24, self.w - 80, 28, f"<b>{title}</b>", align="left", size=21)
        self.text(40, 54, self.w - 80, 18, subtitle, align="left", size=12, color=SUB)
        self.seg(40, 80, self.w - 40, 80,
                 f"endArrow=none;html=1;strokeColor={HAIR};strokeWidth=1;")
        self.seg(40, self.h - 38, self.w - 40, self.h - 38,
                 f"endArrow=none;html=1;strokeColor={HAIR};strokeWidth=1;")
        self.text(40, self.h - 32, self.w - 80, 16, FOOT, align="left", size=10, color=SUB)

    def xml(self):
        body = "\n        ".join(self.cells)
        return (
            f'  <diagram id="{self.pid}" name="{esc(self.name)}">\n'
            f'    <mxGraphModel dx="1100" dy="760" grid="1" gridSize="10" guides="1" '
            f'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
            f'pageWidth="{self.w}" pageHeight="{self.h}" math="0" shadow="0">\n'
            f'      <root>\n'
            f'        <mxCell id="0" />\n'
            f'        <mxCell id="1" parent="0" />\n'
            f'        {body}\n'
            f'      </root>\n'
            f'    </mxGraphModel>\n'
            f'  </diagram>\n')


FOOT = ("Secure Vault — Security & Privacy Toolkit · v0.1.0   |   "
        "Source of truth: docs/architecture/ (01..10). SVGs used as visual reference only. "
        "See 12-drawio-architecture/README.md")


def swimlane(d, x, y, w, h, title, accent, parent="1", startsize=112):
    c = COL[accent]
    style = (f"swimlane;html=1;horizontal=0;startSize={startsize};rounded=1;arcSize=3;"
             f"fillColor=none;swimlaneFillColor=none;strokeColor={c['s']};strokeWidth=1.3;"
             f"dashed=1;dashPattern=4 4;fontColor={c['s']};fontStyle=1;fontSize=12;"
             f"verticalAlign=middle;align=center;collapsible=0;")
    return d.vertex(x, y, w, h, title, style, parent=parent)


def container(d, x, y, w, h, title, accent, parent="1", fill="none", dashed=True):
    c = COL[accent]
    style = (f"rounded=1;html=1;arcSize=3;container=1;collapsible=0;"
             f"fillColor={fill};strokeColor={c['s']};strokeWidth=1.6;"
             f"verticalAlign=top;align=left;spacingLeft=12;spacingTop=6;"
             f"fontColor={c['s']};fontStyle=1;fontSize=12.5;")
    if dashed:
        style += "dashed=1;dashPattern=7 5;"
    return d.vertex(x, y, w, h, title, style, parent=parent)


def legend(d, x, y, items, title="Legend", w=300, parent="1"):
    rowh = 19
    h = 34 + len(items) * rowh
    d.vertex(x, y, w, h, f"<b>{title}</b>",
             f"rounded=1;html=1;fillColor=#ffffff;strokeColor={HAIR};strokeWidth=1;"
             f"verticalAlign=top;align=left;spacingLeft=10;spacingTop=6;fontSize=12;",
             parent=parent)
    ry = y + 40
    for it in items:
        if "swatch" in it:
            c = COL[it["swatch"]]
            stroke = CRIT_S if it.get("crit") else c["s"]
            sw = 2 if it.get("crit") else 1.2
            d.vertex(x + 12, ry - 9, 18, 13, "",
                     f"rounded=0;html=1;fillColor={c['f']};strokeColor={stroke};strokeWidth={sw};",
                     parent=parent)
            if it.get("crit"):
                d.vertex(x + 12 + 18 - 7, ry - 8, 5, 5, "",
                         f"ellipse;html=1;fillColor={CRIT_S};strokeColor=none;", parent=parent)
        elif it.get("line"):
            col = it.get("color", LINE)
            dash = "dashed=1;dashPattern=5 3;" if it.get("dashed") else ""
            d.seg(x + 12, ry - 3, x + 30, ry - 3,
                  f"endArrow=block;endFill=1;html=1;strokeColor={col};strokeWidth=1.7;{dash}",
                  parent=parent)
        d.text(x + 38, ry - 11, w - 48, 16, it["text"], align="left", size=11, parent=parent)
        ry += rowh


def notebox(d, x, y, w, title, lines, parent="1", accent=None, fill="#ffffff"):
    h = 34 + len(lines) * 19
    stroke = COL[accent]["s"] if accent else HAIR
    tcolor = COL[accent]["s"] if accent else INK
    d.vertex(x, y, w, h, f'<b style="color:{tcolor}">{title}</b>',
             f"rounded=1;html=1;fillColor={fill};strokeColor={stroke};strokeWidth=1;"
             f"verticalAlign=top;align=left;spacingLeft=12;spacingTop=6;fontSize=12;",
             parent=parent)
    ry = y + 40
    for ln in lines:
        d.text(x + 12, ry - 11, w - 24, 16, ln, align="left", size=10.5, color="#45505f", parent=parent)
        ry += 19
    return h


VBONE = EDGE + "exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;"


# =============================================================================
# ARCH-01 — Overall System Architecture
# =============================================================================
def arch01():
    W, H = 1240, 1024
    d = Diagram("arch01", "ARCH-01 Overall System Architecture", W, H)
    d.header("ARCH-01 · Overall System Architecture",
             "User → Tauri WebView → IPC command surface → composition root (5 managed states) "
             "→ six domain crates → shared crypto platform → bundled backends")

    BX, BW, SS = 40, 1160, 112
    IL = BX + SS + 8          # inner content left
    IR = BX + BW - 8          # inner content right
    cxm = (IL + IR) / 2

    # Row 1 — USER
    l1 = swimlane(d, BX, 92, BW, 60, "USER", "neutral", startsize=SS)
    user = d.vertex(cxm - 135, 102, 270, 40,
                    boxlabel("User", ["local · single host · offline"]),
                    box_style("neutral"), parent=l1)

    # Row 2 — PRESENTATION
    l2 = swimlane(d, BX, 168, BW, 80, "PRESENTATION", "ui", startsize=SS)
    webview = d.vertex(IL, 180, IR - IL, 56,
                       boxlabel("Tauri 2 WebView — static frontend (withGlobalTauri)",
                                ["index.html · main.js · i18n.js · styles.css",
                                 "22 screen sections (20 routable) · vi/en i18n · CSP: no inline scripts"]),
                       box_style("ui"), parent=l2)

    # Row 3 — IPC BOUNDARY
    l3 = swimlane(d, BX, 264, BW, 64, "IPC BOUNDARY", "ipc", startsize=SS)
    ipc = d.vertex(IL, 274, IR - IL, 44,
                   boxlabel("IPC — Tauri invoke · 38 commands · coded oracle-safe ApiError",
                            ["IpcPassphrase (zeroizing) · file paths cross the boundary, never secret bytes"]),
                   box_style("ipc"), parent=l3)

    # Row 4 — COMPOSITION (root box + 5 managed-state chips)
    l4 = swimlane(d, BX, 344, BW, 120, "COMPOSITION", "comp", startsize=SS)
    comp = d.vertex(IL, 356, IR - IL, 100,
                    boxlabel("sv-app composition root  (desktop/src/lib.rs + src-tauri)  ·  5 managed states"),
                    box_style("comp").replace("verticalAlign=middle", "verticalAlign=top") + "spacingTop=6;",
                    parent=l4)
    chips = [("Backend", "vault"), ("Platform", "crypto / share / QR"),
             ("Stego", "conceal"), ("Meta", "metadata"), ("Watermark", "tamper-evidence")]
    chip_ids = {}
    cw, step = 186, 203
    cstart = IL + 12
    for i, (t, sub) in enumerate(chips):
        cx = cstart + i * step
        chip_ids[t] = d.vertex(cx, 398, cw, 46, boxlabel(t, [sub], tsize=12, ssize=10),
                               box_style("neutral"), parent=comp)

    # Row 5 — DOMAIN CRATES
    l5 = swimlane(d, BX, 480, BW, 92, "DOMAIN CRATES", "domain", startsize=SS)
    dom = [("core", "sv-core", "Secure Vault"), ("plat", "sv-platform", "File crypto services"),
           ("stego", "sv-stego", "Steganography"), ("meta", "sv-meta", "Metadata (ExifTool)"),
           ("qr", "sv-qr", "QR transfer"), ("wm", "sv-watermark", "Tamper-evidence")]
    dom_ids = {}
    dw, dstep = 158, 174.8
    for i, (k, t, sub) in enumerate(dom):
        dom_ids[k] = d.vertex(IL + i * dstep, 492, dw, 72, boxlabel(t, [sub]),
                              box_style("domain"), parent=l5)

    # Row 6 — CRYPTO PLATFORM
    l6 = swimlane(d, BX, 588, BW, 92, "CRYPTO PLATFORM", "plat", startsize=SS)
    traits = d.vertex(IL, 600, 332, 72,
                      boxlabel("sv-crypto-traits", ["backend-free crypto ABI", "secret types: Key32 · SecretBytes"]),
                      box_style("plat"), parent=l6)
    crypto = d.vertex(IL + 350, 600, 332, 72,
                      boxlabel("sv-crypto (impl adapters)", ["BLAKE3 · Argon2id · secretbox", "Ed25519-minisign · Shamir"]),
                      box_style("crit", critical=True), parent=l6)
    types = d.vertex(IL + 700, 600, 332, 72,
                     boxlabel("sv-types", ["DTO + coded error 'island'", "(zero crypto deps)"]),
                     box_style("plat"), parent=l6)

    # Row 7 — BACKENDS / TOOLS
    l7 = swimlane(d, BX, 696, BW, 96, "BACKENDS / TOOLS", "ext", startsize=SS)
    sodium = d.vertex(IL, 708, 246, 76, boxlabel("libsodium", ["FFI · secretbox / Ed25519"]),
                      box_style("crit", critical=True), parent=l7)
    shamir = d.vertex(IL + 262, 708, 246, 76, boxlabel("Shamir sss", ["vendored FFI (static C)"]),
                      box_style("crit", critical=True), parent=l7)
    agebin = d.vertex(IL + 524, 708, 246, 76, boxlabel("age / age-keygen", ["subprocess · BLAKE3-pinned"]),
                      box_style("crit", critical=True), parent=l7)
    exif = d.vertex(IL + 786, 708, 246, 76, boxlabel("ExifTool", ["subprocess · pinned · optional"]),
                    box_style("ext"), parent=l7)

    # backbone
    for a, b in [(user, webview), (webview, ipc), (ipc, comp)]:
        d.edge(a, b, style=VBONE)
    # managed state → domain crate(s)
    d.edge(chip_ids["Backend"], dom_ids["core"])
    d.edge(chip_ids["Platform"], dom_ids["plat"])
    d.edge(chip_ids["Platform"], dom_ids["qr"])
    d.edge(chip_ids["Stego"], dom_ids["stego"])
    d.edge(chip_ids["Meta"], dom_ids["meta"])
    d.edge(chip_ids["Watermark"], dom_ids["wm"])
    # domain crate → shared platform (exact)
    d.edge(dom_ids["core"], traits)
    d.edge(dom_ids["plat"], crypto)
    d.edge(dom_ids["stego"], crypto)
    d.edge(dom_ids["wm"], crypto)
    d.edge(dom_ids["meta"], types)
    d.edge(dom_ids["qr"], types)
    d.edge(crypto, traits)
    # platform → backends
    d.edge(crypto, sodium)
    d.edge(crypto, shamir)
    # composition-wired / runtime spawns (dashed)
    d.edge(dom_ids["core"], agebin, "age payload (composition-wired)", style=EDGE_DASH)
    d.edge(dom_ids["meta"], exif, "runtime spawn", style=EDGE_DASH)

    legend(d, 40, 812, [
        {"swatch": "ui", "text": "Presentation (WebView)"},
        {"swatch": "ipc", "text": "IPC boundary"},
        {"swatch": "comp", "text": "Composition root"},
        {"swatch": "domain", "text": "Domain crate (module)"},
        {"swatch": "plat", "text": "Shared crypto platform"},
        {"swatch": "crit", "crit": True, "text": "Security-critical (keys / crypto / FFI)"},
        {"swatch": "ext", "text": "External bundled tool"},
        {"line": True, "text": "calls / depends-on"},
        {"line": True, "dashed": True, "text": "composition-wired / runtime spawn"},
    ], w=300)

    notebox(d, 360, 812, 840, "How to read", [
        "• A single offline desktop app: the WebView calls the Rust core only through the typed IPC surface;",
        "   no secret value crosses that boundary (the one documented residual is the passphrase string).",
        "• The composition root owns 5 managed states and exposes 38 #[tauri::command]s dispatching to six domain crates.",
        "• Every domain crate reuses the shared platform; only sv-crypto, the FFI backends and the age subprocess are critical.",
        "• sv-types has no crypto dependencies — a DTO structurally cannot carry a secret.",
        "• Vault payload encryption uses age; the vault is not yet a consumer of sv-platform. No network egress anywhere.",
    ])
    return d


# =============================================================================
# ARCH-02 — Security & Trust Boundaries
# =============================================================================
def arch02():
    W, H = 1240, 1052
    d = Diagram("arch02", "ARCH-02 Security & Trust Boundaries", W, H)
    d.header("ARCH-02 · Security & Trust Boundaries",
             "Trust zones from untrusted user input through the sandboxed WebView, the trusted "
             "native backend and crypto core, to hardened subprocesses and storage")

    L, R = 70, 1170
    CW = R - L

    def band(y, h, tag, title, lines, accent, critical=False):
        c = COL[accent]
        ids = d.vertex(L, y, CW, h, "", box_style(accent, critical=critical), parent="1")
        # tag chip (left)
        stroke = CRIT_S if critical else c["s"]
        d.vertex(L + 14, y + 13, 130, 24, f'<b style="color:#ffffff">{tag}</b>',
                 f"rounded=1;arcSize=20;html=1;fillColor={stroke};strokeColor=none;"
                 f"fontColor=#ffffff;fontSize=10.5;fontStyle=1;verticalAlign=middle;align=center;",
                 parent="1")
        d.text(L + 158, y + 12, CW - 174, 18, f"<b>{title}</b>", align="left", size=13.5, parent="1")
        ly = y + 36
        for ln in lines:
            d.text(L + 158, ly, CW - 174, 15, ln, align="left", size=10.5, color="#45505f", parent="1")
            ly += 14.5
        if critical:
            d.vertex(R - 16, y + 9, 7, 7, "", f"ellipse;html=1;fillColor={CRIT_S};strokeColor=none;", parent="1")
        return ids

    def boundary(y, label, note=None):
        d.seg(L, y, R, y, f"endArrow=none;html=1;strokeColor={CRIT_S};strokeWidth=1.6;dashed=1;dashPattern=9 5;")
        tw = len(label) * 7 + 28
        d.vertex((L + R) / 2 - tw / 2, y - 13, tw, 26, f'<b style="color:{CRIT_S}">{label}</b>',
                 f"rounded=1;arcSize=20;html=1;fillColor=#ffffff;strokeColor={CRIT_S};strokeWidth=1.3;"
                 f"fontColor={CRIT_S};fontSize=12;fontStyle=1;verticalAlign=middle;align=center;")
        if note:
            d.text(R - 470, y + 8, 470, 16, note, align="right", size=10, color=SUB)

    band(92, 58, "UNTRUSTED", "User input",
         ["File paths, passphrases, images selected by the user — treated as untrusted input."], "fs")

    band(176, 96, "SANDBOXED", "Frontend — Tauri WebView (static withGlobalTauri)",
         ["CSP: default-src 'self'; no inline scripts.   Capability allowlist: core / dialog / opener only — no fs: / shell:.",
          "Renders all values via textContent (no HTML injection).   Password fields zeroed on navigation and after each task."],
         "ui")

    boundary(300, "IPC TRUST BOUNDARY  (JSON)")
    d.text(L, 308, CW, 14, "Crosses the boundary: file paths + passphrase (zeroizing) — never secret bytes.",
           align="left", size=10.5, color="#45505f")
    d.text(L, 322, CW, 14,
           "Documented residual: serde/JSON copies the passphrase into buffers it cannot zeroize "
           "(mitigate via OS disk/swap encryption; exclude these commands from arg logging).",
           align="left", size=10.5, color="#45505f")

    b_trusted = band(348, 92, "TRUSTED", "Backend — Rust command surface (sv-app)",
                     ["38 commands · coded, oracle-safe ApiError (wrong-passphrase = wrong-share = Unauthorized).",
                      "IpcPassphrase zeroizing · no secret in any DTO · size + decompression-bomb caps · atomic refuse-overwrite writes."],
                     "comp")

    b_crit = band(452, 100, "CRITICAL", "Cryptographic services — shared platform + vault key hierarchy",
                  ["BLAKE3 · Argon2id · libsodium secretbox / Ed25519-minisign · Shamir.   Signature verified BEFORE the credential gate.",
                   "Key32 / SecretBytes zeroize-on-drop · vault master key is RAM-only and never written to disk."],
                  "crit", critical=True)
    d.edge(b_trusted, b_crit, style=VBONE)

    boundary(580, "PROCESS BOUNDARY", "env_clear · BLAKE3 hash-pin · wall-clock timeout · fail-closed")

    band(610, 84, "EXTERNAL", "Bundled external tools — hardened subprocess",
         ["age / age-keygen (file encryption) · ExifTool (metadata).   Spawned with env_clear, a pinned BLAKE3 hash,",
          "a wall-clock timeout, and -config '' for ExifTool (RCE vector closed).   Disabled tool ⇒ fail-closed."],
         "ext")

    boundary(722, "I/O BOUNDARY", "atomic temp → fsync → rename · refuse-overwrite · path-stripped errors")

    band(752, 70, "STORAGE", "File system",
         [".svault · .svenc / .svkey · .minisig · .svshare / .svss · QR PNG · images · keys — all under the user's own paths."],
         "fs")

    legend(d, 70, 858, [
        {"swatch": "fs", "text": "Untrusted input / storage"},
        {"swatch": "ui", "text": "Sandboxed WebView"},
        {"swatch": "comp", "text": "Trusted native backend"},
        {"swatch": "crit", "crit": True, "text": "Security-critical crypto"},
        {"swatch": "ext", "text": "External process (sandboxed)"},
        {"line": True, "dashed": True, "color": CRIT_S, "text": "trust / process / I-O boundary"},
    ], w=290)

    notebox(d, 372, 858, 798, "Boundary controls (defence in depth)", [
        "1. WebView → backend: typed IPC only; no direct filesystem or shell access is granted to the page.",
        "2. Backend → crypto: secrets stay in zeroizing types; the vault signature is checked before any passphrase test,",
        "    so tampering is reported as Corrupted, never as an authentication oracle.",
        "3. Backend → tools: external binaries run as cleaned, hash-pinned, time-bounded subprocesses and fail closed.",
        "4. Anything → disk: writes are atomic and refuse to overwrite; error details are path-stripped.",
    ])
    return d


# =============================================================================
# ARCH-03 — Secure File Lifecycle
# =============================================================================
def arch03():
    W, H = 1500, 902
    d = Diagram("arch03", "ARCH-03 Secure File Lifecycle", W, H)
    d.header("ARCH-03 · Secure File Lifecycle",
             "End-to-end: file/secret → protect → store · hide · transfer → recover → decrypt, "
             "across the Vault, File-encryption, Steganography and Secret-Sharing paths")

    SX = [300, 560, 820, 1080]
    SW, BH = 210, 74
    BX, BW, SS = 150, 1180, 120

    # column headers
    heads = [(85, "INPUT"), ((SX[0] + SW / 2), "PROTECT / OPERATE"),
             ((SX[1] + SW / 2), "STORE · HIDE · TRANSFER"), ((SX[2] + SW / 2), "RECOVER"),
             ((SX[3] + SW / 2), "DECRYPT / OPEN"), (1395, "OUTPUT")]
    for cx, t in heads:
        d.text(cx - 110, 92, 220, 16, f"<b>{t}</b>", align="center", size=11.5, color=SUB)

    # shared input / output
    inp = d.vertex(30, 279, 110, 150, boxlabel("Plaintext", ["file or secret", "(user input)"]),
                   box_style("neutral"))
    outp = d.vertex(1350, 279, 110, 150, boxlabel("Recovered", ["plaintext file", "or secret"]),
                    box_style("neutral"))

    lanes = [
        ("Vault path  (sv-core)", "domain", [
            ("Vault seal", ["Argon2id master · age payload", "minisign over binding root"]),
            (".svault container", ["CBOR header + age payload", "+ signature, on disk"]),
            ("Unlock", ["verify signature → derive key", "→ unwrap identity"]),
            ("Decrypt items", ["age payload → item bytes", "(extract to file)"]),
        ]),
        ("File encryption  (sv-platform)", "ui", [
            ("Encrypt file", ["Argon2id + secretbox", "(SVENC artifact)"]),
            ("Encrypted file", [".svenc on disk", "move / back up freely"]),
            ("— same file —", ["no separate recovery step", "ciphertext is portable"]),
            ("Decrypt file", ["verify MAC → plaintext", "pre-auth cost ceilings"]),
        ]),
        ("Steganography  (sv-stego)", "plat", [
            ("Hide", ["seal (Argon2id+secretbox)", "+ embed LSB / JPEG-DCT"]),
            ("Carrier image", ["PNG / BMP / JPEG", "(visually unchanged)"]),
            ("Extract", ["read header → re-derive", "embedding schedule"]),
            ("Reveal payload", ["secretbox open", "(wrong key ⇒ AuthFailed)"]),
        ]),
        ("Secret sharing  (sv-platform / sv-core)", "comp", [
            ("Split", ["Shamir k-of-n", "SVSH (vault key) / SVSS (DEK)"]),
            ("Shares", [".svshare / .svss", "distribute to holders"]),
            ("Recover", ["combine ≥ threshold", "(decode QR first if used)"]),
            ("Reconstruct", ["rebuild key/secret", "→ secretbox open / unlock"]),
        ]),
    ]

    lane_y = [110, 236, 362, 488]
    LH = 110
    share_stage = {}
    for li, (title, accent, cells) in enumerate(lanes):
        y = lane_y[li]
        ln = swimlane(d, BX, y, BW, LH, title, accent, startsize=SS)
        cell_ids = []
        for i, (t, sub) in enumerate(cells):
            key = "neutral" if t.startswith("—") else accent
            cid = d.vertex(SX[i], y + (LH - BH) / 2, SW, BH, boxlabel(t, sub),
                           box_style(key), parent=ln)
            cell_ids.append(cid)
        # arrows
        d.edge(inp, cell_ids[0])
        d.edge(cell_ids[0], cell_ids[1])
        d.edge(cell_ids[1], cell_ids[2])
        d.edge(cell_ids[2], cell_ids[3])
        d.edge(cell_ids[3], outp)
        if accent == "comp":
            share_stage = {"shares": cell_ids[1], "recover": cell_ids[2]}

    # QR optional node (between Shares and Recover on the sharing lane)
    qy = 624
    qr = d.vertex(SX[1], qy, SW, 56,
                  boxlabel("QR transfer  (optional)", ["share strings → QR PNG (EC-H)", "scan elsewhere → decode (rqrr)"]),
                  box_style("ext"))
    d.edge(share_stage["shares"], qr, "optional", style=EDGE_DASH)
    d.edge(qr, share_stage["recover"], style=EDGE_DASH)

    legend(d, 40, 706, [
        {"swatch": "domain", "text": "Vault path (sv-core)"},
        {"swatch": "ui", "text": "File encryption path (sv-platform)"},
        {"swatch": "plat", "text": "Steganography path (sv-stego)"},
        {"swatch": "comp", "text": "Secret-sharing path (sv-platform / sv-core)"},
        {"swatch": "ext", "text": "QR transfer (sv-qr) — carries shares"},
        {"line": True, "dashed": True, "text": "optional / conditional step"},
    ], w=320)

    notebox(d, 380, 706, 1080, "Notes", [
        "• Four independent protection paths share the same input and produce the same recovered output; a user picks one (or composes them).",
        "• Two distinct encryption mechanisms: the Vault payload uses age; standalone file encryption uses Argon2id + secretbox (SVENC).",
        "• Secret sharing splits a key (the vault master key, or a freshly generated DEK that encrypts the payload) — never the raw passphrase.",
        "• QR transfer is a transport for share strings only; it sits between 'Shares' and 'Recover' and is optional.",
        "• Every recovery is fail-safe: a wrong key, wrong share set, or tampered carrier yields a coded error, not a partial/incorrect result.",
    ])
    return d


# =============================================================================
# ARCH-04 — Component Dependency Map
# =============================================================================
def arch04():
    W, H = 1280, 1140
    d = Diagram("arch04", "ARCH-04 Component Dependency Map", W, H)
    d.header("ARCH-04 · Component Dependency Map",
             "Workspace crates and their exact internal Cargo dependencies, with security-critical "
             "components and external tool spawns highlighted")

    NH = 46
    N = {}

    def node(nid, cx, cy, title, sub, accent, critical=False, w=156):
        N[nid] = d.vertex(cx - w / 2, cy - NH / 2, w, NH,
                          boxlabel(title, [sub] if sub else [], tsize=12.5, ssize=10),
                          box_style(accent, critical=critical))

    node("desktop", 620, 150, "desktop", "Tauri shell (excluded)", "ui", w=200)
    node("app", 620, 250, "sv-app (src-tauri)", "command surface · 38 cmds", "comp", w=240)
    node("core", 175, 386, "sv-core", "vault", "crit", critical=True)
    node("plat", 365, 386, "sv-platform", "file services", "crit", critical=True)
    node("stego", 555, 386, "sv-stego", "steganography", "domain")
    node("wm", 745, 386, "sv-watermark", "tamper-evidence", "domain")
    node("meta", 935, 386, "sv-meta", "metadata", "domain")
    node("qr", 1120, 386, "sv-qr", "QR codec", "domain")
    node("crypto", 365, 524, "sv-crypto", "impl adapters", "crit", critical=True, w=180)
    node("age", 705, 548, "sv-age", "age subprocess", "crit", critical=True)
    node("sss", 235, 648, "sv-sys-sss", "Shamir FFI", "crit", critical=True)
    node("traits", 365, 770, "sv-crypto-traits", "backend-free ABI", "plat", w=190)
    node("sodium", 115, 770, "sv-sys-sodium", "libsodium FFI", "crit", critical=True)
    node("types", 1010, 700, "sv-types", "DTO / error island", "plat", w=190)

    def tool(nid, cx, cy, title, sub):
        N[nid] = d.vertex(cx - 78, cy - 23, 156, 46,
                          boxlabel(title, [sub], tsize=12, ssize=10),
                          f"shape=note;html=1;whiteSpace=wrap;fillColor={COL['ext']['f']};"
                          f"strokeColor={COL['ext']['s']};strokeWidth=1.4;size=12;"
                          f"verticalAlign=middle;align=center;fontColor={INK};")
    tool("agebin", 1150, 548, "age / age-keygen", "external binary")
    tool("exiftool", 1150, 448, "ExifTool", "external binary")

    def dep(a, b, dashed=False, color=None):
        col = color or HAIR
        st = (f"edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;"
              f"strokeColor={col};strokeWidth=1.2;jettySize=auto;")
        if dashed:
            st += "dashed=1;dashPattern=5 4;"
        d.edge(N[a], N[b], style=st)

    dep("sss", "traits")
    dep("age", "traits")
    dep("crypto", "traits"); dep("crypto", "sss"); dep("crypto", "sodium")
    dep("core", "traits"); dep("core", "types"); dep("core", "crypto", dashed=True)  # dev-dep
    dep("plat", "traits"); dep("plat", "crypto"); dep("plat", "types")
    dep("stego", "traits"); dep("stego", "crypto"); dep("stego", "types")
    dep("wm", "traits"); dep("wm", "crypto"); dep("wm", "types")
    dep("meta", "types")
    dep("qr", "types")
    for t in ["core", "plat", "stego", "wm", "meta", "qr", "age"]:
        dep("app", t)
    for t in ["app", "meta", "age"]:
        dep("desktop", t)
    dep("age", "agebin", dashed=True, color=COL["ext"]["s"])
    dep("meta", "exiftool", dashed=True, color=COL["ext"]["s"])

    legend(d, 40, 906, [
        {"swatch": "ui", "text": "Tauri shell (workspace-excluded)"},
        {"swatch": "comp", "text": "Composition root"},
        {"swatch": "domain", "text": "Domain crate"},
        {"swatch": "plat", "text": "Shared ABI / DTO (leaf)"},
        {"swatch": "crit", "crit": True, "text": "Security-critical component"},
        {"swatch": "ext", "text": "External binary (runtime spawn)"},
        {"line": True, "text": "cargo dependency (depends-on)"},
        {"line": True, "dashed": True, "text": "dev-dependency / runtime spawn"},
    ], w=300)

    notebox(d, 360, 906, 880, "Reading the graph", [
        "• Edges are exact internal Cargo path-dependencies (from each crate's Cargo.toml). An arrow A → B means \"A depends on B\".",
        "• sv-crypto-traits is the dependency-light ABI root; sv-types is a leaf with zero crypto deps (so DTOs cannot hold secrets).",
        "• sv-core takes sv-crypto only as a dev-dependency (dashed) — the production vault is generic over the ABI and FFI-free.",
        "• For legibility, sv-app's direct edges to sv-crypto-traits / sv-crypto / sv-types and desktop's edge to sv-types are omitted",
        "    (they exist in the manifests). All other edges are drawn.",
        "• Security-critical = handles key material, performs cryptography, links C/FFI, or executes an external binary.",
        "• age / ExifTool edges are runtime subprocess spawns (hash-pinned), not compile-time dependencies.",
    ])
    return d


# =============================================================================
# ARCH-05 — Deployment Architecture
# =============================================================================
def arch05():
    W, H = 1240, 952
    d = Diagram("arch05", "ARCH-05 Deployment Architecture", W, H)
    d.header("ARCH-05 · Deployment Architecture",
             "Runtime deployment: application bundle, bundled+pinned resources, hardened "
             "subprocess execution, and OS / user-filesystem interaction")

    osz = container(d, 40, 96, 1160, 692,
                    "Operating System  (macOS · Windows · Linux)  ·  no network", "fs")

    bundle = container(d, 70, 142, 690, 612,
                       "Secure Vault application bundle  —  productName: Secure Vault · id: org.secure-vault.desktop · v0.1.0 · bundle.targets: all",
                       "comp", parent=osz, fill="#fbfcfe", dashed=False)

    runtime = d.vertex(90, 200, 320, 74,
                       boxlabel("Tauri 2 runtime", ["Rust core (sv-app + crates)",
                                                    "+ system WebView (WebKit / WebView2 / WebKitGTK)"]),
                       box_style("comp"), parent=bundle)
    frontend = d.vertex(430, 200, 310, 74,
                        boxlabel("Frontend assets", ["frontendDist: frontend/",
                                                     "HTML · JS · CSS · icons (withGlobalTauri)"]),
                        box_style("ui"), parent=bundle)
    d.edge(runtime, frontend, style=EDGE + "startArrow=block;startFill=1;")

    res = container(d, 90, 296, 650, 282,
                    "Resources  (bundle.resources: \"binaries/**/*\")", "ext", parent=bundle, dashed=False)
    age = d.vertex(108, 336, 290, 64, boxlabel("age", ["BLAKE3-pinned · mandatory", "release fails to build if missing"]),
                   box_style("crit", critical=True), parent=res)
    keygen = d.vertex(420, 336, 290, 64, boxlabel("age-keygen", ["BLAKE3-pinned · mandatory", "vault identity generation"]),
                      box_style("crit", critical=True), parent=res)
    exifd = d.vertex(108, 412, 290, 64, boxlabel("ExifTool distribution", ["exiftool + lib/  (or windows .exe)", "self-staged + pinned · optional"]),
                     box_style("ext"), parent=res)
    pins = d.vertex(420, 412, 290, 64, boxlabel("pins embedded at build", ["build.rs emit_pin → BLAKE3", "into the compiled binary"]),
                    box_style("neutral"), parent=res)
    d.text(108, 488, 624, 76,
           "<b style=\"color:#46506a\">Runtime resolution</b><br>"
           "<span style=\"font-size:10.5px;color:#45505f\">• Resolved from the bundled app-resource directory — no env var, no repository path in a packaged build.</span><br>"
           "<span style=\"font-size:10.5px;color:#45505f\">• Runtime re-verifies each binary's BLAKE3 pin before use; release refuses to run an unpinned mandatory binary.</span><br>"
           "<span style=\"font-size:10.5px;color:#45505f\">• SV_*_BIN environment overrides are honoured in debug builds only.</span>",
           align="left", size=11, parent=res)

    spawned = d.vertex(90, 600, 650, 56,
                       boxlabel("Spawned as hardened subprocess",
                                ["env_clear · wall-clock timeout · -config '' (ExifTool) · fail-closed when a tool is absent/unpinned"]),
                       box_style("crit", critical=True), parent=bundle)
    d.edge(age, spawned, "resolve + verify pin")
    d.edge(exifd, spawned)

    # right column (inside OS zone, outside bundle)
    userdata = d.vertex(800, 200, 360, 120,
                        boxlabel("User data on filesystem",
                                 [".svault  ·  .svenc / .svkey  ·  .minisig",
                                  ".svshare / .svss  ·  QR .png  ·  images  ·  keys",
                                  "(under the user's own directories)"]),
                        box_style("fs"), parent=osz)
    osint = d.vertex(800, 344, 360, 96,
                     boxlabel("OS integration",
                              ["File dialogs (tauri-plugin-dialog)",
                               "Open / reveal in folder (tauri-plugin-opener)",
                               "CSPRNG: getrandom / libsodium"]),
                     box_style("fs"), parent=osz)
    sandbox = d.vertex(800, 464, 360, 92,
                       boxlabel("Process sandbox surface",
                                ["WebView ↔ Rust via IPC (no fs: / shell: to page)",
                                 "atomic temp → fsync → rename writes",
                                 "refuse-overwrite · path-stripped errors"]),
                       box_style("comp"), parent=osz)

    d.vertex(800, 600, 360, 150,
             "<b style=\"color:#b0413f\">Out of scope (internal use)</b><br>"
             "<span style=\"font-size:10.5px;color:#45505f\">• Code signing / notarization (hardening item H5)</span><br>"
             "<span style=\"font-size:10.5px;color:#45505f\">• Per-OS signed installer for public distribution</span><br>"
             "<span style=\"font-size:10.5px;color:#45505f\">Per-OS bundle internals (.app / .msi / AppImage) differ;</span><br>"
             "<span style=\"font-size:10.5px;color:#45505f\">the logical structure shown is OS-agnostic.</span><br>"
             "<span style=\"font-size:10.5px;color:#45505f\">Bundling itself (active, targets: all) is configured.</span>",
             f"rounded=1;html=1;arcSize=6;fillColor=#fff8f8;strokeColor={CRIT_S};strokeWidth=1.2;"
             f"verticalAlign=top;align=left;spacingLeft=12;spacingTop=8;", parent=osz)

    d.edge(runtime, userdata, "read / atomic write")
    d.edge(frontend, userdata, "IPC results", style=EDGE + "dashed=1;dashPattern=6 4;")
    d.edge(runtime, sandbox, style=EDGE + "startArrow=block;startFill=1;")

    legend(d, 40, 802, [
        {"swatch": "comp", "text": "Application runtime / native"},
        {"swatch": "ui", "text": "Frontend assets"},
        {"swatch": "ext", "text": "Bundled resources / external tool"},
        {"swatch": "crit", "crit": True, "text": "Security-critical (pinned binary)"},
        {"swatch": "fs", "text": "OS / user filesystem"},
    ], w=320)
    notebox(d, 380, 802, 820, "Deployment notes", [
        "• The system WebView engine is OS-provided (WebKit / WebView2 / WebKitGTK) — only the Rust binary,",
        "   the static frontend assets, and the BLAKE3-pinned tool binaries are bundled.",
        "• A packaged build needs no env var, external setup, or repo path: tools resolve from app resources, pin-verified.",
        "• ExifTool is optional and fail-closed: absence disables only the Analysis module; the rest of the toolkit is unaffected.",
    ])
    return d


# ---- emit -------------------------------------------------------------------
def write_file(d):
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<mxfile host="app.diagrams.net" agent="secure-vault generate-drawio.py" version="24.7.17">\n'
           + d.xml() + '</mxfile>\n')
    path = OUT / f"{d.name.split(' ')[0]}-{d.name.split(' ', 1)[1].lower().replace(' & ', '-').replace(' ', '-')}.drawio"
    path.write_text(xml, encoding="utf-8")
    print("wrote", path.name, len(xml), "bytes")


if __name__ == "__main__":
    for fn in (arch01, arch02, arch03, arch04, arch05):
        write_file(fn())
