# md2pdf AI reference: authoring teaching materials in Markdown

This is an **authoring contract** for assistants creating or reviewing teaching materials for md2pdf. Part I covers pedagogy and editing; Part II specifies supported Markdown and output differences; Part III covers validation and delivery.

| Output | Typical use | Notes |
|---|---|---|
| PDF — LuaLaTeX, default | Reading, printing, worksheets | Custom typesetting and pagination |
| Self-contained HTML5 — `-e html` | Browser delivery, Moodle | Responsive layout; structural accessibility/link checks |
| DOCX — `-e docx` | Editable documents | Partial feature support; see each section |

Several HTML documents can also be packaged as an **IMS Content Package** using `--ims`.

“Must” states a rule; “prefer” indicates a guideline with justified exceptions. Examples marked ❌ illustrate mistakes. **Target-repository conventions take precedence** over generic advice here. For example, a course may retain numbered headings and a manual TOC in its Markdown sources; md2pdf removes them and generates output numbering/navigation.

This reference is not itself a conversion sample: its multiple level-one part headings organize the reference. Actual teaching documents use one H1 title.

The documentation is in English. Write teaching content in the language requested by its author. md2pdf's output-language default remains Galician (`gl`); use `--lang en` for English documents. That setting does not translate all generated labels or CLI messages.

# Part I. Pedagogical and editorial principles

## 1. Purpose and priorities

When creating a unit, lesson, task, self-assessment, or answer key, prioritize:

1. **Technical and conceptual correctness.**
2. **Learning sequence:** introduce concepts after their prerequisites.
3. **Understanding:** explain the mental model before accumulating syntax and edge cases.
4. **Application:** accompany important concepts with examples that can be run, checked, or reasoned through.
5. **Unit coherence:** avoid unnecessary repetition and excessive detail reserved for later activities.
6. **Editorial quality:** use tables, diagrams, callouts, and code when they improve understanding.
7. **Portability:** keep the source suitable for PDF, HTML, and, where applicable, Moodle IMS packaging.

Build a coherent learning sequence rather than an encyclopedia or a set of isolated notes.

## 2. Before drafting

Review existing unit plans, syllabi, learning outcomes, assessment criteria, neighboring activities, and prior materials. Respect their terminology, order, and depth.

- Give each activity a clear role in the progression.
- Do not re-explain previous material at length without a reason.
- Introduce later concepts only as far as necessary for the current point.
- Do not invent links to learning outcomes, assessment criteria, or regulations absent from the supplied sources.
- Keep variable names, projects, paths, examples, and tool versions consistent across a unit.

For a complete unit, first distribute concepts across activities and sessions, then draft each piece.

## 3. Structure of an explanatory activity

Not every activity needs identical sections. A useful progression is:

1. Context or problem: why the topic matters.
2. Core concepts, with explicit relationships between them.
3. A minimal example isolating the new idea.
4. An applied example where it adds value.
5. Contrasts and edge cases that prevent likely mistakes.
6. A synthesis or connection to the next activity.

Tasks, self-assessments, and teacher answer keys may be separate files. Respect that separation rather than duplicating an existing practical task inside a theory document.

## 4. Explanations, examples, and depth

Where relevant, explain what something is, what it is for, how it works, how it differs from prior knowledge, the likely misconception, and how to verify it in practice.

Prefer causal explanations to unexplained memorization rules. Examples should be small, executable where appropriate, and compatible with course tool versions. Show output when needed to understand the result. Avoid unnecessary dependencies, APIs, or advanced syntax.

An explanation should be understandable where it appears. When discussing code or output from elsewhere, repeat the smallest relevant fragment with enough context. A cross-reference can extend an explanation but should not replace the fragment being discussed.

## 5. Terminology and language

Use clear, precise language appropriate to the intended learners. When teaching in a language other than English, introduce the English technical term in italics when learners will encounter it in tools or documentation and the translation is not obvious. Do not add redundant English glosses for immediately recognizable translations.

For Galician materials, examples include *token*, *stack trace*, and *cast* alongside their local explanation. Keep commands, API names, identifiers, filenames, and literal tool terminology unchanged.

