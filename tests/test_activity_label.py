import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from md2pdf.engines.lualatex import _build_activity_label, _tex_escape

LONG_LABEL = ('U1: Arquitecturas e ferramentas de programación '
              'e inserción de código en páxinas web')


class ActivityLabelTests(unittest.TestCase):
    def test_no_break_space_becomes_tie(self):
        self.assertEqual(_tex_escape('páxinas\N{NO-BREAK SPACE}web'),
                         'páxinas~web')

    def test_rules_are_capped_before_drawing(self):
        latex = _build_activity_label(LONG_LABEL, print_mode=False)
        cap = r'\ifdim\wd0>\linewidth'
        self.assertIn(cap, latex)
        self.assertLess(latex.index(cap), latex.index(r'\rule'))

    @unittest.skipUnless(shutil.which('lualatex'), 'lualatex non está instalado')
    def test_long_label_does_not_overflow_the_line(self):
        doc = (
            '\\documentclass{article}\n'
            '\\usepackage{xcolor}\n'
            '\\colorlet{heading-section}{blue!45!black}\n'
            '\\begin{document}\n'
            + _build_activity_label(LONG_LABEL, print_mode=False)
            + 'Texto.\n\\end{document}\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / 'label.tex'
            src.write_text(doc, encoding='utf-8')
            result = subprocess.run(
                ['lualatex', '-interaction=nonstopmode', src.name],
                cwd=tmp, capture_output=True, text=True,
            )
            log = (Path(tmp) / 'label.log').read_text(
                encoding='utf-8', errors='replace')
        self.assertEqual(result.returncode, 0, log[-2000:])
        self.assertFalse('Overfull \\hbox' in log,
                         'o rótulo ou as súas raias saen da liña')


if __name__ == '__main__':
    unittest.main()
