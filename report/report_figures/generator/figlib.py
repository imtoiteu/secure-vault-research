# -*- coding: utf-8 -*-
"""
figlib — thu vien sinh dong thoi ban .drawio (mxGraph goc, chinh sua duoc) va ban .svg
cho cac hinh ky thuat cua bao cao Secure Vault Research.

Nguyen tac: moi hinh duoc mo ta mot lan bang mot DSL nho (Node/Edge/Zone), sau do
duoc "render" ra hai dinh dang. Nho vay ban .drawio va ban .svg luon khop nhau.

Ban .drawio dung SHAPE GOC cua diagrams.net (rounded rectangle, cylinder, note,
umlActor, ellipse, rhombus, hexagon, swimlane...) => mo bang diagrams.net va sua
duoc tung phan tu, KHONG phai anh SVG nhung vao file.
"""
import html
import os
import textwrap
import xml.sax.saxutils as sx

# ---------------------------------------------------------------- palette ---
PALETTE = {
    "ui":      ("#E8F0FE", "#3B6FD4", "#12305F"),
    "app":     ("#E6F4EA", "#2E7D46", "#12401F"),
    "domain":  ("#FFF4E5", "#C77700", "#5A3600"),
    "crypto":  ("#F3E8FD", "#7A3FBF", "#3A1560"),
    "sys":     ("#FDE8E8", "#C0392B", "#5E1611"),
    "store":   ("#EAF6F6", "#0F7B7B", "#0A3D3D"),
    "ext":     ("#EFEFEF", "#5B6675", "#1C2330"),
    "note":    ("#FFFDE7", "#B8A429", "#4A4210"),
    "danger":  ("#FCE4E4", "#B3261E", "#5E1611"),
    "ok":      ("#E3F5E7", "#1E7B34", "#0E3A19"),
    "plain":   ("#FFFFFF", "#5B6675", "#1C2330"),
    "key":     ("#FFF0F6", "#B5197F", "#5A0C3E"),
    "grid":    ("#DDE3EA", "#DDE3EA", "#DDE3EA"),
    "axis":    ("#8A94A4", "#8A94A4", "#8A94A4"),
}
ZONE_FILL = {
    "ui":     ("#F5F8FF", "#8FAEE8"),
    "app":    ("#F3FAF5", "#8FC8A3"),
    "domain": ("#FFFAF2", "#E3BC85"),
    "crypto": ("#FAF5FF", "#BFA0E0"),
    "sys":    ("#FFF6F5", "#E0A29B"),
    "store":  ("#F4FBFB", "#8CC6C6"),
    "ext":    ("#F7F7F8", "#B9C0C9"),
    "danger": ("#FFF5F5", "#E8A6A1"),
    "ok":     ("#F4FBF6", "#9CCBA9"),
}

FONT = "'Segoe UI','Helvetica Neue',Helvetica,Arial,sans-serif"


# --------------------------------------------------------------- elements ---
class Node:
    def __init__(self, nid, x, y, w, h, label, kind="plain", sub="", shape="box",
                 fontsize=12.5, bold=True):
        self.id, self.x, self.y, self.w, self.h = nid, x, y, w, h
        self.label, self.kind, self.sub, self.shape = label, kind, sub, shape
        self.fontsize, self.bold = fontsize, bold


class Edge:
    def __init__(self, src, dst, label="", style="solid", side=None, dashed=False,
                 arrow="classic", bend=None, lx=None, ly=None, fontsize=10.5):
        self.src, self.dst, self.label = src, dst, label
        self.style, self.side, self.dashed = style, side, dashed
        self.arrow, self.bend = arrow, bend
        self.lx, self.ly, self.fontsize = lx, ly, fontsize


class Zone:
    def __init__(self, x, y, w, h, label, kind="ext", sub="", labelpos="tl"):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.label, self.kind, self.sub, self.labelpos = label, kind, sub, labelpos


