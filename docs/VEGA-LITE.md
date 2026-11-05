# Vega-Lite charts

Install the optional dependency into the Python environment that runs md2pdf:

```sh
python -m pip install "vl-convert-python>=1.7,<2"
```

On Arch Linux, use a virtual environment when Python is system-managed; do not use `--break-system-packages`. The launcher must use that environment's Python. Alternatively, activate the environment and run `python md2pdf_runner.py`. On Windows, use the same `python`/`py` interpreter used for md2pdf.

Tested with `vl-convert-python 1.9.0.post1`. It requires neither Node.js nor a browser, and is checked only when a Vega-Lite block is encountered. The renderer uses [vl-convert](https://github.com/vega/vl-convert).

## Syntax

Use a `vega-lite` or `vegalite` fence containing **strict JSON**, without comments or trailing commas. Common diagram attributes `width`, `height`, `caption`, and `#identifier` are supported, along with `theme`.

The default font configuration is `"Source Sans 3", sans-serif`, matching the document's intended visual style. The quotes are required: unquoted, the trailing `3` makes the family name invalid CSS, and vl-convert falls back to Times New Roman. Quote it the same way when a chart sets `config.font`. Actual font availability depends on the renderer; see [label sizing and fonts](DIAGRAMS.md#label-sizing-and-fonts).

Themes: `carbong10`, `carbong100`, `carbong90`, `carbonwhite`, `dark`, `excel`, `fivethirtyeight`, `ggplot2`, `googlecharts`, `latimes`, `powerbi`, `quartz`, `urbaninstitute`, `vox`, or `default`/`none`. Additional styles can be specified in the JSON's `config`. `layout` does not apply to Vega-Lite.

See [examples](vega-lite-examples.md) for histograms, scatter plots with regression, and pie charts. A fitted regression describes the data; it is not a validated prediction.

Output is PDF for LuaLaTeX, PNG for DOCX, and SVG for HTML5. Charts are static, without tooltips or interaction. Fonts must be available to the renderer. JSON `width`/`height` controls chart composition; Markdown attributes control its final document size.

## Optional metadata

```yaml
diagrams:
  vega-lite:
    theme: fivethirtyeight
    width: 85%
```

PyYAML is required only for these metadata settings. Block attributes take precedence.

## Data and trust

Data must be inline in `data.values` or `datasets`. `url`, `href`, and `image` marks are rejected, including nested occurrences. The check is conservative and also rejects data fields with those names. `$schema` may be declared but is not downloaded. External CSV/JSON files are not loaded. The renderer receives `allowed_base_urls=[]` to block external resources. It does not execute Python code from the document.

Conversion runs in a subprocess with a 60-second timeout. This is not a memory/CPU sandbox: use trusted documents.

Missing dependencies, invalid JSON, or conversion failures leave the block as code and emit a warning. Failed conversions do not publish partial outputs. The cache includes the installed `vl-convert-python` version.

## Verification

```sh
python -m unittest discover -s tests -v
```

Real PDF/SVG/PNG tests are skipped when `vl-convert-python` is unavailable. Mermaid, D2, and Graphviz tests remain part of the suite.
