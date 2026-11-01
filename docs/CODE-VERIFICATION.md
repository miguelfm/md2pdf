# Code pagination verification

This report preserves historical measurements and test results. They are not a new verification run for the documentation translation.

## Keeping short code blocks together

Verification was performed on 20 October 2026, starting from `36e48c8`. The installed preamble, Python modules, and filters were identical to the checkout before changes. Installation used `python3 install-md2pdf.py`.

`keep-code.lua` retains the `CodeBlock` and wraps it in `KeepCodeBlock` when it has at most 12 source lines. The local `md2pdf-code-break` style overrides `breakable` at the end of the Shaded options. `code-keep-lines: 0` disables protection. The option is transported from document YAML or `metadata.yaml` to Pandoc, since preprocessing removes front matter; document metadata takes precedence. This mechanism does not use Needspace.

The change covered `keep-code.lua`, `md2pdf-preamble.tex`, asset lookup, the LuaLaTeX engine, converter, metadata handling, installer, `tests/test_keep_code.py`, `tests/fixtures/code-keep.md`, and the user/AI/verification guides.

### Reproduction

Copy [tests/fixtures/code-keep.md](../tests/fixtures/code-keep.md) into a temporary directory and run `md2pdf code-keep.md`. To reproduce the old behavior with the same installation, add:

```yaml
---
code-keep-lines: 0
---
```

For teaching documents, copy Markdown and its local resources to a temporary directory. Convert there without regenerating the teaching repository's PDFs. Compare page counts with `pdfinfo`, extract individual pages with `pdftotext -f N -l N -layout`, and render affected pages with `pdftoppm -f N -l N -png`.

### Before and after

Conversions used temporary copies of teaching sources. That source repository was not modified. Page numbers here are physical pages, including the TOC.

| Document | Pages before | Pages after | Split blocks before | Split blocks after |
|---|---:|---:|---:|---:|
| synthetic | 3 | 3 | 1 | 0 |
| A3_Consola | 18 | 18 | 2 | 1 |
| A4_Repeticion | 22 | 22 | 6 | 4 |
| A3_Clases | 14 | 14 | 2 | 2 |

- Synthetic: six lines previously split 4+2 across pages 2–3; all six moved to page 3.
- A3_Consola, “O tipo e o intervalo”: six lines previously split 5+1 across pages 8–9; all moved to page 9.
- Invoice (62 lines): still split over pages 12–13 with an open continuation box. The break moved from after `int netCents = units * priceCents;` to after `scanner.close();` because preceding composition changed.
- A4_Repeticion: the 10-line menu moved from pages 14–15 to page 15; the 8-line `digitCount` moved from 20–21 to 21. Four longer blocks remained split on the same pages. In the 45-line block, page 19 now ended at `public static int digitCount(int n) {` instead of a Javadoc `*`.
- A3_Clases: the same breaks, including the exact break positions of the 69- and 37-line blocks.

All source code/terminal blocks, excluding rendered diagrams, were checked against PDF box text using PyMuPDF. No block with at most 12 source lines remained split.

### White space

Approximate gap between the final body text and the bottom of the usable area, excluding the footer:

- Synthetic, page 2: 29 mm before the moved block.
- Consola, page 8: 35 mm, previously 5 mm.
- Repeticion, page 14: 33 mm, previously 7 mm.
- Repeticion, pages 15/17: 42/44 mm, previously 5/3 mm, due to following sections moving. Visible gaps remained below one quarter of the usable height.
- Moving `digitCount` did not create a large page-20 gap; its preceding paragraph continued on page 21.

The default stayed at 12 because these documents did not gain pages. It can be lowered for a different layout preference.

### Recorded checks

- Full suite: `python3 -m unittest discover -s tests -v`; **182 tests, OK, 91.624 s**, no failures or skips.
- Twelve new tests: 12/13-line boundaries; YAML and `-M` transport; zero/invalid values; blank lines; composition with compact mode, thresholds, terminal styles, and `hl`; text/console/terminal/bash; lists/callouts; unchanged HTML and DOCX XML; filter order; front-matter precedence and `--no-metadata`.
- An additional PDF combined short code, highlighted compact terminal content inside a callout, code inside a list, and a 62-line block. Normal/print/night modes worked; the long block continued on pages 3–4.
- With `code-keep-lines: 0`, `pdftotext -layout` matched the previous reference exactly, including page breaks.
- Per-page extraction, rasterization, and visual inspection covered affected pages and long continuations. `git diff --check` passed.
- Environment: Python 3.14.8, Pandoc 3.11, LuaHBTeX 1.24.0 (TeX Live 2026).

### Long-block limit

