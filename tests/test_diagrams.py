import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from md2pdf.diagrams.base import RenderContext
from md2pdf.diagrams.processor import process_diagrams
from md2pdf.diagrams.renderers import (D2Renderer, GraphvizRenderer,
                                        MermaidRenderer)
from md2pdf.mermaid import process_mermaid


class DiagramTests(unittest.TestCase):
    def test_layout_arguments_and_relative_d2_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            output = directory / 'out.svg'
            context = RenderContext(directory, 'svg',
                                    options={'layout': 'elk', 'theme': '1'},
                                    source_dir=directory)
            with patch('md2pdf.diagrams.renderers._run', return_value='') as run:
                D2Renderer().render('d2', context, 'a -> b', output)
            command = run.call_args.args[0]
            self.assertIn('--layout=elk', command)
            self.assertIn('--theme=1', command)
            self.assertEqual(Path(command[-2]).parent, directory)
            self.assertFalse(Path(command[-2]).exists())
            self.assertEqual(run.call_args.kwargs['cwd'], directory)
            context = RenderContext(directory, 'svg', options={'layout': 'neato'})
            with patch('md2pdf.diagrams.renderers._run', return_value='') as run:
                GraphvizRenderer().render('dot', context, 'graph { a -- b }', output)
            self.assertIn('-Kneato', run.call_args.args[0])

    def test_compatibility_api_leaves_mermaid_when_mmdc_is_missing(self):
        source = 'Antes\n\n```mermaid\ngraph LR\nA-->B\n```\n\nDespois'
        with patch('md2pdf.diagrams.processor.shutil.which', return_value=None):
            result, new, cached, errors = process_mermaid(source, 'lualatex')
        self.assertEqual(result, source)
        self.assertEqual((new, cached), (0, 0))
        self.assertIn('`mmdc` non está instalado', errors[0])

    def test_fenced_attributes_are_recognised(self):
        source = '```{.mermaid #diagrama}\ngraph LR\nA-->B\n```'
        with patch('md2pdf.diagrams.processor.shutil.which', return_value=None):
            _, _, _, errors = process_mermaid(source, 'docx')
        self.assertEqual(len(errors), 1)

    def test_only_installed_renderer_is_required(self):
        source = '```mermaid\ngraph LR\nA-->B\n```'
        with patch('md2pdf.diagrams.processor.shutil.which', return_value=None):
            _, stats = process_diagrams(source, 'lualatex')
        self.assertEqual(set(stats.errors), {'mermaid'})

    def test_mermaid_command_preserves_pdf_flags_and_environment(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            output = directory / 'diagram.pdf'

            def fake_run(command, **kwargs):
                output.write_bytes(b'%PDF /MediaBox [0 0 100 50]')
                class Result:
                    returncode = 0
                    stdout = stderr = ''
                self.assertIn('--pdfFit', command)
                self.assertEqual(kwargs['stdin'], -3)  # subprocess.DEVNULL
                self.assertEqual(kwargs['env']['PUPPETEER_DISABLE_HEADLESS_WARNING'], '1')
                return Result()

            context = RenderContext(directory, 'pdf')
            with patch('md2pdf.diagrams.renderers.subprocess.run', fake_run):
                error = MermaidRenderer().render('mmdc', context,
                                                  'graph LR\nA-->B', output)
            self.assertEqual(error, '')
            self.assertTrue(output.exists())
            self.assertFalse(output.with_suffix('.mmd').exists())
            config = directory / 'puppeteer-config.json'
            self.assertIn('--no-sandbox', config.read_text())

    def test_mermaid_12_retries_pdf_without_removed_option(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            output = directory / 'diagram.pdf'
            with patch('md2pdf.diagrams.renderers._run', side_effect=[
                    "devolveu 1: error: unknown option '--pdfFit'", '']) as run:
                error = MermaidRenderer().render('mmdc',
                    RenderContext(directory, 'pdf'), 'graph LR\nA-->B', output)
            self.assertEqual(error, '')
            self.assertEqual(run.call_count, 2)
            first, second = run.call_args_list
            self.assertEqual(first.args[0][:-1], second.args[0])
            self.assertEqual(first.kwargs, second.kwargs)
            self.assertNotIn('--pdfFit', second.args[0])
            self.assertFalse(output.with_suffix('.mmd').exists())

    def test_mermaid_does_not_retry_other_pdf_errors(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with patch('md2pdf.diagrams.renderers._run',
                    return_value='devolveu 1: Parse error') as run:
                error = MermaidRenderer().render('mmdc',
                    RenderContext(directory, 'pdf'), 'invalid', directory/'out.pdf')
            self.assertIn('Parse error', error)
            self.assertEqual(run.call_count, 1)

    def test_non_pdf_mermaid_does_not_use_pdf_fit(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            output = directory / 'diagram.svg'
            with patch('md2pdf.diagrams.renderers._run', return_value='') as run:
                MermaidRenderer().render('mmdc', RenderContext(directory, 'svg'),
                                          'graph LR\nA-->B', output)
            self.assertNotIn('--pdfFit', run.call_args.args[0])

    def test_d2_and_graphviz_commands_use_requested_format(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            cases = ((D2Renderer(), 'd2', 'svg', '--theme=0'),
                     (GraphvizRenderer(), 'dot', 'png', '-Tpng'))
            for renderer, executable, fmt, expected in cases:
                with self.subTest(renderer=renderer.name):
                    output = directory / f'{renderer.name}.{fmt}'
                    with patch('md2pdf.diagrams.renderers._run', return_value='') as run:
                        renderer.render(executable, RenderContext(directory, fmt),
                                        'a -> b', output)
                    self.assertIn(expected, run.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
