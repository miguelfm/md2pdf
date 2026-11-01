# Configurable diagrams

md2pdf supports Mermaid, D2, Graphviz, and Vega-Lite. `dot` and `graphviz` are aliases. The external renderers are optional and must be installed separately; their executables must be on `PATH`. See [VEGA-LITE.md](VEGA-LITE.md) for the Python-based chart renderer.

## Usage

````markdown
```{.d2 #fig:architecture layout=elk width=90% caption="Application architecture"}
client -> server: HTTP
server -> data: SQL
```

See @fig:architecture.

```{.dot layout=neato width=12cm caption="Connection graph"}
graph {
    a -- b;
    b -- c;
    c -- a;
}
```
````

An identifier and caption produce a standard Pandoc image/figure. md2pdf resolves `@fig:...` in LuaLaTeX and HTML without `pandoc-crossref`; DOCX does not currently resolve these references. Do not combine `caption` with a second manual “Figure N.” caption for the same figure. Captions are literal text, rather than rich Markdown. Without a caption, ID, or height, the historical centering wrapper is retained.

## Options

| Renderer | Options |
|---|---|
| All | `width`, `height`, `caption`, and `#identifier` (or `id=...`) |
| D2 | `layout=dagre\|elk\|tala`, numeric `theme`, `sketch=true\|false`, `pad=<pixels>`, numeric `dark-theme` |
| Graphviz | `layout=dot\|neato\|fdp\|sfdp\|circo\|twopi\|osage\|patchwork` |
| Mermaid | `layout=dagre\|elk` (also `tidy-tree` where available), `theme`, `look=classic\|handDrawn` |
| Vega-Lite | `theme`; see [the chart guide](VEGA-LITE.md) |

Dimensions must be positive and use `%`, `px`, `pt`, `cm`, `mm`, or `in`. With only width or height, Pandoc handles aspect ratio. Explicitly setting both may distort the image.

D2 light themes use IDs `0–8`, `100–105`, or `300–303`; SVG dark themes include `200–201`. Its default padding is 100 pixels. TALA requires its engine and applicable license.

Mermaid theme values are `base`, `dark`, `default`, `forest`, `neutral`, `neo`, `neo-dark`, `redux`, `redux-dark`, `redux-color`, `redux-dark-color`, and `null`. Availability depends on the installed Mermaid CLI; newer themes and looks require compatible versions. Internal directives such as `%%{init: ...}%%` remain usable.

An invalid value preserves the block as code and emits a warning. Arbitrary command-line arguments are not accepted. Renderer requirements can differ by output: LuaLaTeX requests PDF, DOCX requests PNG, and HTML requests SVG.

## Document defaults

Nested `diagrams:` YAML requires PyYAML:

```sh
python -m pip install PyYAML
```

```yaml
---
diagrams:
  mermaid:
    layout: elk
    theme: forest
    look: handDrawn
  d2:
    layout: elk
    theme: 0
    sketch: false
    pad: 20
  graphviz:
    layout: dot
  vega-lite:
    theme: fivethirtyeight
---
```

The same settings work in `metadata.yaml`. Precedence is evaluated per option:

**Block attribute → front matter → metadata.yaml → default.**

`--no-metadata` disables YAML defaults, but leaves block attributes active. Malformed diagram YAML or missing PyYAML when these settings are used aborts conversion with an explicit error.

## Paths, caching, and trust

Renderer subprocesses run in the Markdown file's directory. D2 creates a temporary source there to resolve relative imports; this requires write permission, and the temporary file is removed afterward. External resources are not automatically downloaded or packaged.

Cache keys account for rendering options and the source directory. Figure attributes do not require rerendering. Blocks that suggest external dependencies (`@`, `image`, or `icon`) bypass reuse: this is a conservative policy rather than a dependency parser.

The key includes the launcher's path, size, and modification time, the source directory, and Mermaid's Puppeteer configuration. This detects launcher changes, but cannot detect every internal Node/Chromium or font update. If necessary, remove the affected renderer's temporary md2pdf cache directory. Vega-Lite keys also include the installed `vl-convert-python` version.

Outputs are published through atomic replacement after a successful run and format validation. Cached files are checked on reuse; a damaged entry triggers a warning and regeneration. An invalid result never replaces a valid entry. Cache-key changes may cause a one-time rebuild without requiring manual cache deletion.

