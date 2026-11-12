import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILTERS = ['auto-table-widths.lua', 'small-table.lua', 'keep-with-next.lua',
           'columns.lua', 'callouts.lua', 'figure-captions.lua']

TABLES = '''
:::: columns

::: {column_attrs_1}

| Referencia | Obxecto |
|---|:---:|
| `start` | A |
| `other` | B |

:::

::: {column_attrs_2}

| Obxecto | Clase | Estado |
|:---:|---|---|
| A | `Point` | (3, 3) |
| B | `Point` | (5, 5) |
| C | `Point` | (0, 0) |

:::

::::
'''


def columns(first='.column', second='.column'):
    return (TABLES.replace('{column_attrs_1}', '{' + first + '}')
                  .replace('{column_attrs_2}', '{' + second + '}'))


@unittest.skipUnless(shutil.which('pandoc'), 'pandoc non está instalado')
class ColumnsTests(unittest.TestCase):
    def render(self, markdown, target='latex'):
        result = subprocess.run(
            ['pandoc', '-f', 'markdown', '-t', target,
             *(f'--lua-filter={ROOT / f}' for f in FILTERS)],
            input=markdown.encode(), capture_output=True, cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        return result.stdout.decode()

    def test_columns_become_top_aligned_minipages(self):
        latex = self.render(columns())
        widths = re.findall(r'\\begin\{minipage\}\[t\]\{([\d.]+)\\linewidth\}', latex)
        # Sen width, as dúas reparten o ancho menos a separación.
        self.assertEqual(widths, ['0.480', '0.480'])
        self.assertIn(r'\par\noindent\begin{minipage}', latex)
        self.assertIn(r'\end{minipage}\hfill\begin{minipage}', latex)
        self.assertIn(r'\end{minipage}\par', latex)
        self.assertEqual(latex.count(r'\begin{tabular}'), 2)

    def test_no_blank_line_between_minipages(self):
        # Unha liña baleira entre as columnas remataría o parágrafo.
        latex = self.render(columns())
        self.assertNotRegex(latex, r'\\end\{minipage\}%?\n\s*\n\\hfill')

    def test_explicit_width_and_share(self):
        latex = self.render(columns('.column width="30%"', '.column'))
        widths = re.findall(r'\{([\d.]+)\\linewidth\}', latex)
        self.assertEqual(widths, ['0.300', '0.660'])

    def test_single_reserve_before_columns(self):
        latex = self.render(columns())
        reserves = [int(n) for n in re.findall(r'\\Needspace\{(\d+)\\baselineskip\}', latex)]
        # A da táboa máis alta, fóra das minipages.
        self.assertEqual(len(reserves), 1)
        self.assertLess(latex.index(r'\Needspace'), latex.index(r'\begin{minipage}'))
        alone = self.render(TABLES.split('::: {column_attrs_2}')[1]
                            .split(':::')[0])
        self.assertEqual(reserves[0], int(re.search(r'\\Needspace\{(\d+)', alone).group(1)))

    def test_lead_in_paragraph_goes_with_columns(self):
        latex = self.render('Ao final do programa:\n' + columns())
        before = latex[:latex.index('Ao final do programa:')].rstrip()
        self.assertRegex(before, r'\\Needspace\{\d+\\baselineskip\}$')
        self.assertEqual(latex.count(r'\Needspace'), 1)

    def test_caption_in_column_uses_captionof(self):
        markdown = columns().replace('| `other` | B |\n',
                                     '| `other` | B |\n\n: Referencias {#tbl:refs}\n', 1)
        latex = self.render(markdown + '\nVéxase @tbl:refs.\n')
        self.assertIn(r'\captionof{table}{Referencias}\label{tbl:refs}' + '\n'
                      r'\noindent\begin{tabular}', latex)
        self.assertNotIn('longtable', latex)
        self.assertNotIn(r'\caption{', latex)
        self.assertNotIn(r'\endfirsthead', latex)
        self.assertIn(r'\ref*{tbl:refs}', latex)

    def test_long_table_in_column_is_tabular(self):
        rows = ''.join(f'| r{i} | {i} |\n' for i in range(10))
        markdown = (':::: columns\n\n::: column\n\n| a | b |\n|---|---|\n' + rows
                    + '\n:::\n\n::: column\n\nTexto.\n\n:::\n\n::::\n')
        latex = self.render(markdown)
        self.assertNotIn('longtable', latex)
        self.assertIn(r'\begin{tabular}', latex)

    def test_caption_outside_columns_stays_longtable(self):
        latex = self.render('| a | b |\n|---|---|\n| 1 | 2 |\n\n: Pé\n')
        self.assertIn(r'\begin{longtable}', latex)
        self.assertNotIn('captionof', latex)

    def test_html_keeps_pandoc_divs(self):
        html = self.render(columns('.column width="30%"', '.column'), target='html')
        self.assertIn('<div class="columns">', html)
        self.assertIn('<div class="column" style="width:30%;">', html)
        self.assertNotIn('minipage', html)


if __name__ == '__main__':
    unittest.main()