class Text:
    def __init__(self, x, y, text, size=11.5, bold=False, color="#34404f",
                 anchor="start", w=260):
        self.x, self.y, self.text, self.size = x, y, text, size
        self.bold, self.color, self.anchor, self.w = bold, color, anchor, w


class Figure:
    def __init__(self, fid, title, subtitle, w, h, source=""):
        self.fid, self.title, self.subtitle = fid, title, subtitle
        self.w, self.h, self.source = w, h, source
        self.zones, self.nodes, self.edges, self.texts = [], [], [], []

    def zone(self, *a, **k):
        self.zones.append(Zone(*a, **k)); return self.zones[-1]

    def node(self, *a, **k):
        self.nodes.append(Node(*a, **k)); return self.nodes[-1]

    def edge(self, *a, **k):
        self.edges.append(Edge(*a, **k)); return self.edges[-1]

    def text(self, *a, **k):
        self.texts.append(Text(*a, **k)); return self.texts[-1]

    def by_id(self, nid):
        for n in self.nodes:
            if n.id == nid:
                return n
        raise KeyError(nid)


# ------------------------------------------------------------ svg helpers ---
def _esc(s):
    return html.escape(s, quote=True)


def _wrap(txt, width):
    """Ngat dong theo so ky tu uoc luong."""
    return textwrap.wrap(txt, width=width) or [""]


def _fit(txt, box_w, size):
    """So ky tu vua mot dong theo be rong hop."""
    per = max(4, int((box_w - 14) / (size * 0.545)))
    return _wrap(txt, per)


def _anchor_point(n, other):
    """Diem noi tren canh hop n huong ve other (truc chinh)."""
    cx, cy = n.x + n.w / 2, n.y + n.h / 2
    ox, oy = other.x + other.w / 2, other.y + other.h / 2
    dx, dy = ox - cx, oy - cy
    if abs(dx) * n.h >= abs(dy) * n.w:
        return (n.x + n.w, cy) if dx > 0 else (n.x, cy)
    return (cx, n.y + n.h) if dy > 0 else (cx, n.y)


SHAPE_SVG = {}


def _svg_shape(n, fill, stroke):
    x, y, w, h = n.x, n.y, n.w, n.h
    s = n.shape
    if s == "cyl":
        ry = min(14, h / 5)
        return (f'<path d="M{x} {y+ry} A{w/2} {ry} 0 0 1 {x+w} {y+ry} '
                f'L{x+w} {y+h-ry} A{w/2} {ry} 0 0 1 {x} {y+h-ry} Z" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>'
                f'<path d="M{x} {y+ry} A{w/2} {ry} 0 0 0 {x+w} {y+ry}" fill="none" '
                f'stroke="{stroke}" stroke-width="1.6"/>')
    if s == "ellipse":
        return (f'<ellipse cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>')
    if s == "rhombus":
        return (f'<polygon points="{x+w/2},{y} {x+w},{y+h/2} {x+w/2},{y+h} {x},{y+h/2}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>')
    if s == "hex":
        k = min(18, w / 5)
        return (f'<polygon points="{x+k},{y} {x+w-k},{y} {x+w},{y+h/2} {x+w-k},{y+h} '
                f'{x+k},{y+h} {x},{y+h/2}" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>')
    if s == "note":
        k = 14
        return (f'<path d="M{x} {y} L{x+w-k} {y} L{x+w} {y+k} L{x+w} {y+h} L{x} {y+h} Z" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>'
                f'<path d="M{x+w-k} {y} L{x+w-k} {y+k} L{x+w} {y+k}" fill="none" '
                f'stroke="{stroke}" stroke-width="1.4"/>')
    if s == "actor":
        cx = x + w / 2
        r = 9
        top = y + 8
        return (f'<circle cx="{cx}" cy="{top+r}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="1.7"/>'
                f'<line x1="{cx}" y1="{top+2*r}" x2="{cx}" y2="{top+2*r+22}" stroke="{stroke}" stroke-width="1.7"/>'
                f'<line x1="{cx-14}" y1="{top+2*r+8}" x2="{cx+14}" y2="{top+2*r+8}" stroke="{stroke}" stroke-width="1.7"/>'
                f'<line x1="{cx}" y1="{top+2*r+22}" x2="{cx-12}" y2="{top+2*r+40}" stroke="{stroke}" stroke-width="1.7"/>'
                f'<line x1="{cx}" y1="{top+2*r+22}" x2="{cx+12}" y2="{top+2*r+40}" stroke="{stroke}" stroke-width="1.7"/>')
    if s == "parallelogram":
        k = 16
        return (f'<polygon points="{x+k},{y} {x+w},{y} {x+w-k},{y+h} {x},{y+h}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>')
    if s == "lifeline":
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>')
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>')


