import shutil
import subprocess
import unittest
from pathlib import Path

from md2pdf.metadata import _extract_md_metadata

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('pandoc'), 'pandoc non está instalado')
class TerminalBlocksTests(unittest.TestCase):
    def render_latex(self, markdown: str, *extra_args: str) -> str:
        cmd = [
            'pandoc', '-f', 'markdown', '-t', 'latex',
            f'--lua-filter={ROOT / "terminal-blocks.lua"}',
            f'--lua-filter={ROOT / "hl-lines.lua"}',
            *extra_args,
        ]
        result = subprocess.run(
            cmd, input=markdown, capture_output=True, text=True, cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def render_html(self, markdown: str, *extra_args: str) -> str:
        cmd = [
            'pandoc', '-f', 'markdown', '-t', 'html',
            f'--lua-filter={ROOT / "terminal-blocks.lua"}',
            *extra_args,
        ]
        result = subprocess.run(
            cmd, input=markdown, capture_output=True, text=True, cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_terminal_languages_wrapped_in_terminalblock_latex(self):
        for lang in ('bash', 'sh', 'zsh', 'console', 'terminal', 'powershell', 'pwsh', 'cmd'):
            md = f'```{lang}\necho "test"\n```\n'
            latex = self.render_latex(md)
            self.assertIn(r'\begin{TerminalBlock}', latex, f'Fallou para {lang}')
            self.assertIn(r'\end{TerminalBlock}', latex, f'Fallou para {lang}')
            self.assertIn(r'\begin{Shaded}', latex)

    def test_non_terminal_languages_not_wrapped(self):
        for lang in ('php', 'python', 'javascript', 'sql', 'json', 'yaml', 'css', 'html'):
            md = f'```{lang}\n$x = 1;\n```\n'
            latex = self.render_latex(md)
            self.assertNotIn(r'\begin{TerminalBlock}', latex, f'Envolveu erradamente {lang}')
            self.assertNotIn(r'\end{TerminalBlock}', latex, f'Envolveu erradamente {lang}')
            self.assertIn(r'\begin{Shaded}', latex)

    def test_unclassed_code_not_wrapped(self):
        md = '```\ntexto plano sen linguaxe\n```\n'
        latex = self.render_latex(md)
        self.assertNotIn(r'\begin{TerminalBlock}', latex)
        self.assertIn(r'\begin{verbatim}', latex)

    def test_terminal_block_with_hl_lines(self):
        md = '```bash {hl="1"}\nls -la\ncd /tmp\n```\n'
        latex = self.render_latex(md)
        self.assertIn(r'\begin{TerminalBlock}', latex)
        self.assertIn(r'\fvset{highlightlines={1}}', latex)
        self.assertIn(r'\end{TerminalBlock}', latex)

    def test_html_receives_terminal_class(self):
        md = '```bash\nls -la\n```\n'
        html = self.render_html(md)
        self.assertIn('terminal', html)
        self.assertIn('bash', html)

    def test_can_be_disabled_via_metadata(self):
        md = '```bash\nls -la\n```\n'
        latex = self.render_latex(md, '-M', 'terminal-blocks=false')
        self.assertNotIn(r'\begin{TerminalBlock}', latex)
        self.assertIn(r'\begin{Shaded}', latex)

    def test_metadata_extraction(self):
        md = '---\ntitle: Proba\nterminal-blocks: false\n---\nCorpo'
        meta = _extract_md_metadata(md)
        self.assertEqual(meta.get('terminal-blocks'), 'false')


if __name__ == '__main__':
    unittest.main()
