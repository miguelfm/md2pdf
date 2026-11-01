import importlib.util
import io
import re
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from md2pdf.engines import build_lualatex_cmd

ROOT = Path(__file__).resolve().parents[1]
FILTERS = ['small-table.lua', 'keep-with-next.lua', 'callouts.lua']


@unittest.skipUnless(shutil.which('pandoc'), 'pandoc non está instalado')
class KeepWithNextTests(unittest.TestCase):
    def render(self, markdown, *args, target='latex', filters=FILTERS):
        result = subprocess.run(
            ['pandoc', '-f', 'markdown', '-t', target,
             *(f'--lua-filter={ROOT / f}' for f in filters), *args],
            input=markdown.encode(), capture_output=True, cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        return result.stdout if target == 'docx' else result.stdout.decode()

    @staticmethod
    def code(lines, info='java'):
        return f'```{info}\n' + '\n'.join(f'line{i};' for i in range(lines)) + '\n```\n'

    def reserve_before(self, latex, text):
        """A reserva que vai xusto antes do parágrafo, ou None."""
        before = latex[:latex.index(text)].rstrip()
        match = re.search(r'\\Needspace\{(\d+)\\baselineskip\}$', before)
        return int(match.group(1)) if match else None

    def test_code_block_after_lead_in(self):
        latex = self.render('Este é o código:\n\n' + self.code(6))
        # Unha liña de parágrafo, seis de código e dúas de marco.
        self.assertEqual(self.reserve_before(latex, 'Este é o código:'), 9)
        self.assertEqual(latex.count(r'\Needspace'), 1)

    def test_lead_in_with_emphasis(self):
        latex = self.render('**Erros habituais:**\n\n- un\n- outro\n')
        self.assertEqual(self.reserve_before(latex, r'\textbf{Erros habituais:}'), 3)

    def test_paragraph_without_colon_is_untouched(self):
        for text in ['Este é o código.', 'Remata en dous puntos: non']:
            with self.subTest(text=text):
                self.assertNotIn(r'\Needspace', self.render(text + '\n\n' + self.code(3)))

    def test_long_paragraph_counts_its_lines(self):
        text = ' '.join(['palabra'] * 40) + ':'
        latex = self.render(text + '\n\n' + self.code(3))
        lines = -(-len(text) // 85)
        self.assertEqual(self.reserve_before(latex, 'palabra palabra'), lines + 3 + 2)

    def test_long_code_reserves_only_its_start(self):
        latex = self.render('Programa:\n\n' + self.code(30))
        self.assertEqual(self.reserve_before(latex, 'Programa:'), 1 + 4 + 2)

    def test_long_code_lines_count_as_they_wrap(self):
        # 30 palabras de 7 letras: 8 por liña de 66 caracteres, catro liñas.
        words = ' '.join(['palabra'] * 30)
        latex = self.render(f'Saída:\n\n```text\n{words}\nfin\n```\n')
        self.assertEqual(self.reserve_before(latex, 'Saída:'), 1 + 4 + 1 + 2)
        # Unha palabra máis longa ca a liña parte en calquera punto.
        latex = self.render('Saída:\n\n```text\n' + 'x' * 150 + '\n```\n')
        self.assertEqual(self.reserve_before(latex, 'Saída:'), 1 + 3 + 2)
        # A sangría conta na primeira liña.
        line = '    ' + ' '.join(['abcdefghi'] * 7)
        latex = self.render(f'Saída:\n\n```text\n{line}\n```\n')
        self.assertEqual(self.reserve_before(latex, 'Saída:'), 1 + 2 + 2)

    def test_wrapped_lines_do_not_change_the_keep_limit(self):
        # keep-code.lua decide coas liñas da fonte: un bloque de 12 liñas
        # segue sendo curto aínda que as súas liñas partan.
        long_line = ' '.join(['palabra'] * 20)
        block = '\n'.join([long_line] * 12)
        latex = self.render(f'Saída:\n\n```text\n{block}\n```\n')
        self.assertEqual(self.reserve_before(latex, 'Saída:'), 1 + 12 * 3 + 2)
        block = '\n'.join([long_line] * 13)
        latex = self.render(f'Saída:\n\n```text\n{block}\n```\n')
        self.assertEqual(self.reserve_before(latex, 'Saída:'), 1 + 4 + 2)

    def test_reserve_never_goes_before_the_document_title(self):
        # md2pdf usa --shift-heading-level-by=-1: o # inicial é o título, e
        # Pandoc só o toma se é o primeiro bloque.
        md = '# Título\n\nCódigo:\n\n' + self.code(3)
        latex = self.render(md, '-s', '--shift-heading-level-by=-1')
        self.assertIn(r'\title{Título}', latex)
        self.assertEqual(self.reserve_before(latex, 'Código:'), 1 + 3 + 2)

    def test_code_keep_lines_metadata(self):
        latex = self.render('Programa:\n\n' + self.code(8), '-M', 'code-keep-lines=5')
        self.assertEqual(self.reserve_before(latex, 'Programa:'), 1 + 4 + 2)
        latex = self.render('Programa:\n\n' + self.code(8), '-M', 'code-keep-lines=0')
        self.assertEqual(self.reserve_before(latex, 'Programa:'), 1 + 4 + 2)

    def test_lists(self):
        for md in ['Unha lista:\n\n- curto\n- outro\n',
                   'Unha lista:\n\n1. curto\n2. outro\n']:
            with self.subTest(markdown=md):
                self.assertEqual(self.reserve_before(self.render(md), 'Unha lista:'), 3)
        long_item = ' '.join(['palabra'] * 80)
        latex = self.render(f'Unha lista:\n\n- {long_item}\n')
        self.assertEqual(self.reserve_before(latex, 'Unha lista:'), 1 + 1 + 4)

    def test_reserve_goes_before_headers(self):
        # Niveis 2 e 3, como as seccións de md2pdf: o nivel 1 é o título.
        latex = self.render('## Sección\n\n### Apartado\n\nCódigo:\n\n' + self.code(2))
        # Entre a cabeceira e o parágrafo, \Needspace deixaría un punto de corte.
        self.assertIsNone(self.reserve_before(latex, 'Código:'))
        self.assertEqual(self.reserve_before(latex, r'\subsection'), 1 + 2 + 2 + 3 + 3)

    def test_nested_lists_and_callouts(self):
        md = ('1. Engade esta liña:\n\n   ```java\n   int x = 1;\n   ```\n\n'
              '::: note\n\nDentro do recadro:\n\n```text\nx\n```\n\n:::\n')
        latex = self.render(md)
        self.assertEqual(self.reserve_before(latex, 'Engade esta liña:'), 4)
        self.assertEqual(self.reserve_before(latex, 'Dentro do recadro:'), 4)

    def test_diagrams_are_not_code(self):
        for info in ['{.mermaid}', '{.dot}']:
            with self.subTest(info=info):
                latex = self.render('Figura:\n\n' + self.code(3, info))
                self.assertNotIn(r'\Needspace', latex)

    def test_metadata_disables(self):
        latex = self.render('Código:\n\n' + self.code(3), '-M', 'keep-with-next=false')
        self.assertNotIn(r'\Needspace', latex)

    def test_small_table_reserve_before_lead_in(self):
        md = 'Unha táboa:\n\n| A | B |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n'
        latex = self.render(md)
        # Dúas filas + 5, como small-table.lua, e a liña do parágrafo.
        self.assertEqual(self.reserve_before(latex, 'Unha táboa:'), 2 + 5 + 1)
        self.assertEqual(latex.count(r'\Needspace'), 1)
        self.assertIn(r'\begin{tabular}', latex)

    def test_small_table_with_wrapped_rows_before_lead_in(self):
        long_text = 'texto longo que ocupa varias liñas na cela ' * 2
        rows = ''.join(f'| {i} | {long_text} |\n' for i in range(3))
        latex = self.render('Unha táboa:\n\n| A | B |\n|---|---|\n' + rows)
        # Máis ca unha liña por fila: as celas parten.
        self.assertGreater(self.reserve_before(latex, 'Unha táboa:'), 3 + 5 + 1)
        self.assertIn(r'\begin{tabular}', latex)

    def test_code_cells_count_with_the_code_width(self):
        # Como na tarefa U3T5 de DWCS: código de 45 caracteres nunha columna
        # de media páxina. A 5 pt por carácter collería nunha liña; o
        # código, a 7,1 pt, parte en dúas.
        call = "`uploadError(['error' => 0, 'size' => 1000])`"
        rows = ''.join(f'| {call} | `{i}` |\n' for i in range(3))
        md = ('Os casos:\n\n| Chamada | Esperado |\n'
              '|----------------------------------------------------|'
              '----------------------------------------------|\n' + rows)
        filters = ['auto-table-widths.lua', 'small-table.lua', 'keep-with-next.lua']
        latex = self.render(md, filters=filters)
        self.assertIn(r'\begin{tabular}', latex)
        self.assertGreater(self.reserve_before(latex, 'Os casos:'), 3 + 5 + 1)

    def test_header_styling_does_not_count_as_text(self):
        # Como na rúbrica de DWCS: unha columna estreita de puntos. O LaTeX
        # co que auto-table-widths destaca a cabeceira leva
        # \color{heading-section}; contado coma texto, a cabeceira dunha
        # columna estreita partía en tres liñas e a reserva pasaba de 13 a 15.
        text = ('Todos os apartados levan as saídas reais da propia VM, '
                'completas e pegadas como texto.')
        rows = ''.join(f'| {i} | {text} |\n' for i in range(4))
        md = 'Peso máximo: 4 puntos.\n\n| Puntos | Descrición |\n|---|---|\n' + rows
        filters = ['auto-table-widths.lua', 'small-table.lua']
        latex = self.render(md, filters=filters)
        # Catro filas de dúas liñas: 4 + 5 + ceil(4 × 0,9).
        self.assertIn('\\Needspace{13\\baselineskip}\n\\noindent\\begin{tabular}', latex)

    def test_large_table_reserve_before_lead_in(self):
        rows = ''.join(f'| {i} | x |\n' for i in range(9))
        latex = self.render('Unha táboa:\n\n| A | B |\n|---|---|\n' + rows)
        self.assertIsNotNone(self.reserve_before(latex, 'Unha táboa:'))
        self.assertEqual(latex.count(r'\Needspace'), 1)
        self.assertIn(r'\begin{longtable}', latex)

    def test_table_after_header_and_lead_in(self):
        md = '## Apartado\n\nUnha táboa:\n\n| A |\n|---|\n| 1 |\n'
        latex = self.render(md)
        self.assertEqual(self.reserve_before(latex, r'\subsection'), 1 + 5 + 1 + 3)
        self.assertEqual(latex.count(r'\Needspace'), 1)

    def test_html_and_docx_unchanged(self):
        md = 'Código:\n\n' + self.code(3) + '\nLista:\n\n- a\n'
        self.assertEqual(self.render(md, target='html'),
                         self.render(md, target='html', filters=[]))
        with zipfile.ZipFile(io.BytesIO(self.render(md, target='docx'))) as archive:
            with_filter = archive.read('word/document.xml')
        with zipfile.ZipFile(io.BytesIO(self.render(md, target='docx', filters=[]))) as archive:
            self.assertEqual(archive.read('word/document.xml'), with_filter)

    def test_engine_filter_order(self):
        with patch('md2pdf.assets.INSTALL_DIR', ROOT):
            cmd = build_lualatex_cmd(
                tmp_path='in.md', output_path='out.pdf', template=ROOT / 'md2pdf.latex',
                toc=False, toc_depth=3, section_numbering='', lang='gl',
                papersize='a4', highlight='auto',
            )
        filters = [Path(cmd[i + 1]).name for i, arg in enumerate(cmd) if arg == '--lua-filter']
        names = ['small-table.lua', 'keep-with-next.lua', 'callouts.lua', 'keep-code.lua']
        positions = [filters.index(name) for name in names]
        self.assertEqual(positions, sorted(positions))

    def test_metadata_transport(self):
        from md2pdf.metadata import _extract_md_metadata
        meta = _extract_md_metadata('---\nkeep-with-next: false # sen reserva\n---\n\nTexto\n')
        self.assertEqual(meta['keep-with-next'], 'false # sen reserva')
        with patch('md2pdf.assets.INSTALL_DIR', ROOT):
            cmd = build_lualatex_cmd(
                tmp_path='in.md', output_path='out.pdf', template=ROOT / 'md2pdf.latex',
                toc=False, toc_depth=3, section_numbering='', lang='gl',
                papersize='a4', highlight='auto', keep_with_next=meta['keep-with-next'],
            )
        self.assertIn('keep-with-next=false', cmd)
        self.assertNotIn('keep-with-next=false', ' '.join(cmd).replace(
            'keep-with-next=false', '', 1))

    @unittest.skipUnless(shutil.which('lualatex') and importlib.util.find_spec('pymupdf'),
                         'precisa LuaLaTeX e PyMuPDF')
    def test_pdf_keeps_lead_in_with_code(self):
        """Sen o filtro, o parágrafo queda só ao pé da páxina 1; con el, pasa á 2."""
        import pymupdf

        filler = ''.join(f'Liña de recheo {i:02d}: texto para achegar o parágrafo ao pé.\\\n'
                         for i in range(FILLER_LINES)) + 'Fin do recheo.\n\n'
        body = filler + 'PARAGRAFO de entrada:\n\n' + self.code(10).replace('line0', 'PRIMEIRA')

        def pages(front_matter):
            with tempfile.TemporaryDirectory() as directory:
                source = Path(directory) / 'example.md'
                output = source.with_suffix('.pdf')
                source.write_text(front_matter + body)
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
                        for marker in ['PARAGRAFO', 'PRIMEIRA']:
                            if marker in text:
                                found.setdefault(marker, number)
                return found

        without = pages('---\nkeep-with-next: false\n---\n\n')
        self.assertEqual(without, {'PARAGRAFO': 1, 'PRIMEIRA': 2},
                         'O recheo xa non deixa o parágrafo ao pé: axustar FILLER_LINES')
        self.assertEqual(pages(''), {'PARAGRAFO': 2, 'PRIMEIRA': 2})


# Liñas de recheo que deixan o parágrafo de entrada na última liña da páxina 1.
FILLER_LINES = 37


if __name__ == '__main__':
    unittest.main()