## 6. Code and terminal examples

Each listing should teach a specific idea. A useful sequence is: introduce the idea, show minimal code, explain non-obvious lines, show the result where helpful, then introduce a variation or common mistake.

Use `hl=` only for lines discussed in the surrounding text. If half a block needs highlighting, simplify or split it.

Separate commands, output, and deliberate error demonstrations clearly. For example, put a command in `bash` and its output in `text`.

## 7. Choosing prose, tables, diagrams, and charts

| Need | Preferred medium |
|---|---|
| Compare properties, options, syntax, or results | Table |
| Simple flow, sequence, or relationship | Mermaid |
| Dense structure, architecture, graph, tree, or automaton | D2 or Graphviz |
| Quantitative data, distributions, trends | Vega-Lite |
| Reasoning, nuance, causes | Prose |

A visual should reduce cognitive load. Use the renderer that expresses the relationship most naturally; do not use Vega-Lite for conceptual diagrams.

When an explanation relates several components, such as a keyboard, terminal, and program, or a client and server, place them in a diagram and show the relevant code/output nearby.

More than six to eight nodes or long labels often makes text too small. Split the diagram, change its orientation or renderer, or use a table. Keep node labels short and put detail in the accompanying text. See section 14.6 for sizing.

## 8. Semantic use of callouts

| Type | Purpose |
|---|---|
| `note` | Clarification or reminder |
| `tip` | Recommended practice or useful shortcut |
| `warning` | Likely mistake or surprising behavior |
| `danger` | Serious failure, data loss, security issue, or hard-to-reverse action |
| `info` | Additional technical context |
| `task` | Practical activity with an editable answer area |

Do not turn every interesting fact into a callout. Several in succession may belong in ordinary prose. Use `warning` and `danger` only when severity justifies them. Syntax is in section 12.

## 9. Tasks, self-assessments, and answer keys

Assess what has already been taught. Do not require an unexplained technique.

- Specify an observable product or result.
- Include restrictions only when they serve the learning goal.
- Request evidence when it helps verify a process or outcome.
- Avoid artificial steps that merely test recipe-following.
- Increase difficulty from direct application toward integration or diagnosis.

Self-assessments should cover important concepts; incorrect choices should reflect plausible misconceptions. Teacher answer keys explain why a solution is correct and, where useful, discuss common mistakes or valid alternatives. Keep answer keys out of student-facing materials. Rubrics should use observable evidence and clear criteria.

## 10. Format-independent writing and accessibility

Avoid position-dependent wording such as “the image below,” “on the next page,” or “on the right.” PDF and HTML can place content differently. Prefer references to named figures, tables, or linked sections.

Every informative figure needs descriptive text. Diagram captions supply HTML alternative text; ordinary image descriptions serve as both caption and alternative text in the supported pipeline. Do not rely only on color to distinguish categories or states.

# Part II. md2pdf syntax and conventions

md2pdf uses Pandoc Markdown. Some parsing rules are stricter than familiar GitHub rendering. Preprocessing transforms or removes some syntax before Pandoc sees it.

## 11. File structure

### 11.1 Blank lines

Always leave blank lines before and after lists, tables, headings, quotations, code blocks, callouts, and display equations. Missing separation can make intended blocks part of the preceding paragraph.

```markdown
❌ Benefits:
- Separation of responsibilities
- Testability

✅ Benefits:

- Separation of responsibilities
- Testability
```

### 11.2 YAML front matter

````markdown
---
module: "Server-side web development"
subject: "Unit 3: Introduction to PHP"
activity: "A01: Control structures"
---

# A01: Control structures
````

| Field | Location / use |
|---|---|
| `module` | PDF title-page context, small caps |
| `subject` | Main title-page text; HTML description metadata |
| `activity` | PDF title page and content-opening label; IMS navigation title |
| `subtitle` | Compatibility alias for `activity` |
| `school` | Lower title-page block |
| `course` | Academic year / course text on the title page |
| `author` | Metadata, HTML header; title-page fallback for absent school |
| `keywords` | PDF/HTML metadata, as a comma-separated string |

