import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from md2pdf.diagrams.common import image_block
from md2pdf.diagrams.processor import DiagramStats, process_diagrams
from md2pdf.diagrams.renderers import D2Renderer
from md2pdf.diagrams.validation import validate_output, pdf_font_warning
from md2pdf.converter import convert_one

SVG = '<svg viewBox="0 0 100 50"><path d="M0 0 L100 50"/></svg>'


def _pdf(text: str | None = 'Diagrama') -> bytes:
    """PDF dunha páxina, con texto ou en branco (para probar a validación)."""
    import pymupdf
    with pymupdf.open() as document:
        page = document.new_page(width=120, height=60)
        if text:
            page.insert_text((10, 30), text)
        return document.tobytes()


class ReliabilityTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec('pymupdf'), 'require PyMuPDF')
    def test_invalid_cache_regenerates_and_bad_success_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = '```d2\na -> b\n```'
            def render(renderer, executable, context, content, output):
                output.write_bytes(_pdf())
                return ''
            with patch('md2pdf.diagrams.processor.cache_dir', return_value=root), \
                 patch('md2pdf.diagrams.processor.shutil.which', return_value='/fake/d2'), \
                 patch.object(D2Renderer, 'render', render):
                _, stats = process_diagrams(source, 'lualatex')
                self.assertEqual(stats.new['d2'], 1)
                cached = next(root.glob('*.pdf'))
                cached.write_bytes(b'%PDF-1.7 truncado')
                _, stats = process_diagrams(source, 'lualatex')
                self.assertEqual(stats.new['d2'], 1)
                self.assertTrue(stats.warnings['d2'])
                validate_output(cached, 'pdf')   # rexenerado e válido
                cached.unlink()
                def invalid(renderer, executable, context, content, output):
                    output.write_bytes(_pdf(None))   # páxina en branco
                    return ''
                with patch.object(D2Renderer, 'render', invalid):
                    out, stats = process_diagrams(source, 'lualatex')
                self.assertEqual(out, source)
                self.assertTrue(stats.errors['d2'])
                self.assertFalse(list(root.glob('*.pdf')))

    @unittest.skipUnless(importlib.util.find_spec('pymupdf'), 'require PyMuPDF')
    def test_launcher_update_invalidates_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            executable = root / 'd2'
            executable.write_text('old')
            calls = []
            def render(renderer, executable, context, content, output):
                calls.append(content)
                output.write_bytes(_pdf())
                return ''
            with patch('md2pdf.diagrams.processor.cache_dir', return_value=root), \
                 patch('md2pdf.diagrams.processor.shutil.which', return_value=str(executable)), \
                 patch.object(D2Renderer, 'render', render):
                for _ in range(2):
                    process_diagrams('```d2\na -> b\n```', 'lualatex')
                executable.write_text('new version')
                process_diagrams('```d2\na -> b\n```', 'lualatex')
            self.assertEqual(len(calls), 2)

    def test_invalid_formats(self):
        with tempfile.TemporaryDirectory() as tmp:
            for fmt, data in [('svg', b'<svg><defs><path/></defs></svg>'),
                              ('svg', b'<svg viewBox="0 0 0 20"><path/></svg>'),
                              ('pdf', b'%PDF-1.7 truncated'),
                              ('png', b'\x89PNG\r\n\x1a\n')]:
                path = Path(tmp) / ('out.' + fmt)
                path.write_bytes(data)
                with self.subTest(fmt=fmt, data=data), self.assertRaises(ValueError):
                    validate_output(path, fmt)

    @unittest.skipUnless(importlib.util.find_spec('pymupdf'), 'require PyMuPDF')
    def test_real_pdf_blank_and_legibility(self):
        import pymupdf
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'out.pdf'
            with pymupdf.open() as doc:
                doc.new_page(width=600, height=100)
                doc.save(path)
            with self.assertRaisesRegex(ValueError, 'baleiro'):
                validate_output(path, 'pdf')
            path.unlink()
            with pymupdf.open() as doc:
                doc.new_page(width=600, height=100).insert_text((20, 30), 'Experimental', fontsize=8)
                doc.save(path)
            validate_output(path, 'pdf')
            self.assertIn('6.4 pt', pdf_font_warning(path, '100%', 483.7))
            path.unlink()
            with pymupdf.open() as doc:
                doc.new_page(width=600, height=100).insert_text((20, 30), 'Night', color=(1, 1, 1))
                doc.save(path)
            validate_output(path, 'pdf')  # Texto branco para fondos escuros.

    def test_strict_stops_before_pandoc_on_diagram_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'input.md'
            source.write_text('# Title\n')
            stats = DiagramStats(new={'d2': 0}, cached={'d2': 0}, errors={'d2': ['failure']})
            with patch('md2pdf.converter.process_diagrams', return_value=('', stats)), \
                 patch('md2pdf.converter.subprocess.run') as run, \
                 redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertFalse(convert_one(source, Path(tmp)/'out.pdf', None,
                                             strict=True, no_metadata=True))
                run.assert_not_called()

    def test_paths_with_spaces_and_parentheses(self):
        self.assertIn('![](<', image_block(Path('/tmp/my charts (1)/a.svg'), '80%', 'lualatex'))
        self.assertIn('my%20charts%20(1)', image_block(Path('/tmp/my charts (1)/a.svg'), '80%', 'lualatex'))

    @unittest.skipIf(sys.platform == 'win32', 'lanzador POSIX')
    def test_installer_wrapper_quotes_paths_and_keeps_python(self):
        spec = importlib.util.spec_from_file_location('installer', Path(__file__).parents[1]/'install-md2pdf.py')
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "teacher's files"
            root.mkdir()
            package = root / 'md2pdf'
            package.mkdir()
            (package/'__init__.py').write_text('')
            (package/'__main__.py').write_text('import sys\ndef main():\n print(sys.executable)\n print(sys.argv[1])\n')
            bin_dir = root / 'bin'
            bin_dir.mkdir()
            with redirect_stdout(io.StringIO()):
                installer._make_linux_wrapper(bin_dir, root)
            result = subprocess.run([str(bin_dir/'md2pdf'), 'two words'], capture_output=True, text=True, check=True)
            self.assertEqual(result.stdout.splitlines(), [sys.executable, 'two words'])
