#!/usr/bin/env python3
"""Định dạng dùng chung cho bộ hồ sơ sáng kiến SecureVault Mobile.

Mục tiêu: ba văn bản DOCX có kiểu chữ, giãn dòng, tiêu đề, bảng và chú thích hình
thống nhất, đạt chất lượng trình bày của một hồ sơ dự thi.

Quy ước trình bày (theo thông lệ văn bản hành chính Việt Nam):
  * chữ Times New Roman 13pt, giãn dòng 1.4, giãn đoạn 6pt
  * lề trên 2.5cm, dưới 2.0cm, trái 3.5cm, phải 1.5cm
  * tiêu đề mục in đậm, đánh số theo cấp
  * bảng có tiêu đề bảng phía trên, hình có chú thích phía dưới
"""
import re


from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

# Bộ đếm bảng và hình. Đánh số thủ công đã ba lần gây lệch số hiệu khi chèn thêm nội dung
# vào giữa tài liệu; đếm tự động theo thứ tự gọi hàm sẽ luôn đúng, kể cả khi sắp xếp lại mục.
_DEM = {"bang": 0, "hinh": 0}


def dat_lai_dem():
    """Gọi ở đầu mỗi văn bản để bắt đầu đếm lại từ 1."""
    _DEM["bang"] = 0
    _DEM["hinh"] = 0


FONT = "Times New Roman"
SIZE = Pt(13)

NAVY = RGBColor(0x12, 0x32, 0x5B)
GREY = RGBColor(0x4B, 0x57, 0x68)
GREEN = RGBColor(0x1E, 0x6B, 0x41)
RED = RGBColor(0xA3, 0x33, 0x2D)


# ------------------------------------------------------------------ tài liệu
def new_document(*, gian_dong=1.4, cach_doan=6):
    """Tài liệu trống đã đặt sẵn phông, lề và kiểu tiêu đề.

    `gian_dong` / `cach_doan` để văn bản có giới hạn số trang (Thuyết minh phải dưới 20
    trang) siết được mật độ chữ mà vẫn giữ nguyên phông và bố cục chung của bộ hồ sơ.
    """
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = FONT
    st.font.size = SIZE
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    pf = st.paragraph_format
    pf.line_spacing = gian_dong
    pf.space_after = Pt(cach_doan)
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # Style Heading mặc định của Word dùng Calibri/xanh nhạt — ép về phông hành chính
    # nhưng vẫn giữ đúng cấp Heading để trường mục lục nhận diện được.
    for name, sz in (("Heading 1", 14), ("Heading 2", 13.5), ("Heading 3", 13)):
        hs = doc.styles[name]
        hs.font.name = FONT
        hs.font.size = Pt(sz)
        hs.font.color.rgb = NAVY
        hs.font.bold = True
        hs.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        hs.paragraph_format.keep_with_next = True

    for s in doc.sections:
        s.page_width = Cm(21.0)      # khổ A4
        s.page_height = Cm(29.7)
        # Lề theo Nghị định 30/2020/NĐ-CP về công tác văn thư — cũng là lề tác giả đã
        # đặt lại trong bản rà soát thủ công, giữ nguyên để hai bản in khớp nhau.
        s.top_margin = Cm(2.5)
        s.bottom_margin = Cm(2.0)
        s.left_margin = Cm(3.5)
        s.right_margin = Cm(1.5)
    return doc


def _run(p, text, *, bold=False, italic=False, size=None, colour=None, font=None):
    r = p.add_run(text)
    r.bold = bold
    r.italic = italic
    r.font.name = font or FONT
    r.font.size = size or SIZE
    r._element.rPr.rFonts.set(qn("w:eastAsia"), font or FONT)
    if colour is not None:
        r.font.color.rgb = colour
    return r


def _nhan_manh(p, text, *, bold=False, italic=False, colour=None):
    """Ghi văn bản, chuyển cặp dấu sao *…* thành chữ nghiêng.

    Các đoạn nội dung dài được viết ở dạng chuỗi Python thuần, nên cách duy nhất để đánh dấu
    nhấn mạnh ngay trong chuỗi là dùng cặp dấu sao. Nếu không xử lý ở đây thì dấu sao sẽ in
    nguyên vào văn bản — lỗi trình bày thấy rõ trên bản in.
    """
    for i, doan in enumerate(re.split(r"\*([^*\n]+)\*", text)):
        if not doan:
            continue
        # Các phần tử ở vị trí lẻ là nội dung nằm giữa hai dấu sao.
        _run(p, doan, bold=bold, italic=italic or i % 2 == 1, colour=colour)