Use **one-line scalar values** for ordinary fields. The simple metadata reader does not accept lists or multiline values; write `keywords: "PHP, web development, backend"`. Nested `diagrams:` configuration is handled separately and requires PyYAML.

The front matter is removed from body content. Prefer the H1 for the title rather than depending on a `title` field. Shared metadata can live in `<unit-prefix>-metadata.yaml` (for example `u3-metadata.yaml` for `U3A1.md`), or `metadata.yaml`; `.yml` also works. Front matter overrides external values field by field.

```yaml
# metadata.yaml shared by a directory
author: "Your name"
school: "Your institution"
course: "2026–2027"
keywords: "PHP, web development, backend"
```

### 11.3 Preprocessor transformations

- `[TOC]` and recognized manual TOCs are removed in favor of generated navigation. Source repositories may still require them.
- Body `---` lines are removed, including within callouts. Do not depend on them as visible separators, or use Setext headings underlined with `---`.
- Heading numbering is removed: `## 1.2. Heading` becomes `## Heading`.
- A meaningful initial number can also be stripped: prefer `## Results for 2024` over `## 2024 results`.

### 11.4 Titles and headings

Use one H1 at the beginning as the document title. Start content sections at H2 (`##`), which becomes the first numbered section level. Follow the target repository's source-numbering convention; md2pdf strips source numbers before generating output numbers.

Do not skip levels or use more than three section levels without a clear need.

The current implementation adds icons using **Galician case-sensitive substrings**:

| Pattern | Icon |
|---|---|
| `Tarefa` | 🎯 |
| `Exercicio` | ✏️ |
| `Reto` | 🏆 |
| `Exemplo` | ▶️ |

These are literal implementation patterns, not English words to substitute into the documentation. Avoid adding duplicate icons. `Retorno` unintentionally matches `Reto`; Galician authors can reword that heading as `Valor de retorno`.

## 12. Callouts

### 12.1 Syntax

Prefer English type names across all output formats:

```markdown
::: warning

Never store passwords in plain text.

:::
```

Leave a blank line after the opening. The preprocessor may insert it, but strict validation still expects correct source structure. Callouts may contain lists, tables, and code blocks.

| Type | Aliases | Current PDF label | DOCX alias styling |
|---|---|---|---|
| `note` | `nota` | `Nota` | `nota` is not recognized |
| `tip` | `consello` | `Consello` | Recognized |
| `warning` | `atención`, `atencion` | `Atención` | `atencion` supported; accented `atención` not recognized |
| `danger` | `perigo` | `Crítico` | Recognized |
| `info` | — | `Info` | — |
| `task` | `tarefa`, `task-box`, `taskbox` | `Tarefa` | Task aliases supported |

An unrecognized DOCX alias may become ordinary text. Generated labels currently remain Galician even for an English source; do not promise complete interface localization.

### 12.2 Interactive tasks

```markdown
::: {.task id="exercise-1" height="4cm" placeholder="Write your answer here..."}

Explain the main advantage of an index in a relational database.

:::
```

- **PDF:** a multiline AcroForm field permits typing and saving with a compatible PDF viewer. Verify the intended viewer's support.
- **HTML:** a `<textarea class="task-box-input">` persists answers in browser `localStorage`; print styling provides a writing area. There is no submission backend.
- **DOCX:** a bold task heading and answer-space placeholder.

Attributes include `id`, `height` (`4cm`, `7em`, `120px`, etc.), and `placeholder`.

### 12.3 Alternative syntax

GitHub/Obsidian `> [!NOTE]`, `[!TIP]`, `[!WARNING]`, `[!DANGER]`, `[!INFO]`, `[!TASK]`, and supported uppercase Galician aliases are converted too.

Leading emoji in quotations can trigger callouts: ⚠️ → `warning`, 💡 → `tip`, 📘 → `info`, 📝 → `note`, ⛔ → `danger`, 🎯 → `task`. Avoid these at the start of a literal quotation if no callout is intended.

## 13. Code blocks

### 13.1 Required language

