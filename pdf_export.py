from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import fitz  # PyMuPDF

def mm(mm_val: float) -> float:
    # PDF body (pt) = mm * 72 / 25.4
    return mm_val * 72.0 / 25.4

@dataclass(frozen=True)
class FieldBox:
    page: int
    x: float
    y: float
    w: float
    h: float
    size: float = 9

def fill_pdf_template(
    template_pdf: Path,
    out_pdf: Path,
    fields: dict[str, str],
    layout: dict[str, FieldBox],
    font_path: Path,
) -> None:
    tpl = fitz.open(str(template_pdf))
    out = fitz.open()

    # skopíruj všetky strany šablóny
    out.insert_pdf(tpl)

    for key, text in fields.items():
        if key not in layout:
            continue
        box = layout[key]
        page = out[box.page]
        rect = fitz.Rect(box.x, box.y, box.x + box.w, box.y + box.h)

        page.insert_textbox(
            rect,
            text or "",
            fontsize=box.size,
            fontname="CustomFont",
            fontfile=str(font_path),
            align=fitz.TEXT_ALIGN_LEFT,
        )

    out.save(str(out_pdf))

def make_debug_grid(template_pdf: Path, out_pdf: Path, step_mm: int = 10) -> None:
    doc = fitz.open(str(template_pdf))
    for p in doc:
        w, h = p.rect.width, p.rect.height
        step = mm(step_mm)
        # vertikálne čiary
        x = 0
        while x < w:
            p.draw_line((x, 0), (x, h))
            x += step
        # horizontálne čiary
        y = 0
        while y < h:
            p.draw_line((0, y), (w, y))
            y += step
    doc.save(str(out_pdf))
