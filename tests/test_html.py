import shutil
import tempfile
import unittest
from pathlib import Path

from md2pdf.config import OUTPUT_EXTENSIONS, TEMPLATE_NAMES
from md2pdf.converter import convert_one
from md2pdf.diagrams.common import FORMAT_BY_ENGINE
from md2pdf.engines.html import build_html_cmd
from md2pdf.html_validation import validate_html


ROOT = Path(__file__).resolve().parents[1]
SVG_DATA = ("data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'"
            "%20viewBox='0%200%2010%2010'%3E%3Ccircle%20cx='5'%20cy='5'"
            "%20r='4'/%3E%3C/svg%3E")


class HtmlEngineTests(unittest.TestCase):
    def assertSvgEmbedded(self, html: str) -> None:
        # Pandoc incrusta o SVG en liña (<svg>) ou como data URI segundo a
        # versión (3.11 usa data:image/svg+xml); as dúas son autocontidas.
        self.assertTrue('<svg ' in html or 'data:image/svg+xml' in html,
                        'o SVG non está incrustado no HTML')

    def _convert(self, source: str, **kwargs) -> tuple[bool, str, Path]:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        directory = Path(temporary.name)
        md = directory / 'test.md'
        out = directory / 'test.html'
        md.write_text(source, encoding='utf-8')
        ok = convert_one(
            md, out, ROOT / 'md2pdf.html', engine='html',
            highlight=str(ROOT / 'drake-jb.theme'), **kwargs,
        )
        html = out.read_text(encoding='utf-8') if out.exists() else ''
        return ok, html, out

    def test_html_engine_configuration(self):
        self.assertEqual(OUTPUT_EXTENSIONS['html'], '.html')
        self.assertEqual(TEMPLATE_NAMES['html'], 'md2pdf.html')
        self.assertEqual(FORMAT_BY_ENGINE['html'], 'svg')

    def test_command_is_standalone_and_uses_html_assets(self):
        cmd = build_html_cmd(
            tmp_path='input.md', output_path='output.html',
            template=ROOT / 'md2pdf.html', toc=True, toc_depth=3,
            section_numbering='1.1.', lang='gl', highlight='pygments',
            callouts=True, night_mode=True, source_dir='/tmp/source',
        )
        joined = ' '.join(map(str, cmd))
        self.assertIn('--to=html5', cmd)
        self.assertIn('--standalone', cmd)
        self.assertIn('--embed-resources', cmd)
        self.assertIn('--section-divs', cmd)
        self.assertIn('--mathml', cmd)
        self.assertIn('--number-sections', cmd)
        self.assertIn('--toc', cmd)
        self.assertIn('night-mode=true', cmd)
        self.assertIn('md2pdf.css', joined)
        self.assertIn('figure-captions.lua', joined)
        self.assertIn('html.lua', joined)
        self.assertLess(joined.index('figure-captions.lua'),
                        joined.index('html.lua'))

    @unittest.skipUnless(shutil.which('pandoc'), 'pandoc non instalado')
    def test_full_html_conversion_preserves_core_features(self):
        source = f'''---
activity: "A99: Proba HTML"
---

# Documento

## Sección

::: tip

Un **consello**.
:::

```java {{hl="2"}}
int a = 1;
int b = 2;
```

| A | B |
|---|---|
| 1 | 2 |
: Datos {{#tbl:datos}}

Véxase a @tbl:datos.

![Punto]({SVG_DATA}){{#fig:punto}}

Véxase a @fig:punto.

![]({SVG_DATA})

*Figura 99. Pé herdado {{#fig:legado}}*

Véxase a @fig:legado.
'''
        ok, html, _ = self._convert(source)
        self.assertTrue(ok)
        self.assertIn('class="tip callout callout-tip"', html)
        self.assertIn('role="note"', html)
        self.assertIn('aria-labelledby="md2pdf-callout-1-title"', html)
        self.assertIn('id="md2pdf-callout-1-title" class="callout-title"', html)
        self.assertIn('data-hl="2"', html)
        self.assertIn('<div class="table-wrapper">', html)
        self.assertIn('<table id="tbl:datos">', html)
        self.assertIn('Táboa 1.', html)
        self.assertIn('href="#tbl:datos" class="crossref">táboa 1</a>', html)
        self.assertIn('<figure id="fig:punto">', html)
        self.assertIn('Figura 1.', html)
        self.assertIn('href="#fig:punto" class="crossref">figura 1</a>', html)
        self.assertIn('<figure id="fig:legado">', html)
        self.assertIn('alt="Pé herdado"', html)
        self.assertIn('Figura 2.', html)
        self.assertIn('Pé herdado', html)
        self.assertNotIn('Figura 2. Figura 99.', html)
        self.assertIn('href="#fig:legado" class="crossref">figura 2</a>', html)
        self.assertIn('<nav id="TOC"', html)
        self.assertIn('A99: Proba HTML', html)
        self.assertEqual(validate_html(_), [])

    @unittest.skipUnless(shutil.which('pandoc'), 'pandoc non instalado')
    def test_local_images_are_embedded(self):
        png = bytes.fromhex(
            '89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489'
            '0000000d49444154789c6360000000020001e221bc330000000049454e44ae426082'
        )
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / 'local.png').write_bytes(png)
            md = directory / 'local.md'
            out = directory / 'local.html'
            md.write_text('# Documento\n\n![Local](local.png){width=25%}\n',
                          encoding='utf-8')
            ok = convert_one(
                md, out, ROOT / 'md2pdf.html', engine='html',
                highlight=str(ROOT / 'drake-jb.theme'),
            )
            self.assertTrue(ok)
            html = out.read_text(encoding='utf-8')
            self.assertIn('data:image/png;base64,', html)
            self.assertNotIn('src="local.png"', html)
            self.assertEqual(validate_html(out), [])

    def test_html_validator_finds_broken_links_duplicate_ids_and_missing_alt(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'bad.html'
            path.write_text('''<!doctype html><html><body>
<div id="dup"></div><span id="dup"></span>
<a href="#missing">rota</a>
<div aria-labelledby="missing-label"></div>
<img src="x.png" alt="">
<span class="broken-crossref" data-ref="fig:non-existe">@fig:non-existe</span>
</body></html>''', encoding='utf-8')
            issues = validate_html(path)
        joined = '\n'.join(issues)
        self.assertIn('identificador HTML duplicado: #dup', joined)
        self.assertIn('ligazón interna rota: #missing', joined)
        self.assertIn('aria-labelledby apunta a un ID inexistente: #missing-label', joined)
        self.assertIn('imaxe #1 sen texto alternativo', joined)
        self.assertIn('referencia cruzada sen destino: @fig:non-existe', joined)

    def test_html_validator_allows_decorative_image(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'ok.html'
            path.write_text(
                '<html><body><img class="decorative" src="x.png" alt=""></body></html>',
                encoding='utf-8')
            self.assertEqual(validate_html(path), [])

    def test_html_validator_checks_accessible_svg_images(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'svg.html'
            path.write_text(
                '<html><body><svg role="img"></svg></body></html>',
                encoding='utf-8')
            issues = validate_html(path)
        self.assertTrue(any('SVG informativo #1 sen nome accesible' in issue
                            for issue in issues))

    @unittest.skipUnless(shutil.which('pandoc'), 'pandoc non instalado')
    def test_strict_rejects_unresolved_cross_reference(self):
        ok, html, out = self._convert(
            '# Documento\n\nVéxase a @fig:non-existe.\n', strict=True,
        )
        self.assertFalse(ok)
        self.assertEqual(html, '')
        self.assertFalse(out.exists())

    @unittest.skipUnless(shutil.which('pandoc'), 'pandoc non instalado')
    def test_mathml_footnotes_modes_and_no_callouts(self):
        source = '''# Documento

## Sección

::: tip

Texto.
:::

A expresión $x^2 + 1$ leva unha nota.[^1]

[^1]: Nota ao pé.
'''
        ok, html, out = self._convert(
            source, night_mode=True, print_mode=True, plain=True,
            callouts=False,
        )
        self.assertTrue(ok)
        self.assertIn('class="night-mode print-mode plain-mode"', html)
        self.assertIn('<math', html)
        self.assertIn('class="footnotes footnotes-end-of-document"', html)
        self.assertIn('<div class="tip">', html)
        self.assertNotIn('<div class="tip callout', html)
        self.assertNotIn('<nav id="TOC"', html)
        self.assertNotIn('header-section-number', html)
        self.assertEqual(validate_html(out), [])

    @unittest.skipUnless(shutil.which('dot'), 'Graphviz non instalado')
    @unittest.skipUnless(shutil.which('pandoc'), 'pandoc non instalado')
    def test_graphviz_svg_is_embedded_and_accessible(self):
        source = '''# Documento

```{.dot #fig:grafo caption="Grafo simple" width=70%}
digraph G { A -> B }
```

Véxase a @fig:grafo.
'''
        ok, html, out = self._convert(source)
        self.assertTrue(ok)
        self.assertIn('<figure id="fig:grafo">', html)
        self.assertIn('alt="Grafo simple"', html)
        self.assertSvgEmbedded(html)
        self.assertIn('role="img"', html)
        self.assertIn('aria-label="Grafo simple"', html)
        self.assertIn('href="#fig:grafo" class="crossref">figura 1</a>', html)
        self.assertEqual(validate_html(out), [])

    @unittest.skipUnless(shutil.which('dot'), 'Graphviz non instalado')
    @unittest.skipUnless(shutil.which('pandoc'), 'pandoc non instalado')
    def test_italic_caption_with_fence_id_has_single_id(self):
        # O id do bloque vai á imaxe; figure-captions.lua move-o á Figure.
        # Non debe quedar duplicado en <img id> e <figure id>.
        source = '''# Documento

```{.dot #fig:grafo}
digraph G { A -> B }
```

*Figura 1. Grafo.*

Véxase a @fig:grafo.
'''
        ok, html, out = self._convert(source)
        self.assertTrue(ok)
        self.assertEqual(html.count('id="fig:grafo"'), 1)
        self.assertRegex(html, r'class="md2pdf-diagram" style="width:[0-9.]+em"')
        self.assertEqual(validate_html(out), [])

    @unittest.skipUnless(shutil.which('mmdc'), 'Mermaid CLI non instalado')
    @unittest.skipUnless(shutil.which('pandoc'), 'pandoc non instalado')
    def test_mermaid_svg_is_embedded(self):
        source = '''# Documento

```{.mermaid #fig:mermaid caption="Fluxo Mermaid"}
flowchart LR
A --> B
```
'''
        ok, html, out = self._convert(source)
        self.assertTrue(ok)
        self.assertSvgEmbedded(html)
        self.assertIn('aria-label="Fluxo Mermaid"', html)
        self.assertEqual(validate_html(out), [])

    @unittest.skipUnless(shutil.which('d2'), 'D2 non instalado')
    @unittest.skipUnless(shutil.which('pandoc'), 'pandoc non instalado')
    def test_d2_svg_is_embedded(self):
        source = '''# Documento

```{.d2 #fig:d2 caption="Fluxo D2"}
A -> B
```
'''
        ok, html, out = self._convert(source)
        self.assertTrue(ok)
        self.assertSvgEmbedded(html)
        self.assertIn('aria-label="Fluxo D2"', html)
        self.assertEqual(validate_html(out), [])


if __name__ == '__main__':
    unittest.main()
