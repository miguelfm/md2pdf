"""Proba de URI PDF coa configuración real de hyperref e filtros do proxecto.

O contorno reducido usa pdfLaTeX: comproba ligazóns, non a maquetación
completa nin as fontes de produción LuaLaTeX.
"""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from md2pdf.preprocess import preprocess_md

ROOT = Path(__file__).resolve().parents[1]

class LinkTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('pandoc') and shutil.which('pdflatex'),
                         'Require Pandoc e pdfLaTeX')
    def test_pdf_uri_with_project_filters(self):
        try:
            from pypdf import PdfReader
        except ImportError:
            self.skipTest('Require pypdf')
        template = (ROOT / 'md2pdf.latex').read_text()
        start = template.index(r'\IfFileExists{xurl.sty}')
        end = template.index('% ── Gráficos')
        links = template[start:end]
        self.assertLess(links.index(r'\usepackage{xurl}'),
                        links.index(r'\usepackage{hyperref}'))
        head = r"""
\documentclass{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[a4paper,margin=22mm]{geometry}
\usepackage{xcolor}
\usepackage{longtable,booktabs,array,calc}
\usepackage{needspace,tcolorbox}
\tcbuselibrary{skins,breakable}
\definecolor{heading-section}{RGB}{30,40,50}
\providecommand{\tightlist}{}
"""
        fixture = preprocess_md((ROOT/'tests/links.md').read_text(), 'lualatex')
        # Extract expected external targets via Pandoc, including autolinks.
        ast = subprocess.run(['pandoc', '-t', 'json'], input=fixture,
                             text=True, capture_output=True, check=True).stdout
        import json
        expected = set()
        def collect(node):
            if isinstance(node, dict):
                if node.get('t') == 'Link' and node['c'][2][0].startswith('https:'):
                    expected.add(node['c'][2][0])
                for v in node.values():
                    collect(v)
            elif isinstance(node, list):
                for v in node:
                    collect(v)
        collect(json.loads(ast))
        for mode, color in [('normal', 'blue'), ('print', 'black'),
                            ('night', 'brown')]:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temp:
                directory = Path(temp)
                tpl = directory/'test.latex'
                tpl.write_text(head + links + '\n' + r'\begin{document}' +
                               '\n$body$\n' + r'\end{document}')
                command = ['pandoc', '-s', '--template', str(tpl),
                           '-V', 'colorlinks=true', '-V', 'urlcolor='+color,
                           '-V', 'linkcolor='+color,
                           '--pdf-engine=pdflatex', '-o', str(directory/'links.pdf')]
                for f in ('auto-table-widths.lua', 'small-table.lua',
                          'callouts.lua', 'br.lua', 'hl-lines.lua', 'figure-captions.lua'):
                    command += ['--lua-filter', str(ROOT/f)]
                run = subprocess.run(command, input=fixture, text=True,
                                     capture_output=True, timeout=90)
                self.assertEqual(run.returncode, 0, run.stderr)
                if os.environ.get('MD2PDF_LINK_TEST_OUTPUT'):
                    output_dir = Path(os.environ['MD2PDF_LINK_TEST_OUTPUT'])
                    output_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(directory/'links.pdf', output_dir/(mode+'.pdf'))
                reader = PdfReader(directory/'links.pdf')
                uris, internal = set(), False
                for page in reader.pages:
                    for ref in page.get('/Annots', []):
                        annotation = ref.get_object()
                        action = annotation.get('/A', {})
                        if action.get('/S') == '/URI':
                            uris.add(str(action['/URI']))
                        if '/Dest' in annotation or action.get('/S') == '/GoTo':
                            internal = True
                self.assertEqual(uris, expected)
                self.assertNotIn('https://example.org/non-enlazar', uris)
                self.assertTrue(internal)

if __name__ == '__main__':
    unittest.main()
