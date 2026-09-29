import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('pandoc'), 'pandoc non está instalado')
class CompactCodeTests(unittest.TestCase):
    def render_latex(self, markdown: str, *extra_args: str) -> str:
        cmd = [
            'pandoc', '-f', 'markdown', '-t', 'latex',
            f'--lua-filter={ROOT / "terminal-blocks.lua"}',
            f'--lua-filter={ROOT / "compact-code.lua"}',
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
            f'--lua-filter={ROOT / "compact-code.lua"}',
            *extra_args,
        ]
        result = subprocess.run(
            cmd, input=markdown, capture_output=True, text=True, cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_compact_class_wrapped_in_compactblock_latex(self):
        md = '```python {.compact}\ndef test():\n    return 42\n```\n'
        latex = self.render_latex(md)
        self.assertIn(r'\begin{CompactBlock}', latex)
        self.assertIn(r'\end{CompactBlock}', latex)
        self.assertIn(r'\begin{Shaded}', latex)

    def test_compacto_class_wrapped_in_compactblock_latex(self):
        md = '```python {.compacto}\ndef test():\n    return 42\n```\n'
        latex = self.render_latex(md)
        self.assertIn(r'\begin{CompactBlock}', latex)
        self.assertIn(r'\end{CompactBlock}', latex)

    def test_compact_attribute_wrapped_in_compactblock_latex(self):
        md = '```python {compact=true}\ndef test():\n    return 42\n```\n'
        latex = self.render_latex(md)
        self.assertIn(r'\begin{CompactBlock}', latex)
        self.assertIn(r'\end{CompactBlock}', latex)

    def test_uncompact_code_not_wrapped(self):
        md = '```python\ndef test():\n    return 42\n```\n'
        latex = self.render_latex(md)
        self.assertNotIn(r'\begin{CompactBlock}', latex)
        self.assertNotIn(r'\end{CompactBlock}', latex)
        self.assertIn(r'\begin{Shaded}', latex)

    def test_threshold_triggers_compact_latex(self):
        lines = '\n'.join(f'x_{i} = {i}' for i in range(10))
        md = f'```python\n{lines}\n```\n'
        # Limiar en 8 liñas: o bloque ten 10 -> debe ser compacto
        latex = self.render_latex(md, '-M', 'code-compact-threshold=8')
        self.assertIn(r'\begin{CompactBlock}', latex)
        self.assertIn(r'\end{CompactBlock}', latex)

    def test_below_threshold_not_compact_latex(self):
        lines = '\n'.join(f'x_{i} = {i}' for i in range(5))
        md = f'```python\n{lines}\n```\n'
        # Limiar en 10 liñas: o bloque ten 5 -> non debe ser compacto
        latex = self.render_latex(md, '-M', 'code-compact-threshold=10')
        self.assertNotIn(r'\begin{CompactBlock}', latex)

    def test_global_disable_via_metadata(self):
        md = '```python {.compact}\ndef test():\n    return 42\n```\n'
        latex = self.render_latex(md, '-M', 'code-compact=false')
        self.assertNotIn(r'\begin{CompactBlock}', latex)

    def test_composition_with_terminal_blocks(self):
        md = '```bash {.compact}\nls -la\n```\n'
        latex = self.render_latex(md)
        self.assertIn(r'\begin{TerminalBlock}', latex)
        self.assertIn(r'\begin{CompactBlock}', latex)
        self.assertIn(r'\end{CompactBlock}', latex)
        self.assertIn(r'\end{TerminalBlock}', latex)

    def test_composition_with_hl_lines(self):
        md = '```python {.compact hl="1"}\ndef test():\n    return 42\n```\n'
        latex = self.render_latex(md)
        self.assertIn(r'\begin{CompactBlock}', latex)
        self.assertIn(r'\fvset{highlightlines={1}}', latex)
        self.assertIn(r'\end{CompactBlock}', latex)

    def test_html_receives_compact_class(self):
        md = '```python {.compact}\ndef test():\n    return 42\n```\n'
        html = self.render_html(md)
        self.assertIn('compact', html)
        self.assertIn('python', html)

    def test_html_uncompact_code_no_compact_class(self):
        md = '```python\ndef test():\n    return 42\n```\n'
        html = self.render_html(md)
        self.assertNotIn('compact', html)


if __name__ == '__main__':
    unittest.main()
