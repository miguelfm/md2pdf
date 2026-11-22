# HTML5 output

The `html` engine produces a single self-contained HTML5 file from the same Markdown used for PDF and DOCX.

```sh
md2pdf document.md -e html --lang en
md2pdf document.md -e html --lang en -o document.html
```

## Architecture

The engine uses Pandoc's HTML5 writer directly, without an intermediate site generator.

| File | Responsibility |
|---|---|
| `md2pdf/engines/html.py` | Pandoc command construction |
| `md2pdf.html` | HTML5 template |
| `md2pdf.css` | Typography, responsive layout, callouts, tables, figures, and printing |
| `html.lua` | HTML callout semantics, captions, and cross-references |
| `md2pdf/diagrams/` | Shared diagram pipeline, requesting SVG for HTML |

Pandoc runs with `--embed-resources`, incorporating CSS, local images, and SVG into the `.html` file.

## Features shared with PDF

- A compact centered table of contents.
- Pandoc section numbering through `--number-sections`.
- `note`, `tip`, `warning`, `danger`, and `info` callouts.
- Interactive tasks (`task`, `tarefa`, `task-box`) with `<textarea>` answer fields, stored in browser `localStorage` per document and task.
- Syntax highlighting and `hl="1,3,5-7"` for selected code lines.
- Terminal blocks (`bash`, `sh`, `.terminal`, etc.) with distinct backgrounds and borders in day, night, and print modes.
- Compact code blocks (`.compact` or `code-compact-threshold`).
- Numbered figures and tables; legacy `*Figura N. ...*` captions are normalized before the HTML filter to avoid duplicate numbering.
- `@fig:`, `@tbl:`, and `@tab:` references as internal links.
- Mermaid, D2, Graphviz, and Vega-Lite rendered as SVG.
- Footnotes and MathML equations.
- `--night`, `--print`, `--plain`, `--no-terminal-blocks`, `--no-toc`, `--no-number`, `--watch`, and `--strict`.

LaTeX pagination rules (`needspace`, `longtable`, `small-table.lua`, etc.) do not run in screen HTML. Printing uses CSS page-break rules.

## Responsive layout and accessibility checks

- Every table is wrapped in `div.table-wrapper`. Narrow-screen horizontal scrolling belongs to the wrapper, preserving the native semantics of `<table>`.
- Callouts have `role="note"` and `aria-labelledby` pointing to their visible title.
- A legacy figure caption supplies `alt` text when the image has no alternative text.
- Informative images without `alt` trigger a warning. Purely decorative images can use `{.decorative}`.
- Final-output checks detect duplicate IDs, broken internal links, missing `aria-labelledby` targets, and unresolved `@fig:`/`@tbl:` references.
- With `--strict`, these problems invalidate the output and the generated HTML is removed.

Checks run on the final HTML, covering elements introduced by filters and Pandoc. They address specific structural issues; they are not a complete accessibility audit.

## Limits

- `--titlepage` does not apply; the title is part of the HTML page.
- DOCX still does not resolve md2pdf's custom `@fig:`/`@tbl:` references.
- Screen HTML is responsive rather than an imitation of an A4 page. `@media print` defines a basic A4 layout for browser printing.
- Vega-Lite charts are static; tooltips and interactivity are not retained.
- Task answers remain in local browser storage. There is no server-side submission or synchronization service.

## Diagrams

| Output engine | Diagram format |
|---|---|
| LuaLaTeX | PDF |
| DOCX | PNG |
| HTML5 | SVG |

Caches are separate by format, so one diagram source can coexist in all three outputs.

Without explicit `width`, diagram width is expressed in `em`, rather than a percentage. The image has class `md2pdf-diagram`, with `font-size: .96rem`, matching table text. Since width in `em` uses the image's own font size, labels retain that target size on narrow screens until `max-width: 100%` must shrink the image to fit. An explicit `width=80%` is respected.

## Self-contained files

A local image such as:

```markdown
![Application architecture](img/architecture.png){width=80%}
```

is embedded rather than retained as an external dependency. The same applies to CSS and generated SVG. System font availability can still affect rendering.

## Moodle / IMS packaging

HTML output is also the basis of multidocument IMS packages:

```sh
md2pdf U1/ --ims U1-moodle.zip --lang en
```

Each Markdown file becomes self-contained HTML; md2pdf adds `imsmanifest.xml` and builds a ZIP. Links between included `.md` files are rewritten to their HTML counterparts. See [IMS.md](IMS.md).
