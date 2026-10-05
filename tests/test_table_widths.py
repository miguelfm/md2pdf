import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Pandoc reparte (\linewidth - 2(n-1)\tabcolsep) entre as n columnas; en A4 con
# marxes de 22 mm, \linewidth = 472.3pt e \tabcolsep = 6pt.
LINE_PT = 472.3
TABCOLSEP_PT = 6

TIPOS_PHP = '''\
| Tipo | Nome en PHP | Valores | Tamaño | Exemplo |
|---|---|---|---|---|
| Enteiro | `int` | Números sen parte decimal, positivos ou negativos | 64 bits na maioría de plataformas | `$idade = 17;` |
| Decimal | `float` | Números con parte decimal ou en notación científica | 64 bits (precisión dobre IEEE 754) | `$prezo = 19.95;` |
| Cadea | `string` | Secuencia de caracteres entre comiñas simples ou dobres | Limitado pola memoria dispoñible | `$nome = "Ana";` |
| Booleano | `bool` | Só pode valer `true` ou `false` | 1 byte | `$activo = true;` |
'''


AMBITOS_INI = '''\
| Ámbito | Onde se pode cambiar |
|---|---|
| `PHP_INI_SYSTEM` | No `php.ini` ou na configuración do servidor web |
| `PHP_INI_PERDIR` | Tamén na configuración por directorio, pero non con `ini_set()` |
| `PHP_INI_USER` | Desde o código con `ini_set()` ou nun ficheiro `.user.ini` |
| `PHP_INI_ALL` | En calquera dos lugares anteriores |
'''


