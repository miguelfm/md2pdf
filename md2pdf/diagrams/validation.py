"""Validación estrutural; inspección adicional con PyMuPDF/Pillow opcionais."""
import math
import importlib.util
import struct
import zlib
from pathlib import Path
from xml.etree import ElementTree as ET


def validation_warning(fmt: str) -> str | None:
    if fmt == 'pdf' and importlib.util.find_spec('pymupdf') is None:
        level = 'estrutural' if importlib.util.find_spec('pypdf') else 'básica (cabeceira e final)'
        return (f'validación PDF {level}; instala PyMuPDF para detectar páxinas '
                'en branco e estimar a lexibilidade')
    if fmt == 'png' and importlib.util.find_spec('PIL') is None:
        return 'validación PNG estrutural; instala Pillow para comprobar a decodificación'
    return None


def validate_output(path: Path, fmt: str) -> None:
    """Lanza ValueError para saídas truncadas, incorrectas ou baleiras detectables.

    Non demostra que unha figura sexa semanticamente correcta ou lexible.
    """
    try:
        data = path.read_bytes()
        if fmt == 'svg':
            root = ET.fromstring(data)
            if root.tag.split('}')[-1] != 'svg':
                raise ValueError('a raíz non é svg')
            # Non contar definicións de símbolos, máscaras ou marcadores.
            def graphical(node):
                tag = node.tag.split('}')[-1]
                if tag in {'defs', 'clipPath', 'mask', 'marker', 'symbol', 'metadata'}:
                    return False
                if tag in {'path', 'rect', 'circle', 'ellipse', 'line', 'polyline',
                           'polygon', 'text', 'image', 'use', 'foreignObject'}:
                    return True
                return any(graphical(child) for child in node)
            if not graphical(root):
                raise ValueError('SVG sen elementos gráficos')
            viewbox = root.get('viewBox')
            if viewbox:
                values = [float(v) for v in viewbox.replace(',', ' ').split()]
                if len(values) != 4 or not all(map(math.isfinite, values)) or min(values[2:]) <= 0:
                    raise ValueError('viewBox inválido')
        elif fmt == 'pdf':
            if not data.startswith(b'%PDF-') or b'%%EOF' not in data[-1024:]:
                raise ValueError('PDF truncado ou cabeceira incorrecta')
            try:
                import pymupdf
            except ImportError:
                try:
                    from pypdf import PdfReader
                except ImportError:
                    return  # Só validación básica sen bibliotecas opcionais.
                reader = PdfReader(path)
                if len(reader.pages) != 1 or not reader.pages[0].get_contents():
                    raise ValueError('o PDF debe conter unha páxina con contido')
            else:
                with pymupdf.open(path) as document:
                    if len(document) != 1 or document.is_repaired:
                        raise ValueError('PDF danado ou con máis dunha páxina')
                    page = document[0]
                    if page.rect.is_empty or page.rect.is_infinite:
                        raise ValueError('dimensións PDF incorrectas')
                    # A canle alfa preserva gráficos brancos para fondos escuros.
                    pix = page.get_pixmap(matrix=pymupdf.Matrix(.5, .5),
                                          colorspace=pymupdf.csGRAY, alpha=True)
                    if not pix.samples or max(pix.samples[1::2]) == 0:
                        raise ValueError('PDF visualmente baleiro')
        elif fmt == 'png':
            if not data.startswith(b'\x89PNG\r\n\x1a\n'):
                raise ValueError('cabeceira PNG incorrecta')
            pos, kinds = 8, []
            while pos < len(data):
                length = struct.unpack('>I', data[pos:pos+4])[0]
                kind = data[pos+4:pos+8]
                payload = data[pos+8:pos+8+length]
                crc = struct.unpack('>I', data[pos+8+length:pos+12+length])[0]
                if zlib.crc32(kind + payload) & 0xffffffff != crc:
                    raise ValueError('CRC PNG incorrecto')
                if not kinds and (kind != b'IHDR' or length != 13 or
                                  min(struct.unpack('>II', payload[:8])) <= 0):
                    raise ValueError('dimensións PNG incorrectas')
                kinds.append(kind)
                pos += length + 12
            if not kinds or kinds[-1] != b'IEND' or b'IDAT' not in kinds:
                raise ValueError('PNG incompleto')
            try:
                from PIL import Image
            except ImportError:
                return
            with Image.open(path) as picture:
                picture.load()
                if picture.convert('RGBA').getchannel('A').getbbox() is None:
                    raise ValueError('PNG totalmente transparente')
        else:
            raise ValueError(f'formato descoñecido: {fmt}')
    except Exception as error:
        raise ValueError(f'saída {fmt.upper()} inválida: {error}') from error


def pdf_font_warning(path: Path, width: str, textwidth: float) -> str | None:
    """Estimación para ancho porcentual; non cambia o tamaño da figura."""
    if not width.endswith('%'):
        return None
    try:
        import pymupdf
        with pymupdf.open(path) as document:
            page = document[0]
            sizes = [span['size'] for block in page.get_text('dict')['blocks']
                     for line in block.get('lines', []) for span in line['spans']
                     if span['text'].strip()]
            if sizes:
                effective = min(sizes) * textwidth * float(width[:-1]) / 100 / page.rect.width
                if effective < 8:
                    return (f'texto estimado de {effective:.1f} pt; revisa a figura, '
                            'aumenta width ou divide o diagrama')
    except (ImportError, ValueError, OSError, RuntimeError):
        pass
    return None