Declare a language for every fence. Missing languages become `text` with a warning and fail strict conversion. Use `text` for terminal output, directory trees, or non-code content.

Common tags include `php`, `html`, `css`, `javascript`, `typescript`, `bash`, `sql`, `json`, `yaml`, `xml`, `python`, `java`, `c`, `cpp`, `markdown`, and `text`.

When showing fenced Markdown as an example, use a longer outer fence than the inner one.

### 13.2 Highlighting lines — PDF and HTML

````markdown
```php {hl="3,5"}
public function store(Request $request)
{
    $validated = $request->validate([
        'name'  => 'required|max:255',
        'email' => 'required|email',
    ]);
}
```
````

Valid forms include `"3"`, `"1,3,5"`, `"2-6"`, and `"1,3,7-9"`. Count from the first line inside the fence, including blank lines. Highlighting applies only to that block and combines with compact/terminal styles. DOCX ignores it, so identify the discussed element in prose as well.

### 13.3 Code captions and references are unsupported

A `: Caption` after a code block appears literally; `@lst:` does not resolve. Introduce code in the preceding paragraph and, if needed, link to its containing section.

### 13.4 Emoji inside code

PDF preprocessing replaces supported emoji with text equivalents, such as ✅ → `[OK]`. Avoid emoji inside code unless the example requires them. Exact replacement strings are implementation-defined.

### 13.5 Terminal blocks

Use an appropriate shell language (`bash`, `sh`, `powershell`, `zsh`, `console`, `cmd`, etc.). PDF and HTML give these blocks distinct styling so readers can distinguish terminal commands from application source code.

Do not add artificial `$`, `>`, `#`, or `>_` prompts to copyable commands unless input/output distinction specifically requires them. md2pdf does not inject such prompts.

### 13.6 Compact listings

````markdown
```python {.compact}
class StudentRepository:
    def __init__(self, connection):
        self.connection = connection
```
````

`.compacto` and `compact=true` are also accepted. Default PDF compact text is 10 pt with 13 pt leading, accommodating roughly 77 columns. Combine with `hl` or use `code-compact-threshold: 25` to compact blocks of at least 25 source lines automatically.

For the normal leading ratio at a smaller size, add `compact-leading="proportional"` to an already compact block. That attribute alone does not enable compact mode.

### 13.7 Marked words and inline code

```markdown
The comparison is [strict]{.mark}.

The condition is [`x < 0 || x > 100`]{.mark}.
```

`.mark` works in PDF and HTML prose. To make inline code bold, place double asterisks outside its backticks, following repository emphasis rules. Markdown inside a code fence remains literal; use `hl` for whole code lines.

### 13.8 Code page breaks — LuaLaTeX

Blocks of up to **12 source lines**, including blank lines, are kept whole and move to the next page if needed:

```yaml
code-keep-lines: 12  # inclusive maximum; 0 disables protection
```

This works with text/terminal blocks, compact mode, automatic thresholds, line highlighting, lists, callouts, and print/night palettes. The threshold does not count extra visual lines created by wrapping, so avoid values that could make a block taller than a page. Lower it if moved blocks leave excessive white space.

Longer blocks can split with open continuation boxes. `lines before break=3` controls the fragment before the break; it does not guarantee three final-fragment lines. Do not add ad hoc `\Needspace` near long tables. HTML/DOCX are unaffected by the PDF protection; HTML print CSS has its own `pre` break rules.

## 14. Diagrams and charts

### 14.1 Common rules

The preprocessor renders `mermaid`, `d2`, `dot`/`graphviz`, and `vega-lite`/`vegalite` blocks. Use attributes to supply a caption, ID, and optional dimensions:

````markdown
```{.mermaid #fig:login-flow caption="Authentication flow"}
flowchart LR
  A[Form] --> B{Valid credentials?}
  B -->|Yes| C[Dashboard]
  B -->|No| A
```

As @fig:login-flow shows, failed validation returns to the form.
````

All renderers support `#id`/`id=`, `caption`, `width`, and `height`. Dimensions use `%`, `px`, `pt`, `cm`, `mm`, or `in`.

