import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

import md2pdf
from md2pdf.config import ENGINES, DEFAULT_ENGINE
from md2pdf.engines import build_docx_cmd, build_html_cmd, build_lualatex_cmd


class PackageTests(unittest.TestCase):
    def test_package_imports_and_active_engines(self):
        self.assertIsNotNone(md2pdf)
        self.assertEqual(ENGINES, ('lualatex', 'docx', 'html'))
        self.assertEqual(DEFAULT_ENGINE, 'lualatex')
        self.assertTrue(callable(build_lualatex_cmd))
        self.assertTrue(callable(build_docx_cmd))
        self.assertTrue(callable(build_html_cmd))
        self.assertIsNone(importlib.util.find_spec('md2pdf.engines.typst'))

    def test_module_cli_help_loads_without_import_errors(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, '-m', 'md2pdf', '--help'],
            cwd=root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('lualatex', result.stdout)
        self.assertIn('docx', result.stdout)
        self.assertIn('html', result.stdout)
        self.assertIn('--serif', result.stdout)
        self.assertNotIn('typst', result.stdout.lower())

    def test_default_and_serif_font_cmd(self):
        root = Path(__file__).resolve().parents[1]
        template = root / 'md2pdf.latex'
        # Default: sans-serif
        cmd_sans = build_lualatex_cmd(
            tmp_path='in.md', output_path='out.pdf', template=template,
            toc=False, toc_depth=3, section_numbering='', lang='gl',
            papersize='a4', highlight='auto',
        )
        self.assertIn('-V', cmd_sans)
        mainfont_idx = cmd_sans.index('-V')
        self.assertTrue(any('mainfont=Source Sans' in str(c) for c in cmd_sans))
        self.assertTrue(any('body-font=sans' in str(c) for c in cmd_sans))

        # Serif mode
        cmd_serif = build_lualatex_cmd(
            tmp_path='in.md', output_path='out.pdf', template=template,
            toc=False, toc_depth=3, section_numbering='', lang='gl',
            papersize='a4', highlight='auto', serif=True,
        )
        self.assertTrue(any('mainfont=Source Serif' in str(c) for c in cmd_serif))
        self.assertTrue(any('body-font=serif' in str(c) for c in cmd_serif))


if __name__ == '__main__':
    unittest.main()
