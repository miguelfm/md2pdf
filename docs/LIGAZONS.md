# Ligazóns nos PDF

Usa ligazóns Markdown explícitas:

```markdown
[Manual de PHP](https://www.php.net/manual/es/)

<https://www.php.net/manual/es/>
```

Un URL entre backticks é código, non unha ligazón PDF explícita.
Inclúe https:// ou http:// no destino das ligazóns externas.

O modelo carga xurl, se está instalado, antes de hyperref. Facilita dividir
URL longas entre liñas sen modificar o destino. Se falta xurl, mantense o
comportamento anterior; non se desactivan as ligazóns.
Non se cambiaron as cores, referencias internas nin as opcións print/night.

## Verificación desta actualización

tests/links.md cobre parágrafos, URL longas, parámetros, fragmentos, táboas,
callouts, referencias internas e URL escritas como código.
tests/test_links.py comproba os destinos URI reais dun PDF usando os filtros
do proxecto e a sección de hyperref do modelo, con cores azul/negro/marrón.
Require Pandoc, pdfLaTeX, os paquetes TeX usados e pypdf.

Esta proba usa un modelo reducido: non certifica a maquetación completa dos
modos normal/print/night. A proba completa con LuaLaTeX non puido realizarse
no contorno de desenvolvemento por falta de luaotfload e fontes de produción.

Para comprobalo na instalación habitual:

```bash
md2pdf tests/links.md --no-toc -o links-normal.pdf
md2pdf tests/links.md --no-toc --print -o links-print.pdf
md2pdf tests/links.md --no-toc --night -o links-night.pdf
```
