"""Compatibilidade coas versións actuais de Pandoc, KOMA-Script e mermaid-cli."""

import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from md2pdf import config
from md2pdf.converter import _pandoc_warnings
from md2pdf.diagrams import renderers

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('pandoc'), 'pandoc non está instalado')
class KomaFontsizeTests(unittest.TestCase):
    def render_template(self) -> str:
        cmd = [
            'pandoc', '-f', 'markdown', '-t', 'latex', '-s',
            f'--template={ROOT / "md2pdf.latex"}',
            '-V', 'fontsize=13pt', '-V', 'papersize=a4',
        ]
        result = subprocess.run(
            cmd, input='Texto.\n', capture_output=True, text=True, cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_documentclass_uses_fontsize_key(self):
        header = self.render_template().split(']{scrartcl}')[0]
        self.assertIn('fontsize=13pt', header)
        self.assertIsNone(re.search(r'^\s*13pt,', header, re.MULTILINE))

    def compile_log(self, size_option: str) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            tex = Path(tmp) / 'proba.tex'
            tex.write_text(
                f'\\documentclass[{size_option},a4paper,parskip=half-]{{scrartcl}}\n'
                '\\begin{document}Texto.\\end{document}\n',
                encoding='utf-8',
            )
            subprocess.run(
                ['lualatex', '-interaction=nonstopmode', tex.name],
                capture_output=True, text=True, cwd=tmp, timeout=180,
            )
            log = tex.with_suffix('.log').read_text(encoding='utf-8', errors='replace')
        self.assertIn('Document Class: scrartcl', log)
        return log

    @unittest.skipUnless(shutil.which('lualatex'), 'lualatex non está instalado')
    def test_koma_does_not_switch_to_old_version(self):
        self.assertIn('version=first', self.compile_log('13pt'))
        log = self.compile_log('fontsize=13pt')
        self.assertNotIn('version=first', log)
        self.assertNotIn('deprecated option', log)


class PandocFlagTests(unittest.TestCase):
    def with_version(self, first_line: str):
        config._pandoc_version_cache = None
        completed = subprocess.CompletedProcess([], 0, stdout=first_line + '\n', stderr='')
        return mock.patch.object(config.subprocess, 'run', return_value=completed)

    def tearDown(self):
        config._pandoc_version_cache = None

    def test_old_pandoc_keeps_old_flags(self):
        with self.with_version('pandoc 3.1.11.1'):
            self.assertEqual(config._pandoc_version(), (3, 1, 11, 1))
            self.assertEqual(config._pandoc_highlight_flag(), '--highlight-style')
            self.assertEqual(config._pandoc_math_flag('mathml'), '--mathml')

    def test_pandoc_38_uses_syntax_highlighting(self):
        with self.with_version('pandoc 3.8'):
            self.assertEqual(config._pandoc_highlight_flag(), '--syntax-highlighting')
            self.assertEqual(config._pandoc_math_flag('mathml'), '--mathml')

    def test_pandoc_311_uses_math_method(self):
        with self.with_version('pandoc 3.11'):
            self.assertEqual(config._pandoc_math_flag('mathml'), '--math-method=mathml')

    def test_unreadable_version_falls_back_to_old_flags(self):
        with self.with_version(''):
            self.assertEqual(config._pandoc_version(), (0,))
            self.assertEqual(config._pandoc_highlight_flag(), '--highlight-style')

    @unittest.skipUnless(shutil.which('pandoc'), 'pandoc non está instalado')
    def test_installed_pandoc_gives_no_deprecation_warning(self):
        config._pandoc_version_cache = None
        cmd = [
            'pandoc', '-f', 'markdown', '-t', 'html', '-s',
            '--metadata', 'title=Proba',
            f'{config._pandoc_highlight_flag()}={ROOT / "drake-jb.theme"}',
            config._pandoc_math_flag('mathml'),
        ]
        result = subprocess.run(
            cmd, input='Texto $x^2$.\n', capture_output=True, text=True, cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('Deprecated', result.stderr)


class PandocWarningTests(unittest.TestCase):
    def test_collects_unique_warnings(self):
        stderr = (
            '[WARNING] Deprecated: --highlight-style. Use --syntax-highlighting instead.\n'
            'This is LuaHBTeX, Version 1.24.0\n'
            '[WARNING] Could not fetch resource imaxe.png\n'
            '[WARNING] Could not fetch resource imaxe.png\n'
        )
        self.assertEqual(_pandoc_warnings(stderr), [
            'Deprecated: --highlight-style. Use --syntax-highlighting instead.',
            'Could not fetch resource imaxe.png',
        ])

    def test_no_warnings(self):
        self.assertEqual(_pandoc_warnings('Output written on x.pdf\n'), [])


@unittest.skipUnless(shutil.which('pandoc'), 'pandoc non está instalado')
class ListingsOptionTests(unittest.TestCase):
    def test_listings_is_accepted_with_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'proba.md'
            source.write_text('---\ntitle: Proba\n---\n\n# Proba\n', encoding='utf-8')
            result = subprocess.run(
                [sys.executable, '-m', 'md2pdf', str(source), '--listings',
                 '-e', 'html', '-o', str(Path(tmp) / 'proba.html')],
                capture_output=True, text=True, cwd=ROOT, timeout=180,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('--listings está obsoleta', result.stderr)
            self.assertTrue((Path(tmp) / 'proba.html').exists())


class MermaidPdfFitTests(unittest.TestCase):
    def setUp(self):
        renderers._mmdc_supports_pdf_fit.cache_clear()

    tearDown = setUp

    def with_help(self, text: str):
        completed = subprocess.CompletedProcess([], 0, stdout=text, stderr='')
        return mock.patch.object(renderers.subprocess, 'run', return_value=completed)

    def test_old_mmdc_keeps_pdf_fit(self):
        with self.with_help('  -f, --pdfFit   Scale PDF to fit chart\n'):
            self.assertTrue(renderers._mmdc_supports_pdf_fit('mmdc'))

    def test_mmdc_12_drops_pdf_fit(self):
        with self.with_help('  --pdf-paper-format <format>   If set, output a PDF...\n'):
            self.assertFalse(renderers._mmdc_supports_pdf_fit('mmdc'))

    def test_unreadable_help_tries_pdf_fit(self):
        with mock.patch.object(renderers.subprocess, 'run', side_effect=OSError):
            self.assertTrue(renderers._mmdc_supports_pdf_fit('mmdc'))


@unittest.skipUnless(shutil.which('mmdc'), 'mmdc non está instalado')
class MermaidCli12IntegrationTests(unittest.TestCase):
    def test_mermaid_v12_renders_with_options_and_modern_types(self):
        from md2pdf.diagrams.processor import process_diagrams
        source = (
            "```{.mermaid theme=neo layout=elk look=handDrawn}\n"
            "flowchart TD\n"
            "    A --> B\n"
            "```\n\n"
            "```mermaid\n"
            "usecase-beta\n"
            "    actor User\n"
            "    User --> Login(Login)\n"
            "```\n"
        )
        out, stats = process_diagrams(source, 'lualatex')
        self.assertEqual(stats.errors.get('mermaid', []), [])
        self.assertEqual(stats.new.get('mermaid', 0) + stats.cached.get('mermaid', 0), 2)
        self.assertNotIn('```mermaid', out)


@unittest.skipUnless(shutil.which('dot'), 'dot non está instalado')
class GraphvizCompatibilityTests(unittest.TestCase):
    def test_graphviz_version_and_layouts(self):
        from md2pdf.diagrams.processor import process_diagrams
        source = (
            "```{.dot layout=neato #fig:rede caption=\"Rede neato\"}\n"
            "graph { a -- b; b -- c; c -- a; }\n"
            "```\n\n"
            "```{.dot layout=circo #fig:circular caption=\"Anel circo\"}\n"
            "graph { 1 -- 2 -- 3 -- 4 -- 1; }\n"
            "```\n"
        )
        for engine in ('lualatex', 'html', 'docx'):
            out, stats = process_diagrams(source, engine)
            self.assertEqual(stats.errors.get('graphviz', []), [])
            self.assertEqual(stats.new.get('graphviz', 0) + stats.cached.get('graphviz', 0), 2)
            self.assertNotIn('```{.dot', out)


@unittest.skipUnless(shutil.which('d2'), 'd2 non está instalado')
class D2CompatibilityTests(unittest.TestCase):
    def test_d2_modern_features_and_options(self):
        from md2pdf.diagrams.processor import process_diagrams
        source = (
            "```{.d2 layout=elk theme=1 sketch pad=10 dark-theme=201 #fig:d2elk caption=\"Diagrama D2 ELK Sketch\"}\n"
            "x -> y: chamada\n"
            "y -> z: proceso\n"
            "```\n\n"
            "```{.d2 #fig:d2sql caption=\"Táboa SQL D2\"}\n"
            "users: {\n"
            "  shape: sql_table\n"
            "  id: int {constraint: primary_key}\n"
            "  name: string\n"
            "}\n"
            "```\n"
        )
        for engine in ('lualatex', 'html', 'docx'):
            out, stats = process_diagrams(source, engine)
            self.assertEqual(stats.errors.get('d2', []), [])
            self.assertEqual(stats.new.get('d2', 0) + stats.cached.get('d2', 0), 2)
            self.assertNotIn('```{.d2', out)


@unittest.skipUnless(importlib.util.find_spec('vl_convert'), 'vl-convert-python non instalado')
class VegaLiteCompatibilityTests(unittest.TestCase):
    def test_vegalite_version_themes_and_modern_features(self):
        from md2pdf.diagrams.processor import process_diagrams
        source = (
            "```{.vega-lite theme=fivethirtyeight #fig:rendemento caption=\"Rendemento\"}\n"
            "{\n"
            "  \"$schema\": \"https://vega.github.io/schema/vega-lite/v5.json\",\n"
            "  \"data\": {\"values\": [{\"mes\": \"Xan\", \"val\": 12}, {\"mes\": \"Feb\", \"val\": 19}]},\n"
            "  \"mark\": \"bar\",\n"
            "  \"encoding\": {\n"
            "    \"x\": {\"field\": \"mes\", \"type\": \"nominal\"},\n"
            "    \"y\": {\"field\": \"val\", \"type\": \"quantitative\"}\n"
            "  }\n"
            "}\n"
            "```\n\n"
            "```{.vega-lite theme=ggplot2 #fig:dispersao caption=\"Dispersión\"}\n"
            "{\n"
            "  \"data\": {\"values\": [{\"x\": 1, \"y\": 2}, {\"x\": 2, \"y\": 5}]},\n"
            "  \"mark\": \"point\",\n"
            "  \"encoding\": {\n"
            "    \"x\": {\"field\": \"x\", \"type\": \"quantitative\"},\n"
            "    \"y\": {\"field\": \"y\", \"type\": \"quantitative\"}\n"
            "  }\n"
            "}\n"
            "```\n"
        )
        for engine in ('lualatex', 'html', 'docx'):
            out, stats = process_diagrams(source, engine)
            self.assertEqual(stats.errors.get('vega-lite', []), [])
            self.assertEqual(stats.new.get('vega-lite', 0) + stats.cached.get('vega-lite', 0), 2)
            self.assertNotIn('```{.vega-lite', out)


if __name__ == '__main__':
    unittest.main()