Fences of three or more backticks or tildes are recognized in one pass. A diagram shown as an example inside a longer fence is not executed. Detection supports document-level blocks with up to three leading spaces; it does not implement Pandoc's entire list and blockquote grammar.

**Attribute validation does not sandbox the diagram languages. Process trusted documents only.**

## Verification

From the repository root:

```sh
python -m unittest discover -s tests -v
```

Tests with fake renderers cover integration, commands, formats, failures, options, caching, and compatibility. They do not replace visual checks with the real executables.

## Validation and readability

Install optional checks into the same Python environment used for the installer:

```sh
python -m pip install PyMuPDF Pillow
python install-md2pdf.py
```

These libraries are optional for existing installations. The installer also checks for `mmdc`, `d2`, `dot`, `vl-convert-python`, PyYAML, and `xurl`; it does not install dependencies. Launchers use the interpreter selected at installation time. If that interpreter or virtual environment moves, rerun the installer with the intended Python.

| Format | Validation |
|---|---|
| SVG | Valid XML, an `svg` root, a positive `viewBox` when present, and graphic elements outside definitions. CSS visibility is not evaluated. |
| PDF | Header and trailer; with pypdf, a one-page structure with content; with PyMuPDF, opening without repair, a valid single page, and rasterization to detect pages without rendered marks. PyMuPDF takes precedence. |
| PNG | Header, dimensions, chunks, and CRC; with Pillow, decoding and detection of complete transparency. Image meaning is not evaluated. |

White content on transparency is retained for dark-background documents. Very fine or pale details may need manual inspection. Missing optional libraries produce a warning about the reduced validation level. These checks do not guarantee a correct, visible, readable final document: inspect representative PDFs, particularly figures with backgrounds, custom styles, or external resources.

## Label sizing and fonts

The target label size is **12 pt in PDF** and **`.96rem` in HTML**, close to the default 13 pt PDF body. Without explicit width, md2pdf calculates a width intended to reach this size:

- It measures the most prevalent text size in the generated PDF using PyMuPDF, or SVG `font-size` attributes. For PNG, or without a measurement library, it uses the renderer's nominal size.
- Graphviz renders graph, node, and edge text at 12 pt. Explicit `fontsize` and `fontname` attributes take precedence.
- Mermaid renders with `fontSize: 16px` (12 pt at 96 DPI). md2pdf queries `mmdc --help` once and adds `--pdfFit` only when supported; Mermaid CLI 12 removed it.
- Graphviz and Mermaid use Source Sans 3. D2 and Vega-Lite retain their renderer-specific font behavior; the tested vl-convert environment did not resolve the Source Sans 3 OTF font even with its directory registered.
- Width is limited to the text line and height to 560 pt (about 20 cm). A diagram that cannot fit at the target size is reduced.

With PyMuPDF, a warning is emitted if estimated final text is more than 10% below the target, including when a manual width causes the reduction. This uses the engine's reference text width, which may differ for custom margins or columns; text converted to outlines cannot be measured. Explicit width and height retain priority.

A horizontal flow with more than four nodes may become too small: change orientation, shorten labels, or split it rather than shrinking it further.

```sh
md2pdf document.md --strict
```

`--strict` stops before Pandoc when diagram errors occur, as well as for structural lint errors. Small-text and reduced-validation warnings do not abort conversion. Without strict mode, a failed diagram stays as source code and a final message reports unrendered graphics. Enable strict mode in automated delivery commands.

Additional integration checks use:

```sh
python -m pip install PyMuPDF Pillow PyYAML 'vl-convert-python>=1.7,<2'
python -m unittest discover -s tests -v
```

## Renderer architecture

- **Protocol and base class** (`md2pdf.diagrams.base`): `Renderer` defines the contract. `BaseRenderer` provides executable lookup (`find_executable`), cache fingerprints (`cache_tag`), option filtering (`filter_render_options`), and missing-dependency messages.
- **Adapters** (`md2pdf.diagrams.renderers`, `md2pdf.diagrams.vegalite`): `MermaidRenderer`, `D2Renderer`, `GraphvizRenderer`, and `VegaLiteRenderer` declare `allowed_options`, `boolean_flags`, and `render_option_keys`, and implement `validate_option`.
- **Processor** (`md2pdf.diagrams.processor`): `process_diagrams` handles the single-pass scan, hash-based caching (a truncated SHA-1 content digest), and common Pandoc figure attributes (`width`, `height`, `caption`, `id`), delegating renderer-specific behavior to the adapters.
