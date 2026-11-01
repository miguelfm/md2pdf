# Revisión de code-keep-lines

Verificación realizada o 20 de outubro de 2026 sobre a revisión de partida `36e48c8`.

O preámbulo, os módulos Python e os filtros existentes comprobáronse contra a instalación antes de cambialos: idénticos. A instalación final faise con `python3 install-md2pdf.py`.

Implementación: `keep-code.lua` conserva o CodeBlock e envólveo en KeepCodeBlock se ten ata 12 liñas; o estilo local md2pdf-code-break anula breakable ao final das opcións de Shaded. `code-keep-lines: 0` desactívao. Inclúe transporte do metadato desde o YAML do documento ou metadata.yaml (o primeiro ten prioridade) ata Pandoc, pois o preprocesamento elimina o front matter. Non usa Needspace.

Ficheiros cambiados:
- keep-code.lua
- md2pdf-preamble.tex
- md2pdf/assets.py
- md2pdf/engines/lualatex.py
- md2pdf/converter.py
- md2pdf/metadata.py
- install-md2pdf.py
- tests/test_keep_code.py
- tests/fixtures/code-keep.md
- docs/VERIFICACION-CODIGO.md
- docs/README.md
- docs/md2pdf-ai-reference.md

## Reprodución

O caso sintético está en [`tests/fixtures/code-keep.md`](../tests/fixtures/code-keep.md). Copialo a un directorio temporal e executar `md2pdf code-keep.md`. Para reproducir o comportamento anterior coa mesma instalación, engadir ao comezo do Markdown:

```yaml
---
code-keep-lines: 0
---
```

Para os documentos de docencia, copiar os Markdown e os recursos locais que usen a un directorio temporal. Converter alí, sen rexenerar os PDF do repositorio de materiais. Comparar o número de páxinas con `pdfinfo`, extraer cada páxina con `pdftotext -f N -l N -layout` e renderizar as afectadas con `pdftoppm -f N -l N -png`.

## PDF: antes e despois

Fontes copiadas de ~/Documents/docencia, conversións executadas con md2pdf no directorio temporal. Non se modificou nin rexenerou nada no repositorio docencia. Todas as páxinas indicadas aquí son físicas (inclúen o índice), non a numeración impresa.

| Documento | Páxinas antes | Páxinas despois | Bloques partidos antes | Bloques partidos despois |
|---|---:|---:|---:|---:|
| synthetic | 3 | 3 | 1 | 0 |
| A3_Consola | 18 | 18 | 2 | 1 |
| A4_Repeticion | 22 | 22 | 6 | 4 |
| A3_Clases | 14 | 14 | 2 | 2 |

- Sintético: seis liñas repartidas 4+2 nas páxinas 2–3; despois, as seis na 3.
- A3_Consola, bloque de «O tipo e o intervalo»: 5+1 nas páxinas 8–9; despois, as seis na 9.
- Invoice (62 liñas): segue nas 12–13, coa caixa aberta. O corte pasa de despois de `int netCents = units * priceCents;` a despois de `scanner.close();`, por cambios na composición anterior.
- A4_Repeticion: o bloque de menú de 10 liñas pasa de 14–15 a 15; digitCount de 8 liñas pasa de 20–21 a 21. Os outros catro bloques longos seguen partidos nas mesmas páxinas. O de 45 liñas cambia o punto do corte: agora remata a páxina 19 en `public static int digitCount(int n) {`, antes remataba nun `*` de Javadoc.
- A3_Clases: mesmos cortes, incluídos os puntos exactos dos dous bloques partidos (69 e 37 liñas).

Comprobáronse todos os bloques de fonte (agás diagramas) contra o texto das caixas PDF con PyMuPDF; ningún bloque de ata 12 liñas queda partido despois. O reconto inclúe os bloques de código e de terminal; exclúe os diagramas renderizados.

## Espazo en branco

