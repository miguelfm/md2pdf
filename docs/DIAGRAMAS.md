# Diagramas configurables

Vega-Lite está integrado como renderizador opcional de gráficos de datos.
Consulta VEGA-LITE.md para instalación, sintaxe e restricións de datos.

Esta versión admite Mermaid, D2, Graphviz e Vega-Lite. Os bloques dot e graphviz son
alias. Non instala os renderizadores: deben estar no PATH.

## Uso

````markdown
```{.d2 #fig:arquitectura layout=elk width=90% caption="Arquitectura da aplicación"}
cliente -> servidor: HTTP
servidor -> datos: SQL
```

Véxase a @fig:arquitectura.

```{.dot layout=neato width=12cm caption="Grafo de conexións"}
graph {
    a -- b;
    b -- c;
    c -- a;
}
```
````

O identificador e o pé xeran unha imaxe/figura estándar de Pandoc.
A resolución de `@fig:...` é propia de md2pdf: funciona en LuaLaTeX e HTML sen `pandoc-crossref`; DOCX non a resolve actualmente.
Non combines caption cun segundo pé manual «Figura N.» para a mesma figura.
Sen caption/id/height consérvase o envoltorio de centrado histórico.
Os pés son texto literal, non Markdown enriquecido.

## Opcións

- Todos: width, height, caption e #identificador (ou id=...).
- Dimensións positivas con %, px, pt, cm, mm ou in.
- Só width ou height: a proporción queda a cargo de Pandoc.
- Ambas dimensións explícitas poden deformar a imaxe; úsanse só se se desexa.
- D2: layout=dagre|elk|tala e theme=identificador-numérico.
- Graphviz: layout=dot|neato|fdp|sfdp|circo|twopi|osage|patchwork.
- Mermaid: mantén as opcións do renderizado anterior; non admite layout/theme
  neste adaptador. Pódese seguir usando a configuración interna de Mermaid.

Un valor incorrecto conserva o bloque como código e emite un aviso.
Non se admiten argumentos de consola arbitrarios. TALA require o seu motor
instalado e as condicións de licenza correspondentes.
Os renderizadores poden ter dependencias adicionais segundo o formato. LuaLaTeX solicita PDF, DOCX solicita PNG e HTML solicita SVG; D2, Mermaid, Graphviz e Vega-Lite poden ter requisitos diferentes para cada saída.

## Valores por documento

O YAML aniñado require PyYAML, só se se usa diagrams:
python -m pip install PyYAML

```yaml
---
diagrams:
  d2:
    layout: elk
    theme: 0
  graphviz:
    layout: dot
---
```

Tamén se admite en metadata.yaml. Prioridade, por opción:
bloque > front matter > metadata.yaml > predeterminado.
--no-metadata desactiva os valores YAML, non os atributos dos bloques.
YAML incorrecto ou falta de PyYAML ao usar diagrams abortan a conversión
cunha mensaxe explícita, en vez de ignorar a configuración.

## Rutas, caché e seguridade

Os subprocesos usan como directorio de traballo o do Markdown.
D2 crea unha fonte temporal nese mesmo directorio para resolver imports
relativos; require permiso de escritura e elimínaa ao rematar.
Os recursos externos non se descargan nin se empaquetan automaticamente.

A caché incorpora layout/tema e o directorio de orixe para os novos
renderizadores. Os atributos de figura non obrigan a renderizar de novo.
Esta actualización cambia a clave de caché tamén para Mermaid: a primeira
conversión rexenera os gráficos, sen necesidade de borrar a caché antiga.
Os bloques con indicios de recursos externos (@, image ou icon) non reutilizan
a caché: é unha política conservadora, non un analizador de dependencias.
A clave inclúe ruta, tamaño e data de modificación do lanzador, directorio
de orixe e, para Mermaid, configuración de Puppeteer. Detecta cambios no
lanzador, pero non todas as actualizacións internas de Node/Chromium ou fontes.
Nestes casos pódese eliminar a carpeta temporal md2pdf do renderizador afectado.
As saídas publícanse mediante substitución atómica tras unha execución correcta
e a validación do formato. A caché tamén se valida ao reutilizala; se está
danada, avísase e téntase rexenerar. Un resultado inválido nunca substitúe
unha entrada válida.

Vallas de tres ou máis backticks e tiles recoñécense nunha soa pasada.
Un diagrama escrito como exemplo dentro dunha valla maior non se executa.
Esta detección admite bloques ao nivel do documento con ata tres espazos;
non pretende implementar toda a gramática de listas e citas de Pandoc.

