import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from md2pdf.engines import build_lualatex_cmd

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('pandoc'), 'pandoc non está instalado')
class ProportionalCompactTests(unittest.TestCase):
    def render(self, markdown, target='latex', *args):
        result = subprocess.run(
            ['pandoc', '-f', 'markdown', '-t', target,
             f'--lua-filter={ROOT / "terminal-blocks.lua"}',
             f'--lua-filter={ROOT / "compact-code.lua"}',
             f'--lua-filter={ROOT / "keep-code.lua"}',
             f'--lua-filter={ROOT / "hl-lines.lua"}', *args],
            input=markdown, text=True, capture_output=True, cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_proportional_option_and_local_scope(self):
        markdown = ('```text {.compact compact-leading="proportional"}\n'
                    'A\nB\n```\n\n```text {.compact}\nC\nD\n```\n')
        latex = self.render(markdown)
        self.assertEqual(latex.count(r'\begin{ProportionalCompactBlock}'), 1)
        self.assertEqual(latex.count(r'\begin{CompactBlock}'), 1)
        self.assertLess(latex.index(r'\end{ProportionalCompactBlock}'),
                        latex.index(r'\begin{CompactBlock}'))

    def test_terminal_keep_and_highlighting(self):
        latex = self.render('```bash {.compact compact-leading="proportional" '
                            'hl="2"}\na\nb\n```\n')
        markers = [r'\begin{TerminalBlock}', r'\begin{ProportionalCompactBlock}',
                   r'\begin{KeepCodeBlock}', r'\fvset{highlightlines={2}}',
                   r'\begin{Shaded}', r'\end{Shaded}',
                   r'\fvset{highlightlines={}}', r'\end{KeepCodeBlock}',
                   r'\end{ProportionalCompactBlock}', r'\end{TerminalBlock}']
        positions = [latex.index(marker) for marker in markers]
        self.assertEqual(positions, sorted(positions))

    def test_html_class_and_disable(self):
        markdown = '```text {.compact compact-leading="proportional"}\na\n```\n'
        self.assertIn('compact-proportional', self.render(markdown, 'html'))
        disabled = self.render(markdown, 'latex', '-M', 'code-compact=false')
        self.assertNotIn(r'\begin{ProportionalCompactBlock}', disabled)
        plain = self.render('```text {compact-leading="proportional"}\na\n```')
        self.assertNotIn(r'\begin{ProportionalCompactBlock}', plain)

    @unittest.skipUnless(shutil.which('lualatex') and
                         importlib.util.find_spec('pymupdf'),
                         'precisa LuaLaTeX e PyMuPDF')
    def test_pdf_preserves_font_leading_ratio(self):
        import pymupdf

        markdown = ('```text\nNORMAL_ONE\nNORMAL_TWO\n```\n\n'
                    '```text {.compact}\nDENSE_ONE\nDENSE_TWO\n```\n\n'
                    '```text {.compact compact-leading="proportional"}\n'
                    'SCALED_ONE\nSCALED_TWO\n```\n\n'
                    '```text\nAFTER_ONE\nAFTER_TWO\n```\n')
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'example.md'
            output = source.with_suffix('.pdf')
            source.write_text(markdown)
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
            lines = {}
            with pymupdf.open(output) as document:
                for page in document:
                    for block in page.get_text('dict')['blocks']:
                        for line in block.get('lines', []):
                            spans = line['spans']
                            text = ''.join(span['text'] for span in spans)
                            lines[text] = (spans[0]['size'], spans[0]['origin'][1])

        def measure(prefix):
            first, second = lines[prefix + '_ONE'], lines[prefix + '_TWO']
            return first[0], second[1] - first[1]

        normal_size, normal_gap = measure('NORMAL')
        dense_size, dense_gap = measure('DENSE')
        scaled_size, scaled_gap = measure('SCALED')
        after_size, after_gap = measure('AFTER')
        self.assertAlmostEqual(scaled_size, dense_size, delta=0.01)
        self.assertLess(scaled_size, normal_size)
        self.assertGreater(scaled_gap, dense_gap)
        self.assertAlmostEqual(scaled_gap,
                               normal_gap * scaled_size / normal_size,
                               delta=0.02,
                               msg=f'normal={(normal_size, normal_gap)}, '
                                   f'proporcional={(scaled_size, scaled_gap)}')
        self.assertAlmostEqual(after_size, normal_size, delta=0.01)
        self.assertAlmostEqual(after_gap, normal_gap, delta=0.02)


if __name__ == '__main__':
    unittest.main()
