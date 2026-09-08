#!/usr/bin/env python3
"""Bộ sinh sơ đồ cho hồ sơ sáng kiến SecureVault Mobile.

Mỗi sơ đồ được mô tả một lần bằng cấu trúc dữ liệu (hộp + mũi tên), rồi xuất ra
đồng thời hai định dạng:

  * SVG  — dùng để render PNG chèn vào DOCX
  * .drawio (mxGraph XML) — để tác giả mở bằng diagrams.net và chỉnh sửa nếu cần

Nhờ vậy hai bản luôn khớp nhau về nội dung, tránh tình trạng sửa một bên quên bên kia.
Bảng màu dùng nền sáng cho phù hợp in ấn và chèn vào văn bản.
"""

import html
import pathlib
import xml.sax.saxutils as sax

OUT_SVG = pathlib.Path(__file__).parent / "hinh-anh" / "svg"
OUT_DIO = pathlib.Path(__file__).parent / "hinh-anh" / "drawio"

# ---------------------------------------------------------------- bảng màu
PALETTE = {
    "layer":   ("#EEF3FB", "#3A6EA5", "#12325B"),   # nền, viền, chữ
    "core":    ("#E7F4EC", "#2E7D4F", "#14432A"),   # lõi đã kiểm chứng
    "mobile":  ("#FDF0E3", "#C4772B", "#6B3E10"),   # thành phần riêng cho mobile
    "danger":  ("#FBE9E9", "#B3403A", "#5F1B17"),   # rủi ro / không khả dụng
    "neutral": ("#F2F3F5", "#6B7280", "#1F2933"),
    "accent":  ("#E8EBFA", "#4C51BF", "#242A6B"),
}

FONT = "Segoe UI, Roboto, Helvetica, Arial, sans-serif"


