import shutil
import subprocess
import unittest
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / 'md2pdf.latex'


@unittest.skipUnless(shutil.which('pandoc'), 'pandoc non está instalado')
class TocDepthTests(unittest.TestCase):
    def render(self, depth=None):
        command = ['pandoc', '--standalone', '--to', 'latex',
                   '--template', str(TEMPLATE), '--toc']
        if depth is not None:
            command += ['--toc-depth', str(depth)]
        result = subprocess.run(command, input='# Tema\n\nTexto.\n',
                                text=True, capture_output=True, check=True)
        return result.stdout

    def test_explicit_depth_reaches_latex(self):
        for depth in (1, 2, 3):
            with self.subTest(depth=depth):
                self.assertTrue(
                    r'\setcounter{tocdepth}{' + str(depth) + '}'
                    in self.render(depth), f'profundidade {depth} ausente')

    def test_default_remains_three(self):
        self.assertTrue(r'\setcounter{tocdepth}{3}' in self.render(),
                        'profundidade por defecto ausente')


@unittest.skipUnless(all(shutil.which(tool) for tool in
                       ('pandoc', 'lualatex', 'pdftotext', 'pdfinfo')),
                     'faltan ferramentas de PDF')
class TocPaginationTests(unittest.TestCase):
    def test_short_and_long_indexes_keep_their_content(self):
        import os
        import signal
        import sys
        import tempfile
        project = TEMPLATE.parent
        for count in (3, 70):
            with self.subTest(entries=count), tempfile.TemporaryDirectory() as temp:
                source = Path(temp) / 'indice.md'
                source.write_text('# Proba do índice\n\n' + '\n\n'.join(
                    f'## Tema {number}\n\nTexto de proba.'
                    for number in range(count)))
                process = subprocess.Popen(
                    [sys.executable, '-m', 'md2pdf', str(source)],
                    cwd=project, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, text=True, start_new_session=True)
                try:
                    stdout, stderr = process.communicate(timeout=45)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.communicate()
                    self.fail('o índice non rematou en 45 segundos')
                self.assertEqual(process.returncode, 0, stdout + stderr)
                pdf = source.with_suffix('.pdf')
                text = subprocess.check_output(
                    ['pdftotext', '-layout', str(pdf), '-'], text=True)
                first = text.split('\f')[0]
                self.assertIn('Proba do índice', first)
                self.assertIn('Índice', first)
                self.assertIn('Tema 0', first)
                self.assertGreaterEqual(text.count(f'Tema {count - 1}'), 2)
                info = subprocess.check_output(['pdfinfo', str(pdf)], text=True)
                pages = int(info.split('Pages:')[1].splitlines()[0])
                self.assertLess(pages, 30)


if __name__ == '__main__':
    unittest.main()