def render_svg(f: Figure) -> str:
    out = [f'<?xml version="1.0" encoding="UTF-8"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{f.w}" height="{f.h}" '
           f'viewBox="0 0 {f.w} {f.h}" role="img" aria-label="{_esc(f.title)}">',
           '<defs>',
           '<marker id="arw" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
           'markerHeight="7" orient="auto-start-reverse">'
           '<path d="M0 0 L10 5 L0 10 z" fill="#44506080"/></marker>',
           '<marker id="arwd" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
           'markerHeight="7" orient="auto-start-reverse">'
           '<path d="M0 0 L10 5 L0 10 z" fill="#8a94a4"/></marker>',
           '<marker id="arwo" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" '
           'markerHeight="8" orient="auto-start-reverse">'
           '<path d="M0 0 L10 5 L0 10 z" fill="none" stroke="#445060" stroke-width="1.4"/></marker>',
           '</defs>',
           f'<style>text{{font-family:{FONT};fill:#1c2330}}'
           '.ttl{font-size:20px;font-weight:700}'
           '.sub{font-size:12px;fill:#5b6675}'
           '.zl{font-size:12px;font-weight:700}'
           '.zs{font-size:10.5px;fill:#67707d}'
           '.el{font-size:10.5px;fill:#3a4插}'
           '.src{font-size:10px;fill:#77808c}</style>'.replace("插", "5060"),
           f'<rect x="0" y="0" width="{f.w}" height="{f.h}" fill="#ffffff"/>']

    out.append(f'<text class="ttl" x="26" y="34">{_esc(f.title)}</text>')
    if f.subtitle:
        out.append(f'<text class="sub" x="26" y="54">{_esc(f.subtitle)}</text>')

    for z in f.zones:
        fill, stroke = ZONE_FILL.get(z.kind, ZONE_FILL["ext"])
        out.append(f'<rect x="{z.x}" y="{z.y}" width="{z.w}" height="{z.h}" rx="10" '
                   f'fill="{fill}" stroke="{stroke}" stroke-width="1.4" stroke-dasharray="6 4"/>')
        out.append(f'<text class="zl" x="{z.x+12}" y="{z.y+19}" fill="#3b4655">{_esc(z.label)}</text>')
        if z.sub:
            out.append(f'<text class="zs" x="{z.x+12}" y="{z.y+34}">{_esc(z.sub)}</text>')

    # edges first (behind nodes)
    for e in f.edges:
        a, b = f.by_id(e.src), f.by_id(e.dst)
        p1 = _anchor_point(a, b)
        p2 = _anchor_point(b, a)
        dash = ' stroke-dasharray="6 4"' if e.dashed else ''
        col = "#8a94a4" if e.dashed else "#5b6675"
        mk = "arwo" if e.arrow == "open" else ("arwd" if e.dashed else "arw")
        if e.bend == "ortho":
            mx = (p1[0] + p2[0]) / 2
            d = f'M{p1[0]} {p1[1]} L{mx} {p1[1]} L{mx} {p2[1]} L{p2[0]} {p2[1]}'
        elif e.bend == "orthoV":
            my = (p1[1] + p2[1]) / 2
            d = f'M{p1[0]} {p1[1]} L{p1[0]} {my} L{p2[0]} {my} L{p2[0]} {p2[1]}'
        else:
            d = f'M{p1[0]} {p1[1]} L{p2[0]} {p2[1]}'
        marker = '' if e.arrow == "none" else f' marker-end="url(#{mk})"'
        out.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="1.5"{dash}{marker}/>')
        if e.label:
            lx = e.lx if e.lx is not None else (p1[0] + p2[0]) / 2
            ly = e.ly if e.ly is not None else (p1[1] + p2[1]) / 2 - 5
            lines = _wrap(e.label, 30)
            bw = max(len(l) for l in lines) * e.fontsize * 0.53 + 10
            bh = len(lines) * (e.fontsize + 3) + 4
            out.append(f'<rect x="{lx-bw/2}" y="{ly-bh+4}" width="{bw}" height="{bh}" rx="3" '
                       f'fill="#ffffffe0"/>')
            for i, l in enumerate(lines):
                out.append(f'<text x="{lx}" y="{ly - bh + 4 + (i+1)*(e.fontsize+3) - 3}" '
                           f'text-anchor="middle" font-size="{e.fontsize}" fill="#3a5060">{_esc(l)}</text>')

    for n in f.nodes:
        fill, stroke, txtc = PALETTE.get(n.kind, PALETTE["plain"])
        out.append(_svg_shape(n, fill, stroke))
        if n.shape == "actor":
            lines = _fit(n.label, n.w + 40, 11.5)
            base = n.y + n.h - (len(lines) - 1) * 14 - 2
            for i, l in enumerate(lines):
                out.append(f'<text x="{n.x+n.w/2}" y="{base+i*14}" text-anchor="middle" '
                           f'font-size="11.5" font-weight="600" fill="{txtc}">{_esc(l)}</text>')
            continue
        lines = _fit(n.label, n.w, n.fontsize)
        sublines = _fit(n.sub, n.w, 10) if n.sub else []
        total = len(lines) * (n.fontsize + 3) + (len(sublines) * 12.5 if sublines else 0)
        cy = n.y + n.h / 2 - total / 2 + n.fontsize
        fw = "700" if n.bold else "500"
        for i, l in enumerate(lines):
            out.append(f'<text x="{n.x+n.w/2}" y="{cy + i*(n.fontsize+3)}" text-anchor="middle" '
                       f'font-size="{n.fontsize}" font-weight="{fw}" fill="{txtc}">{_esc(l)}</text>')
        for i, l in enumerate(sublines):
            out.append(f'<text x="{n.x+n.w/2}" y="{cy + len(lines)*(n.fontsize+3) + i*12.5 - 1}" '
                       f'text-anchor="middle" font-size="10" fill="{txtc}bb">{_esc(l)}</text>')

    for t in f.texts:
        fw = "700" if t.bold else "400"
        lines = _wrap(t.text, max(10, int(t.w / (t.size * 0.5))))
        for i, l in enumerate(lines):
            out.append(f'<text x="{t.x}" y="{t.y + i*(t.size+3)}" text-anchor="{t.anchor}" '
                       f'font-size="{t.size}" font-weight="{fw}" fill="{t.color}">{_esc(l)}</text>')

    if f.source:
        for i,ln in enumerate(_wrap(f.source, 190)):
            out.append(f'<text class="src" x="26" y="{f.h-26+i*13}">{_esc(ln)}</text>')
    out.append('</svg>')
    return "\n".join(out)


