# Links in PDFs

Use explicit Markdown links:

```markdown
[PHP manual](https://www.php.net/manual/en/)

<https://www.php.net/manual/en/>
```

A URL in backticks is code, rather than an explicit PDF link. Include `https://` or `http://` in external link destinations.

When installed, `xurl` is loaded before `hyperref`, allowing long URLs to break across lines without changing their targets. Without `xurl`, existing link behavior is retained. Link colors, internal references, and print/night options are unaffected by that optional package.

## Historical verification

`tests/links.md` covers paragraphs, long URLs, parameters, fragments, tables, callouts, internal references, and URLs written as code. `tests/test_links.py` checks actual PDF URI destinations using the project filters and the template's hyperref section, with blue/black/brown link colors. It requires Pandoc, pdfLaTeX, the relevant TeX packages, and pypdf.

This test uses a reduced template and does not certify the complete normal/print/night layout. At the time of this verification, a complete LuaLaTeX run was unavailable in the development environment because luaotfload and the production fonts were missing.

To check a normal installation:

```sh
md2pdf tests/links.md --no-toc -o links-normal.pdf
md2pdf tests/links.md --no-toc --print -o links-print.pdf
md2pdf tests/links.md --no-toc --night -o links-night.pdf
```
