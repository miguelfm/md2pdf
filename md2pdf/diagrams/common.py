"""Caché, dimensións e saída Markdown compartidas polos diagramas."""
import hashlib
import re
import subprocess
import tempfile
from pathlib import Path

FORMAT_BY_ENGINE = {'lualatex': 'pdf', 'docx': 'png', 'html': 'svg'}
TEXTWIDTH_PT = {'lualatex': 483.7, 'docx': 468.0, 'html': 696.0}
# HTML usa SVG para manter diagramas vectoriais nítidos e escalables.
# As etiquetas dos diagramas van a 12 pt (próximo ao corpo de 13 pt sen
# desbordar). A altura máxima (560 pt, uns 20 cm) deixa sitio ao pé e permite
# diagramas verticais, que son os que caben con letra deste tamaño.
TARGET_FONT_PT, MAX_HEIGHT_PT, FALLBACK_WIDTH = 12.0, 560.0, '100%'
# Corpo do PDF (13 pt). En HTML o ancho vai en em, non nun % do contedor:
# cunha porcentaxe, nun móbil o diagrama encollía ata ser ilexible. As imaxes
# levan a clase DIAGRAM_CLASS, á que o CSS lle dá o tamaño das celas das
# táboas (.96rem); como o em dun width é o da propia imaxe, 1 em = etiqueta.
# Pandoc descarta os anchos en rem.
BODY_FONT_PT = 13.0
DIAGRAM_CLASS = 'md2pdf-diagram'
_SVG_FONT_RE = re.compile(rb'font-size\s*=\s*["\']([\d.]+)(?:px|pt)?["\']')
_CROPBOX_RE = re.compile(rb'/CropBox\s*\[\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\]')
_PDF_RE = re.compile(rb'/MediaBox\s*\[\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\]')
_SVG_TAG_RE = re.compile(rb'<svg\b[^>]*>', re.DOTALL)
_SVG_VIEWBOX_RE = re.compile(rb'viewBox\s*=\s*["\']\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)')
_PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'

def cache_dir(name: str) -> Path:
    path = Path(tempfile.gettempdir()) / f'md2pdf-{name}'
    path.mkdir(parents=True, exist_ok=True)
    return path

def content_hash(content: str, fmt: str, tag: str) -> str:
    return hashlib.sha1(f'{content}|{fmt}|{tag}'.encode()).hexdigest()[:16]

def natural_size_px(path: Path, fmt: str) -> tuple[float, float] | None:
    try:
        if fmt == 'pdf':
            data = path.read_bytes()
            match = _CROPBOX_RE.search(data) or _PDF_RE.search(data)
            if match:
                x0, y0, x1, y1 = map(float, match.groups())
                w, h = abs(x1 - x0), abs(y1 - y0)
                if w > 0 and h > 0:
                    return w / 0.75, h / 0.75
            try:
                proc = subprocess.run(['pdfinfo', str(path)], stdout=subprocess.PIPE,
                                      stderr=subprocess.DEVNULL, text=True, timeout=2)
                if proc.returncode == 0:
                    m = re.search(r'Page size:\s*([-\d.]+)\s*x\s*([-\d.]+)', proc.stdout)
                    if m:
                        return float(m.group(1)) / 0.75, float(m.group(2)) / 0.75
            except Exception:
                pass
            return None
        if fmt == 'svg':
            with path.open('rb') as stream: tag = _SVG_TAG_RE.search(stream.read(8192))
            match = _SVG_VIEWBOX_RE.search(tag.group(0)) if tag else None
            return (float(match.group(1)), float(match.group(2))) if match else None
        if fmt == 'png':
            with path.open('rb') as stream: head = stream.read(24)
            if len(head) < 24 or not head.startswith(_PNG_SIGNATURE): return None
            return float(int.from_bytes(head[16:20], 'big')), float(int.from_bytes(head[20:24], 'big'))
    except (OSError, ValueError): return None
    return None

def dominant_font_size(path: Path, fmt: str) -> float | None:
    """Tamaño de letra que leva máis caracteres, nas unidades de natural_size_px.

    Os renderizadores non sempre respectan o tamaño pedido: mmdc --pdfFit, por
    exemplo, encaixa o diagrama en 800 px de ancho e a letra sae entre 7 e
    12 pt. Mídese no PDF (PyMuPDF) e nos atributos font-size do SVG (Graphviz,
    Vega-Lite); o SVG de Mermaid leva o tamaño en CSS e o PNG non ten texto,
    así que neses casos devolve None e úsase o tamaño nominal.
    """
    counts: dict[float, int] = {}
    try:
        if fmt == 'pdf':
            import pymupdf
            with pymupdf.open(path) as document:
                for block in document[0].get_text('dict')['blocks']:
                    for line in block.get('lines', []):
                        for span in line['spans']:
                            size = round(span['size'], 2)
                            counts[size] = counts.get(size, 0) + len(span['text'].strip())
            counts = {size / 0.75: n for size, n in counts.items() if n}
        elif fmt == 'svg':
            for match in _SVG_FONT_RE.finditer(path.read_bytes()):
                size = float(match.group(1))
                counts[size] = counts.get(size, 0) + 1
    except (ImportError, OSError, ValueError, RuntimeError):
        return None
    positive = {size: n for size, n in counts.items() if size > 0}
    return max(positive, key=positive.get) if positive else None

def width_attr(path: Path, fmt: str, engine: str, font_px: float) -> str:
    size, textwidth = natural_size_px(path, fmt), TEXTWIDTH_PT.get(engine)
    font_px = dominant_font_size(path, fmt) or font_px
    if not size or not textwidth or min(size) <= 0 or font_px <= 0: return FALLBACK_WIDTH
    width, height = size
    if engine == 'html':
        # Ancho absoluto en em; o CSS (max-width: 100%) só o reduce se non cabe.
        scale = min(1/font_px, MAX_HEIGHT_PT/TARGET_FONT_PT/height)
        return f'{width*scale:.2f}em'
    scale = min(TARGET_FONT_PT/font_px, MAX_HEIGHT_PT/height)
    return f'{min(100.0, 100.0*width*scale/textwidth):.1f}%'

def image_block(path: Path, width: str, engine: str) -> str:
    uri = path.as_posix().replace(' ', '%20').replace('>', '%3E').replace('<', '%3C')
    classes = f'.{DIAGRAM_CLASS} ' if engine == 'html' else ''
    image = f'![](<{uri}>){{{classes}width={width}}}'
    if engine == 'lualatex':
        return '\n\n```{=latex}\n\\begingroup\\centering\n```\n\n'+image+'\n\n```{=latex}\n\\par\\endgroup\n```\n\n'
    return f'\n\n{image}\n\n'
