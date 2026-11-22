# File attachments in PDFs

A local link with the `attach` class embeds the file in the PDF:

```markdown
The program [`DuplicateCost.java`](code/A8/DuplicateCost.java){.attach}
compares both algorithms.
```

In PDF output, `attach.lua` turns the link into a file attachment annotation
(`attachfile2`). The link text keeps its formatting and is followed by a
paperclip icon; activating it opens or saves the embedded file. The text and
the icon are part of the page content, with an annotation of the same size
and an empty appearance on top: `\textattachfile` alone would draw the text
only inside the annotation, and a viewer that hides annotations would lose
the file name as well.

Each file is also registered once among the document's attachments
(`embedfile`, `/EmbeddedFiles` in the catalog), however many links point
to it. Some viewers list only those: zathura with its poppler plugin shows
no attachment for a PDF that only has annotations. The viewer
shows only the file name, without the path. Text files get `text/plain`
from their extension, and other files `application/octet-stream`; set
`mimetype=` in the link attributes to change it.

In HTML the link points to the file and has a `download` attribute. In DOCX
and the other outputs it stays an ordinary link.

The path is relative to the document's directory. A missing file or a URL
stops the conversion, so no PDF is produced with an empty attachment.

## Viewer support

The file is always inside the PDF, but not every viewer exposes it.
Observed on 5 November 2026:

- poppler 26.10, used by zathura's `:export`, listed the document
  attachments and not the annotation ones.
- Chromium 156 on Linux drew the paperclip, did not react to clicks on the
  link or the icon, and showed no attachments panel, not even for the
  document attachments.

The paperclip already marks the link as an attachment, so the link text can
be just the file name, with the path in the destination. A reader whose
viewer does not open attachments sees that name: make sure the file can be
found under it wherever the material is published.

## Verification

`tests/test_attach.py` checks the generated LaTeX, the HTML and native
outputs, the errors for a missing file and for a URL, and, when LuaLaTeX,
`attachfile2` and `pdfdetach` are available, that a PDF built with the
project template embeds byte-identical files under their bare names,
including a name with an underscore, without the local directory. With
pypdf, it also checks that the link text is in the page content, that
the page has one attachment annotation per link, and that the document
attachments hold each file once.
