"""Compatibilidade coas versións actuais de Pandoc, KOMA-Script e mermaid-cli."""

import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('pandoc'), 'pandoc non está instalado')
class KomaFontsizeTests(unittest.TestCase):
    def render_template(self) -> str:
        cmd = [
            'pandoc', '-f', 'markdown', '-t', 'latex', '-s',
            f'--template={ROOT / "md2pdf.latex"}',
            '-V', 'fontsize=13pt', '-V', 'papersize=a4',
        ]
        result = subprocess.run(
            cmd, input='Texto.\n', capture_output=True, text=True, cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_documentclass_uses_fontsize_key(self):
        header = self.render_template().split(']{scrartcl}')[0]
        self.assertIn('fontsize=13pt', header)
        self.assertIsNone(re.search(r'^\s*13pt,', header, re.MULTILINE))

    def compile_log(self, size_option: str) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            tex = Path(tmp) / 'proba.tex'
            tex.write_text(
                f'\\documentclass[{size_option},a4paper,parskip=half-]{{scrartcl}}\n'
                '\\begin{document}Texto.\\end{document}\n',
                encoding='utf-8',
            )
            subprocess.run(
                ['lualatex', '-interaction=nonstopmode', tex.name],
                capture_output=True, text=True, cwd=tmp, timeout=180,
            )
            log = tex.with_suffix('.log').read_text(encoding='utf-8', errors='replace')
        self.assertIn('Document Class: scrartcl', log)
        return log

    @unittest.skipUnless(shutil.which('lualatex'), 'lualatex non está instalado')
    def test_koma_does_not_switch_to_old_version(self):
        self.assertIn('version=first', self.compile_log('13pt'))
        log = self.compile_log('fontsize=13pt')
        self.assertNotIn('version=first', log)
        self.assertNotIn('deprecated option', log)


if __name__ == '__main__':
    unittest.main()