A validación de atributos non é unha sandbox para as linguaxes gráficas:
procesa só documentos de confianza.

## Verificación

Executar desde a raíz do proxecto:

```bash
python -m unittest discover -s tests -v
```

As probas usan renderizadores simulados para validar integración, comandos,
formatos, erros, opcións, caché e compatibilidade. Non substitúen as probas
visuais cos executables reais instalados.

## Validación e lexibilidade

Instala as comprobacións adicionais no mesmo Python co que executas o instalador:

```bash
python -m pip install PyMuPDF Pillow
python install-md2pdf.py
```

Son opcionais para conservar instalacións existentes. O instalador comproba tamén
mmdc, d2, dot, vl-convert-python, PyYAML e xurl; non instala dependencias.
Os lanzadores usan o Python empregado na instalación. Se moves ou eliminas ese
Python/contorno virtual, executa de novo o instalador co contorno correcto.

- SVG: XML válido, raíz svg, viewBox positivo se existe e elementos gráficos fóra
  das definicións. Non analiza a visibilidade que resulta do CSS.
- PDF: cabeceira e final; con pypdf, estrutura dunha páxina con contido; con
  PyMuPDF, apertura sen reparación, unha páxina válida e rasterización para
  detectar páxinas sen marcas renderizadas. Consérvase o texto branco
  sobre transparencia para documentos con fondo escuro. Os detalles moi finos ou moi claros
  poden requirir revisión manual. PyMuPDF ten prioridade sobre pypdf.
- PNG: cabeceira, dimensións, chunks e CRC; con Pillow tamén decodificación e
  detección de transparencia total. Non se comproba o significado da imaxe.

Se faltan as bibliotecas opcionais, emítese un aviso do nivel de validación.
Non é unha garantía de representación visual perfecta: cómpre revisar o
PDF final, especialmente figuras con fondos, estilos ou recursos externos.

## Tamaño e fonte das etiquetas

As etiquetas saen cun tamaño obxectivo de 12 pt no PDF (elixido conscientemente para achegar a tipografía dos diagramas á do corpo de texto de 13 pt sen provocar desbordamentos nin verticais nin horizontais na páxina A4) e `.96rem` no HTML. Sen `width` explícito, o ancho calcúlase para chegar a ese tamaño:

- Mídese a letra que leva máis caracteres no PDF xerado (PyMuPDF) ou nos
  atributos `font-size` do SVG. Sen medida (PNG, sen PyMuPDF) úsase o tamaño
  nominal do renderizador.
- Graphviz renderiza xa a 12 pt, cun só tamaño para gráfico, nodos e
  arestas. Os atributos `fontsize` e `fontname` escritos no diagrama teñen
  prioridade.
- Mermaid renderiza nativamente con `fontSize: 16px` (12 pt a 96 DPI) e conta
  con soporte automático para `mmdc 12.0.0+` (xestionando a retirada de `--pdfFit`
  mediante fallback limpo).
- Fonte: Source Sans 3, a sans do documento, en Graphviz e Mermaid. D2 e
  Vega-Lite manteñen a súa: vl-convert non atopa a Source Sans 3 (OTF) nin
  rexistrando o cartafol.
- O ancho non pasa da liña e a altura, de 560 pt (uns 20 cm). Se o diagrama
  non cabe ao tamaño obxectivo, redúcese.

Con PyMuPDF, se a letra final queda máis dun 10 % por debaixo do obxectivo
(por non caber ou por un `width` manual, en % ou en unidades absolutas),
emítese un aviso. Usa o ancho de texto de referencia do motor; pode diferir
con outras marxes ou columnas, e non mide texto convertido a contornos. Os
atributos width/height explícitos seguen tendo prioridade. Un fluxo
horizontal de máis de catro nodos adoita non caber: orientalo en vertical,
acurtar as etiquetas ou dividilo é mellor que reducilo.

```bash
md2pdf documento.md --strict
```

`--strict` detén a conversión antes de Pandoc se hai erros nos gráficos, ademais
dos erros de lint que xa comprobaba. Os avisos de tamaño ou de validación
reducida non abortan. Sen `--strict`, mantense o código fonte do bloque que
fallou e indícase ao final que o documento contén gráficos sen renderizar.
Para entregas automatizadas, activa `--strict` no comando do teu Makefile.

As probas de integración adicionais requiren PyMuPDF e Pillow:

```bash
python -m pip install PyMuPDF Pillow PyYAML 'vl-convert-python>=1.7,<2'
python -m unittest discover -s tests -v
```
