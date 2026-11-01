# Diagram update verification

This is a historical verification report. Its results describe the environment and revision tested at the time, rather than a fresh test of every current renderer.

## Changes covered

PDF/SVG/PNG output and cache validation; regeneration of damaged entries; invalidation after launcher/configuration changes; readability warnings; strict-mode failure on diagram errors; paths with spaces; an installer that pins the Python interpreter and checks optional dependencies; documentation updates.

This update did not change the sizing algorithm or Mermaid arguments. The new cache key requires one rebuild. Fuller validation requires PyMuPDF and Pillow; see [DIAGRAMS.md](DIAGRAMS.md) for installation and limits.

## Recorded results

- 31 automated tests passed, with no skips.
- Real Vega-Lite PDF, SVG, and PNG conversion, plus cache reuse.
- All seven Mermaid PDFs supplied for the review passed validation.
- A teaching Markdown sample (`U1A3_Estrutura.md`) retained an image in the Pandoc AST and `includegraphics` in LaTeX, including with a temporary path containing spaces. The renderer call was replaced by copying the supplied PDF; this was not a fresh mmdc render.
- The sample retained its automatic width of 98.2% and emitted an estimated 6.6 pt text-size warning.
- Tests covered corruption, cache reuse, superficially successful but invalid outputs, blank PDF pages, white content intended for dark backgrounds, strict mode, and launcher paths with spaces/apostrophes.

## Limits

The real Mermaid, D2, and Graphviz CLIs were not installed in that environment; command construction and integration used substitutes. The complete production LuaLaTeX template was not compiled because TeX was incomplete. The link test used pdfLaTeX and the project's filters/template snippet.

A representative production build still requires visual review. Validators detect specific defects; they do not guarantee correct, visible, readable content throughout the final document.
