import io
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from md2pdf.engines import build_lualatex_cmd
from md2pdf.converter import convert_one

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('pandoc'), 'pandoc non está instalado')
class KeepCodeTests(unittest.TestCase):
    def render(self, markdown, *args, target='latex', keep=True):
        filters = ['callouts.lua', 'terminal-blocks.lua', 'compact-code.lua']
        if keep:
            filters.append('keep-code.lua')
        filters.append('hl-lines.lua')
        result = subprocess.run(
            ['pandoc', '-f', 'markdown', '-t', target,
             *(f'--lua-filter={ROOT / f}' for f in filters), *args],
            input=markdown.encode(), capture_output=True, cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        return result.stdout if target == 'docx' else result.stdout.decode()

    @staticmethod
    def block(lines, info='java'):
        return f'```{info}\n' + '\n'.join(f'line{i};' for i in range(lines)) + '\n```\n'

    def test_default_boundary_and_local_scope(self):
        latex = self.render(self.block(12) + '\n' + self.block(13))
        self.assertEqual(latex.count(r'\begin{KeepCodeBlock}'), 1)
        self.assertEqual(latex.count(r'\end{KeepCodeBlock}'), 1)
        self.assertLess(latex.index(r'\end{KeepCodeBlock}'), latex.rindex(r'\begin{Shaded}'))
        self.assertEqual(latex.count(r'\begin{Shaded}'), 2)

    def test_metadata_yaml_and_cli(self):
        for meta in [3, 6, 20]:
            with self.subTest(threshold=meta):
                latex = self.render(f'---\ncode-keep-lines: {meta}\n---\n\n'
                                    + self.block(meta) + '\n' + self.block(meta + 1))
                self.assertEqual(latex.count(r'\begin{KeepCodeBlock}'), 1)
        self.assertNotIn(r'\begin{KeepCodeBlock}',
                         self.render(self.block(6), '-M', 'code-keep-lines=5'))

    def test_zero_disables(self):
        self.assertNotIn(r'\begin{KeepCodeBlock}',
                         self.render(self.block(1), '-M', 'code-keep-lines=0'))

    def test_invalid_metadata_uses_default(self):
        self.assertIn(r'\begin{KeepCodeBlock}',
                      self.render(self.block(12), '-M', 'code-keep-lines=invalid'))

    def test_blank_lines_count(self):
        md = '```text\na\n\nb\n```\n'
        self.assertNotIn(r'\begin{KeepCodeBlock}', self.render(md, '-M', 'code-keep-lines=2'))
        self.assertIn(r'\begin{KeepCodeBlock}', self.render(md, '-M', 'code-keep-lines=3'))

    def test_compact_terminal_and_highlight_composition(self):
        latex = self.render(self.block(6, 'bash {.compact hl="2,4-5"}'))
        markers = [r'\begin{TerminalBlock}', r'\begin{CompactBlock}',
                   r'\begin{KeepCodeBlock}', r'\fvset{highlightlines={2,4,5}}',
                   r'\begin{Shaded}', r'\end{Shaded}',
                   r'\fvset{highlightlines={}}', r'\end{KeepCodeBlock}',
                   r'\end{CompactBlock}', r'\end{TerminalBlock}']
        positions = [latex.index(marker) for marker in markers]
        self.assertEqual(positions, sorted(positions))

    def test_compact_threshold_still_independent(self):
        latex = self.render(self.block(6) + '\n' + self.block(13),
                            '-M', 'code-compact-threshold=6')
        self.assertEqual(latex.count(r'\begin{CompactBlock}'), 2)
        self.assertEqual(latex.count(r'\begin{KeepCodeBlock}'), 1)

    def test_text_and_terminal_languages(self):
        for language in ['text', 'console', 'terminal', 'bash']:
            with self.subTest(language=language):
                latex = self.render(self.block(6, language))
                self.assertIn(r'\begin{KeepCodeBlock}', latex)
                self.assertIn(r'\begin{Shaded}', latex)

    def test_callouts_and_lists(self):
        code = self.block(6, 'java {hl="2"}')
        for md in ['::: note\n\n' + code + '\n:::\n',
                   '- Exemplo:\n\n' + ''.join('  ' + line + '\n' for line in code.splitlines())]:
            with self.subTest(markdown=md):
                latex = self.render(md)
                self.assertIn(r'\begin{KeepCodeBlock}', latex)
                self.assertIn(r'\begin{Shaded}', latex)
                self.assertIn(r'\fvset{highlightlines={2}}', latex)

    def test_html_and_docx_unchanged(self):
        md = self.block(6, 'bash {.compact hl="2"}')
        self.assertEqual(self.render(md, target='html'), self.render(md, target='html', keep=False))
        for keep in [True, False]:
            with zipfile.ZipFile(io.BytesIO(self.render(md, target='docx', keep=keep))) as archive:
                xml = archive.read('word/document.xml')
            if keep:
                expected = xml
            else:
                self.assertEqual(xml, expected)

    def test_engine_filter_order(self):
        # Usar os activos da fonte, independentemente da instalación local.
        with patch('md2pdf.assets.INSTALL_DIR', ROOT):
            cmd = build_lualatex_cmd(
                tmp_path='in.md', output_path='out.pdf', template=ROOT / 'md2pdf.latex',
                toc=False, toc_depth=3, section_numbering='', lang='gl',
                papersize='a4', highlight='auto', code_keep_lines='0 # desactivar',
            )
        filters = [Path(cmd[i + 1]).name for i, arg in enumerate(cmd) if arg == '--lua-filter']
        names = ['terminal-blocks.lua', 'compact-code.lua', 'keep-code.lua', 'hl-lines.lua']
        positions = [filters.index(name) for name in names]
        self.assertEqual(positions, sorted(positions))
        self.assertIn('code-keep-lines=0', cmd)

    def test_conversion_transports_metadata_before_stripping_yaml(self):
        for front_matter, no_metadata, expected in [
            ('', False, '5'),
            ('---\ncode-keep-lines: 0\n---\n\n', False, '0'),
            ('---\ncode-keep-lines: 0 # desactivar\n---\n\n', False, '0 # desactivar'),
            ('---\ncode-keep-lines: 0\n---\n\n', True, None),
        ]:
            with self.subTest(front_matter=front_matter, no_metadata=no_metadata):
                with tempfile.TemporaryDirectory() as directory:
                    source = Path(directory) / 'example.md'
                    output = source.with_suffix('.pdf')
                    source.write_text(front_matter + '# Exemplo\n\n' + self.block(6))
                    (source.parent / 'metadata.yaml').write_text('code-keep-lines: 5\n')
                    output.write_bytes(b'fake PDF')
                    with patch('md2pdf.converter.build_lualatex_cmd', return_value=['pandoc']) as build:
                        with patch('md2pdf.converter.subprocess.run') as run:
                            run.return_value = subprocess.CompletedProcess(['pandoc'], 0, '', '')
                            self.assertTrue(convert_one(source, output, ROOT / 'md2pdf.latex',
                                                        no_metadata=no_metadata))
                    self.assertEqual(build.call_args.kwargs['code_keep_lines'], expected)


if __name__ == '__main__':
    unittest.main()
