cat > pdf_export.py <<'PY'
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import fitz  # PyMuPDF

def mm(mm_val: float) -> float:
    return mm_val * 72.0 / 25.4  # mm -> pt

@dataclass(frozen=True)
class FieldBox:
    page: int
    x: float
    y: float
    w: float
    h: float
    size: float = 9

def make_debug_grid(template_pdf: Path, out_pdf: Path, step_mm: int = 10) -> None:
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(template_pdf))
    step = mm(step_mm)

    for p in doc:
        w, h = p.rect.width, p.rect.height

        x = 0.0
        while x < w:
            p.draw_line((x, 0), (x, h))
            x += step

        y = 0.0
        while y < h:
            p.draw_line((0, y), (w, y))
            y += step

    doc.save(str(out_pdf))
PY