Medida aproximada entre o último texto do corpo e o límite inferior da área útil; exclúese o pé de páxina.

- Sintético, páxina 2: 29 mm antes do bloque desprazado.
- Consola, páxina 8: 35 mm (antes 5 mm).
- Repeticion, páxina 14: 33 mm (antes 7 mm).
- Repeticion, páxinas 15 e 17: 42 e 44 mm (antes 5 e 3 mm), por desprazamentos das seguintes seccións. Son ocos visibles, aínda inferiores a un cuarto da altura útil.
- O desprazamento de digitCount non deixa un oco grande na páxina 20: o parágrafo anterior continúa na 21.

Mantense 12 como valor por defecto: estes documentos non medran en páxinas. Pódese reducir segundo as preferencias de composición de cada documento.

## Verificación

- Suite completa: `python3 -m unittest discover -s tests -v`; **182 tests, OK, 91,624 s**, sen fallos nin omisións.
- 12 tests novos: límites 12/13, YAML e -M, cero, valores inválidos, liñas baleiras, composición con compact/limiar/terminal/hl, text/console/terminal/bash, listas/callouts, HTML e XML de DOCX idénticos, orde dos filtros e transporte desde o conversor (prioridade do front matter e --no-metadata).
- PDF adicional de composición: código curto, terminal compacto resaltado dentro dun callout, código nunha lista e bloque longo de 62 liñas. Correcto nos modos normal, --print e --night; o bloque longo continúa nas páxinas 3–4.
- PDF con code-keep-lines: 0: o pdftotext -layout coincide exactamente coa referencia anterior, incluídos os saltos de páxina.
- Extracción con pdftotext por páxina, renderizado con pdftoppm e inspección visual das páxinas afectadas e dos cortes longos.
- git diff --check sen erros.
- Entorno: Python 3.14.8, Pandoc 3.11, LuaHBTeX 1.24.0 (TeX Live 2026).

## Límite dos bloques longos

Mantense lines before break=3. Non se garante un mínimo de tres liñas no fragmento final; en Repeticion segue existindo un bloque longo cunha chave soa na páxina seguinte. A documentación e o algoritmo de tcolorbox controlan o espazo anterior ao corte; non se introduce un parche dos algoritmos internos nin se modifica fvextra.