# --------------------------------------------------------- drawio helpers ---
SHAPE_STYLE = {
    "box": "rounded=1;arcSize=8;whiteSpace=wrap;html=1;",
    "cyl": "shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=12;whiteSpace=wrap;html=1;",
    "ellipse": "ellipse;whiteSpace=wrap;html=1;",
    "rhombus": "rhombus;whiteSpace=wrap;html=1;",
    "hex": "shape=hexagon;perimeter=hexagonPerimeter2;whiteSpace=wrap;html=1;",
    "note": "shape=note;size=14;whiteSpace=wrap;html=1;",
    "actor": "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;",
    "parallelogram": "shape=parallelogram;perimeter=parallelogramPerimeter;whiteSpace=wrap;html=1;fixedSize=1;",
    "lifeline": "rounded=1;arcSize=6;whiteSpace=wrap;html=1;",
}


def _h(text):
    """Thoat ky tu cho phan noi dung HTML ben trong nhan cua draw.io."""
    return sx.escape(text)


def _attr(html):
    """Thoat toan bo chuoi HTML mot lan nua de dat vao thuoc tinh XML."""
    return sx.escape(html, {'"': "&quot;", "'": "&apos;"})


def _dw_label(n):
    html = _h(n.label)
    if n.sub:
        html += "<br><font style='font-size:9px'>" + _h(n.sub) + "</font>"
    return _attr(html)