@unittest.skipUnless(shutil.which('pandoc'), 'pandoc non está instalado')
class TableWidthTests(unittest.TestCase):
    def render_latex(self, markdown: str) -> str:
        result = subprocess.run(
            ['pandoc', '-f', 'markdown', '-t', 'latex',
             f'--lua-filter={ROOT / "auto-table-widths.lua"}'],
            input=markdown, capture_output=True, text=True, cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def widths(self, markdown: str) -> list[float]:
        return [float(w) for w in
                re.findall(r'\\real\{([0-9.]+)\}', self.render_latex(markdown))]

    def test_short_words_column_fits_its_longest_word(self):
        widths = self.widths(TIPOS_PHP)
        avail = LINE_PT - 2 * TABCOLSEP_PT * (len(widths) - 1)
        # «Booleano» mide ~47pt e «Decimal» 44pt en Source Serif 4 \small.
        self.assertGreaterEqual(widths[0] * avail, 47)
        self.assertAlmostEqual(sum(widths), 1.0, places=3)

    def test_space_comes_from_columns_with_more_text(self):
        widths = self.widths(TIPOS_PHP)
        # As columnas curtas («Nome en PHP», «Exemplo») conservan o ancho; o
        # que gaña a primeira sae das de máis texto («Valores», «Tamaño»),
        # que xa parten en dúas liñas.
        self.assertAlmostEqual(widths[1], 0.1080, places=3)
        self.assertAlmostEqual(widths[4], 0.1340, places=3)
        self.assertLess(widths[2] + widths[3], 0.4160 + 0.2600)

    def test_minimums_that_do_not_fit_keep_the_smaller_ones(self):
        widths = self.widths('''\
| Dato | Apache con mod_php | Servidor integrado | Terminal |
|---|---|---|---|
| php.ini habitual en Debian | /etc/php/8.5/apache2/php.ini | /etc/php/8.5/cli/php.ini | /etc/php/8.5/cli/php.ini |
| memory_limit | Valor observado en Apache | Valor observado no servidor integrado | Valor observado en CLI |
''')
        avail = LINE_PT - 2 * TABCOLSEP_PT * (len(widths) - 1)
        # Os catro mínimos suman máis da liña. En sans-serif «memory_limit»
        # mide ~72.3pt (75.5pt en serif) e cabe enteira; as rutas de cli (120.9pt),
        # que TeX non pode dividir, como moito invaden 8pt do espazo entre
        # columnas; a ruta de apache2, a máis longa, é a única que se parte.
        self.assertGreaterEqual(widths[0] * avail, 72.0)
        self.assertGreaterEqual(widths[2] * avail, 120.9 - 8)
        self.assertGreaterEqual(widths[3] * avail, 120.9 - 8)
        self.assertAlmostEqual(sum(widths), 1.0, places=3)

    def test_minimums_with_serif_font(self):
        widths = self.widths('''---
body-font: serif
---
| Dato | Apache con mod_php | Servidor integrado | Terminal |
|---|---|---|---|
| php.ini habitual en Debian | /etc/php/8.5/apache2/php.ini | /etc/php/8.5/cli/php.ini | /etc/php/8.5/cli/php.ini |
| memory_limit | Valor observado en Apache | Valor observado no servidor integrado | Valor observado en CLI |
''')
        avail = LINE_PT - 2 * TABCOLSEP_PT * (len(widths) - 1)
        # Con fonte serif («body-font: serif»), «memory_limit» mide 75.5pt
        self.assertGreaterEqual(widths[0] * avail, 75.5)
        self.assertGreaterEqual(widths[2] * avail, 120.9 - 8)
        self.assertGreaterEqual(widths[3] * avail, 120.9 - 8)
        self.assertAlmostEqual(sum(widths), 1.0, places=3)

    def test_equal_dashes_stay_automatic(self):
        rows = ('| Enteiro | Números sen parte decimal, positivos ou negativos, '
                'ata o límite da plataforma | 8 |\n')
        for sep in ('|---|---|---|', '|:---:|---|---:|', '|:---|:---:|---|',
                    '|:-|-|-:|', '| :--- | --- |  ---: |'):
            with self.subTest(sep=sep):
                widths = self.widths('| A | B | C |\n' + sep + '\n' + rows)
                # O cálculo automático dá á columna de texto moito máis ca
                # un terzo; con anchos manuais (guións iguais) serían ~1/3.
                self.assertGreater(widths[1], 0.5)

    def test_different_dashes_are_manual_widths(self):
        widths = self.widths(
            '| A | B | C |\n|------|--|------------|\n'
            '| Enteiro | Números sen parte decimal, positivos ou negativos, '
            'ata o límite da plataforma | 8 |\n')
        # Pandoc: ancho ∝ guións (máis dous puntos) → 6/20, 2/20, 12/20.
        self.assertEqual(len(widths), 3)
        for got, expected in zip(widths, (0.3, 0.1, 0.6)):
            self.assertAlmostEqual(got, expected, places=3)

    def test_table_that_fits_keeps_natural_width(self):
        # «Resto da división enteira» ten máis de 20 caracteres, pero a
        # táboa enteira cabe sen partir en menos do 85 % da liña.
        latex = self.render_latex('''\
| Operador | Operación | Exemplo | Resultado |
|:-:|---|:-:|:-:|
| `+` | Suma | `7 + 2` | 9 |
| `%` | Resto da división enteira | `7 % 2` | 1 |
''')
        self.assertIn(r'\begin{longtable}[]{@{}clcc@{}}', latex)
        self.assertIn(r'\setlength{\LTleft}{\fill}', latex)

    def test_natural_width_ignores_pandoc_relative_widths(self):
        # Unha liña de máis de 72 caracteres fai que Pandoc dea anchos
        # relativos; se a táboa cabe, bórranse e quedan columnas l.
        latex = self.render_latex(
            '| Superglobal | Contido |\n|---|---|\n'
            '| `$_SERVER` | Datos da petición e do servidor: método, ruta, '
            'cabeceiras |\n| `$_GET` | Valores enviados na cadea de consulta |\n')
        self.assertIn(r'\begin{longtable}[]{@{}ll@{}}', latex)

    def test_table_to_fill_keeps_full_width(self):
        latex = self.render_latex(
            '| Dato | Apache | Terminal |\n|---|---|---|\n'
            '| SAPI | | |\n| memory_limit | | |\n')
        self.assertIn(r'\real{', latex)
        self.assertNotIn(r'\setlength{\LTleft}{\fill}', latex)

    def test_short_table_keeps_natural_width(self):
        latex = self.render_latex(
            '| A | B | A && B |\n|---|---|---|\n'
            '| V | V | V |\n| V | F | F |\n| F | F | F |\n')
        self.assertNotIn(r'\real{', latex)
        self.assertIn(r'\setlength{\LTleft}{\fill}', latex)

    def test_short_identifier_is_not_split_at_underscore(self):
        latex = self.render_latex(AMBITOS_INI)
        self.assertIn(r'\mbox{\texttt{PHP\_INI\_SYSTEM}}', latex)
        widths = [float(w) for w in
                  re.findall(r'\\real\{([0-9.]+)\}', latex)]
        avail = LINE_PT - 2 * TABCOLSEP_PT * (len(widths) - 1)
        # Co corpo en Source Sans 3, a Source Code Pro mide 7,118pt por
        # carácter: a columna ten que caber enteiro PHP_INI_SYSTEM.
        self.assertGreaterEqual(widths[0] * avail, 14 * 7.118)

    def test_short_body_expression_is_not_split(self):
        latex = self.render_latex('O operador `$c ? $a : $b` escolle un valor.\n')
        self.assertIn(r'\mbox{\texttt{\$c ? \$a : \$b}}', latex)

    def test_table_expression_keeps_break_points(self):
        latex = self.render_latex('| Expresión |\n|---|\n| `$c ? $a : $b` |\n')
        self.assertNotIn(r'\mbox{\texttt{\$c', latex)
        self.assertIn(r'?\discretionary{}{}{}', latex)

    def test_long_identifier_can_split_at_underscore(self):
        latex = self.render_latex('Texto `zend_exception_ignore_args` longo.\n')
        self.assertIn(r'\_\discretionary{}{}{}', latex)


@unittest.skipUnless(
    shutil.which('pandoc') and shutil.which('lualatex')
    and shutil.which('pdftotext'),
    'pandoc, lualatex ou pdftotext non están instalados')
class TableWidthPdfTests(unittest.TestCase):
    def test_example_table_has_no_hyphenated_words(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / 'taboa.md'
            pdf = Path(tmp) / 'taboa.pdf'
            src.write_text(TIPOS_PHP, encoding='utf-8')
            run = subprocess.run(
                [sys.executable, '-m', 'md2pdf', '--no-toc', '-o', str(pdf),
                 str(src)],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            text = subprocess.run(['pdftotext', '-layout', str(pdf), '-'],
                                  capture_output=True, text=True).stdout
        for word in ('Enteiro', 'Decimal', 'Booleano'):
            self.assertIn(word, text)

    def test_identifier_column_keeps_each_row_on_one_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / 'ambitos.md'
            pdf = Path(tmp) / 'ambitos.pdf'
            src.write_text(AMBITOS_INI, encoding='utf-8')
            run = subprocess.run(
                [sys.executable, '-m', 'md2pdf', '--no-toc', '-o', str(pdf),
                 str(src)],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            bbox = subprocess.run(['pdftotext', '-bbox', str(pdf), '-'],
                                  capture_output=True, text=True).stdout
        y = {word: float(ymin) for ymin, word in re.findall(
            r'yMin="([0-9.]+)"[^>]*>([^<]+)</word>', bbox)}
        # Cada identificador vai na mesma liña ca o texto da súa fila.
        self.assertAlmostEqual(y['PHP_INI_SYSTEM'], y['No'], delta=2)
        self.assertAlmostEqual(y['PHP_INI_PERDIR'], y['Tamén'], delta=2)


if __name__ == '__main__':
    unittest.main()
