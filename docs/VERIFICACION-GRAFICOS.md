# Verificación da actualización de gráficos

## Cambios

Validación das saídas e da caché PDF/SVG/PNG; rexeneración de entradas danadas;
invalidación por cambios no lanzador/configuración; avisos de lexibilidade;
`--strict` aborta ante erros gráficos; rutas con espazos; instalador co Python
fixado e comprobacións opcionais; documentación actualizada.

Non se cambia o algoritmo de dimensionado nin os argumentos de Mermaid.
A nova clave obriga a rexenerar os gráficos unha vez. A validación máis completa
require PyMuPDF e Pillow; véxase DIAGRAMAS.md para instalación e límites.

## Resultados neste contorno

- 31 probas automatizadas superadas, sen omisións.
- Vega-Lite real: PDF, SVG, PNG e reutilización de caché.
- Os sete PDF de Mermaid achegados polo usuario superan a validación.
- O Markdown U1A3_Estrutura.md, usando o gráfico xa renderizado do usuario,
  conserva unha imaxe na árbore de Pandoc e includegraphics na saída LaTeX,
  tamén cunha ruta temporal con espazos. A chamada ao renderizador substituíuse
  pola copia do PDF de mostra; non foi unha rexeneración con mmdc.
- O gráfico de mostra conserva o ancho automático de 98,2 % e emite o aviso
  de texto estimado de 6,6 pt.
- Probas de corrupción, caché, saída aparentemente correcta pero inválida,
  páxina PDF baleira, texto branco para fondo escuro, modo estrito e lanzador
  con espazos e apóstrofos.

## Límites da verificación

Non se executaron os CLI reais de Mermaid, D2 ou Graphviz porque non están
instalados neste contorno. Os seus comandos e a integración teñen probas con
substitutos. Non se compilou o documento completo coa plantilla de produción
LuaLaTeX: a instalación TeX do contorno está incompleta. A proba de ligazóns
usa pdfLaTeX e os filtros/snippet do proxecto.

Cómpre revisar visualmente unha compilación representativa no equipo docente.
Os validadores detectan defectos concretos, pero non garanten que todo o
contido sexa correcto, visible e lexible no documento final.
