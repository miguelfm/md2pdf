# Saída HTML5

O motor `html` xera un único ficheiro HTML5 autocontido a partir do mesmo Markdown usado para PDF e DOCX.

```bash
md2pdf documento.md -e html
md2pdf documento.md -e html -o documento.html
```

## Arquitectura

A saída usa directamente o writer HTML5 de Pandoc. Non introduce Quarto, MkDocs nin outro xerador intermedio.

- `md2pdf/engines/html.py`: constrúe o comando Pandoc.
- `md2pdf.html`: template HTML5.
- `md2pdf.css`: tipografía, layout responsive, callouts, táboas, figuras e impresión.
- `html.lua`: semántica específica de HTML para callouts, captions e referencias cruzadas.
- `md2pdf/diagrams/`: reutilízase sen duplicar o pipeline; o formato de saída para HTML é SVG.

Pandoc execútase con `--embed-resources`, polo que CSS, imaxes e SVG locais quedan incorporados no propio `.html`.

## Paridade coa saída PDF

Mantéñense, adaptadas a tecnoloxías web nativas:

- índice automático compacto e centrado;
- numeración de seccións mediante `--number-sections` de Pandoc (sen lóxica propia duplicada);
- callouts `note`, `tip`, `warning`, `danger` e `info`;
- resaltado sintáctico;
- `hl="1,3,5-7"` para destacar liñas concretas de código;
- figuras e táboas numeradas;
- compatibilidade cos pés de figura herdados do pipeline PDF (`*Figura N. ...*`), normalizados antes do filtro HTML para evitar numeración duplicada;
- referencias `@fig:` e `@tbl:`/`@tab:` como ligazóns internas;
- Mermaid, D2, Graphviz e Vega-Lite como SVG;
- notas ao pé;
- ecuacións mediante MathML;
- `--night`, `--print`, `--plain`, `--no-toc`, `--no-number`, `--watch` e `--strict`.

As regras exclusivas de paxinación LaTeX (`needspace`, `longtable`, `small-table.lua`, etc.) non se executan no HTML de pantalla. Para impresión úsanse regras CSS de salto de páxina.

## Segunda iteración: responsive, accesibilidade e validación

A saída HTML aplica unha segunda capa de robustez sen engadir dependencias:

- cada táboa queda dentro dun `div.table-wrapper`; o scroll horizontal en pantallas estreitas pertence ao contedor e o elemento `<table>` conserva a súa semántica nativa;
- os callouts teñen `role="note"` e `aria-labelledby`, ligado ao seu título visible;
- se unha figura herdada ten pé pero a imaxe non ten texto alternativo, o pé úsase como `alt`;
- as imaxes informativas sen `alt` xeran un aviso. As puramente decorativas poden marcarse con `{.decorative}`;
- ao finalizar a conversión compróbanse IDs duplicados, ligazóns internas rotas, destinos `aria-labelledby` inexistentes e referencias `@fig:`/`@tbl:` sen destino;
- con `--strict`, calquera destes problemas invalida a saída e o HTML xerado elimínase.

Estas comprobacións realízanse sobre o HTML final, polo que tamén cobren elementos introducidos polos filtros e polo propio Pandoc.

## Limitacións deliberadas

- `--titlepage` non aplica: o título intégrase na páxina HTML.
- `--listings` segue sendo exclusivo de LuaLaTeX.
- DOCX continúa sen resolver as referencias propias `@fig:`/`@tbl:`.
- O HTML non intenta imitar unha páxina A4 na pantalla; é responsive. `@media print` si define unha composición A4 básica para imprimir desde o navegador.
- Os gráficos Vega-Lite son estáticos; non se conservan tooltips nin interacción.

## Diagramas

O formato por motor é:

| Motor | Formato de diagramas |
|---|---|
| LuaLaTeX | PDF |
| DOCX | PNG |
| HTML5 | SVG |

A caché é independente por formato, polo que a mesma fonte de diagrama pode coexistir nas tres saídas.

Sen `width` explícito, o ancho do diagrama exprésase en `em`, non en porcentaxe. A imaxe leva a clase `md2pdf-diagram`, que lle dá `font-size: .96rem`, o tamaño das celas das táboas; como o `em` dun `width` é o da propia imaxe, as etiquetas quedan a ese tamaño tamén nas pantallas estreitas (no PDF, 12 pt). O CSS (`max-width: 100%`) só o reduce cando non cabe. Cunha porcentaxe, nun móbil o diagrama encollía co contedor ata ser ilexible. Un `width=80%` escrito no bloque respéctase tal cal.

## Ficheiro autocontido

Unha imaxe local como:

```markdown
![Arquitectura](img/arquitectura.png){width=80%}
```

non queda como dependencia externa no resultado: Pandoc incorpóraa no HTML. O mesmo ocorre co CSS e cos SVG xerados polos renderizadores.


## Empaquetado IMS para Moodle

A saída HTML serve tamén como base para paquetes IMS con varios documentos:

```bash
md2pdf U1/ --ims U1-moodle.zip
```

Cada Markdown convértese a HTML autocontido e `md2pdf` xera o `imsmanifest.xml` e o ZIP. As ligazóns entre ficheiros `.md` incluídos no paquete reescríbense aos HTML correspondentes. Consulta [IMS.md](IMS.md).
