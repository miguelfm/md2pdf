import importlib.util
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from md2pdf.engines import build_lualatex_cmd
from md2pdf.engines.lualatex import (
    ACTIVITY_LABEL_MARK, _activity_label_block, _build_activity_label, _tex_escape,
)

ROOT = Path(__file__).resolve().parents[1]

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


    def test_label_block_reserves_the_label_and_the_section(self):
        label = _build_activity_label('A01: Tarefa 1', print_mode=False)
        block = _activity_label_block(label, before_section=True)
        lines = block.splitlines()
        self.assertEqual(lines[:3], ['```{=latex}', ACTIVITY_LABEL_MARK,
                                     r'\Needspace{14\baselineskip}'])
        self.assertLess(block.index(r'\Needspace'), block.index(r'\begin{center}'))
        # Ao final do documento non hai cabeceira despois: só o rótulo.
        end = _activity_label_block(label, before_section=False)
        self.assertIn(r'\Needspace{6\baselineskip}', end)


LABEL_BLOCK = _activity_label_block(
    _build_activity_label('A01: Tarefa 1', print_mode=False), before_section=True)


@unittest.skipUnless(shutil.which('pandoc'), 'pandoc non está instalado')
class ActivityLabelReserveTests(unittest.TestCase):
    """As reservas dos filtros non quedan entre o rótulo e a súa cabeceira."""

    def render(self, markdown, filters):
        result = subprocess.run(
            ['pandoc', '-f', 'markdown', '-t', 'latex',
             *(f'--lua-filter={ROOT / f}' for f in filters)],
            input=markdown.encode(), capture_output=True, cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        return result.stdout.decode()

    def reserve_before_label(self, latex):
        before = latex[:latex.index(ACTIVITY_LABEL_MARK)].rstrip()
        match = re.search(r'\\Needspace\{(\d+)\\baselineskip\}$', before)
        return int(match.group(1)) if match else None

    def test_lead_in_reserve_goes_before_the_label(self):
        code = '```java\n' + '\n'.join(f'line{i};' for i in range(6)) + '\n```\n'
        latex = self.render(LABEL_BLOCK + '## Tarefa\n\nEste é o código:\n\n' + code,
                            ['keep-with-next.lua'])
        # Parágrafo e código (9), a cabeceira (3) e o rótulo (6).
        self.assertEqual(self.reserve_before_label(latex), 9 + 3 + 6)
        between = latex[latex.index(r'\end{center}'):latex.index(r'\subsection{Tarefa}')]
        self.assertNotIn(r'\Needspace', between)

    def test_small_table_reserve_goes_before_the_label(self):
        table = '| A | B |\n|---|---|\n| 1 | x |\n| 2 | y |\n'
        latex = self.render(LABEL_BLOCK + '## Tarefa\n\n' + table, ['small-table.lua'])
        # Dúas filas e cinco liñas, que xa contan a cabeceira, e o rótulo (6).
        self.assertEqual(self.reserve_before_label(latex), 2 + 5 + 6)

    @unittest.skipUnless(shutil.which('lualatex') and importlib.util.find_spec('pymupdf'),
                         'precisa LuaLaTeX e PyMuPDF')
    def test_pdf_keeps_the_label_with_its_section(self):
        """Sen a reserva, o rótulo queda ao pé da páxina 1; con ela, pasa á 2."""
        import pymupdf

        filler = ''.join(f'Liña de recheo {i:02d}: texto para achegar o rótulo ao pé.\\\n'
                         for i in range(LABEL_FILLER_LINES)) + 'Fin do recheo.\n\n'
        section = '## SECCION\n\nPrimeiro parágrafo da sección.\n'
        old_block = LABEL_BLOCK.replace(ACTIVITY_LABEL_MARK + '\n', '').replace(
            '\\Needspace{14\\baselineskip}\n', '')

        def pages(block):
            with tempfile.TemporaryDirectory() as directory:
                source = Path(directory) / 'example.md'
                output = source.with_suffix('.pdf')
                source.write_text(filler + block + section)
                with patch('md2pdf.assets.INSTALL_DIR', ROOT):
                    command = build_lualatex_cmd(
                        tmp_path=str(source), output_path=str(output),
                        template=ROOT / 'md2pdf.latex', toc=False, toc_depth=3,
                        section_numbering='', lang='gl', papersize='a4',
                        highlight=str(ROOT / 'drake-jb.theme'),
                    )
                result = subprocess.run(command, capture_output=True, text=True,
                                        cwd=ROOT, timeout=180)
                self.assertEqual(result.returncode, 0, result.stderr)
                found = {}
                with pymupdf.open(output) as document:
                    for number, page in enumerate(document, 1):
                        text = page.get_text()
                        for marker in ['A01', 'SECCION']:
                            if marker in text:
                                found.setdefault(marker, number)
                return found

        self.assertEqual(pages(old_block), {'A01': 1, 'SECCION': 2},
                         'O recheo xa non deixa o rótulo ao pé: axustar LABEL_FILLER_LINES')
        self.assertEqual(pages(LABEL_BLOCK), {'A01': 2, 'SECCION': 2})


# Liñas de recheo que deixan o rótulo ao pé da páxina 1 sen sitio para a sección.
LABEL_FILLER_LINES = 33


if __name__ == '__main__':
    unittest.main()
