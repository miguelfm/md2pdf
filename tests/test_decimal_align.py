import shutil
import subprocess
import unittest
from pathlib import Path

from md2pdf.metadata import _extract_md_metadata

ROOT = Path(__file__).resolve().parents[1]

OPERADORES = '''\
| Operador | Operación | Exemplo | Resultado |
|:-:|---|:-:|:-:|
| `+` | Suma | `7 + 2` | 9 |
| `*` | Multiplicación | `7 * 2` | 14 |
| `/` | División | `7 / 2` | 3.5 |
| `**` | Potencia | `7 ** 2` | 49 |
'''


@unittest.skipUnless(shutil.which('pandoc'), 'pandoc non está instalado')
class DecimalAlignTests(unittest.TestCase):
    def render(self, markdown: str, *args: str, to: str = 'latex') -> str:
        result = subprocess.run(
            ['pandoc', '-f', 'markdown', '-t', to, *args,
             f'--lua-filter={ROOT / "auto-table-widths.lua"}'],
            input=markdown, capture_output=True, text=True, cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_numeric_column_with_decimals_is_aligned(self):
        latex = self.render(OPERADORES)
        # Parte enteira sobre o oco de «14», decimal sobre o de «.5».
        self.assertIn(r'\hphantom{14}\llap{9}\rlap{}\hphantom{.5}', latex)
        self.assertIn(r'\hphantom{14}\llap{3}\rlap{.5}\hphantom{.5}', latex)
        self.assertIn(r'\hphantom{14}\llap{49}\rlap{}\hphantom{.5}', latex)
        # O aliñamento da columna segue sendo o do Markdown (centrada).
        self.assertIn(r'\begin{longtable}[]{@{}clcc@{}}', latex)

    def test_integer_only_column_is_not_changed(self):
        latex = self.render('| A | B |\n|---|---|\n| x | 1 |\n| y | 22 |\n')
        self.assertNotIn(r'\hphantom', latex)

    def test_column_with_text_is_not_changed(self):
        latex = self.render(
            '| A | B |\n|---|---|\n| x | 1.5 |\n| y | 22 |\n| z | n/d |\n')
        self.assertNotIn(r'\hphantom', latex)

    def test_empty_cells_and_decimal_comma(self):
        latex = self.render(
            '| A | B |\n|---|---|\n| x | 0,75 |\n| y |  |\n| z | -12 |\n')
        self.assertIn(r'\hphantom{-12}\llap{0}\rlap{,75}\hphantom{,75}', latex)
        self.assertIn(r'\hphantom{-12}\llap{-12}\rlap{}\hphantom{,75}', latex)

    def test_can_be_disabled_with_metadata(self):
        latex = self.render(OPERADORES, '-M', 'decimal-align=false')
        self.assertNotIn(r'\hphantom', latex)

    def test_other_formats_are_not_changed(self):
        html = self.render(OPERADORES, to='html')
        self.assertIn('<td style="text-align: center;">3.5</td>', html)


class DecimalAlignMetadataTests(unittest.TestCase):
    def test_front_matter_key_is_read(self):
        meta = _extract_md_metadata('---\ndecimal-align: false\n---\n\nTexto\n')
        self.assertEqual(meta.get('decimal-align'), 'false')


if __name__ == '__main__':
    unittest.main()
