import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from md2pdf.diagrams.processor import process_diagrams
from md2pdf.diagrams.vegalite import validate_spec, VegaLiteRenderer
from md2pdf.preprocess import preprocess_md

SPEC = {"data": {"values": [{"x": 1, "y": 2}, {"x": 2, "y": 4}]},
        "mark": "point",
        "encoding": {"x": {"field": "x", "type": "quantitative"},
                     "y": {"field": "y", "type": "quantitative"}}}

class VegaTests(unittest.TestCase):
    def test_reject_external_resources(self):
        for spec in ([], {"data": {"url": "https://example.org/a.csv"}},
                     {"layer": [{"mark": "image"}]},
                     {"encoding": {"href": {"value": "file:///tmp/a"}}}):
            with self.assertRaises(ValueError):
                validate_spec(spec)

    def test_missing_dependency_preserves_block(self):
        text = '```vega-lite\n{}\n```'
        with patch.object(VegaLiteRenderer, 'find_executable', return_value=None):
            out, stats = process_diagrams(text, 'lualatex')
        self.assertEqual(out, text)
        self.assertIn('vl-convert-python', stats.errors['vega-lite'][0])

    def test_preprocess_protects_json(self):
        text = '```{.vega-lite width=80%}\n{"title":"💡","mark":"point"}\n```'
        self.assertIn('{"title":"💡"', preprocess_md(text, 'lualatex'))

    @unittest.skipUnless(importlib.util.find_spec('vl_convert'), 'vl-convert-python non instalado')
    def test_real_all_formats_and_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch('md2pdf.diagrams.processor.cache_dir', return_value=root):
                for engine, fmt, signature in (
                    ('lualatex', 'pdf', b'%PDF'), ('docx', 'png', b'\x89PNG')):
                    text = '```{.vega-lite #fig:datos width=80% caption="Datos"}\n'+json.dumps(SPEC)+'\n```'
                    out, stats = process_diagrams(text, engine)
                    self.assertFalse(stats.errors['vega-lite'], stats.errors)
                    self.assertEqual(stats.new['vega-lite'], 1)
                    self.assertIn('#fig:datos width=80%', out)
                    file = next(root.glob('*.'+fmt))
                    self.assertIn(signature, file.read_bytes()[:100])
                    _, stats = process_diagrams(text, engine)
                    self.assertEqual(stats.cached['vega-lite'], 1)

    @unittest.skipUnless(importlib.util.find_spec('vl_convert'), 'vl-convert-python non instalado')
    def test_bad_json_and_network_preserve_source(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch('md2pdf.diagrams.processor.cache_dir', return_value=Path(directory)):
                for body in ('{invalid', '{"data":{"url":"https://example.org/data"}}'):
                    text = '```vegalite\n'+body+'\n```'
                    out, stats = process_diagrams(text, 'lualatex')
                    self.assertEqual(out, text)
                    self.assertTrue(stats.errors['vega-lite'])
                    self.assertEqual(list(Path(directory).iterdir()), [])

if __name__ == '__main__':
    unittest.main()

