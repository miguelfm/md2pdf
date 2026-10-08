import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('pandoc'), 'pandoc non está instalado')
class HighlightingTests(unittest.TestCase):
    def render(self, markdown: str, output_format: str = 'latex') -> str:
        args = [
            'pandoc', '-f', 'markdown', '-t', output_format,
            f'--lua-filter={ROOT / "hl-lines.lua"}',
        ]
        if output_format == 'latex':
            args.extend(['-s', f'--template={ROOT / "md2pdf.latex"}'])
        result = subprocess.run(
            args, input=markdown, capture_output=True, text=True,
            cwd=ROOT, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_only_highlighted_block_keeps_pandoc_definitions(self):
        latex = self.render('```java {hl="1"}\nint x = 12;\n```\n')
        self.assertIn(r'\DefineVerbatimEnvironment{Highlighting}', latex)
        self.assertIn(r'\newcommand{\DataTypeTok}', latex)
        self.assertIn(r'\begin{Highlighting}', latex)

    def test_line_groups_are_reset_before_the_next_block(self):
        latex = self.render(
            '```java {hl="1,3-4"}\nint x = 12;\n\n'
            'if (x < 0) {\n    x = 0;\n}\n```\n\n'
            '```java\nint y = 20;\n```\n'
        )
        self.assertIn(r'\fvset{highlightlines={1,3,4}}', latex)
        reset = latex.index(r'\fvset{highlightlines={}}')
        self.assertLess(latex.index(r'\end{Highlighting}'), reset)
        self.assertLess(reset, latex.rindex(r'\begin{Highlighting}'))

    def test_html_preserves_code_and_highlight_attribute(self):
        html = self.render('```java {hl="1"}\nint x = 12;\n```\n', 'html5')
        self.assertIn('data-hl="1"', html)
        self.assertIn('int', html)
        self.assertIn('12', html)

    def test_mark_loads_support_without_a_code_block(self):
        latex = self.render('[palabra]{.mark}\n\n[`x < 0`]{.mark}\n')
        self.assertIn(r'\usepackage[soul]{lua-ul}', latex)
        self.assertIn(r'\hl{palabra}', latex)
        self.assertIn(r'\hl{\mbox{\texttt{', latex)

    def test_plain_document_does_not_load_mark_support(self):
        self.assertNotIn('lua-ul', self.render('Texto sen marcas.\n'))

    @unittest.skipUnless(shutil.which('lualatex'), 'lualatex non está instalado')
    def test_pdf_conversion_of_previous_failures(self):
        samples = {
            'highlighted': (
                '```java {.compact hl="1-2"}\n'
                'int x = 12;\nSystem.out.println(x);\n```\n\n'
                '```bash {hl="1"}\npwd\n```\n'
            ),
            'marked': '[palabra]{.mark}\n\n[`x < 0 || x > 100`]{.mark}\n',
        }
        with tempfile.TemporaryDirectory() as tmp:
            for name, markdown in samples.items():
                with self.subTest(name=name):
                    source = Path(tmp) / f'{name}.md'
                    source.write_text(markdown, encoding='utf-8')
                    result = subprocess.run(
                        [sys.executable, '-m', 'md2pdf', '--plain',
                         '--no-metadata', str(source)],
                        capture_output=True, text=True, cwd=ROOT, timeout=120,
                    )
                    self.assertEqual(
                        result.returncode, 0, result.stdout + result.stderr,
                    )
                    self.assertTrue(source.with_suffix('.pdf').is_file())


if __name__ == '__main__':
    unittest.main()
