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
        self.assertNotIn('typst', result.stdout.lower())


if __name__ == '__main__':
    unittest.main()