def render_drawio(f: Figure) -> str:
    cells = []
    cid = [2]

    def nid():
        cid[0] += 1
        return f"c{cid[0]}"

    idmap = {}
    cells.append(f'<mxCell id="ttl" value="{_attr(_h(f.title))}" '
                 f'style="text;html=1;fontSize=20;fontStyle=1;align=left;verticalAlign=middle;'
                 f'fontFamily=Helvetica;" vertex="1" parent="1">'
                 f'<mxGeometry x="26" y="12" width="{f.w-52}" height="28" as="geometry"/></mxCell>')
    if f.subtitle:
        cells.append(f'<mxCell id="sub" value="{_attr(_h(f.subtitle))}" '
                     f'style="text;html=1;fontSize=12;align=left;verticalAlign=middle;'
                     f'fontColor=#5B6675;fontFamily=Helvetica;" vertex="1" parent="1">'
                     f'<mxGeometry x="26" y="40" width="{f.w-52}" height="20" as="geometry"/></mxCell>')

    for i, z in enumerate(f.zones):
        fill, stroke = ZONE_FILL.get(z.kind, ZONE_FILL["ext"])
        val = _h(z.label)
        if z.sub:
            val += f"<br><font style='font-size:9px;color:#67707d'>{_h(z.sub)}</font>"
        cells.append(
            f'<mxCell id="z{i}" value="{_attr(val)}" '
            f'style="rounded=1;arcSize=6;whiteSpace=wrap;html=1;fillColor={fill};'
            f'strokeColor={stroke};dashed=1;dashPattern=6 4;verticalAlign=top;align=left;'
            f'spacingLeft=10;spacingTop=4;fontSize=12;fontStyle=1;fontColor=#3B4655;'
            f'container=0;fontFamily=Helvetica;" vertex="1" parent="1">'
            f'<mxGeometry x="{z.x}" y="{z.y}" width="{z.w}" height="{z.h}" as="geometry"/></mxCell>')

    for n in f.nodes:
        fill, stroke, txtc = PALETTE.get(n.kind, PALETTE["plain"])
        style = SHAPE_STYLE.get(n.shape, SHAPE_STYLE["box"])
        style += (f"fillColor={fill};strokeColor={stroke};fontColor={txtc};"
                  f"fontSize={int(n.fontsize)};fontStyle={1 if n.bold else 0};"
                  f"strokeWidth=1.6;fontFamily=Helvetica;")
        i = nid()
        idmap[n.id] = i
        cells.append(f'<mxCell id="{i}" value="{_dw_label(n)}" style="{style}" vertex="1" parent="1">'
                     f'<mxGeometry x="{n.x}" y="{n.y}" width="{n.w}" height="{n.h}" as="geometry"/></mxCell>')

    for e in f.edges:
        st = ("edgeStyle=orthogonalEdgeStyle;rounded=1;" if e.bend else
              "edgeStyle=none;rounded=0;")
        st += "html=1;jettySize=auto;orthogonalLoop=1;exitPerimeter=1;entryPerimeter=1;"
        st += f"strokeColor={'#8A94A4' if e.dashed else '#5B6675'};strokeWidth=1.5;"
        if e.dashed:
            st += "dashed=1;dashPattern=6 4;"
        if e.arrow == "none":
            st += "endArrow=none;"
        elif e.arrow == "open":
            st += "endArrow=open;endFill=0;"
        else:
            st += "endArrow=classic;endFill=1;"
        st += f"fontSize={int(e.fontsize)};fontColor=#3A5060;labelBackgroundColor=#FFFFFF;fontFamily=Helvetica;"
        cells.append(f'<mxCell id="{nid()}" value="{_attr(_h(e.label))}" style="{st}" edge="1" '
                     f'parent="1" source="{idmap[e.src]}" target="{idmap[e.dst]}">'
                     f'<mxGeometry relative="1" as="geometry"/></mxCell>')

    for t in f.texts:
        al = {"start": "left", "middle": "center", "end": "right"}[t.anchor]
        x = t.x if t.anchor == "start" else (t.x - t.w / 2 if t.anchor == "middle" else t.x - t.w)
        cells.append(f'<mxCell id="{nid()}" value="{_attr(_h(t.text))}" '
                     f'style="text;html=1;align={al};verticalAlign=top;fontSize={int(t.size)};'
                     f'fontStyle={1 if t.bold else 0};fontColor={t.color};fontFamily=Helvetica;" '
                     f'vertex="1" parent="1">'
                     f'<mxGeometry x="{x}" y="{t.y-t.size}" width="{t.w}" height="{t.size*2.4}" as="geometry"/></mxCell>')

    if f.source:
        cells.append(f'<mxCell id="srcnote" value="{_attr(_h(f.source))}" '
                     f'style="text;html=1;align=left;fontSize=10;fontColor=#77808C;fontFamily=Helvetica;" '
                     f'vertex="1" parent="1">'
                     f'<mxGeometry x="26" y="{f.h-26}" width="{f.w-52}" height="18" as="geometry"/></mxCell>')

    body = "\n        ".join(cells)
    return (f'<mxfile host="secure-vault-report" modified="2026-08-20T00:00:00.000Z" '
            f'agent="figlib" version="24.7.7" type="device">\n'
            f'  <diagram id="{f.fid}" name="{_attr(_h(f.fid))}">\n'
            f'    <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" '
            f'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{f.w}" '
            f'pageHeight="{f.h}" math="0" shadow="0">\n'
            f'      <root>\n'
            f'        <mxCell id="0"/>\n'
            f'        <mxCell id="1" parent="0"/>\n'
            f'        {body}\n'
            f'      </root>\n'
            f'    </mxGraphModel>\n'
            f'  </diagram>\n'
            f'</mxfile>\n')


# ------------------------------------------------------------------ write ---
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REGISTRY = []


def emit(f: Figure, chapter):
    svg = render_svg(f)
    dw = render_drawio(f)
    sub = f"chapter{chapter}"
    for d in (os.path.join(BASE, sub), os.path.join(BASE, "svg"), os.path.join(BASE, "drawio")):
        os.makedirs(d, exist_ok=True)
    svg_path = os.path.join(BASE, "svg", f.fid + ".svg")
    dw_path = os.path.join(BASE, "drawio", f.fid + ".drawio")
    with open(svg_path, "w", encoding="utf-8") as fh:
        fh.write(svg)
    with open(dw_path, "w", encoding="utf-8") as fh:
        fh.write(dw)
    # ban sao theo chuong de tien tra cuu
    with open(os.path.join(BASE, sub, f.fid + ".svg"), "w", encoding="utf-8") as fh:
        fh.write(svg)
    with open(os.path.join(BASE, sub, f.fid + ".drawio"), "w", encoding="utf-8") as fh:
        fh.write(dw)
    REGISTRY.append((f.fid, f.title, f.source, chapter))
    return svg_path
