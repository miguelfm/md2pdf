"""Tamaño e familia da letra dos diagramas: coma as celas das táboas."""
import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from md2pdf.diagrams.common import (TARGET_FONT_PT, TEXTWIDTH_PT,
                                    dominant_font_size, width_attr)
from md2pdf.diagrams.renderers import DOT_FONT, GraphvizRenderer
from md2pdf.diagrams.validation import pdf_font_warning

HAS_PYMUPDF = importlib.util.find_spec('pymupdf') is not None


def _pdf(path: Path, width: float, spans: list[tuple[str, float]]) -> None:
    """PDF dunha páxina co texto de cada tupla (texto, tamaño en pt)."""
    import pymupdf
    with pymupdf.open() as document:
        page = document.new_page(width=width, height=100)
        for row, (text, size) in enumerate(spans):
            page.insert_text((5, 20 + 25 * row), text, fontsize=size)
        document.save(path)


@unittest.skipUnless(HAS_PYMUPDF, 'require PyMuPDF')
class MeasuredFontTests(unittest.TestCase):
    def test_dominant_size_is_the_one_with_most_characters(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'd.pdf'
            # Un título curto grande e dúas etiquetas longas pequenas.
            _pdf(path, 300, [('Título', 14), ('Navegador web', 8), ('Servidor Apache', 8)])
            self.assertAlmostEqual(dominant_font_size(path, 'pdf'), 8 / 0.75, places=2)

    def test_scale_uses_measured_size_not_nominal(self):
        # Coma mmdc --pdfFit: o renderizador di 16 px pero a letra sae a 8 pt.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'd.pdf'
            _pdf(path, 200, [('Navegador', 8)])
            width = width_attr(path, 'pdf', 'lualatex', font_px=16.0)
            expected = 100 * 200 * (TARGET_FONT_PT / 8) / TEXTWIDTH_PT['lualatex']
            self.assertAlmostEqual(float(width[:-1]), expected, places=1)

    def test_html_width_puts_labels_at_table_size(self):
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 50">'
               '<text font-size="10.00">A</text><text font-size="10.00">B</text></svg>')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'd.svg'
            path.write_text(svg, encoding='utf-8')
            width = width_attr(path, 'svg', 'html', font_px=16.0)
            # 1 em da imaxe é a letra das táboas: o texto de 10 unidades pasa a 1 em.
            self.assertAlmostEqual(float(width[:-2]), 200 / 10, places=2)

    def test_warning_only_below_ninety_percent_of_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'd.pdf'
            _pdf(path, TEXTWIDTH_PT['lualatex'], [('Etiqueta', TARGET_FONT_PT)])
            self.assertIsNone(pdf_font_warning(path, '100%', TEXTWIDTH_PT['lualatex']))
            self.assertIsNone(pdf_font_warning(path, '91%', TEXTWIDTH_PT['lualatex']))
            self.assertIn('10.2 pt', pdf_font_warning(path, '85%', TEXTWIDTH_PT['lualatex']))
            # Ancho absoluto: 8 cm dun PDF de 472,3 pt de ancho.
            self.assertIn('obxectivo', pdf_font_warning(path, '8cm', TEXTWIDTH_PT['lualatex']))


@unittest.skipUnless(HAS_PYMUPDF and shutil.which('dot'), 'require PyMuPDF e Graphviz')
class GraphvizFontTests(unittest.TestCase):
    def test_labels_render_at_target_size_in_source_sans(self):
        import pymupdf
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = 'digraph { A [label="Navegador"]; A -> B [label="petición"]; label="Título" }'
            output = root / 'g.pdf'
            from md2pdf.diagrams.base import RenderContext
            error = GraphvizRenderer().render(shutil.which('dot'),
                RenderContext(root, 'pdf'), source, output)
            self.assertEqual(error, '')
            with pymupdf.open(output) as document:
                spans = [(span['font'], round(span['size'], 2))
                         for block in document[0].get_text('dict')['blocks']
                         for line in block.get('lines', []) for span in line['spans']
                         if span['text'].strip()]
            self.assertTrue(spans)
            self.assertEqual({size for _, size in spans}, {TARGET_FONT_PT})
            if 'SourceSans3' in subprocess.run(['fc-match', '-f', '%{file}', 'Source Sans 3'],
                                               capture_output=True, text=True).stdout:
                self.assertTrue(all(font.startswith('SourceSans3') for font, _ in spans), spans)

    def test_font_name_is_not_parsed_as_size(self):
        # «Source Sans 3» sen coma: Pango le «3» coma tamaño e cambia de familia.
        self.assertIn(',', DOT_FONT)


if __name__ == '__main__':
    unittest.main()
