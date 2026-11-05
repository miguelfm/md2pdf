"""Ficheiros adxuntos con attach.lua: [texto](ruta){.attach}."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'class Demo {\n    // Comentario con tiles: ñ, á\n}\n'


def has_tex_package(name):
    if not shutil.which('kpsewhich'):
        return False
    result = subprocess.run(['kpsewhich', f'{name}.sty'],
                            capture_output=True, text=True)
    return result.returncode == 0 and result.stdout.strip() != ''


@unittest.skipUnless(shutil.which('pandoc'), 'pandoc non está instalado')
class AttachFilterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        (self.dir / 'code' / 'A8').mkdir(parents=True)
        (self.dir / 'code' / 'A8' / 'Demo.java').write_text(SOURCE)
        (self.dir / 'code' / 'A8' / 'U2T4_usuario.java').write_text(SOURCE)
        (self.dir / 'data.bin').write_bytes(b'\x00\x01')

    def tearDown(self):
        self.tmp.cleanup()

    def pandoc(self, markdown, target='latex'):
        return subprocess.run(
            ['pandoc', '-f', 'markdown', '-t', target,
             f'--lua-filter={ROOT / "attach.lua"}'],
            input=markdown, capture_output=True, text=True, cwd=self.dir)

    def test_latex_uses_basename_and_text_type(self):
        result = self.pandoc(
            'O programa [`code/A8/Demo.java`](code/A8/Demo.java){.attach}.')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            r'\mdattachfile{mimetype=text/plain,ucfilespec={Demo.java},'
            r'description={Demo.java}}{code/A8/Demo.java}'
            r'{\texttt{code/A8/Demo.java}}', result.stdout)

    def test_unknown_extension_and_explicit_mimetype(self):
        result = self.pandoc('[a](data.bin){.attach} '
                             '[b](data.bin){.attach mimetype=image/png}')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('mimetype=application/octet-stream', result.stdout)
        self.assertIn('mimetype=image/png', result.stdout)

    def test_ordinary_links_are_untouched(self):
        result = self.pandoc('[Demo](code/A8/Demo.java)')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('mdattachfile', result.stdout)
        self.assertIn(r'\href{code/A8/Demo.java}{Demo}', result.stdout)

    def test_missing_file_stops_conversion(self):
        result = self.pandoc('[x](code/A8/Missing.java){.attach}')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('non existe o ficheiro adxunto code/A8/Missing.java',
                      result.stderr)

    def test_url_stops_conversion(self):
        result = self.pandoc('[x](https://example.org/Demo.java){.attach}')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('ten que ser un ficheiro local', result.stderr)

    def test_html_is_a_download_link(self):
        result = self.pandoc('[Demo](code/A8/Demo.java){.attach}', 'html')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('<a href="code/A8/Demo.java" download="Demo.java">',
                      result.stdout)
        self.assertNotIn('attach', result.stdout.replace('Demo.java', ''))

    def test_docx_keeps_a_plain_link(self):
        result = self.pandoc('[Demo](code/A8/Demo.java){.attach}', 'native')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Link', result.stdout)
        self.assertNotIn('"attach"', result.stdout)

    @unittest.skipUnless(shutil.which('lualatex') and shutil.which('pdfdetach')
                         and has_tex_package('attachfile2'),
                         'fan falta lualatex, pdfdetach e attachfile2')
    def test_pdf_embeds_identical_file_without_path(self):
        markdown = ('O programa [`code/A8/Demo.java`](code/A8/Demo.java)'
                    '{.attach} e a partida '
                    '[`U2T4_usuario.java`](code/A8/U2T4_usuario.java){.attach}.\n')
        (self.dir / 'doc.md').write_text(markdown)
        result = subprocess.run(
            ['pandoc', 'doc.md', '-o', 'doc.pdf', '--pdf-engine=lualatex',
             f'--template={ROOT / "md2pdf.latex"}', '-s',
             # As variables que md2pdf pasa sempre ao modelo
             '-V', 'lang=galician', '-V', 'papersize=a4',
             '-V', 'fontsize=13pt', '-V', 'mainfont=Source Sans 3',
             '-V', 'monofont=Source Code Pro',
             '-H', str(ROOT / 'md2pdf-preamble.tex'),
             f'--lua-filter={ROOT / "attach.lua"}'],
            capture_output=True, text=True, cwd=self.dir)
        self.assertEqual(result.returncode, 0, result.stderr)
        listing = subprocess.run(['pdfdetach', '-list', 'doc.pdf'],
                                 capture_output=True, text=True,
                                 cwd=self.dir).stdout
        self.assertIn('2 embedded files', listing)
        self.assertIn('1: Demo.java', listing)
        self.assertIn('2: U2T4_usuario.java', listing)
        out = self.dir / 'out'
        out.mkdir()
        subprocess.run(['pdfdetach', '-saveall', '../doc.pdf'], cwd=out,
                       check=True)
        self.assertEqual((out / 'Demo.java').read_text(), SOURCE)
        self.assertEqual((out / 'U2T4_usuario.java').read_text(), SOURCE)
        # A ruta local do equipo non vai no PDF
        self.assertNotIn(str(self.dir).encode(),
                         (self.dir / 'doc.pdf').read_bytes())
        # O texto da ligazón vai no contido da páxina, non só na aparencia
        # da anotación: un visor que non debuxa as anotacións tamén o amosa.
        try:
            import pypdf
        except ImportError:
            self.skipTest('falta pypdf para ler o contido da páxina')
        page = pypdf.PdfReader(self.dir / 'doc.pdf').pages[0]
        self.assertIn('code/A8/Demo.java', page.extract_text())
        annots = [a.get_object() for a in page.get('/Annots', [])]
        attachments = [a for a in annots
                       if a.get('/Subtype') == '/FileAttachment']
        self.assertEqual(len(attachments), 2)


if __name__ == '__main__':
    unittest.main()
