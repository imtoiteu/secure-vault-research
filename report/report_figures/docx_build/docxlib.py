# -*- coding: utf-8 -*-
"""
docxlib — dung tai lieu Word theo dung khuon mau cua bao cao tham chieu:
A4, le 3,5/1,5/2,5/2 cm, Times New Roman 14pt, gian dong 1,2, thut dau dong 1,25 cm,
can deu hai ben; tieu de chuong can giua, in dam.

Hinh ky thuat duoc chen bang SVG (kem anh PNG du phong) theo dung co che
`asvg:svgBlip` cua Word — mo trong Word se hien ban vector.
"""
import os
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor, Emu
from docx.opc.part import Part
from docx.opc.packuri import PackURI
from PIL import Image

FIGDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BODY_FONT = "Times New Roman"
MONO_FONT = "Consolas"
SVG_EXT_URI = "{96DAC541-7B7A-43D3-8B79-37D633B846F1}"
SVG_NS = "http://schemas.microsoft.com/office/drawing/2016/SVG/main"
CONTENT_W_CM = 16.2   # 21 - 3.5 - 1.5 + mot chut


# ------------------------------------------------------------------ setup ---
def new_document():
    doc = Document()
    s = doc.sections[0]
    s.page_width, s.page_height = Cm(21), Cm(29.7)
    s.left_margin, s.right_margin = Cm(3.5), Cm(1.5)
    s.top_margin, s.bottom_margin = Cm(2.5), Cm(2.0)

    n = doc.styles["Normal"]
    n.font.name = BODY_FONT
    n.font.size = Pt(13)
    n.element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)
    pf = n.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.first_line_indent = Cm(1.25)
    pf.line_spacing = 1.35
    pf.space_after = Pt(4)
    pf.space_before = Pt(0)

    for name, size in (("Heading 1", 14), ("Heading 2", 13), ("Heading 3", 13)):
        st = doc.styles[name]
        st.font.name = BODY_FONT
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = RGBColor(0, 0, 0)
        st.element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)
        st.paragraph_format.space_before = Pt(10)
        st.paragraph_format.space_after = Pt(6)
        st.paragraph_format.first_line_indent = Cm(0)
        st.paragraph_format.line_spacing = 1.3
        st.paragraph_format.keep_with_next = True
    doc.styles["Heading 1"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.styles["Heading 1"].paragraph_format.space_before = Pt(14)
    _add_page_numbers(doc)
    return doc


def _add_page_numbers(doc):
    footer = doc.sections[0].footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    run = p.add_run()
    for instr in ("begin", None, "separate", None, "end"):
        fld = OxmlElement("w:fldChar") if instr != None or True else None
    r = run._r
    f1 = OxmlElement("w:fldChar"); f1.set(qn("w:fldCharType"), "begin")
    it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = " PAGE "
    f2 = OxmlElement("w:fldChar"); f2.set(qn("w:fldCharType"), "end")
    r.append(f1); r.append(it); r.append(f2)
    run.font.name = BODY_FONT
    run.font.size = Pt(12)


# --------------------------------------------------------------- helpers ----
def _fmt_runs(p, text):
    """Ho tro **in dam** va `ma nguon` trong mot doan."""
    import re
    parts = re.split(r"(\*\*.+?\*\*|`[^`]+`)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            r = p.add_run(part[2:-2]); r.bold = True
        elif part.startswith("`") and part.endswith("`"):
            r = p.add_run(part[1:-1]); r.font.name = MONO_FONT; r.font.size = Pt(11.5)
            r._element.rPr.rFonts.set(qn("w:eastAsia"), MONO_FONT)
        else:
            r = p.add_run(part)
        r.font.name = BODY_FONT if not (part.startswith("`")) else MONO_FONT


def para(doc, text, indent=True, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=13,
         bold=False, italic=False, space_after=4, color=None):
    p = doc.add_paragraph()
    p.paragraph_format.alignment = align
    p.paragraph_format.first_line_indent = Cm(1.25 if indent else 0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.35
    _fmt_runs(p, text)
    for r in p.runs:
        r.font.size = Pt(size)
        if bold:
            r.bold = True
        if italic:
            r.italic = True
        if color:
            r.font.color.rgb = color
    return p


def bullet(doc, text, level=0):
    p = doc.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.left_indent = Cm(1.0 + level * 0.7)
    p.paragraph_format.first_line_indent = Cm(-0.45)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.3
    _fmt_runs(p, ("– " if level == 0 else "· ") + text)
    for r in p.runs:
        r.font.size = Pt(13)
    return p


def heading(doc, text, level, page_break=False):
    if page_break:
        doc.add_page_break()
    lines = text.split("\n")
    h = doc.add_heading(lines[0], level=level)
    for extra in lines[1:]:
        r = h.add_run()
        r.add_break()
        r2 = h.add_run(extra)
        r2.bold = True
        r2.font.name = BODY_FONT
        r2.font.size = Pt(14 if level == 1 else 13)
    for r in h.runs:
        r.font.name = BODY_FONT
        r.font.color.rgb = RGBColor(0, 0, 0)
    return h


def caption(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(10)
    p.paragraph_format.line_spacing = 1.2
    r = p.add_run(text)
    r.bold = True
    r.font.name = BODY_FONT
    r.font.size = Pt(12.5)
    return p


# --------------------------------------------------------- SVG embedding ----
def _add_svg_part(doc, svg_path):
    """Them tep SVG vao goi docx va tra ve rId lien ket tu document part."""
    part = doc.part
    n = len([p for p in part.package.iter_parts() if str(p.partname).endswith(".svg")]) + 1
    uri = PackURI("/word/media/figure%d.svg" % n)
    with open(svg_path, "rb") as fh:
        blob = fh.read()
    svg_part = Part(uri, "image/svg+xml", blob, part.package)
    rId = part.relate_to(
        svg_part,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image")
    return rId


def _attach_svg(pic_run, svg_rid):
    """Gan svgBlip vao the a:blip cua anh vua chen (co che SVG cua Word)."""
    from lxml import etree
    blips = pic_run._element.findall(".//" + qn("a:blip"))
    if not blips:
        raise RuntimeError("khong tim thay a:blip")
    blip = blips[0]
    A = "http://schemas.openxmlformats.org/drawingml/2006/main"
    R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    extLst = etree.SubElement(blip, "{%s}extLst" % A)
    ext = etree.SubElement(extLst, "{%s}ext" % A)
    ext.set("uri", SVG_EXT_URI)
    svgblip = etree.SubElement(ext, "{%s}svgBlip" % SVG_NS, nsmap={"asvg": SVG_NS})
    svgblip.set("{%s}embed" % R, svg_rid)


def figure(doc, fid, cap_text, max_w_cm=CONTENT_W_CM, max_h_cm=20.0):
    """Chen mot hinh ky thuat: PNG du phong + lop vector SVG, kem chu thich."""
    png = os.path.join(FIGDIR, "png", fid + ".png")
    svg = os.path.join(FIGDIR, "svg", fid + ".svg")
    with Image.open(png) as im:
        w, h = im.size
    ratio = h / w
    w_cm = max_w_cm
    if w_cm * ratio > max_h_cm:
        w_cm = max_h_cm / ratio
    p = doc.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run()
    run.add_picture(png, width=Cm(w_cm))
    if os.path.exists(svg):
        _attach_svg(run, _add_svg_part(doc, svg))
    caption(doc, cap_text)
    return p


def screenshot(doc, name, cap_text, max_w_cm=CONTENT_W_CM, max_h_cm=13.5):
    png = os.path.join(FIGDIR, "screenshots", name)
    with Image.open(png) as im:
        w, h = im.size
    ratio = h / w
    w_cm = max_w_cm
    if w_cm * ratio > max_h_cm:
        w_cm = max_h_cm / ratio
    p = doc.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(png, width=Cm(w_cm))
    caption(doc, cap_text)
    return p


def placeholder(doc, text, instruction):
    p = doc.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(12.5)
    r.font.color.rgb = RGBColor(0xB3, 0x26, 0x1E)
    _shade(p, "FFF3F3")
    q = doc.add_paragraph()
    q.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    q.paragraph_format.first_line_indent = Cm(0)
    q.paragraph_format.space_after = Pt(8)
    r2 = q.add_run(instruction)
    r2.italic = True
    r2.font.size = Pt(11.5)
    return p


def _shade(p, hexcolor):
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hexcolor)
    pPr.append(shd)


# ------------------------------------------------------------------ table ---
def table(doc, cap_text, headers, rows, widths=None, size=11, header_fill="DCE6F1"):
    caption(doc, cap_text)
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    hdr = t.rows[0].cells
    for i, htxt in enumerate(headers):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.15
        r = p.add_run(htxt); r.bold = True
        r.font.name = BODY_FONT; r.font.size = Pt(size)
        _cell_shade(hdr[i], header_fill)
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.paragraph_format.alignment = (WD_ALIGN_PARAGRAPH.LEFT if i or len(headers) < 3
                                            else WD_ALIGN_PARAGRAPH.LEFT)
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            _fmt_runs(p, str(val))
            for r in p.runs:
                if r.font.name != MONO_FONT:
                    r.font.name = BODY_FONT
                r.font.size = Pt(size) if r.font.name != MONO_FONT else Pt(size - 0.5)
    if widths:
        _fixed_layout(t)
        total = sum(widths)
        for i, wd in enumerate(widths):
            w = Cm(CONTENT_W_CM * wd / total)
            for row in t.rows:
                row.cells[i].width = w
    _repeat_header(t)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def _fixed_layout(t):
    tblPr = t._tbl.tblPr
    for tag in ("w:tblLayout", "w:tblW"):
        for el in tblPr.findall(qn(tag)):
            tblPr.remove(el)
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed")
    tblPr.append(lay)
    tw = OxmlElement("w:tblW")
    tw.set(qn("w:w"), str(int(Cm(CONTENT_W_CM).twips)))
    tw.set(qn("w:type"), "dxa")
    tblPr.append(tw)


def _cell_shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)


def _repeat_header(t):
    tr = t.rows[0]._tr
    trPr = tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def codeblock(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.left_indent = Cm(0.8)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.line_spacing = 1.05
    _shade(p, "F4F6F8")
    lines = text.strip("\n").split("\n")
    for i, ln in enumerate(lines):
        r = p.add_run(ln)
        r.font.name = MONO_FONT
        r.font.size = Pt(10.5)
        r._element.rPr.rFonts.set(qn("w:eastAsia"), MONO_FONT)
        if i < len(lines) - 1:
            r.add_break()
    return p


def render(doc, blocks):
    """Dich mot danh sach khoi noi dung thanh cac phan tu Word."""
    for b in blocks:
        kind = b[0]
        if kind == "h1":
            heading(doc, b[1], 1, page_break=(len(b) < 3 or b[2]))
        elif kind == "h2":
            heading(doc, b[1], 2)
        elif kind == "h3":
            heading(doc, b[1], 3)
        elif kind == "p":
            para(doc, b[1])
        elif kind == "pn":          # doan khong thut dau dong
            para(doc, b[1], indent=False)
        elif kind == "b":
            bullet(doc, b[1])
        elif kind == "b2":
            bullet(doc, b[1], level=1)
        elif kind == "fig":
            figure(doc, b[1], b[2], **(b[3] if len(b) > 3 else {}))
        elif kind == "shot":
            screenshot(doc, b[1], b[2], **(b[3] if len(b) > 3 else {}))
        elif kind == "ph":
            placeholder(doc, b[1], b[2])
        elif kind == "tbl":
            table(doc, b[1], b[2], b[3], b[4] if len(b) > 4 else None,
                  b[5] if len(b) > 5 else 11)
        elif kind == "code":
            codeblock(doc, b[1])
        elif kind == "center":
            para(doc, b[1], indent=False, align=WD_ALIGN_PARAGRAPH.CENTER,
                 bold=(len(b) > 2 and b[2]))
        elif kind == "pagebreak":
            doc.add_page_break()
        elif kind == "note":
            p = para(doc, b[1], indent=False, size=12, italic=True)
            p.paragraph_format.left_indent = Cm(0.8)
        else:
            raise ValueError("khoi khong ro: " + kind)