- Every informative diagram must have a caption; otherwise HTML warns about missing alternative text and fails strict conversion.
- Captions are literal text, not Markdown. Do not include a manual “Figure N.” prefix.
- Usually omit dimensions; if needed, set width or height rather than both, to avoid distortion.
- One diagram per block.
- Unsupported attributes/values, missing renderers, or syntax errors preserve source code and warn; strict mode fails.

### 14.2 Mermaid

Available diagram types depend on the installed Mermaid CLI. Common types include flowcharts, sequences, classes, states, ER diagrams, Gantt charts, pie charts, mind maps, and timelines. Newer chart types require compatible versions; do not assume every syntax is available in every release.

Keep labels short; use supported `<br/>` or Markdown-string syntax when a break is necessary. Renderer attributes include `layout=dagre|elk`, `look=classic|handDrawn`, and themes such as `base`, `dark`, `default`, `forest`, `neutral`, `neo`, `neo-dark`, `redux`, `redux-dark`, `redux-color`, `redux-dark-color`, and `null`. Defaults can also be set under `diagrams.mermaid`.

### 14.3 D2

Useful for architectures, SQL structures, classes, and conceptual relationships:

- `layout=dagre|elk|tala`; dagre is the default. TALA needs its separate engine/license.
- Numeric `theme`: light IDs `0–8`, `100–105`, `300–303`; default `0`.
- `sketch=true|false` or bare `sketch`.
- `pad=<pixels>`; D2 defaults to 100, often reducible to 20 or 0.
- Numeric `dark-theme`, such as `200–201`, for SVG dark-mode display.
- Document defaults under `diagrams.d2`.

````markdown
```{.d2 #fig:architecture layout=elk sketch caption="Application architecture"}
client -> server: HTTP
server -> data: SQL
```
````

Avoid external icons/images in portable course sources; resources are not automatically downloaded or packaged by the renderer.

### 14.4 Graphviz

Use equivalent `dot` or `graphviz` fences for graphs, trees, or automata. Layouts: `dot`, `neato`, `fdp`, `sfdp`, `circo`, `twopi`, `osage`, and `patchwork`.

````markdown
```{.dot #fig:automaton caption="Transitions between two states"}
digraph {
    rankdir=LR;
    q0 -> q1 [label="1"];
    q1 -> q0 [label="1"];
}
```
````

### 14.5 Vega-Lite

Use static charts for quantitative data. Content must be **strict JSON** without comments or trailing commas. Supply inline `data.values`/`datasets`, or supported generators such as `sequence`. External `url`/`href` and `image` marks are rejected, including data fields with these names.

The configured font is `"Source Sans 3", sans-serif`, subject to renderer font availability; keep the quotes if a chart overrides `config.font`. Themes include `carbong10`, `carbong100`, `carbong90`, `carbonwhite`, `dark`, `excel`, `fivethirtyeight`, `ggplot2`, `googlecharts`, `latimes`, `powerbi`, `quartz`, `urbaninstitute`, `vox`, and `default`/`none`. Additional styles may be set in JSON `config`.

````markdown
```{.vega-lite #fig:times theme=fivethirtyeight width=85% caption="Response time distribution"}
{
  "data": {"values": [{"time": 12}, {"time": 15}, {"time": 15},
                      {"time": 18}, {"time": 22}, {"time": 25}]},
  "mark": "bar",
  "encoding": {
    "x": {"field": "time", "type": "quantitative", "bin": {"maxbins": 5},
          "title": "Time (ms)"},
    "y": {"aggregate": "count", "title": "Frequency"}
  }
}
```
````

JSON dimensions control composition; Markdown dimensions control final size. Charts have no interactive tooltips. Describe a regression transform as a fitted relationship in the supplied data, not as a validated prediction.

### 14.6 Sizing and readability

Without explicit dimensions, md2pdf aims for 12 pt PDF diagram labels and `.96rem` HTML labels. It measures generated text where possible; Graphviz and Mermaid use Source Sans 3. Explicit `fontsize`/`fontname` settings take precedence, so omit them unless intentional.