class Diagram:
    def __init__(self, name, title, width, height, subtitle=""):
        self.name = name
        self.title = title
        self.subtitle = subtitle
        self.w = width
        self.h = height
        self.boxes = []   # (id, x, y, w, h, lines, style, dashed)
        self.arrows = []  # (x1,y1,x2,y2,label,dashed)
        self.notes = []   # (x, y, text, size, anchor, bold, colour)

    def box(self, bid, x, y, w, h, lines, style="neutral", dashed=False):
        if isinstance(lines, str):
            lines = [lines]
        self.boxes.append((bid, x, y, w, h, lines, style, dashed))

    def arrow(self, x1, y1, x2, y2, label="", dashed=False):
        self.arrows.append((x1, y1, x2, y2, label, dashed))

    def note(self, x, y, text, size=12, anchor="start", bold=False, colour="#3F4A5A"):
        self.notes.append((x, y, text, size, anchor, bold, colour))

    # ------------------------------------------------------------ SVG
    def to_svg(self):
        p = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}" font-family="{FONT}">',
            f'<rect width="{self.w}" height="{self.h}" fill="#FFFFFF"/>',
            '<defs><marker id="ah" markerWidth="10" markerHeight="8" refX="9" refY="4" '
            'orient="auto"><path d="M0,0 L10,4 L0,8 z" fill="#55607A"/></marker></defs>',
        ]
        p.append(
            f'<text x="{self.w/2}" y="34" font-size="20" font-weight="700" '
            f'text-anchor="middle" fill="#12203A">{sax.escape(self.title)}</text>'
        )
        if self.subtitle:
            p.append(
                f'<text x="{self.w/2}" y="56" font-size="13" text-anchor="middle" '
                f'fill="#5A6779">{sax.escape(self.subtitle)}</text>'
            )

        for x1, y1, x2, y2, label, dashed in self.arrows:
            dash = ' stroke-dasharray="6,4"' if dashed else ""
            p.append(
                f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#55607A" '
                f'stroke-width="1.7" marker-end="url(#ah)"{dash}/>'
            )
            if label:
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                tw = len(label) * 6.2 + 10
                p.append(
                    f'<rect x="{mx - tw/2}" y="{my - 10}" width="{tw}" height="17" rx="3" '
                    f'fill="#FFFFFF" opacity="0.95"/>'
                    f'<text x="{mx}" y="{my + 3}" font-size="11.5" text-anchor="middle" '
                    f'fill="#44506A">{sax.escape(label)}</text>'
                )

        for _bid, x, y, w, h, lines, style, dashed in self.boxes:
            fill, stroke, text = PALETTE[style]
            dash = ' stroke-dasharray="7,4"' if dashed else ""
            p.append(
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="{fill}" '
                f'stroke="{stroke}" stroke-width="1.6"{dash}/>'
            )
            n = len(lines)
            first_size = 13.5 if n > 1 else 13
            total = 17 * n
            start = y + h / 2 - total / 2 + 12.5
            for i, ln in enumerate(lines):
                size = first_size if i == 0 else 11.5
                weight = "600" if i == 0 else "400"
                colour = text if i == 0 else "#4B5768"
                p.append(
                    f'<text x="{x + w/2}" y="{start + i*17}" font-size="{size}" '
                    f'font-weight="{weight}" text-anchor="middle" fill="{colour}">'
                    f'{sax.escape(ln)}</text>'
                )

        for x, y, t, size, anchor, bold, colour in self.notes:
            weight = "700" if bold else "400"
            p.append(
                f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
                f'text-anchor="{anchor}" fill="{colour}">{sax.escape(t)}</text>'
            )

        p.append("</svg>")
        return "\n".join(p)

    # ------------------------------------------------------------ drawio
    def to_drawio(self):
        cells = [
            '<mxCell id="0"/>',
            '<mxCell id="1" parent="0"/>',
        ]
        cells.append(
            f'<mxCell id="title" value="{html.escape(self.title, quote=True)}" style="text;html=1;'
            f'fontSize=20;fontStyle=1;align=center;" vertex="1" parent="1">'
            f'<mxGeometry x="0" y="10" width="{self.w}" height="30" as="geometry"/></mxCell>'
        )
        if self.subtitle:
            cells.append(
                f'<mxCell id="subtitle" value="{html.escape(self.subtitle, quote=True)}" style="text;html=1;'
                f'fontSize=13;align=center;fontColor=#5A6779;" vertex="1" parent="1">'
                f'<mxGeometry x="0" y="42" width="{self.w}" height="20" as="geometry"/></mxCell>'
            )

        for bid, x, y, w, h, lines, style, dashed in self.boxes:
            fill, stroke, text = PALETTE[style]
            # Thuộc tính XML không chứa được thẻ HTML thô: phải thoát toàn bộ chuỗi,
            # kể cả các thẻ <b>/<br/>. draw.io sẽ giải mã lại khi mở tệp.
            raw = "<br/>".join(
                (f"<b>{html.escape(l)}</b>" if i == 0 and len(lines) > 1 else html.escape(l))
                for i, l in enumerate(lines)
            )
            label = html.escape(raw, quote=True)
            dash = "dashed=1;" if dashed else "dashed=0;"
            cells.append(
                f'<mxCell id="{bid}" value="{label}" style="rounded=1;whiteSpace=wrap;html=1;'
                f'fillColor={fill};strokeColor={stroke};fontColor={text};{dash}arcSize=8;'
                f'verticalAlign=middle;" vertex="1" parent="1">'
                f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
            )

        for i, (x1, y1, x2, y2, label, dashed) in enumerate(self.arrows):
            dash = "dashed=1;" if dashed else "dashed=0;"
            cells.append(
                f'<mxCell id="e{i}" value="{html.escape(label, quote=True)}" style="endArrow=block;html=1;'
                f'strokeColor=#55607A;{dash}fontSize=11;" edge="1" parent="1">'
                f'<mxGeometry relative="1" as="geometry">'
                f'<mxPoint x="{x1}" y="{y1}" as="sourcePoint"/>'
                f'<mxPoint x="{x2}" y="{y2}" as="targetPoint"/></mxGeometry></mxCell>'
            )

        for i, (x, y, t, size, anchor, bold, colour) in enumerate(self.notes):
            al = {"start": "left", "middle": "center", "end": "right"}[anchor]
            cells.append(
                f'<mxCell id="n{i}" value="{html.escape(t, quote=True)}" style="text;html=1;fontSize={size};'
                f'align={al};fontColor={colour};{"fontStyle=1;" if bold else ""}" '
                f'vertex="1" parent="1">'
                f'<mxGeometry x="{x if al != "center" else x-150}" y="{y-14}" '
                f'width="300" height="20" as="geometry"/></mxCell>'
            )

        body = "\n        ".join(cells)
        return (
            f'<mxfile host="SecureVault" modified="2026-09-08T00:00:00.000Z" agent="tao-so-do.py" '
            f'version="24.0.0">\n'
            f'  <diagram id="{self.name}" name="{html.escape(self.title)}">\n'
            f'    <mxGraphModel dx="{self.w}" dy="{self.h}" grid="1" gridSize="10" guides="1" '
            f'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
            f'pageWidth="{self.w}" pageHeight="{self.h}" math="0" shadow="0">\n'
            f'      <root>\n        {body}\n      </root>\n'
            f'    </mxGraphModel>\n  </diagram>\n</mxfile>\n'
        )

    def write(self):
        OUT_SVG.mkdir(parents=True, exist_ok=True)
        OUT_DIO.mkdir(parents=True, exist_ok=True)
        (OUT_SVG / f"{self.name}.svg").write_text(self.to_svg(), encoding="utf-8")
        (OUT_DIO / f"{self.name}.drawio").write_text(self.to_drawio(), encoding="utf-8")
        return self.name
