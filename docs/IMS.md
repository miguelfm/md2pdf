# IMS packages for Moodle

md2pdf can bundle Markdown documents into an **IMS Content Package** for Moodle. This is a packaging layer, not a fourth rendering engine: each `.md` is converted to self-contained HTML5, then the HTML files and an `imsmanifest.xml` are placed in a ZIP.

```sh
md2pdf U1/ --ims U1-moodle.zip --lang en
md2pdf U1/*.md --ims U1-moodle.zip --ims-title "Unit 1: Introduction to programming" --lang en
```

```text
U1-moodle.zip
├── imsmanifest.xml
├── U1A1_Introduction.html
├── U1A2_Execution.html
└── U1A3_....html
```

CSS, local images, and SVG diagrams remain embedded in each HTML file. The manifest declares each document as a `webcontent` resource.

## Navigation and ordering

IMS items follow the order collected by md2pdf. Directory inputs use **natural order**, so `U1A2` precedes `U1A10`. Explicit file inputs retain command-line order; a shell-expanded wildcard follows the order supplied by the shell.

Navigation titles use the first available value:

1. `activity` metadata;
2. `title` metadata;
3. the first Markdown H1;
4. the filename.

The package title defaults to the ZIP basename. Override it with `--ims-title`.

## Links between documents

Link to another included Markdown document using a relative path:

```markdown
[Next activity](U1A2_Execution.md#the-java-case)
```

md2pdf rewrites the filename to its packaged HTML counterpart and preserves the fragment:

```html
<a href="U1A2_Execution.html#the-java-case">...</a>
```

Pandoc's heading IDs do not include section numbers after md2pdf preprocessing. Rewriting a filename does not repair a fragment such as `#2-the-java-case`. For stable links, declare an explicit target ID:

```markdown
## 2. The Java case {#the-java-case}
```

A local `.md` link whose document is excluded from the package generates a warning. With `--strict`, it prevents ZIP generation.

## Linked resources

Other local linked files, such as starter code, PDFs, or exercise ZIPs, are copied into the package's **`recursos/`** directory. This directory name is part of the current implementation, including for English documents.

```markdown
Download the [starter code](resources/exercise.zip).
```

```text
U1-moodle.zip
├── imsmanifest.xml
├── U1A1_Introduction.html
└── recursos/
    └── exercise.zip
```

Links are rewritten to the packaged path. A file is copied once even if several documents link to it, and is declared as a `<file>` in each IMS resource that uses it. Distinct files sharing a basename receive suffixes such as `exercise-2.zip`.

Missing resources generate a warning and retain the original link; strict mode prevents ZIP generation. Images use the HTML embedding pipeline instead of this resource-copy mechanism.

## Supported HTML options

IMS reuses HTML output, including `--no-toc`, `--no-number`, `--no-callouts`, `--no-metadata`, `--night`, `--print`, `--plain`, `--strict`, `--toc-depth`, `--lang`, `--highlight`, and an HTML `--template`.

`--titlepage` does not apply. `--watch` is not implemented for IMS. `-o/--output` is not used; provide the destination directly to `--ims`.

## Import into Moodle

Add an **IMS content package** resource to the Moodle course and upload the ZIP. Moodle uses the organization in `imsmanifest.xml` for navigation.

The package follows IMS Content Packaging 1.1.4, with `imsmanifest.xml` at the ZIP root.
