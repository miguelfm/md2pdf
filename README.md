# md2pdf

**Write Markdown once. Publish a typeset PDF, an editable Word document, or a self-contained HTML page.**

md2pdf is a command-line document publishing tool built on [Pandoc](https://pandoc.org/). It adds a coordinated set of templates, filters, and checks for technical documentation and teaching materials: readable code, diagrams, tables, equations, callouts, and consistent typography across formats.

It runs on Linux and Windows. PDF output uses LuaLaTeX; HTML and DOCX output do not require a TeX installation.

## What can you use it for?

- **Teaching materials:** course notes, programming lessons, lab guides, worksheets, and answer areas that students can fill in.
- **Technical documentation:** tutorials, reference guides, architecture explanations, and reports with code and diagrams.
- **Multiple delivery formats:** distribute a PDF for reading or printing, a DOCX for editing, and an HTML file for a browser from the same source.
- **Moodle courses:** package several Markdown documents and their linked resources into an IMS Content Package with navigation between activities.

## Choose an output

| Output | Best suited to | What to expect |
|---|---|---|
| **PDF** — LuaLaTeX, the default | Reading, printing, and worksheets | Custom typography and page layout, multipage tables, vector diagrams, and AcroForm task fields |
| **HTML5** — `-e html` | Browser reading and web delivery | A responsive file with embedded CSS and local images, SVG diagrams, MathML, and task answers stored in the browser |
| **DOCX** — `-e docx` | Editing in Word or LibreOffice | An editable document, with simpler callout formatting and fewer layout features |
| **IMS ZIP** — `--ims course.zip` | Importing a set of activities into Moodle | HTML documents, an IMS manifest, linked local resources, and rewritten links between included documents |

IMS is a packaging layer over HTML, rather than a separate rendering engine.

## Highlights

- Convert a file, several files, or a directory; use `--watch` to rebuild while you edit.
- Render **Mermaid, D2, Graphviz, and Vega-Lite** blocks using optional renderers, with caching and output validation.
- Use syntax highlighting, highlighted code lines, compact listings, and distinct terminal blocks.
- Add callouts, numbered figures and tables, cross-references, footnotes, and equations.
- Share course metadata between documents and optionally generate a PDF title page.
- Select a warm reading palette with `--night`, a print palette with `--print`, or serif PDF body text with `--serif`.
- Catch structural Markdown problems and failed diagrams with `--strict`; HTML also checks internal links, IDs, and image descriptions.

## Get started

Clone the repository, or download and extract its ZIP, then open a terminal in its root directory. This project uses the included installer; it is not installed with `pip install md2pdf`.

1. Install **Python** and **Pandoc**. Pandoc 3.8 or later is recommended.
2. For **PDF**, also install LuaLaTeX and the required TeX packages and fonts. See the [Linux dependency instructions](docs/README.md#dependencies) or the [Windows installation guide](docs/INSTALL_WINDOWS.md).
3. Install md2pdf with the Python interpreter you want its launcher to use:

```sh
python install-md2pdf.py
```

The installer copies the application and its assets into your user directories. It checks dependencies but does not install them. Add the launcher directory to `PATH` if prompted, then reopen your terminal.

```sh
# PDF, with English document language
md2pdf notes.md --lang en

# A single HTML file, without requiring LaTeX
md2pdf notes.md -e html --lang en

# An editable Word document
md2pdf notes.md -e docx --lang en

# Rebuild as you edit
md2pdf notes.md --lang en --watch

# Check structure and diagrams as part of the conversion
md2pdf notes.md --lang en --strict

# Build a Moodle package from a directory of activities
md2pdf course/ --ims course.zip --ims-title "Introduction to programming" --lang en
```

**Document language defaults to Galician (`gl`).** Pass `--lang en` for English documents. This selects document language metadata and typesetting rules; it does not translate your content or every built-in label. Some generated labels and command-line messages currently remain in Galician.

## A small source example

Save this as `notes.md`:

````markdown
---
author: "Your name"
subject: "Introduction to programming"
activity: "Variables and values"
---

# Variables and values

## Your first variable

A variable gives a name to a value:

```python {hl="1"}
message = "Hello, world!"
print(message)
```

::: tip

Choose names that describe what a value represents.

:::

## Try it

::: {.task id="first-variable" height="4cm" placeholder="Write your answer here..."}

What changes if you assign a different string to `message`?

:::
````

Use one level-one heading for the document title, start sections at `##`, and leave blank lines around lists, tables, code, and callouts. PDF task fields depend on your viewer's form support; HTML answers are stored locally in the browser, without a submission service.

## Documentation

- [User guide](docs/README.md): installation, options, Markdown syntax, typography, and customization.
- [Windows installation](docs/INSTALL_WINDOWS.md): assisted setup scripts and manual instructions.
- [Diagrams](docs/DIAGRAMS.md) and [Vega-Lite charts](docs/VEGA-LITE.md), with [chart examples](docs/vega-lite-examples.md).
- [HTML output](docs/HTML.md), [Moodle / IMS packages](docs/IMS.md), [PDF links](docs/LINKS.md), and [file attachments](docs/ATTACHMENTS.md).
- [AI authoring reference](docs/md2pdf-ai-reference.md): an optional guide for drafting teaching materials that work with md2pdf.
- Historical verification notes: [diagram validation](docs/DIAGRAM-VERIFICATION.md) and [code pagination](docs/CODE-VERIFICATION.md).

## Current limits

PDF, HTML, and DOCX share a source format, but their features differ. DOCX does not implement md2pdf's figure/table cross-references or line highlighting. Vega-Lite charts are static. Diagrams require their corresponding renderer, and visual checks are still needed for final documents.

Process Markdown from trusted sources: Pandoc, LaTeX, and the diagram tools are not a sandbox. Read the [diagram guide](docs/DIAGRAMS.md#paths-caching-and-trust) for renderer and resource restrictions.

## Development

Run the application from a checkout without installing it:

```sh
python md2pdf_runner.py notes.md -e html --lang en
```

Run the existing test suite from the repository root:

```sh
python -m unittest discover -s tests -v
```

Some integration tests require Pandoc, TeX, fonts, or optional Python libraries and renderers. After changing an installed application's source or assets, rerun `python install-md2pdf.py` to update its installed copy.

## License

See [LICENSE](LICENSE) for the GNU General Public License, version 3. Third-party components retain their respective licenses.