Tall or wide diagrams must shrink to fit the page. With PyMuPDF, an estimated PDF text size more than 10% below target produces a nonfatal warning. Split the diagram, shorten labels, or change `LR`/`TB` orientation; shrinking width further makes readability worse.

### 14.7 Document defaults

Nested defaults in front matter or `metadata.yaml` require PyYAML:

```yaml
diagrams:
  d2:
    layout: elk
  graphviz:
    layout: dot
  vega-lite:
    width: 85%
```

Precedence per option: block attribute → front matter → metadata file → default. See [DIAGRAMS.md](DIAGRAMS.md) for complete renderer, cache, validation, and trust limits.

## 15. Tables

```markdown
| Method | Route | Description |
|--------|-------|-------------|
| GET | `/users` | List users |
| POST | `/users` | Create a user |

: User resource routes {#tbl:routes}
```

Place the caption after the table, separated by a blank line; reference it with `@tbl:routes`.

- Use equal separator dash counts for content-based widths. A table that fits without wrapping may be centered at natural width; empty answer columns force full width. Unequal dash counts request proportional manual widths where Pandoc supplies them.
- Avoid long unbroken URLs or fully qualified names inside cells. Abbreviate and explain the full form in prose.
- Prefer concise cells rather than several paragraphs per cell.
- Numeric PDF columns with decimals can align by decimal separator. Use plain numbers (`3.5`, not `3.5 s` or inline code). `|:-:|` centers the aligned numeric group.
- PDF tables up to six rows stay whole. Longer tables can split with repeated subdued headings and protection for the first four/penultimate rows. Prefer several focused tables to one enormous table.
- Use `<br>` for a deliberate line break in a cell (PDF/HTML; the custom DOCX behavior is not implemented).

```markdown
| Option | Values |
|--------|--------|
| `visibility` | `public`<br>`protected`<br>`private` |
```

## 16. Images and figures

### 16.1 Captions

```markdown
![Laravel MVC architecture](images/mvc-laravel.png){#fig:mvc width=80%}

The controller separates the model and view in @fig:mvc.
```

The description supplies a numbered caption and HTML alternative text. Informative `![](image.png)` without text warns in HTML and fails strict mode. Pure decoration can use `![](logo.png){.decorative}`.

Do not add legacy manual `*Figura 3. ...*` captions. Paths are relative to the source Markdown; HTML and IMS embed local images.

### 16.2 Large images

**Raster images wider than roughly 800 px or vector PDFs without explicit width can make LuaLaTeX hang in the current pipeline.** Provide a width:

```markdown
![Deployment diagram](img/deployment.png){width=100%}
```

Images are constrained to text width. Resize a copy when necessary rather than destroying the original source image.

### 16.3 Placement

PDF figures stay at their source location rather than floating. Place a figure after the paragraph introducing it; do not add LaTeX placement commands to ordinary teaching sources.

## 17. References and links

### 17.1 Figures and tables

Use `@fig:id`, `@tbl:id`, or `@tab:id`. Capitalized forms such as `@Fig:id` capitalize the generated label. Current labels remain Galician.

These resolve in PDF and HTML, with clickable links in HTML. DOCX retains the literal reference; if DOCX is the main target, name the figure descriptively in prose. An unresolved HTML reference warns and fails strict conversion.

### 17.2 Section links

`@sec:`, `@eq:`, and `@lst:` are unsupported. Use explicit heading IDs:

```markdown
## Explicit conversion {#explicit-conversion}

See [Explicit conversion](#explicit-conversion).
```

Pandoc otherwise generates lowercase IDs with hyphens, stripped punctuation, and potentially retained accents. Preprocessing strips section numbers but does not rewrite link destinations: a source heading `## 1. Conversions` can become `#conversions`, leaving an old `#1-conversions` link broken.

For stable references, declare the ID on the target heading and use the same ID in links, including cross-document links such as `A5_Operators.md#explicit-conversion`. Prefer descriptive IDs without numbers or accents. HTML strict mode checks internal destinations; inspect links between documents in the final package too.

### 17.3 External links

