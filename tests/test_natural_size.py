"""Tamaño natural dos diagramas PDF que non levan a páxina á vista."""
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from md2pdf.diagrams.common import natural_size_px

SIZE = (374 / 0.75, 576 / 0.75)


class NaturalSizeTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec('pymupdf'), 'require PyMuPDF')
    def test_pdf_with_object_streams(self):
        # O cairo de Graphviz en Windows garda a páxina nun fluxo comprimido
        import pymupdf
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'diagrama.pdf'
            with pymupdf.open() as document:
                document.new_page(width=374, height=576)
                document.save(path, use_objstms=1, garbage=3, deflate=True)
            self.assertNotIn(b'/MediaBox', path.read_bytes())
            with patch('md2pdf.diagrams.common.subprocess.run',
                       side_effect=AssertionError('non debe chamar a pdfinfo')):
                self.assertEqual(natural_size_px(path, 'pdf'), SIZE)

    def test_pdfinfo_output_in_cp1252(self):
        # pdfinfo en Windows escribe a data co fuso horario en cp1252
        real_run = subprocess.run
        script = ("import sys; sys.stdout.buffer.write("
                  "'CreationDate: Hora est\\xe1ndar romance\\n"
                  "Page size: 374 x 576 pts\\n'.encode('cp1252'))")

        def fake_pdfinfo(command, **kwargs):
            return real_run([sys.executable, '-c', script], **kwargs)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'diagrama.pdf'
            path.write_bytes(b'%PDF-1.7\n')
            with patch.dict(sys.modules, {'pymupdf': None}), \
                 patch('md2pdf.diagrams.common.subprocess.run',
                       side_effect=fake_pdfinfo):
                self.assertEqual(natural_size_px(path, 'pdf'), SIZE)


if __name__ == '__main__':
    unittest.main()
