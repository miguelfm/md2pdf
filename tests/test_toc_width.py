import contextlib
import io
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from md2pdf.converter import convert_one
from md2pdf.engines.lualatex import _build_toc_width_header
from md2pdf.metadata import _extract_md_metadata

ROOT = Path(__file__).resolve().parents[1]
TOOLS = all(shutil.which(tool) for tool in ('pandoc', 'lualatex'))


class TocHeaderTests(unittest.TestCase):
    def test_lua_path_is_hex_encoded(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / 'índice # con espazos'
            folder.mkdir()
            script = folder / 'toc-width.lua'
            script.write_text('return {}', encoding='utf-8')
            header = folder / 'toc-width.tex'
            header.write_text('@MD2PDF_TOC_LUA_HEX@', encoding='utf-8')
            with patch('md2pdf.engines.lualatex._find_asset',
                       side_effect=lambda name: folder / name):
                result = Path(_build_toc_width_header())
            try:
                self.assertEqual(bytes.fromhex(result.read_text()).decode(),
                                 script.resolve().as_posix())
            finally:
                result.unlink()

    def test_missing_asset_does_not_break_old_installations(self):
        with patch('md2pdf.engines.lualatex._find_asset', return_value=None):
            self.assertIsNone(_build_toc_width_header())

    def test_front_matter_can_disable_automatic_width(self):
        self.assertEqual(_extract_md_metadata('---\ntoc-auto-width: false\n---\n\n# Tema\n')['toc-auto-width'], 'false')


class TocRetryTests(unittest.TestCase):
    def run_results(self, results):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'test.md'
            source.write_text('# Tema\n\nTexto.\n', encoding='utf-8')
            output = source.with_suffix('.pdf')
            output.write_bytes(b'%PDF-test')
            observed = []

            def execute(command, **kwargs):
                observed.append(list(command))
                return results[len(observed)-1]

            with patch('md2pdf.converter.build_lualatex_cmd',
                       return_value=['pandoc', str(source), '-o', str(output)]), \
                 patch('md2pdf.converter.prepare_lualatex_extras',
                       side_effect=lambda **kwargs: (kwargs['processed'], [], True)), \
                 patch('md2pdf.converter.subprocess.run', side_effect=execute), \
                 contextlib.redirect_stdout(io.StringIO()), \
                 contextlib.redirect_stderr(io.StringIO()):
                result = convert_one(source, output, ROOT / 'md2pdf.latex')
            for command in observed[1:]:
                self.assertIn('-H', command)
                self.assertFalse(Path(command[-1]).exists(), 'o temporal debe borrarse')
            return result, observed

    def test_unstable_references_retry_with_fixed_width(self):
        warning = SimpleNamespace(returncode=0, stdout='', stderr='[WARNING] MD2PDF_TOC_UNSTABLE')
        stable = SimpleNamespace(returncode=0, stdout='', stderr='')
        result, calls = self.run_results([warning, stable])
        self.assertTrue(result)
        self.assertEqual(len(calls), 2)

    def test_repeated_instability_is_a_failure(self):
        warning = SimpleNamespace(returncode=0, stdout='', stderr='[WARNING] MD2PDF_TOC_UNSTABLE')
        result, calls = self.run_results([warning, warning])
        self.assertFalse(result)
        self.assertEqual(len(calls), 2)

    def test_latex_error_is_not_retried(self):
        error = SimpleNamespace(returncode=1, stdout='', stderr='! LaTeX Error: test')
        result, calls = self.run_results([error])
        self.assertFalse(result)
        self.assertEqual(len(calls), 1)


@unittest.skipUnless(TOOLS, 'precisa Pandoc e LuaLaTeX')
class TocWidthPdfTests(unittest.TestCase):
    def convert(self, directory, name, text):
        source = Path(directory) / (name + '.md')
        source.write_text(text, encoding='utf-8')
        result = subprocess.run([sys.executable, '-m', 'md2pdf', str(source)],
                                cwd=ROOT, capture_output=True, text=True, timeout=90)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('MD2PDF_TOC_UNSTABLE', result.stderr)
        return source.with_suffix('.pdf'), result

    @staticmethod
    def entry_gap(page, title):
        groups = {}
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                for span in line['spans']:
                    groups.setdefault(round(span['origin'][1], 1), []).append(span)
        for spans in groups.values():
            spans.sort(key=lambda s: s['bbox'][0])
            matches = [s for s in spans if title in s['text']]
            if matches:
                self_title = max(s['bbox'][2] for s in matches)
                page_number = spans[-1]
                if page_number['text'].strip().isdigit():
                    return (page_number['bbox'][0]-self_title)*25.4/72
        raise AssertionError('o título non aparece enteiro nunha liña do índice')

    def test_default_optimizes_and_optout_preserves_reference(self):
        import pymupdf
        title = 'Métodos que consultan e métodos que modifican'
        body = '# Proba\n\n## Introdución\n\nTexto.\n\n## Usar un obxecto\n\n### ' + title + '\n\nTexto.\n'
        with tempfile.TemporaryDirectory() as directory:
            auto_path, result = self.convert(directory, 'automatico', body)
            fixed_path, _ = self.convert(directory, 'fixo', '---\ntoc-auto-width: false\n---\n\n' + body)
            auto, fixed = pymupdf.open(auto_path), pymupdf.open(fixed_path)
            auto_gap = self.entry_gap(auto[0], title)
            fixed_gap = self.entry_gap(fixed[0], title)
            self.assertGreaterEqual(auto_gap, 5.7)
            self.assertLess(auto_gap, fixed_gap-5)
            self.assertNotIn('keeping reference width', result.stderr)
            self.assertEqual(len(auto), len(fixed))
            for index in range(1, len(auto)):
                self.assertEqual(auto[index].get_pixmap().samples, fixed[index].get_pixmap().samples)

    def test_actual_three_digit_page_numbers_are_reserved(self):
        import pymupdf
        text = '# Cifras\n\n\\setcounter{page}{999}\n\n## Introdución\n\nTexto.\n\n## Remate\n\nTexto.\n'
        with tempfile.TemporaryDirectory() as directory:
            path, result = self.convert(directory, 'cifras', text)
            pdf = pymupdf.open(path)
            self.assertIn('999', pdf[0].get_text())
            self.assertGreaterEqual(self.entry_gap(pdf[0], 'Introdución'), 5.7)
            self.assertNotIn('keeping reference width', result.stderr)

    def test_vertical_math_falls_back_explicitly(self):
        text = '# Fórmula\n\n## Fracción $\\frac{1}{2}$\n\nTexto.\n'
        with tempfile.TemporaryDirectory() as directory:
            path, result = self.convert(directory, 'formula', text)
            self.assertTrue(path.exists())
            self.assertIn('unsupported', result.stderr)

    def test_stable_pass_reuses_the_verified_width(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.md'
            source.write_text('# Caché\n\n## Introdución\n\nTexto.\n\n## Remate\n\nTexto.\n', encoding='utf-8')
            tex = source.with_name('cache.tex')
            prepared = subprocess.run([sys.executable, '-m', 'md2pdf', str(source), '-o', str(tex)],
                                      cwd=ROOT, capture_output=True, text=True, timeout=30)
            self.assertEqual(prepared.returncode, 0, prepared.stderr)
            reports = []
            for _ in range(3):
                result = subprocess.run(['lualatex', '-interaction=nonstopmode', '-halt-on-error', tex.name],
                                        cwd=directory, capture_output=True, text=True, timeout=45)
                self.assertEqual(result.returncode, 0, result.stdout[-2000:])
                log = tex.with_suffix('.log').read_text(encoding='utf-8')
                reports.append(re.sub(r'\s+', '', log))
            self.assertIn('cached=true', reports[-1])
            self.assertIn('fallback=0', reports[-1])
            second = int(re.search(r'trials=(\d+)', reports[1]).group(1))
            third = int(re.search(r'trials=(\d+)', reports[2]).group(1))
            self.assertLess(third, second)
            self.assertLessEqual(third, 4)


if __name__ == '__main__':
    unittest.main()
