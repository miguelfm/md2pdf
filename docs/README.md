# md2pdf user guide

md2pdf converts Markdown into PDF, DOCX, and self-contained HTML5 on Linux and Windows. It combines Pandoc with custom templates, Lua filters, preprocessing, and validation for technical documentation and teaching materials.

See the [project introduction](../README.md) for use cases and a short example. This guide covers installation, authoring, output differences, command-line options, typography, and customization.

## Contents

- [Installation](#installation)
- [Usage](#usage)
- [Command-line options](#command-line-options)
- [Metadata](#metadata)
- [Markdown preprocessing](#markdown-preprocessing)
- [Callouts and interactive tasks](#callouts-and-interactive-tasks)
- [Code](#code)
- [Diagrams and charts](#diagrams-and-charts)
- [Equations and cross-references](#equations-and-cross-references)
- [Tables](#tables)
- [Images and figures](#images-and-figures)
- [Output formats and reading modes](#output-formats-and-reading-modes)
- [Typography and pagination](#typography-and-pagination)
- [Validation](#validation)
- [Using AI assistants](#using-ai-assistants)
- [Project structure](#project-structure)
- [Design decisions](#design-decisions)
- [Customization](#customization)
- [Possible future work](#possible-future-work)
- [License](#license)

## Installation

### Dependencies

Install Python and Pandoc for all three output engines. Pandoc 3.8 or later is recommended; md2pdf selects older compatibility flags when needed (`--highlight-style` before 3.8 and `--mathml` before 3.11).

```sh
# Arch Linux
sudo pacman -S pandoc

# Debian/Ubuntu
sudo apt install pandoc

# Windows
winget install JohnMacFarlane.Pandoc
```

For **PDF**, install LuaLaTeX, the TeX packages used by the template, and the document fonts. The following is the Arch Linux dependency set used by this project; package names and distribution packaging can change:

```sh
sudo pacman -S texlive texlive-latexextra texlive-fontsrecommended \
               texlive-luatex texlive-binextra \
               texlive-langspanish texlive-langenglish \
               texlive-fontsextra
sudo pacman -S adobe-source-sans-fonts adobe-source-serif-fonts \
               adobe-source-code-pro-fonts otf-stix
```

Source Sans 3 is the default body and heading font; Source Serif 4 is used with `--serif`, Source Code Pro for code, and STIX Two Math for equations. TeX font packages and system font registration are different: LuaLaTeX/luaotfload must be able to find the OpenType fonts. The current code selects Source Code Pro for monospaced text; installing JetBrains Mono alone does not make it the default.

For **Windows**, follow [INSTALL_WINDOWS.md](INSTALL_WINDOWS.md), which includes assisted scripts and manual installation steps.

For **HTML and DOCX**, LaTeX is not required. Optional renderers may have their own format-specific requirements.

Install only the diagram tools you need:

```sh
# Arch Linux: external diagram executables
sudo pacman -S mermaid-cli d2 graphviz

# Mermaid on other systems with Node.js
npm install -g @mermaid-js/mermaid-cli

# Optional Python chart renderer and validation libraries
python -m pip install PyMuPDF Pillow PyYAML 'vl-convert-python>=1.7,<2'
```

Use a virtual environment when Python is system-managed. PyYAML is needed for nested `diagrams:` settings. PyMuPDF and Pillow improve output validation; pypdf provides a PDF structural fallback. The installer checks dependencies and does not install them.

### Install md2pdf

Run from the repository root using the intended Python interpreter:

```sh
python install-md2pdf.py
```

On Linux, the launcher is installed at `~/.local/bin/md2pdf`; the package, templates, filters, and theme are copied to `~/.local/share/md2pdf/`. On Windows they are placed in `%LOCALAPPDATA%\md2pdf\`, with a `md2pdf.cmd` launcher.

The launcher uses the Python interpreter selected during installation. Do not delete or move its virtual environment. If you move it or select a different Python, reinstall md2pdf.

Installed resources are read from the installed copy, not from your checkout. After changing source code or assets, rerun the installer.

If necessary, add the Linux launcher directory to `PATH`:

```sh
# Fish
fish_add_path ~/.local/bin

# Bash: add to ~/.bashrc; Zsh: add to ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"
```

Reopen your terminal after persistent PATH changes. See the Windows guide for user-level PATH configuration.

### Uninstall

```sh
python install-md2pdf.py --remove
```

### Run from a checkout

Without installing a launcher:

```sh
python md2pdf_runner.py notes.md -e html --lang en
```

## Usage

```sh
# One file: PDF through LuaLaTeX, without a separate title page
md2pdf notes.md --lang en

# A separate PDF title page
md2pdf notes.md --lang en --titlepage

# An explicit output filename; one input only
md2pdf notes.md --lang en -o output.pdf

# Several files, each producing its own output
md2pdf *.md --lang en

# All Markdown files collected from a directory
md2pdf course/ --lang en

# Omit the table of contents or section numbering
md2pdf notes.md --lang en --no-toc
md2pdf notes.md --lang en --no-number

# Editable Word / LibreOffice output
md2pdf notes.md -e docx --lang en

# A self-contained HTML5 file
md2pdf notes.md -e html --lang en

# Table-of-contents depth and highlighting theme
md2pdf notes.md --lang en --toc-depth=2 --highlight=tango

# Disable decimal alignment in PDF tables
md2pdf notes.md --lang en --no-decimal-align

# Rebuild while editing
md2pdf notes.md --lang en --watch
```

**The default document language is `gl` (Galician).** Pass `--lang en` for English language metadata and typesetting. This does not translate source content, CLI messages, or all generated labels. Galician callout labels and keyword-based heading icons remain part of the current implementation.

### Watch mode

`--watch` keeps running and recompiles when input Markdown or associated metadata changes. It uses standard-library polling once per second. With several inputs, any detected change rebuilds all of them. Press `Ctrl+C` to stop.

A viewer that reloads updated PDFs, such as SumatraPDF on Windows or Zathura/Evince on Linux, can be used alongside the editor. Watch mode is not implemented for IMS packaging.

## Command-line options

| Option | Purpose | Default / scope |
|---|---|---|
| `-o`, `--output` | Output filename; requires one input | Input basename with `.pdf`, `.docx`, or `.html` |
| `-e`, `--engine` | `lualatex`, `docx`, or `html` | `lualatex` |
| `--no-toc` | Omit the table of contents | TOC enabled |
| `--no-number` | Disable section numbering | Numbering enabled |
| `--titlepage` | Generate a separate title page | PDF only; off |
| `--listings` | Legacy option, accepted but ignored with a warning | Deprecated |
| `--print` | Print palette: black links, reduced backgrounds | PDF/HTML; off |
| `--night` | Warm sepia reading palette | PDF/HTML; off |
| `--serif` | Use Source Serif 4 for body text | Default body is sans-serif |
| `--inline-pill` | Add a subtle background to inline code | Experimental; off |
| `--watch` | Rebuild when Markdown/metadata changes | Off |
| `--plain` | Omit TOC, styled title, activity label, and numbering | Off |
| `--debug` | Keep temporary files and print the Pandoc command | Off |
| `--strict` | Fail on structural Markdown and diagram errors; also validate HTML/IMS targets | Off |
| `--no-callouts` | Disable callout filtering | Callouts enabled |
| `--no-decimal-align` | Disable decimal alignment in numeric table columns | PDF alignment enabled |
| `--no-terminal-blocks` | Disable distinct terminal-block styling | Styling enabled |
| `--no-metadata` | Ignore metadata files and front matter | Metadata enabled |
| `--toc-depth` | Table-of-contents depth | `3` |
| `--lang` | Document language | `gl` |
| `--paper` | Paper size | `a4` |
| `--highlight` | Syntax theme | `drake-jb.theme` when found, otherwise `pygments` |
| `--template` | Custom LuaLaTeX/HTML template | Automatic lookup; not applicable to DOCX |
| `--ims PACKAGE.zip` | Package input documents as HTML in an IMS ZIP | Off |
| `--ims-title TITLE` | IMS organization title | ZIP filename without extension |

Use `md2pdf --help` for the installed CLI's available options. For IMS, set the output through `--ims`, rather than `-o`.

## Metadata

The document title is taken from its first level-one heading. Standard metadata, including author, keywords, and language, is included where supported by the output format.

Metadata is loaded from an external file, then overridden field by field by the Markdown file's YAML front matter. md2pdf looks first for a unit-specific name such as `u3-metadata.yaml` for `U3A1.md`, then `metadata.yaml`; `.yml` is also supported.

```yaml
# metadata.yaml shared by a directory of course documents
author: "Your name"
school: "Your institution"
keywords: "PHP, web development, backend"
course: "2026–2027"
```

````markdown
---
module: "Server-side web development"
subject: "Unit 3: Introduction to PHP"
activity: "A01: Control structures"
---

# A01: Control structures
````

| Field | Use |
|---|---|
| `module` | Context line on a PDF title page |
| `subject` | Main title-page text; HTML description metadata |
| `activity` | PDF title page and content-opening label; IMS navigation title |
| `subtitle` | Compatibility alias for `activity` |
| `school` | Lower title-page block |
| `author` | Document metadata; title-page fallback when `school` is absent |
| `course` | Academic year / course text on the title page |
| `keywords` | Comma-separated metadata string |
| `body-font` | `serif` selects serif body text |
| `decimal-align` | `false` disables PDF decimal alignment |
| `terminal-blocks` | `false` disables distinct terminal backgrounds |
| `inline-pill` | `true` enables the optional inline-code background |
| `code-compact-threshold` | Source-line count at which code becomes compact; `0` disables automatic compaction |
| `code-keep-lines` | Maximum source lines for keeping an entire PDF code block together; default `12`, `0` disables |
| `keep-with-next` | `false` disables the reservation keeping an introductory paragraph with its following block |
| `diagrams` | Nested defaults for individual diagram renderers; requires PyYAML |

Use single-line scalar values for ordinary fields; lists and multiline values are not supported by the simple metadata reader. The nested `diagrams:` section is handled separately. Omit metadata entirely if not needed, or pass `--no-metadata` to disable loading it.

Inspect PDF metadata with:

```sh
pdfinfo document.pdf
```

## Markdown preprocessing

Before Pandoc conversion, md2pdf:

- Removes manual TOC sections recognized by the preprocessor, plus Typora `[TOC]` markers, so Pandoc can generate the output TOC.
- Removes `---` body separators, including within callouts, while handling front matter separately.
- Strips manual heading numbering, such as `## 1. Heading` becoming `## Heading`.
- Converts GitHub/Obsidian callouts into Pandoc fenced divs and ensures the required blank line after their opening.
- Extracts YAML front matter instead of rendering it as body text.
- Adds icons to headings containing configured Galician keywords.
- Converts supported emoji to FontAwesome5 icons for LuaLaTeX, and to plain-text equivalents inside code when preparing PDF output.
- Detects missing code languages; these become warnings and cause strict-mode failure rather than automatic syntax inference.

Fenced examples are protected from ordinary prose transformations. PDF emoji replacement in code is a deliberate format-specific exception.

Use one `#` title per document, sections beginning at `##`, and blank lines around block elements. A heading beginning with a number followed by a space can lose that number: prefer `## Results for 2024` over `## 2024 results`.

### Automatic heading icons

The current case-sensitive substring patterns are Galician and do not change with `--lang`:

| Pattern | Icon | Intended use |
|---|---|---|
| `Tarefa` | 🎯 | Required task |
| `Exercicio` | ✏️ | Guided exercise |
| `Reto` | 🏆 | Challenge |
| `Exemplo` | ▶️ | Example |

An existing emoji is not duplicated. LaTeX icons are scaled to 90%. Substring matching also means `Retorno` matches `Reto`; reword a heading if that icon is unintended. Edit `HEADING_ADMONITIONS` in `md2pdf/config.py` to customize these patterns.

## Callouts and interactive tasks

Use English type names for the most consistent behavior across outputs:

```markdown
::: note

Call `session_start()` before sending HTML output.

:::
```

GitHub/Obsidian syntax also works:

```markdown
> [!WARNING]
> Never store passwords in plain text.
```

| Type | Accepted aliases | PDF color | Purpose |
|---|---|---|---|
| `note` | `nota` | Blue | Clarification or reminder |
| `tip` | `consello` | Green | Recommended practice |
| `warning` | `atención`, `atencion` | Orange | Common mistake or caution |
| `danger` | `perigo` | Red | Serious failure or data/security risk |
| `info` | — | Cyan | Additional technical context |
| `task` | `tarefa`, `task-box`, `taskbox` | Indigo | Editable answer area |

Not every Galician alias is styled in DOCX: `nota` and accented `atención` are not recognized there, while `atencion` is supported. Generated labels such as `Nota`, `Atención`, and `Tarefa` currently remain Galician.

A blockquote starting with ⚠️, 💡, 📘, 📝, ⛔, or 🎯 can also become a corresponding callout. Use ordinary quotes without these leading emoji when you intend a quotation.

### Interactive tasks

```markdown
::: {.task id="exercise-1" height="4cm" placeholder="Write your answer here..."}

Explain the difference between TCP and UDP.

:::
```

- **PDF:** an AcroForm multiline `\TextField` allows editing and saving answers in viewers with compatible form support. Check the intended viewer before distributing a worksheet.
- **HTML:** a `<textarea class="task-box-input">` saves answers in browser `localStorage` per document/task. Printing uses a bordered writing area. Storage is local to the browser; there is no answer-submission service.
- **DOCX:** a bold task heading and an answer-space placeholder replace the interactive field.

Task attributes include `id`, `height` (for example `4cm`, `7em`, or `120px`), and `placeholder`. GitHub-style `> [!TASK]` is also accepted.

## Code

### Syntax highlighting and line highlighting

Always declare a language, including `text` for output or directory trees. The bundled `drake-jb.theme` uses a GitHub Light-inspired palette. Pandoc syntax definitions cover common web and programming languages.

````markdown
```php {hl="1,3,5-7"}
$user = $_POST['user'];
$hash = password_hash($pass, PASSWORD_DEFAULT);
echo $user;
$stmt = $pdo->prepare($sql);
$stmt->execute([$hash]);
$result = $stmt->fetch();
```
````

`hl` accepts individual lines and ranges, counting from the first line inside the block, including blank lines. LuaLaTeX uses `hl-lines.lua` and fvextra's native `highlightlines`; HTML retains the attribute as `data-hl` and marks lines in the browser. DOCX does not implement this feature. Highlight only the lines discussed in the explanation, and identify them in prose too.

Customize the PDF highlight background in the preamble:

```latex
\colorlet{hl-line-bg}{yellow!18!white}
\fvset{highlightcolor=hl-line-bg}
```

The bundled `javadoc.xml` adjusts Pandoc's Javadoc syntax so accented comment text receives consistent comment styling. It is loaded with `--syntax-definition` in PDF and HTML.

### Terminal blocks

Shell languages such as `bash`, `sh`, `zsh`, `powershell`, `console`, and `cmd`, or the `.terminal` class, receive subtly different borders and backgrounds in PDF and HTML. Day, night, and print palettes are supported. md2pdf does not inject prompts or headers that would interfere with copying commands.

Use `--no-terminal-blocks` or `terminal-blocks: false` to disable the distinction. Keep commands and their output in separate language-tagged blocks when this improves clarity.

### Compact code

Normal PDF code is approximately 10.8 pt with 15.4 pt leading and room for about 71 columns. Compact mode uses 10 pt with 13 pt leading, about 77 columns, reducing listing height by roughly 16% under the default layout.

````markdown
```python {.compact}
class StudentRepository:
    def __init__(self, connection):
        self.connection = connection
```
````

`.compacto` and `compact=true` are also accepted. Compact blocks can combine terminal styling and line highlighting:

````markdown
```bash {.compact hl="1"}
docker run -d --name db -p 5432:5432 postgres:16
docker logs -f db
```
````

For compact text with the normal mode's leading ratio, use:

````markdown
```php {.compact compact-leading="proportional"}
<?php for ($i = $total + 1; $i <= $maxTotal; $i++): ?>
    <td></td>
<?php endfor; ?>
```
````

In PDF this keeps 10 pt type and reduces normal leading proportionally, about 7.7% with the defaults. HTML similarly retains the normal ratio. The attribute alone does not activate compact mode; without it, `.compact` uses the denser 13 pt leading.

To compact every listing with at least 25 source lines:

```yaml
code-compact-threshold: 25
```

The default threshold is `0` (disabled).

### Code pagination

In PDF, blocks of up to 12 source lines, including blank lines, are kept together. Set `code-keep-lines` to change the inclusive threshold, or `0` to disable protection. This works with terminal blocks, compact mode, highlights, lists, callouts, and print/night palettes.

Longer listings can split across pages. Their boxes open at the break: the first fragment has no bottom border and the continuation has no top border; the final fragment closes normally. `lines before break=3` controls the initial fragment, but does not guarantee three lines in the final fragment.

The threshold counts source lines, rather than wrapped visual lines. Avoid a threshold that could create a box taller than the page. Moving a short block may leave blank space; lower the threshold if needed. Do not add ad hoc `\Needspace` commands around code near long tables.

### Inline code and marked text

By default, inline code is monospaced, with a theme-colored foreground and no background. `--inline-pill`, `inline-pill: true`, or `\mdpdfinlinepilltrue` enables the experimental pill background: subtle gray `#F0F2F5` by day, cream `#EDE8DC` at night, and transparent in print. Rounded corners and horizontal padding are 1.5 pt, with no vertical padding to disturb paragraph leading.

Short inline code is protected from splitting: at most 8 characters, or at most 15 without separators, with a separate 20-character rule outside tables. An underscore does not by itself split a protected identifier. Longer paths and expressions can break at separators without visible hyphens.

In tables, if protected code does not fit the assigned cell, it can break at spaces, operators, and separators, then underscores as a secondary option. Automatic widths use the same segmentation; manual widths are respected. A warning indicates code that still cannot fit. There are no arbitrary breaks inserted into identifiers to hide a width problem.

Write backslashes, accents, tildes, and carets literally inside Markdown backticks; the filters escape them for LaTeX. Do not add LaTeX escapes yourself. To highlight a word or inline expression in PDF and HTML:

```markdown
The comparison is [strict]{.mark}.

Check [`x < 0 || x > 100`]{.mark}.
```

These spans do not act inside fenced code. Code blocks do not support numbered captions or `@lst:` references; introduce them in prose and link to their containing section.

## Diagrams and charts

Supported fences are `mermaid`, `d2`, `dot`/`graphviz`, and `vega-lite`/`vegalite`. Each renderer is optional and is checked only when its block type is used.

````markdown
```{.mermaid #fig:flow caption="Request processing"}
flowchart LR
    A[Request] --> B{Valid?}
    B -->|Yes| C[Response]
    B -->|No| D[Error]
```

See @fig:flow.
````

Use a caption for every informative diagram. It supplies the figure description and HTML alternative text. Do not add a second manual “Figure N.” caption. Captions are literal text, not rich Markdown.

- **Mermaid:** flows, sequences, classes, states, ER diagrams, and other types supported by the installed CLI. Attributes include `layout`, `theme`, and `look`; availability depends on that version.
- **D2:** architecture, conceptual diagrams, and SQL structures. Supports `layout=dagre|elk|tala`, numeric themes, `sketch`, `pad`, and `dark-theme`.
- **Graphviz:** graphs, trees, and automata. Layouts include `dot`, `neato`, `fdp`, `sfdp`, `circo`, `twopi`, `osage`, and `patchwork`.
- **Vega-Lite:** quantitative charts from inline JSON data, including bars, lines, scatter plots, histograms, and regression fits. Outputs are static, without interactive tooltips.

````markdown
```{.d2 layout=elk sketch caption="Client and database services"}
client -> server: HTTP
server -> database: SQL
```

```{.dot caption="State transitions"}
digraph {
    rankdir=LR;
    q0 -> q1 [label="1"];
}
```
````

The shared pipeline requests vector PDF for LuaLaTeX, PNG for DOCX, and SVG for HTML. Mermaid CLI 12 removed `--pdfFit`; md2pdf queries `mmdc --help` and uses the flag only when supported.

Rendering uses subprocesses with timeouts and validated caches. Missing tools or failed diagrams leave source code and warnings in normal mode, and fail conversion with `--strict`. Renderer attributes do not provide a sandbox; use trusted sources.

See [DIAGRAMS.md](DIAGRAMS.md) for options, per-document YAML defaults, paths, caching, validation levels, sizing, and architecture; [VEGA-LITE.md](VEGA-LITE.md) for chart dependencies and data restrictions; and [vega-lite-examples.md](vega-lite-examples.md) for runnable charts.

## Equations and cross-references

Pandoc accepts standard inline `$...$` and display `$$...$$` mathematics:

```markdown
Inline: $E = mc^2$.

$$
\int_a^b f(x)\,dx = F(b) - F(a)
$$
```

PDF uses STIX Two Math through `unicode-math`. HTML uses MathML: `--math-method=mathml` with Pandoc 3.11 or later, and `--mathml` with earlier versions.

md2pdf resolves figure and table references in LuaLaTeX (`figure-captions.lua`) and HTML (`html.lua`) without `pandoc-crossref`:

```markdown
![System diagram](img/diagram.png){#fig:system width=80%}

The process is shown in @fig:system.

| Engine | Editable |
|--------|----------|
| LuaLaTeX | No |
| DOCX | Yes |

: Output comparison {#tbl:engines}

See @tbl:engines.
```

Use `@fig:`, `@tbl:`, or `@tab:`. Initial-capital forms (`@Fig:`, `@Tbl:`) capitalize the generated label. Current generated labels are Galician. In HTML the references are clickable internal links.

`@sec:`, `@eq:`, and `@lst:` are not resolved. DOCX does not resolve this custom figure/table reference system either. For sections, use explicit IDs and normal Markdown links:

```markdown
## Explicit conversion {#explicit-conversion}

See [Explicit conversion](#explicit-conversion).
```

Preprocessing removes heading numbering but does not rewrite link fragments. An old `#1-conversion` link can therefore break when the output heading becomes `conversion`. Declare stable IDs for references within and between documents. Pandoc's automatic IDs can retain accented letters.

## Tables

### Content-based widths

`auto-table-widths.lua` calculates widths from cell content instead of relying on arbitrary Markdown separator lengths:

- A table that fits without wrapping within 85% of the line is centered at natural width. Columns left empty for student answers force full text width.
- Effective cell length is capped at 60 characters so a long listing does not consume all width.
- Header text, short monospaced code, and long words contribute minimum widths. Glyph-width tables use the selected body font, bold Source Sans headings, and Source Code Pro.
- Space is taken from the column whose shrinkage adds the least table height, using a 2 pt lookahead margin. Ties prefer the column with more spare width.
- Minimums are not imposed above 60% of a line. When all minimums cannot fit, the smallest are satisfied first and the remaining columns share the rest.
- Unbreakable prose may overrun a cell slightly; the estimator allows 8 pt before forcing adjustment. Long code uses its available break points.

### Manual widths

Different dash counts in a separator request proportional widths; the filter then preserves Pandoc's calculated widths and applies heading styling only:

```markdown
| Type | Description | Example |
|------|--------------------------|------------|
```

Pandoc calculates relative widths only when a table line exceeds 72 characters. Alignment colons also affect its calculation. The filter detects equal dash counts despite their colons so an ordinary centered/right-aligned table can still receive automatic sizing.

### Long tables and page breaks

PDF tables of up to six rows use an unbreakable `tabular` with reserved space. Longer tables remain `longtable`, repeating column headings on continuation pages in a subdued, normal-weight italic style (`heading-section!65`). No extra continuation/footer rows are inserted.

The first four body rows and the penultimate row are protected with `\\*`, reducing very short initial fragments and a lone final row. Zebra-striping state is reset at the start of each long table. Minor color-pattern shifts can still occur on continuation pages of very long tables.

### Table styling

- `\small` text: about 11.86 pt with 17.14 pt leading under the default 13 pt layout.
- `\arraystretch{1.5}` adds row spacing; horizontal `\tabcolsep` is 6 pt.
- Bold sans-serif column headings use `heading-section`, matching the current day/night/print palette.
- Alternating rows use `gray!6!white`; redundant horizontal `\toprule`, `\midrule`, and `\bottomrule` rules are suppressed.
- HTML tables inherit body line-height with vertical padding of `.37rem` (`.36rem` on narrow screens), and live in responsive scrolling wrappers.
- PDF numeric columns with at least one decimal align on the decimal separator when all nonempty cells contain numbers. Both dot and comma decimal forms are accepted. Units or inline-code formatting prevent numeric detection. Markdown alignment positions the aligned group as a whole.

```markdown
| Operator | Operation | Result |
|:-:|---|:-:|
| `*` | Multiplication | 14 |
| `/` | Division | 3.5 |
```

Disable PDF decimal alignment with `--no-decimal-align` or `decimal-align: false`.

### Line breaks and vertical alignment

Use `<br>` within cells for a deliberate line break. `br.lua` converts it to LaTeX `\newline{}` only inside tables; HTML handles it natively, while DOCX does not implement this custom behavior.

Pandoc's `p{}` columns are top-aligned. Inline-code boxes are anchored with `\leavevmode` so they align with other cell content. Do not redefine `p{}` recursively using `\newcolumntype`: that can cause infinite recursion with LuaLaTeX/fontspec/polyglossia.

## Images and figures

Images are limited to text width. In PDF, figures are placed at their source position rather than floating freely. Captions are centered, in smaller type, with a bold numbered label.

```markdown
![Application architecture](img/architecture.png){#fig:architecture width=80%}
```

Informative images need descriptive text. Purely decorative images can use `![](logo.png){.decorative}`. In HTML and IMS, local images are embedded into the output.

**Large raster images (roughly over 800 px wide) and vector PDFs without explicit dimensions can make LuaLaTeX hang in the current sizing pipeline.** Set a width, such as `{width=100%}`, or resize the source. If resizing, work on a copy when the original must be preserved:

```sh
magick large.png -resize 800x smaller.png
```

The problem involves the interaction of Pandoc's `\pandocbounded{}`, `adjustbox`, and fixed-position figures. Diagram preprocessing supplies explicit dimensions to avoid it.

Screenshot borders are not implemented reliably; see [possible future work](#possible-future-work).

## File attachments

A local link with the `attach` class embeds the file in the PDF, with a paperclip icon after the link text:

```markdown
[`code/A8/DuplicateCost.java`](code/A8/DuplicateCost.java){.attach}
```

Each file is also listed once among the document's attachments, for viewers that only show those. The viewer shows only the file name. In HTML the link downloads the file; in DOCX it is an ordinary link. A missing file or a URL stops the conversion. Some viewers do not open attachments, so keep the path in the link text. See [ATTACHMENTS.md](ATTACHMENTS.md).

## Output formats and reading modes

### PDF / LuaLaTeX

The default output uses a project-owned KOMA-Script template and preamble: body typography, table layout, code blocks, vector FontAwesome5 icons, footnotes, and STIX Two Math equations. Compilation time depends on the document, fonts, diagrams, and TeX environment; previous short-document runs typically took several seconds.

### DOCX

```sh
md2pdf notes.md -e docx --lang en
```

DOCX is generated by Pandoc without LaTeX. Headings, paragraphs, lists, tables, footnotes, metadata, and a Pandoc TOC/section numbering are supported. Callouts become text with bold label prefixes through `callouts-docx.lua`.

Limits include no md2pdf syntax highlighting or `hl` line highlighting, no custom `@fig:`/`@tbl:` resolution, and no PDF title-page or print layout. Unsupported PDF-only options can be ignored with a warning.

If `reference.docx` is found alongside the assets, it supplies Word styles. Create a base file and edit its styles in Word or LibreOffice:

```sh
pandoc -o reference.docx --print-default-data-file reference.docx
```

### HTML5

```sh
md2pdf notes.md -e html --lang en
```

HTML uses Pandoc's native HTML5 writer, `md2pdf.html`, `md2pdf.css`, and `html.lua`. CSS, local images, and generated SVG are embedded with `--embed-resources`. It supports callouts, code highlighting, figure/table links, responsive tables, MathML, print/night modes, and local task-answer storage.

Screen layout is responsive; LaTeX page reservation rules do not apply. Browser printing uses CSS break properties and basic A4 page rules. `--titlepage` does not apply. See [HTML.md](HTML.md) for details and accessibility checks.

### Moodle / IMS

```sh
md2pdf U1/ --ims U1-moodle.zip --ims-title "Unit 1: Introduction to programming" --lang en
```

The ZIP contains `imsmanifest.xml` at its root and self-contained HTML for every input document. Directory inputs use natural order; explicit file inputs retain their CLI order. Navigation titles use `activity`, then `title`, the first H1, or the filename.

Links between included Markdown files are rewritten to HTML. Other linked local files are packaged under `recursos/`. Missing documents/resources warn in normal mode and prevent package generation in strict mode. See [IMS.md](IMS.md).

### Print mode

`--print` uses black links, white code backgrounds with gray borders, unfilled inline code, and no alternating PDF table-row shading. LuaLaTeX callouts retain borders but lose colored fills. HTML applies the print appearance on screen as well as its `@media print` rules.

```sh
md2pdf notes.md --lang en --print -o notes-print.pdf
```

### Warm reading mode

`--night` is a **warm light/sepia palette**, not a dark background:

| Element | Color |
|---|---|
| Page | `#F5F0E8` |
| Text | `#2C1A0E` |
| Code background | `#EDE8DC` |
| Inline-code text | `#7A4F2E` |
| Links, callout accents, TOC title | `#8B6347` |
| Section / subsection / subsubsection | `#6B3A1F` / `#8B5230` / `#A86A42` |

Icons use muted orange `#8B6347`, medium brown `#7A4F2E`, sienna `#A0522D`, or warm beige `#9E8872` according to their role.

```sh
md2pdf notes.md --lang en --night -o notes-warm.pdf
```

## Typography and pagination

### Fonts, color, and spacing

The default body and headings use Source Sans 3 (with Source Sans Pro as a fallback). `--serif` or `body-font: serif` selects Source Serif 4 for body text. Code uses Source Code Pro. PDF tables use lining numerals; serif running text can use old-style numerals. HTML uses Source families where installed and web-safe fallbacks otherwise.

Day-mode section colors are slate blue: `#1C2F4A`, `#2E4B72`, and `#4A6A96` from sections to subsubsections. Print mode uses black.

The PDF preamble enables microtype protrusion and approximately ±1% font expansion to improve optical margins and spacing. Paragraphs use `0.45em` separation without indentation. Code uses `0.45em` before and `0.7em` after; quotations use `0.45em` before and `0.6em` after.

| Heading | Before | After | Approximate total with paragraph spacing |
|---|---|---|---|
| Section | `1.2em` | `0.4em` | `1.65em` / `0.85em` |
| Subsection | `1.0em` | `0.3em` | `1.45em` / `0.75em` |
| Subsubsection | `0.8em` | `0.3em` | `1.25em` / `0.75em` |

Numbered procedural lists use bold theme-colored markers and `itemsep=0.5em`; nested lists and ordinary bullets use the more compact `0.25em`. HTML mirrors these distinctions with `::marker` and relative spacing. This separates multline instructions while keeping short feature lists compact.

### Widows, orphans, and introductory paragraphs

The PDF defaults discourage isolated lines with `\widowpenalty=3000`, `\clubpenalty=3000`, and `\displaywidowpenalty=2000` without making composition impossible.

Section, subsection, and subsubsection headings reserve 8, 7, and 6 baseline lines. Consecutive headings share protection: `\if@nobreak` avoids forcing a break between a heading and its immediate subheading.

`small-table.lua` reserves a heading and its following table together. For up to six rows, the estimate is rows plus five baseline lines, plus wrapping allowances of 0.9 lines per extra visual row line. Consecutive headings add three lines per earlier heading. For longer tables, it reserves the column header and the first protected body fragment, estimating each row at 1.4 lines plus 0.9 per extra wrapped line.

Cell wrapping estimates use about 5 pt per prose character and 7.1 pt per code character; long words can wrap, and LaTeX commands such as `\color` do not count as visible text. These are estimates: an overestimate can move content earlier than necessary.

A paragraph ending in a colon before code, a list, or a table is kept with the material it introduces. `keep-with-next.lua` estimates prose at about 85 characters per line and code at 66, reserving a whole short block or the first four lines of a longer one. Source lines still determine `code-keep-lines`. A list reserves its first item, up to four lines; tables use their own estimator.

Reservations can move above preceding section headings, but never above the level-one document title: Pandoc must see it as the first block to extract the title. `keep-with-next: false` disables introductory-paragraph protection.

Standalone small tables retain the simpler rows-plus-five reservation, without extra wrapping allowance: an unbreakable table already moves whole if it cannot fit. Long tables remain splittable. See the historical [code pagination verification](CODE-VERIFICATION.md) for measured cases and limitations.

### Titles and activity labels

Without `--titlepage`, the document title is centered before the TOC. If `activity` is present, an opening label appears before the first `##`, with decorative rules sized to the text. Long labels wrap; nonbreaking spaces in the metadata are preserved as LaTeX `~`.

The label uses `heading-section` and reserves 14 baselines: approximately six for itself and eight for the following section. If no section follows, it reserves six. The `% md2pdf:activity-label` marker lets pagination filters place combined reservations before the label.

With `--titlepage`, the separate PDF cover uses `module` as a tracked small-caps context line, `subject` as the main title, `activity` as the subtitle, and `school`/`course` in the lower-right block. `author` is the fallback when school is absent. The activity label also opens the content. About 28% of the page height is left above the cover text.

There are no running page headers. Page numbers sit at the lower outside corner through KOMA-Script's `\rofoot` and `\lefoot`, keeping repeated header text out of copied code.

### Language and hyphenation

The default document language is Galician; use `--lang` for another language. The default setup also includes English/Spanish language handling and technical-word hyphenation exceptions. `\tolerance=1500` allows somewhat wider spaces before excessive hyphenation.

## Validation

Before conversion, md2pdf reports a leading BOM, unclosed or misplaced YAML, missing or unclosed code fences, malformed/unclosed callouts, missing blank lines after callout openings, and multiple level-one headings.

Normally these are warnings. With `--strict`, structural problems stop conversion before Pandoc and return a nonzero status. Diagram failures also stop strict conversion. Diagram small-text and reduced-validation warnings do not.

HTML checks the final output for duplicate IDs, broken internal links, invalid `aria-labelledby` targets, unresolved figure/table references, and informative images without alternative text. Strict mode removes invalid generated HTML. IMS adds checks for excluded Markdown destinations and missing local resources.

Pandoc's own `[WARNING]` messages are also shown after conversion, deduplicated and limited to ten. They do not automatically become strict-mode failures.

```sh
md2pdf notes.md --lang en --strict
md2pdf notes.md -e html --lang en --strict
```

There is no separate lint-only CLI mode. Validation catches specific defects, not all visual or semantic issues. Inspect final diagrams and representative pages. See [diagram validation](DIAGRAMS.md#validation-and-readability) and [PDF links](LINKS.md) for check coverage and historical verification limits.

## Using AI assistants

[md2pdf-ai-reference.md](md2pdf-ai-reference.md) is an optional authoring contract for assistants creating teaching materials. It brings together pedagogy, supported syntax, format differences, and delivery checks.

Provide it at the start of the conversation or in the assistant's instructions, with your unit plan and existing material:

```text
[Contents of md2pdf-ai-reference.md]

Create an activity on [topic] using the reference above.
Write the material in [language] and follow the target repository's conventions.
```

The reference helps avoid unsupported references, malformed callouts, missing blank lines, and GitHub-specific Markdown assumptions. A teacher still chooses the learning progression, which code lines deserve highlighting, callout severity, and whether diagrams are readable.

## Project structure

```text
md2pdf/
├── README.md                  Project introduction
├── LICENSE                    GNU GPL version 3 text
├── md2pdf_runner.py           Checkout / installed Windows entry point
├── install-md2pdf.py          User-level Linux and Windows installer
├── md2pdf/                    Python package
│   ├── __main__.py            CLI and watch mode
│   ├── config.py              Defaults, fonts, mappings, version compatibility
│   ├── assets.py              Asset and dependency lookup
│   ├── metadata.py            Metadata extraction
│   ├── preprocess.py          Markdown preprocessing
│   ├── lint.py                Structural checks
│   ├── converter.py           Conversion orchestration
│   ├── ims.py                 IMS packaging
│   ├── diagrams/              Renderer protocol, adapters, processing, cache
│   ├── mermaid.py             Mermaid compatibility API
│   └── engines/               LuaLaTeX, DOCX, and HTML engines
├── md2pdf.latex               Pandoc / KOMA-Script PDF template
├── md2pdf-preamble.tex        PDF styling and typography
├── md2pdf.html                Pandoc HTML5 template
├── md2pdf.css                 Responsive HTML, night, and print styling
├── drake-jb.theme             Syntax highlighting theme
├── javadoc.xml                Javadoc syntax adjustment
├── *.lua                      Pandoc transformations and layout filters
├── scripts/windows/           Assisted Windows setup and smoke sample
├── tests/                     Automated tests and fixtures
└── docs/                      User guides, examples, and verification notes
```

Filters include `auto-table-widths.lua`, `small-table.lua`, `br.lua`, `callouts.lua`, `callouts-docx.lua`, `html.lua`, `hl-lines.lua`, `compact-code.lua`, `keep-code.lua`, `keep-with-next.lua`, `terminal-blocks.lua`, `term-pairs.lua`, and `figure-captions.lua`.

## Design decisions

### Pandoc and LuaLaTeX

Pandoc supplies one document model for the three outputs. LuaLaTeX and the custom KOMA-Script `scrartcl` template provide PDF typography and explicit control of tables, page breaks, headings, links, and code boxes. The class option is `fontsize=13pt`, rather than the short `13pt` form that puts KOMA-Script into its historical `version=first` compatibility mode.

A previous Typst engine was removed because it lacked feature parity: filters, callouts, line highlighting, references, and newer inline-code handling diverged. PDF now has one supported composition engine; HTML uses Pandoc's native writer rather than duplicating another PDF layout implementation.

The title page is generated as LaTeX and injected with Pandoc `-B` separately from the body template, avoiding competing cover-page mechanisms.

### Default page layout

A4 side margins are 22 mm, leaving a 166 mm text area (about 472.3 pt). Top/bottom margins are 14/16 mm, with 7 mm footskip. These defaults balance room for code and tables with readable prose.

`ragged2e` settings include:

```latex
\setlength{\RaggedRightRightskip}{0pt plus 3.8em}
\RaggedRightParfillskip=0pt plus 0.75\textwidth
```

The right-skip setting encourages moderate line lengths; the paragraph-fill setting discourages very short final lines without inserting rigid boxes. Actual line lengths and page density depend on content and fonts. HTML uses `text-wrap: pretty` where supported. These choices do not by themselves certify accessibility conformance.

### Fonts and color

Source Sans, Source Serif, and Source Code provide a related visual vocabulary. STIX Two Math supplies OpenType mathematics through `unicode-math`, compatible with the fontspec-based PDF setup.

The bundled highlighting palette was selected for contrast on `#f6f8fa`. Recorded contrast ratios include:

| Token | Color | Recorded contrast |
|---|---|---|
| Normal | `#24292e` | 13.8:1 |
| Keyword | `#cf3544` | 4.7:1 |
| Operator | `#cf222e` | 5.0:1 |
| Variable | `#b54700` | 5.1:1 |
| DataType | `#005cc5` | 5.9:1 |
| Function | `#6f42c1`, bold | 6.1:1 |
| String | `#0a3069` | 12.0:1 |
| Comment | `#6a737d`, italic | 4.5:1 |
| Preprocessor | `#8250df`, bold | 4.7:1 |
| Attribute | `#953800` | 6.9:1 |
| Other | `#1b7c83` | 4.6:1 |

### Why replace emoji in PDF?

FontAwesome5 icons follow ordinary LaTeX colors, so print/night modes can recolor them. Color emoji fonts embed their own colors and do not respond to `\color{}` in the same way. Vector icons also avoid requiring a platform-specific color emoji font.

Supported PDF emoji include ⚠️ 💡 📘 ❌ ✅ ✓ 🔴 🐛 🖥️ 🌐 ▶️ ⏹ 📝 🔒 🔑 📂 📁 🚀 ⚙️ 🎯 💻 ✏️ 🏆 ⛔. In code, mappings use plain text such as `[OK]`, `[X]`, `[bug]`, `[Web]`, `[PC]`, `[nota]`, `[lock]`, `[key]`, `[dir]`, `[cfg]`, or `[obj]`. Mapping strings remain implementation-defined and are not translated by this documentation.

To experiment with native color emoji, customize `EMOJI_MAP` and configure a suitable font in the preamble; this changes print/night behavior and is not the default:

```latex
\newfontfamily\emojifont{NotoColorEmoji}[Renderer=HarfBuzz]
\usepackage{newunicodechar}
\newunicodechar{🚀}{{\emojifont 🚀}}
```

### Why render diagrams before Pandoc?

An early nested Python → Pandoc → Lua → mmdc → Chromium pipeline could hang while Chromium inherited file descriptors and waited for input. Python subprocess control allows explicit `stdin=DEVNULL`, controlled environment, and timeouts. Mermaid's Puppeteer configuration uses `--no-sandbox` for environments where Chromium's sandbox is unavailable; documents must therefore be trusted.

Preprocessing produces ordinary Markdown images with explicit sizes. Pandoc then receives standard image content, avoiding renderer subprocesses inside Lua filters and the separate LuaLaTeX issue with unsized vector images.

## Customization

### Assets and lookup

Assets are looked up in the running package's parent directory (`INSTALL_DIR`: the installed data directory or checkout root), then the current working directory. Template lookup additionally searches Pandoc's template directories. Use `--template` for an explicit template path.

Edit installed assets deliberately, or edit the checkout and rerun the installer; a checkout edit alone does not update an installed launcher.

### Highlighting and visual style

- `drake-jb.theme`: Pandoc JSON highlighting palette.
- `md2pdf-preamble.tex`: PDF headers/footers, microtypography, widow/orphan rules, heading protection, language exceptions, spacing, quotations, figures, code, tables, mathematics, TOC/heading colors, and icons.
- `md2pdf.css` and `md2pdf.html`: HTML styling and structure.
- `reference.docx`: optional Word styles.

### Font selection

`md2pdf/config.py` declares `FONT_CANDIDATES`; `_detect_font()` checks candidates with `luaotfload-tool`. Current candidates prefer Source Sans 3 / Source Sans Pro for sans, Source Serif 4 / Source Serif Pro for serif, and Source Code Pro for mono. To select another monospaced font, change the candidate configuration rather than relying on installation alone.

Add technical-word exceptions to `\hyphenation{}` in the PDF preamble.

### Table width tuning

Important `auto-table-widths.lua` parameters include:

| Parameter | Default meaning |
|---|---|
| `MAX_CELL_LEN = 60` | Effective cell-length cap |
| `CHAR_WIDTH = 0.013` | Estimated mono character width as a fraction of the line |
| `MAX_MBOX_LEN = 15` | Short-code protection limit, alongside the shorter unconditional rule |
| `NATURAL_MAX_TOTAL = 0.85` | Natural-width table threshold |
| `SANS_REGULAR_PT`, `SERIF_PT` | Measured body-font glyph widths at table size |
| `SANS_BOLD_PT` | Bold heading glyph widths |
| `SPACE_PT`, `OTHER_PT` | Word spacing / fallback glyph width; body-font dependent |
| `LINE_PT = 472.3` | Reference A4 text width with 22 mm side margins |
| `TABCOLSEP_PT = 6` | Cell side padding |
| `WORD_MARGIN = 1.03` | Word-width safety margin |
| `OVERFLOW_PT = 8` | Allowed small overflow for unbreakable words |
| `LOOKAHEAD_PT = 2` | Margin while choosing a column to shrink |

The selected body family changes the measurement tables. Explicit per-table widths can instead be requested with different separator dash counts; see [manual widths](#manual-widths).

### Heading icons and callouts

Edit `HEADING_ADMONITIONS` and `CALLOUT_BLOCKQUOTE_TYPES` in `md2pdf/config.py`. PDF callout styles are defined in `callouts.lua`; HTML and DOCX have their own filters. Keep behavior consistent across the formats you intend to support.

### PDF metadata in the preamble

For custom PDF language/producer metadata:

```latex
\AtBeginDocument{%
  \hypersetup{%
    pdflang=en,
    pdfcreator={md2pdf + LuaLaTeX + Pandoc},
    pdfproducer={md2pdf},%
  }%
}
```

Prefer the existing `--lang` option for ordinary document-language selection.

## Possible future work

These are ideas, **not implemented features or delivery commitments**:

- Interactive task-list checkboxes with PDF form fields and persistent HTML controls.
- Embedded starter files in PDFs and corresponding HTML downloads.
- Collapsible hints/solutions, with format-appropriate fallbacks.
- An optional wider notes margin for Cornell-style study materials.
- More configurable semantic callout titles.
- A dedicated `<kbd>` rendering filter.
- Further stabilization of the experimental inline-code pill styling.
- Reliable subtle borders around screenshots.

The older roadmap also mentioned escaping inline backslashes; current filters already handle literal backslashes, tildes, carets, and accented text, so that is documented as supported behavior rather than a pending feature.

## License

See [LICENSE](../LICENSE) for the GNU General Public License, version 3. Third-party components retain their respective licenses.