# ------------------------------------------------------------------ khối văn bản
def quocHieu(doc):
    """Quốc hiệu — tiêu ngữ."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(0)
    _run(p, "CỘNG HOÀ XÃ HỘI CHỦ NGHĨA VIỆT NAM", bold=True, size=Pt(13))
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    _run(p, "Độc lập – Tự do – Hạnh phúc", bold=True, size=Pt(13))
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(12)
    _run(p, "―――――――――――――", size=Pt(11))


def tieuDeChinh(doc, text, sub=None):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(4) if sub else Pt(14)
    _run(p, text, bold=True, size=Pt(16), colour=NAVY)
    if sub:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(14)
        _run(p, sub, italic=True, size=Pt(12.5), colour=GREY)


def h1(doc, text, *, sang_trang=False):
    """Tiêu đề cấp 1. `sang_trang=True` bắt đầu trang mới bằng thuộc tính “ngắt trang trước”
    của chính đoạn tiêu đề — cách này không để lại đoạn rỗng như khi chèn ký tự ngắt trang,
    nên không sinh ra trang trắng khi trang trước vừa vặn kín."""
    p = doc.add_paragraph(style="Heading 1")
    p.paragraph_format.page_break_before = sang_trang
    p.paragraph_format.space_before = Pt(0) if sang_trang else Pt(14)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _run(p, text, bold=True, size=Pt(14), colour=NAVY)
    return p


def h2(doc, text):
    p = doc.add_paragraph(style="Heading 2")
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _run(p, text, bold=True, size=Pt(13.5), colour=NAVY)
    return p


def h3(doc, text):
    p = doc.add_paragraph(style="Heading 3")
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    _run(p, text, bold=True, italic=True, size=Pt(13))
    return p


def para(doc, text, *, bold=False, italic=False, align=None, indent=True, colour=None):
    p = doc.add_paragraph()
    if align:
        p.alignment = align
    if indent:
        p.paragraph_format.first_line_indent = Cm(0.8)
    _nhan_manh(p, text, bold=bold, italic=italic, colour=colour)
    return p


def rich(doc, parts, *, indent=True, align=None):
    """Đoạn văn có nhiều đoạn chữ với định dạng khác nhau.

    `parts` là danh sách (text, kiểu) với kiểu ∈ {"", "b", "i", "bi", "code"}.
    """
    p = doc.add_paragraph()
    if align:
        p.alignment = align
    if indent:
        p.paragraph_format.first_line_indent = Cm(0.8)
    for text, kind in parts:
        if kind == "code":
            _run(p, text, font="Consolas", size=Pt(11.5))
        else:
            _nhan_manh(p, text, bold="b" in kind, italic="i" in kind)
    return p


def bullet(doc, text, *, level=0, bold_head=None):
    p = doc.add_paragraph(style="List Bullet" if level == 0 else "List Bullet 2")
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.left_indent = Cm(0.8 + 0.7 * level)
    if bold_head:
        _run(p, bold_head, bold=True)
    _nhan_manh(p, text)
    return p


def numbered(doc, text, *, bold_head=None):
    p = doc.add_paragraph(style="List Number")
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.left_indent = Cm(0.8)
    if bold_head:
        _run(p, bold_head, bold=True)
    _run(p, text)
    return p


def caption(doc, text, *, above=False):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2 if not above else 8)
    p.paragraph_format.space_after = Pt(10 if not above else 4)
    p.paragraph_format.first_line_indent = Cm(0)
    _run(p, text, italic=True, size=Pt(11.5), colour=GREY)
    return p


def hinh(doc, path, caption_text, width_cm=15.0):
    """Chèn hình kèm chú thích phía dưới; số hiệu "Hình N." được thêm tự động."""
    _DEM["hinh"] += 1
    caption_text = f"Hình {_DEM['hinh']}. {caption_text}"
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.first_line_indent = Cm(0)
    p.add_run().add_picture(str(path), width=Cm(width_cm))
    caption(doc, caption_text)


def placeholder_hinh(doc, ten_hinh, mo_ta, chieu_cao_cm=6.0):
    """Ô trống có viền cho hình tác giả cần tự bổ sung (không được bịa ảnh)."""
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = t.rows[0].cells[0]
    _viền_ô(cell, sz=6, color="9AA4B0", dashed=True)
    cell.width = Cm(15)
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(int(chieu_cao_cm * 8))
    p.paragraph_format.space_after = Pt(int(chieu_cao_cm * 8))
    _run(p, f"[Vị trí gắn ảnh chụp — {ten_hinh}]\n", bold=True, colour=GREY, size=Pt(12))
    _run(p, mo_ta, italic=True, colour=GREY, size=Pt(11))
    caption(doc, f"{ten_hinh}. {mo_ta}")


def _viền_ô(cell, sz=6, color="7F7F7F", dashed=False):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "dashed" if dashed else "single")
        el.set(qn("w:sz"), str(sz))
        el.set(qn("w:color"), color)
        borders.append(el)
    tcPr.append(borders)


def _to_mau(cell, hex_colour):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), hex_colour)
    tcPr.append(shd)


def bang(doc, tieu_de, headers, rows, widths=None, note=None):
    """Bảng có tiêu đề phía trên, hàng đầu tô nền, tự động canh chữ.

    `tieu_de` chỉ cần phần mô tả; số hiệu "Bảng N." được thêm tự động theo thứ tự xuất hiện.
    Truyền chuỗi rỗng nếu muốn bảng không có tiêu đề.
    """
    if tieu_de:
        _DEM["bang"] += 1
        caption(doc, f"Bảng {_DEM['bang']}. {tieu_de}", above=True)
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, htxt in enumerate(headers):
        _to_mau(hdr[i], "DCE6F1")
        p = hdr[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.first_line_indent = Cm(0)
        _run(p, htxt, bold=True, size=Pt(12))
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            p = cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.0    # ô bảng gọn hơn hẳn thân bài
            p.paragraph_format.first_line_indent = Cm(0)
            p.alignment = (
                WD_ALIGN_PARAGRAPH.CENTER if i > 0 and len(str(val)) < 22
                else WD_ALIGN_PARAGRAPH.LEFT
            )
            _run(p, str(val), size=Pt(11.5))
    if widths:
        for r in t.rows:
            for i, w in enumerate(widths):
                r.cells[i].width = Cm(w)
    if note:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.first_line_indent = Cm(0)
        _run(p, note, italic=True, size=Pt(11), colour=GREY)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def khung_nhan_manh(doc, tieu_de, dong, mau="E7F4EC", vien="2E7D4F"):
    """Khung nhấn mạnh dùng cho kết luận/luận điểm quan trọng."""
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = t.rows[0].cells[0]
    _to_mau(cell, mau)
    _viền_ô(cell, sz=8, color=vien)
    cell.width = Cm(15.5)
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.first_line_indent = Cm(0)
    _run(p, tieu_de, bold=True, size=Pt(12.5), colour=NAVY)
    for d in dong:
        q = cell.add_paragraph()
        q.paragraph_format.space_after = Pt(2)
        q.paragraph_format.first_line_indent = Cm(0)
        _run(q, d, size=Pt(12))
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def ngat_trang(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def chu_ky(doc, trai, phai, dia_danh="……………, ngày ….. tháng ….. năm 202…"):
    """Khối ký tên hai cột."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(14)
    _run(p, dia_danh, italic=True)

    t = doc.add_table(rows=1, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, (tieu, ghi) in enumerate((trai, phai)):
        c = t.rows[0].cells[i]
        c.width = Cm(7.75)
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Cm(0)
        _run(p, tieu, bold=True, size=Pt(12.5))
        q = c.add_paragraph()
        q.alignment = WD_ALIGN_PARAGRAPH.CENTER
        q.paragraph_format.first_line_indent = Cm(0)
        _run(q, ghi, italic=True, size=Pt(11.5), colour=GREY)
        for _ in range(3):
            c.add_paragraph()


def danh_so_trang(doc):
    """Chèn số trang vào chân trang."""
    for section in doc.sections:
        footer = section.footer
        p = footer.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Cm(0)
        r = p.add_run()
        r.font.name = FONT
        r.font.size = Pt(11)
        for instr in ("begin", "instr", "separate", "end"):
            el = OxmlElement(f"w:fld{instr}" if instr != "instr" else "w:instrText")
            if instr == "begin":
                el = OxmlElement("w:fldChar")
                el.set(qn("w:fldCharType"), "begin")
            elif instr == "instr":
                el = OxmlElement("w:instrText")
                el.set(qn("xml:space"), "preserve")
                el.text = " PAGE "
            elif instr == "separate":
                el = OxmlElement("w:fldChar")
                el.set(qn("w:fldCharType"), "separate")
            else:
                el = OxmlElement("w:fldChar")
                el.set(qn("w:fldCharType"), "end")
            r._r.append(el)


def muc_luc(doc, tieu_de="MỤC LỤC", *, sang_trang=False):
    """Chèn trường mục lục tự động (Word/LibreOffice sẽ điền khi mở và cập nhật trường)."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.page_break_before = sang_trang
    p.paragraph_format.space_after = Pt(10)
    _run(p, tieu_de, bold=True, size=Pt(14), colour=NAVY)

    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    r = p.add_run()
    fld = OxmlElement("w:fldChar"); fld.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve")
    instr.text = r' TOC \o "1-3" \h \z \u '
    sep = OxmlElement("w:fldChar"); sep.set(qn("w:fldCharType"), "separate")
    txt = OxmlElement("w:t")
    txt.text = "Nhấn chuột phải vào đây rồi chọn “Cập nhật trường” để hiện mục lục."
    end = OxmlElement("w:fldChar"); end.set(qn("w:fldCharType"), "end")
    for e in (fld, instr, sep, txt, end):
        r._r.append(e)
    r.font.name = FONT
    r.font.size = Pt(12)


# ------------------------------------------------------------------ tiêu đề văn bản
def tieu_de_quan_doi(doc, don_vi_tren="TỔNG CỤC II", don_vi_duoi="HỌC VIỆN KHOA HỌC QUÂN SỰ"):
    """Khối tiêu đề hai cột theo mẫu hồ sơ: tên đơn vị bên trái, quốc hiệu bên phải."""
    t = doc.add_table(rows=1, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    trai, phai = t.rows[0].cells
    trai.width = Cm(6.4)
    phai.width = Cm(9.6)

    p = trai.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.first_line_indent = Cm(0)
    _run(p, don_vi_tren, size=Pt(12.5))
    q = trai.add_paragraph()
    q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    q.paragraph_format.space_after = Pt(0)
    q.paragraph_format.first_line_indent = Cm(0)
    _run(q, don_vi_duoi, bold=True, size=Pt(12.5))
    r = trai.add_paragraph()
    r.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r.paragraph_format.first_line_indent = Cm(0)
    _run(r, "―――――――", size=Pt(10))

    p = phai.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.first_line_indent = Cm(0)
    _run(p, "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", bold=True, size=Pt(12.5))
    q = phai.add_paragraph()
    q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    q.paragraph_format.space_after = Pt(0)
    q.paragraph_format.first_line_indent = Cm(0)
    _run(q, "Độc lập – Tự do – Hạnh phúc", bold=True, size=Pt(12.5))
    r = phai.add_paragraph()
    r.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r.paragraph_format.first_line_indent = Cm(0)
    _run(r, "―――――――――――――――", size=Pt(10))

    doc.add_paragraph().paragraph_format.space_after = Pt(6)


def dong_dien(doc, nhan, gia_tri="", *, dam_nhan=True, cach_sau=4):
    """Một dòng thông tin kiểu biểu mẫu: 'Nhãn: ...........'."""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(cach_sau)
    p.paragraph_format.first_line_indent = Cm(0)
    # Căn trái, không căn đều: dòng biểu mẫu kết thúc bằng dấu chấm lửng, nếu căn đều thì
    # các từ bị kéo giãn ra toàn bề ngang trông rất xấu.
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _run(p, f"{nhan}: ", bold=dam_nhan)
    _run(p, gia_tri if gia_tri else "…" * 30)
    return p


def o_danh_dau(doc, muc, danh_dau=True):
    """Dòng trong danh mục hồ sơ kèm theo, có ô đánh dấu."""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.left_indent = Cm(0.8)
    p.paragraph_format.first_line_indent = Cm(0)
    _run(p, "☑  " if danh_dau else "☐  ", size=Pt(13))
    _run(p, muc)
    return p


def trang_bia(doc, ten_hoa, *, dia_danh_nam="Hà Nội, năm 2026",
              don_vi_tren="TỔNG CỤC II", don_vi_duoi="HỌC VIỆN KHOA HỌC QUÂN SỰ",
              nhan="HỒ SƠ"):
    """Trang bìa theo mẫu hồ sơ: tên đơn vị trên cùng, tên sáng kiến giữa trang, địa danh dưới.

    Dựng bằng một bảng một ô chiếm trọn trang thay vì các đoạn rời, để khối chữ không bị đẩy
    sang trang sau khi độ dài tên sáng kiến thay đổi.
    """
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    o = t.rows[0].cells[0]

    def dong(text, *, bold=False, size=13.0, cach_sau=0):
        p = o.add_paragraph() if o.paragraphs[0].text or o.paragraphs[0].runs else o.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.space_after = Pt(cach_sau)
        if text:
            _run(p, text, bold=bold, size=Pt(size))
        return p

    dong(don_vi_tren, size=13)
    dong(don_vi_duoi, bold=True, size=13)
    for _ in range(9):
        dong("")
    dong(nhan, bold=True, size=14, cach_sau=10)
    dong(ten_hoa, bold=True, size=14)
    for _ in range(10):
        dong("")
    dong(dia_danh_nam, bold=True, size=14)
    ngat_trang(doc)
