cat > make_grid.py <<'PY'
from pathlib import Path
from pdf_export import make_debug_grid

make_debug_grid(
    Path("templates/cp_template.pdf"),
    Path("tmp/cp_template_grid.pdf"),
    step_mm=5
)
print("OK -> tmp/cp_template_grid.pdf")
PY

ls -l make_grid.py
