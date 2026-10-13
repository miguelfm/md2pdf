import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from md2pdf.diagrams.processor import process_diagrams, fenced_blocks
from md2pdf.diagrams.renderers import D2Renderer, GraphvizRenderer
from md2pdf.diagrams.base import RenderContext
from md2pdf.diagrams.settings import load_diagram_defaults
from md2pdf.preprocess import preprocess_md

class ExtendedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.calls = []
        self.addCleanup(patch.stopall)
        patch('md2pdf.diagrams.processor.cache_dir', return_value=self.root).start()
        patch('md2pdf.diagrams.processor.shutil.which', return_value='/fake/cli').start()
        def render(renderer, executable, context, content, output):
            self.calls.append((context, content))
            if context.output_format == 'svg':
                output.write_text('<svg viewBox="0 0 160 80"><rect width="100" height="60"/></svg>')
            elif context.output_format == 'pdf':
                import pymupdf
                with pymupdf.open() as document:
                    document.new_page(width=120, height=60).insert_text((10, 30), 'Diagram')
                    document.save(output)
            else:
                from PIL import Image
                Image.new('RGB', (160, 80), 'black').save(output)
            return ''
        for cls in ('MermaidRenderer', 'D2Renderer', 'GraphvizRenderer'):
            patch('md2pdf.diagrams.renderers.'+cls+'.render', render).start()

    def test_outer_example_untouched(self):
        text = '````markdown\n```mermaid\nA-->B\n```\n````\n'
        self.assertEqual(process_diagrams(text, 'lualatex')[0], text)
        self.assertEqual(self.calls, [])

    def test_preprocessing_preserves_attributes_and_examples(self):
        text = '````markdown\n```mermaid\nA-->B\n```\n````\n\n~~~{.d2 layout=elk}\na -> b\n~~~'
        processed = preprocess_md(text, 'lualatex')
        out, stats = process_diagrams(processed, 'lualatex')
        self.assertIn('```mermaid', out)
        self.assertEqual(stats.new, {'d2': 1})

    def test_cache_and_formats(self):
        for engine in ('lualatex', 'docx'):
            text = '```mermaid\ngraph LR\nA-->B\n```'
            first, stats = process_diagrams(text, engine)
            self.assertEqual(stats.new['mermaid'], 1)
            second, stats = process_diagrams(text, engine)
            self.assertEqual(stats.cached['mermaid'], 1)
            self.assertEqual(first, second)
        self.assertEqual(len(self.calls), 2)

    def test_layout_invalidates_but_width_does_not(self):
        for attrs in ('layout=elk', 'layout=elk width=80%', 'layout=dagre', 'layout=dagre sketch=true', 'layout=dagre sketch=true pad=20'):
            process_diagrams('```{.d2 '+attrs+'}\na -> b\n```', 'lualatex')
        self.assertEqual(len(self.calls), 4)

    def test_defaults_overridden_and_caption(self):
        out, stats = process_diagrams(
            '```{.d2 layout=elk #fig:demo width=90% caption="Un exemplo"}\na -> b\n```',
            'lualatex', defaults={'d2': {'layout': 'dagre', 'theme': 1}})
        self.assertEqual(self.calls[0][0].options, {'layout': 'elk', 'theme': '1'})
        self.assertIn('![Un exemplo]', out)
        self.assertIn('#fig:demo width=90%', out)

    def test_invalid_option_preserves_source(self):
        for attributes in ('layout=bad', 'width=-5%', 'args=--evil', 'sketch=invalid', 'pad=-5', 'dark-theme=bad'):
            text = '```{.d2 '+attributes+'}\na -> b\n```'
            out, stats = process_diagrams(text, 'lualatex')
            self.assertEqual(out, text)
            self.assertTrue(stats.errors['d2'])
        self.assertFalse(self.calls)

    def test_empty_cache_is_not_reused(self):
        text = '```d2\na -> b\n```'
        process_diagrams(text, 'lualatex')
        for path in self.root.glob('*.pdf'):
            path.write_bytes(b'')
        _, stats = process_diagrams(text, 'lualatex')
        self.assertEqual(stats.new['d2'], 1)

    def test_failure_does_not_publish_partial_output(self):
        def fail(renderer, executable, context, content, output):
            output.write_text('partial')
            return 'erro simulado'
        with patch.object(D2Renderer, 'render', fail):
            text = '```d2\na -> b\n```'
            out, stats = process_diagrams(text, 'lualatex')
        self.assertEqual(out, text)
        self.assertTrue(stats.errors['d2'])
        self.assertEqual(list(self.root.iterdir()), [])

    def test_external_resources_disable_cache(self):
        for _ in range(2):
            process_diagrams('```d2\n...@shared\n```', 'lualatex')
        self.assertEqual(len(self.calls), 2)

    def test_settings_merge(self):
        metadata = self.root/'metadata.yaml'
        metadata.write_text('diagrams:\n  d2:\n    layout: dagre\n    theme: 1\n')
        defaults = load_diagram_defaults(
            '---\ndiagrams:\n  d2:\n    layout: elk\n---\n', metadata)
        self.assertEqual(defaults, {'d2': {'layout': 'elk', 'theme': 1}})

    def test_d2_modern_options_and_defaults(self):
        text = '```{.d2 sketch pad=15 dark-theme=201}\na -> b\n```'
        out, stats = process_diagrams(
            text, 'lualatex', defaults={'d2': {'sketch': False, 'pad': 50, 'theme': 3}})
        self.assertEqual(stats.new['d2'], 1)
        self.assertEqual(self.calls[0][0].options, {
            'sketch': 'true', 'pad': '15', 'dark-theme': '201', 'theme': '3'
        })

    def test_mermaid_options_and_defaults(self):
        out, stats = process_diagrams(
            '```{.mermaid layout=elk theme=dark look=handDrawn #fig:fluxo caption="Fluxo"}\nflowchart TD\nA-->B\n```',
            'lualatex', defaults={'mermaid': {'layout': 'dagre', 'theme': 'forest', 'look': 'classic'}})
        self.assertEqual(self.calls[0][0].options, {'layout': 'elk', 'theme': 'dark', 'look': 'handDrawn'})
        self.assertIn('![Fluxo]', out)
        self.assertIn('#fig:fluxo', out)

    def test_mermaid_invalid_options_preserve_source(self):
        for attributes in ('layout=invalido', 'theme=invalido', 'look=invalido'):
            text = f'```{{.mermaid {attributes}}}\nflowchart TD\nA-->B\n```'
            out, stats = process_diagrams(text, 'lualatex')
            self.assertEqual(out, text)
            self.assertTrue(stats.errors['mermaid'])

    def test_mermaid_options_invalidate_cache(self):
        for attrs in ('theme=forest', 'theme=forest width=80%', 'theme=dark', 'layout=elk'):
            process_diagrams(f'```{{.mermaid {attrs}}}\nflowchart TD\nA-->B\n```', 'lualatex')
        self.assertEqual(len(self.calls), 3)

    def test_unclosed_and_non_diagram_fences_untouched(self):
        for text in ('```d2\na -> b', '```python\n```d2\na -> b\n```'):
            self.assertEqual(process_diagrams(text, 'lualatex')[0], text)

if __name__ == '__main__':
    unittest.main()