`lines before break=3` remains in place. It does not guarantee three lines in the final fragment; one long Repeticion listing still leaves a lone closing brace on the following page. No patch to internal tcolorbox/fvextra break algorithms was introduced. See the [tcolorbox breakable algorithm and options](https://github.com/T-F-S/tcolorbox/blob/master/doc/latex/tcolorbox/tcolorbox.doc.breakable.tex).

All 42 installed assets/Python files matched the source byte for byte at final verification. The three teaching Markdown sources were unchanged. The four final PDFs were regenerated after the last metadata adjustment, retaining the reviewed text and page breaks.

Source SHA-256 values:

| Source | SHA-256 |
|---|---|
| A3_Consola.md | `1dcdb26e3476e0aa10d9f6deb3f94ed56c8a3bbf51537ef5dddc47e5a8d39f1f` |
| A4_Repeticion.md | `930a6068d87e8da36b80fe756cccbcaf03395960764a15fd3e983ccfd21e61b1` |
| A3_Clases.md | `7ab3194604daa16bfdc4c5ee50876260625ea93e5e03ee82b661d6c2afafa493` |
| synthetic.md | `ef3744e6ed5c29b52672d36ac8ee4d2d607d4fc64f2c9f3a767e2d02fad0bec9` |

## Introductory paragraphs and wrapped lines

Review on 1 November 2026 started from `93864ce`, with checkout filters matching installed files before the change.

Two teaching documents (DWCS U2A1/U2A5) left an introductory paragraph at a page bottom, separated from its code/table:

- **Code:** a five-source-line `text` block, including a 217-character line, occupied nine visual PDF lines and 154 pt. The old reservation counted source lines, reserving nine baselines (169 pt) for the paragraph and block. The paragraph stayed, while the unbreakable block moved.
- **Table:** a six-row table with mostly wrapped cells measured about 275 pt. The old rows-plus-five-plus-paragraph estimate reserved 13 baselines (244 pt), which was insufficient.

Changes:

- `keep-with-next.lua` estimates code wrapping at 66 characters, measured for 10.8 pt Source Code Pro. The 217-/92-character lines estimate to four/two visual lines. Overlong words can break anywhere. The `code-keep-lines` threshold still counts source lines.
- `small-table.lua` adds 0.9 baseline lines for each extra wrapped row line when reserving small tables together with preceding content.
- Blocks/tables without wrapping retain their former reservation.

Reservations became 13 baselines (244 pt) for about 204 pt of content, and 19 (357 pt) for about 330 pt. Both introductory paragraphs then moved with their blocks. Four new tests in `tests/test_keep_with_next.py` and `tests/test_small_table.py` failed with the old filters and passed with the new ones.

### Document title extraction

A separate pre-existing error appeared for a document beginning with a level-one title, introductory paragraph, and code: `LaTeX Error: No \title given`. Moving Needspace above the title prevented Pandoc's `--shift-heading-level-by=-1` title extraction, which requires the title to be the first block.

Reservations now stop at level-one headings; an immediately following table does not reserve space before the title. Two regression tests were added, and `test_reserve_goes_before_headers` now uses section levels 2/3.

### Code-heavy cells

DWCS U3T5, a five-row table with code in every cell, still left an introductory paragraph alone. The estimator used 5 pt per character for code, while 11.8 pt Source Code Pro measured 7.1 pt. A 45-character call was incorrectly estimated as one line in a 243 pt cell instead of two.

Code now uses 7.1 pt per character, with wrapping for words wider than a column. The reservation rose from 15 to 19 baselines (357 pt for about 330 pt). A new regression test fails with the old filter.

### Excessive table reservations

A four-row, two-lines-per-row rubric with a narrow points column gained a page and left half a page blank. The estimator removed LaTeX commands but counted the `heading-section` argument of `\color` as visible text, making a 49 pt heading cell appear to need three lines. Removing that argument reduced the reservation from 15 to 13 baselines; a regression test covers it.

The standalone rubric still had seven pages because its roughly 210 pt table fit in 220 pt, while the 245 pt reservation forced a break. Standalone unbreakable tables do not need the extra wrapped-line allowance: they return to rows-plus-five, reducing the rubric to six pages. Another regression test covers this case.

## Activity labels stranded at page bottoms — 1 November 2026

PROG tasks U1T3, U2T2, and U4T1–U4T3 could leave `activity` labels at the bottom of one page and the first `##` heading on the next. In U4T1, the label ended 125 pt above the footer while the following section requested 151 pt.

The measured label occupies about 118 pt, or six baselines. Its block now starts with `\Needspace{14\baselineskip}` (6 + 8) and the marker `% md2pdf:activity-label`. Both pagination filters move the first section's reservation above the label and add its six lines.

Three tests in `tests/test_activity_label.py` cover this. Filter tests fail with the old filters; the PDF test verifies that the unprotected label is on page 1 while the section is on page 2, and that the protected pair moves together to page 2.