Referencia primaria: [algoritmo e opcións de tcolorbox](https://github.com/T-F-S/tcolorbox/blob/master/doc/latex/tcolorbox/tcolorbox.doc.breakable.tex).

Verificación final: os 42 activos e ficheiros Python instalados coinciden byte a byte coa fonte. As tres fontes Markdown de docencia seguen idénticas ás copias previas. Os catro PDF posteriores volveron converterse tras o último axuste de metadatos: o texto e os saltos coinciden coa revisión visual.

SHA-256 das fontes usadas:
- A3_Consola.md: `1dcdb26e3476e0aa10d9f6deb3f94ed56c8a3bbf51537ef5dddc47e5a8d39f1f`
- A4_Repeticion.md: `930a6068d87e8da36b80fe756cccbcaf03395960764a15fd3e983ccfd21e61b1`
- A3_Clases.md: `7ab3194604daa16bfdc4c5ee50876260625ea93e5e03ee82b661d6c2afafa493`
- synthetic.md: `ef3744e6ed5c29b52672d36ac8ee4d2d607d4fc64f2c9f3a767e2d02fad0bec9`

## Reserva do parágrafo de entrada con liñas que parten

Revisión do 1 de novembro de 2026 sobre `93864ce`, cos filtros do repositorio idénticos aos instalados antes do cambio.

Dous documentos de docencia (U2A1 e U2A5 de DWCS) deixaban o parágrafo que presenta un bloque ao pé da páxina, separado do bloque:

- **Código.** Un bloque `text` de 5 liñas, unha de 217 caracteres, ocupa 9 liñas no PDF e 154 pt. `keep-with-next.lua` reservaba 9 liñas base (169 pt) para o parágrafo, de dúas liñas, e o bloque, porque contaba as liñas da fonte. A reserva pasaba, o parágrafo quedaba e o bloque, en KeepCodeBlock, saltaba enteiro.
- **Táboa.** Unha táboa de 6 filas, case todas de dúas liñas, mide uns 275 pt. `small-table.lua` reservaba 6 + 5 + 2 = 13 liñas base (244 pt) para a táboa e o parágrafo, cunha liña por fila.

Cambios:

- `keep-with-next.lua`: as liñas de código cóntanse repartindo as palabras en 66 caracteres, o ancho medido no PDF para Source Code Pro de 10,8 pt (as liñas de 217 e 92 caracteres dan 4 e 2, como no PDF); unha palabra máis longa parte en calquera punto. O límite de `code-keep-lines` segue usando as liñas da fonte.
- `small-table.lua`: as táboas pequenas suman 0,9 liñas por cada liña de máis dunha fila, coa estimación das celas que xa usaban as longas, nos catro sitios que reservaban `nrows + 5`.
- Os bloques e as táboas sen liñas que parten reservan o mesmo ca antes.

Resultado nos dous casos: 13 liñas base (244 pt) para un conxunto de uns 204 pt, e 19 (357 pt) para uns 330 pt; o parágrafo pasa á páxina seguinte co bloque.

Verificación: catro probas novas en `tests/test_keep_with_next.py` e `tests/test_small_table.py`, que fallan cos filtros anteriores e pasan cos novos.

Ao rexenerar o material de docencia apareceu outro erro, anterior a este cambio: un documento que empeza polo título e un parágrafo de entrada (`# U1T3. …`, «Parte deste programa…:» e un bloque) non se convertía, con «LaTeX Error: No \title given». `keep-with-next.lua` e `small-table.lua` levan a reserva por riba das cabeceiras anteriores, tamén do título de nivel 1; con `--shift-heading-level-by=-1`, Pandoc só toma ese título se é o primeiro bloque. Agora a reserva non sobe por riba dunha cabeceira de nivel 1, e unha táboa que vai xusto despois do título non reserva nada antes del. Dúas probas novas, que fallan cos filtros anteriores; `test_reserve_goes_before_headers` pasa a usar os niveis 2 e 3, os das seccións de md2pdf.

Na revisión posterior dos PDF rexenerados apareceu un terceiro caso: a tarefa U3T5 de DWCS, cunha táboa de cinco filas con código en todas as celas, deixaba o parágrafo de entrada só. O estimador das celas contaba 5 pt por carácter tamén no código, que no PDF vai en Source Code Pro de 11,8 pt e ocupa 7,1 pt por carácter: as chamadas de 45 caracteres collían, segundo a estimación, nunha liña dunha columna de 243 pt, e no PDF ocupan dúas. Agora o código mide 7,1 pt por carácter, e unha palabra máis longa ca a columna parte. A reserva da U3T5 pasa de 15 a 19 liñas base (357 pt para uns 330). Unha proba nova falla co filtro anterior.

Un cuarto caso apareceu ao comparar os PDF vellos do material cos convertidos de novo: a rúbrica das tarefas de DWCS, cunha táboa de catro filas de dúas liñas e unha columna estreita de puntos, gañaba unha páxina e deixaba media páxina baleira. A reserva era de 15 liñas base (283 pt) para uns 190 pt. A cabeceira de cada columna leva o LaTeX co que `auto-table-widths.lua` a destaca, `\textsf{\bfseries\color{heading-section}{}…}`; o estimador quitaba as ordes e as chaves pero deixaba `heading-section`, que contaba como unha palabra de 15 caracteres (75 pt) e partía a cabeceira da columna de puntos, de 49 pt, en tres liñas. Agora quítase o argumento de `\color`, e a reserva desa táboa é de 13 liñas base. Unha proba nova falla co filtro anterior.