```markdown
[PHP manual](https://www.php.net/manual/en/)

<https://www.php.net/manual/en/>
```

Include `https://` or `http://`. A URL in backticks is code, not an explicit link.

### 17.4 Document and resource links

```markdown
Continue with [Type conversions](U1A5_Operators.md#type-conversions).
```

IMS rewrites included Markdown destinations to HTML and copies other linked local resources such as starter code, PDFs, and ZIPs. See section 19.

To put a small source file inside the PDF, add the `attach` class to a local link, with the file name as link text and the path as destination: `` [`Demo.java`](code/A8/Demo.java){.attach} ``. Do not attach files that the reader must not receive yet, such as solutions. See [ATTACHMENTS.md](ATTACHMENTS.md).

## 18. Other elements

### 18.1 Lists

Leave a blank line before a list. Align nested items with the parent item's text and generally keep nesting to two levels. Use numbered lists for ordered procedures: PDF/HTML emphasize markers and add spacing between steps. Use bullets for unordered items.

### 18.2 Definition lists

```markdown
`app/`
:   The application's main directory.

`routes/`
:   Route definitions, including `web.php` and `api.php`.
```

### 18.3 Emphasis and inline code

Use bold for key terms, italics for work titles or introduced foreign terms, and backticks for identifiers, files, and commands.

Inline code defaults to a theme-colored monospaced face without a background. `--inline-pill` adds an experimental subtle fill. Long paths/expressions can wrap; outside tables, code up to 20 characters is kept whole. Table code can break at available separators when needed, with underscores as a secondary option. Manual widths remain respected; warnings indicate remaining overflow.

Write `\n`, `\t`, `\\`, tildes, carets, and accented characters literally in backticks. Filters handle LaTeX escaping. Prefer a fenced block when length or context requires it.

### 18.4 Quotations

Use `>` for quoted text, and callouts for notices. Leading mapped emoji can turn a quotation into a callout (section 12.3).

### 18.5 Emoji

PDF vector mappings currently include ⚠️ 💡 📘 ❌ ✅ ✓ 🔴 🐛 🖥️ 🌐 ▶️ ⏹ 📝 🔒 🔑 📂 📁 🚀 ⚙️ 🎯 💻 ✏️ 🏆 ⛔. Other emoji may be missing in PDF. Use sparingly and do not substitute them for semantic callouts.

### 18.6 Footnotes

```markdown
Laravel uses Eloquent[^eloquent] for data access.

[^eloquent]: Eloquent implements the Active Record pattern.
```

### 18.7 Equations

Use inline `$O(n \log n)$` or display mathematics:

```markdown
$$
\bar{x} = \frac{1}{n} \sum_{i=1}^{n} x_i
$$
```

Do not add `{#eq:...}` or `@eq:...`: equation cross-references are unsupported. Refer to the formula descriptively in prose.

### 18.8 Side-by-side columns

Pandoc's column divs place short blocks next to each other, such as two small tables that are read together:

```markdown
:::: columns

::: column

| Reference | Object |
|---|:---:|
| `start` | A |

:::

::: {.column width="55%"}

| Object | Class | State |
|:---:|---|---|
| A | `Point` | (3, 3) |

:::

::::
```

The outer div uses four colons so that it can contain the three-colon inner ones. Leave a blank line after each opening. In PDF, `columns.lua` turns each column into a top-aligned minipage; columns without `width` share the width left by the others, minus a 4% gap. A column cannot break across pages, so keep its content short. The reservations of the inner tables are replaced by a single one before the group, which also keeps an introductory paragraph ending in a colon with it. HTML uses flexbox and stacks the columns on narrow screens; DOCX keeps them one after another. Do not describe the layout in the text ("on the left"): name the tables by their content.

## 19. Moodle and IMS packages

Use self-contained HTML for an individual activity, or package a unit:

```sh
md2pdf U1/ --ims U1-moodle.zip --ims-title "Unit 1: Introduction to programming" --lang en
```

Authoring implications:

- Directory inputs use natural filename order (`U1A2` before `U1A10`); explicit file inputs retain CLI order. Name files accordingly.
- Navigation titles use `activity`, then `title`, the first H1, or the filename. Give activities short, distinctive titles.
- Use relative Markdown links. A local `.md` excluded from the package warns and fails strict packaging.
- Other linked local files are copied under the implementation's `recursos/` directory. Missing files warn and fail strict packaging.
- CSS, images, and SVG diagrams are embedded in each HTML document.
- Avoid instructions dependent on physical pages or screen position.

See [IMS.md](IMS.md) for the manifest, rewritten links, duplicate resource names, and supported CLI options.

# Part III. Validation and delivery

## 20. Automatic validation and strict mode

Before conversion, md2pdf reports leading BOMs, malformed/unclosed front matter, missing/unclosed code fences, callout opening/closing errors, missing blank lines after callout openings, and multiple H1 headings.

Diagram failures also warn. HTML adds checks for duplicate IDs, broken internal links, unresolved figure/table references, invalid `aria-labelledby` targets, and informative images without alternative text. IMS checks missing resources and excluded Markdown destinations.

Normal mode continues after these warnings where possible, retaining failed diagrams as source code. `--strict` makes these structural/rendering/target errors fail conversion with a nonzero status. Small diagram text and reduced-validation warnings remain nonfatal.

```sh
md2pdf document.md --lang en --strict
md2pdf document.md -e html --lang en --strict
```

There is no separate check-only CLI mode. Passing validation does not establish that every figure is readable or that the complete document is accessible.

## 21. LaTeX failures and likely causes

These are diagnostic starting points, not unique explanations for each error:

| Message | Possible cause |
|---|---|
| `Extra }, or forgotten $` | Unclosed/malformed callout |
| `Undefined control sequence` | An unclosed code block swallowing later content, or missing preamble/package |
| `Missing $ inserted` | A special character outside code/math |
| `File ended while scanning` | An unclosed source construct |
| `Paragraph ended before \@makecol` | Malformed callout near an unclosed block |
| LuaLaTeX never completes | A large image or vector PDF without explicit width; see section 16.2 |

Inspect the actual source context and logs rather than changing unrelated formatting until the error disappears.

## 22. Delivery checklist

### Content and pedagogy

- [ ] Concepts follow prerequisites and the unit plan.
- [ ] Repetition has a learning purpose; later topics are not introduced in excessive detail.
- [ ] Learning-outcome and assessment mappings come from supplied sources.
- [ ] Examples are focused, coherent, and executable where appropriate.
- [ ] Explanations include the code/output they discuss nearby.
- [ ] Relationships between components have a useful diagram, with relevant code/output alongside.
- [ ] Each table/diagram is the clearest representation of its content.
- [ ] Callouts have a semantic purpose, with justified severity.
- [ ] Student-facing materials exclude teacher answer keys.

### Syntax

- [ ] Ordinary metadata fields are single-line values; `activity` is supplied when required by the course.
- [ ] There is one H1; source numbering/TOC conventions match the repository.
- [ ] No meaningful heading number or accidental `Reto` substring triggers unwanted preprocessing.
- [ ] Body content does not rely on removed `---` separators or manual TOCs.
- [ ] Blank lines surround block elements.
- [ ] Every fence has a language; `hl` marks discussed lines; compact mode is used selectively.
- [ ] Callouts use English type names and blank lines after openings.
- [ ] Informative figures have descriptions; decorative images use `.decorative`.
- [ ] Large images/vector PDFs have explicit width.
- [ ] References use supported figure/table syntax or ordinary section links, without `@sec:`, `@eq:`, or `@lst:`.
- [ ] Inline code is literal Markdown without manual LaTeX escaping.
- [ ] Link fragments match declared target IDs rather than obsolete numbered TOC anchors.
- [ ] External links include a scheme; inter-activity links use relative Markdown paths.

### Verification

- [ ] Run md2pdf and investigate its warnings.
- [ ] Use strict mode for final delivery, including HTML strict mode for web/Moodle output.
- [ ] Set the intended document language explicitly when it differs from the default.
- [ ] Inspect final figures and representative pages visually.
