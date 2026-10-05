# Referencia md2pdf para IA: redacción de materiais docentes en Markdown

Este documento é o **contrato de redacción** para unha IA que cree ou revise materiais
docentes destinados a **md2pdf**. Fixa dúas cousas: os criterios pedagóxicos e editoriais
que deben cumprir os materiais (parte I) e a sintaxe Markdown que md2pdf interpreta
correctamente (parte II). A parte III recolle a validación e a lista de comprobación final.

md2pdf xera tres saídas a partir do mesmo Markdown:

| Saída | Uso habitual | Notas |
|---|---|---|
| PDF (LuaLaTeX, por defecto) | Apuntes para ler ou imprimir | Maior calidade tipográfica |
| HTML5 autocontido (`-e html`) | Web, Moodle | Responsive; valida accesibilidade e ligazóns |
| DOCX (`-e docx`) | Documento editable | Soporte parcial: ver as notas de cada sección |

Varios HTML poden empaquetarse ademais como **IMS Content Package** para Moodle (`--ims`).

Convencións deste documento: «debe» indica unha regra; «convén» ou «preferir», un criterio
que admite excepcións xustificadas. Os exemplos marcados con ❌ son erros que hai que evitar.
As convencións do repositorio de destino prevalecen sobre as recomendacións xerais desta referencia. Por exemplo, `docencia` mantén títulos numerados e índices manuais nas fontes Markdown; md2pdf retíraos e xera a numeración e o índice da saída.

Este ficheiro é unha referencia, non un material para converter: as súas cabeceiras `#` de
parte só organizan esta referencia. Nos materiais, usa un único título de nivel 1 e
segue as normas de numeración do repositorio de destino.

---

# Parte I. Criterios pedagóxicos e editoriais

## 1. Finalidade e prioridades

Ao xerar unha unidade, actividade, tarefa, autoavaliación ou solucionario, prioriza nesta
orde:

1. **Corrección técnica e conceptual.**
2. **Secuencia pedagóxica:** cada concepto aparece despois dos seus prerrequisitos.
3. **Comprensión:** explicar o modelo mental antes de acumular sintaxe ou casos especiais.
4. **Aplicación:** acompañar os conceptos importantes con exemplos que se poidan executar,
   comprobar ou razoar.
5. **Coherencia coa unidade:** non repetir sen motivo contidos xa tratados nin adiantar
   en detalle contidos reservados para actividades posteriores.
6. **Calidade editorial:** táboas, diagramas, callouts e código só cando melloren
   realmente a comprensión.
7. **Portabilidade:** o mesmo Markdown debe funcionar en PDF, HTML e, cando corresponda,
   nun paquete IMS para Moodle.

O obxectivo é construír unha **secuencia de aprendizaxe**, non unha enciclopedia nin unha
colección de apuntes illados.

## 2. Antes de redactar

Se existen guía da unidade, programación, resultados de aprendizaxe (RA), criterios de
avaliación (CA), actividades veciñas ou materiais xa escritos, revísaos antes de crear
contido novo e:

- respecta a orde, nomenclatura e profundidade xa establecidas;
- comproba que cada actividade ten unha función clara dentro da progresión;
- non expliques de novo con detalle o que xa se traballou antes;
- introduce só os conceptos posteriores imprescindibles para entender o punto actual;
- non inventes correspondencias con RA/CA ou normativa que non estean nas fontes
  proporcionadas;
- mantén consistentes nomes de variables, exemplos, proxectos, rutas e ferramentas entre
  as actividades dunha mesma unidade.

Para unha unidade completa, planifica primeiro a distribución de conceptos entre
actividades e sesións, e redacta despois cada peza.

## 3. Estrutura dunha actividade de contidos

Non todas as actividades necesitan as mesmas seccións, pero a progresión habitual é:

1. **Contexto ou problema:** para que serve o que se vai aprender.
2. **Conceptos fundamentais:** poucos por sección e con relación explícita entre eles.
3. **Exemplo mínimo:** illa a idea nova sen ruído accidental.
4. **Exemplo aplicado:** achégase ao uso real cando aporte valor.
5. **Contrastes e casos límite:** só os que axuden a evitar erros previsibles.
6. **Síntese ou conexión coa actividade seguinte.**

Tarefas, autoavaliacións e solucionarios poden ir en ficheiros separados. Se o proxecto xa
segue esta separación, non dupliques no ficheiro teórico unha práctica que xa existe como
tarefa.

## 4. Teoría, exemplos e profundidade

As explicacións deben responder, cando sexa relevante: **que é**, **para que serve**,
**como funciona**, **que cambia respecto do que o alumnado xa coñece**, **que erro
conceptual é máis probable** e **como se comproba na práctica**.

Prefire explicacións causais a regras para memorizar: se un comportamento ten unha razón
técnica sinxela, explícaa.

Os exemplos deben ser pequenos, executables e coherentes coa versión das ferramentas do
curso. Se a saída é importante para entender o exemplo, amósaa. Non introduzas
dependencias, APIs ou sintaxe avanzada innecesarias para o obxectivo inmediato.

## 5. Terminoloxía

Emprega galego claro e preciso. Na primeira aparición útil dun termo técnico que o
alumnado atopará en documentación, ferramentas ou código, engade o termo inglés en cursiva:
código fonte (*source code*), tempo de execución (*runtime*), forzado de tipos (*cast*),
ámbito (*scope*). Despois usa o termo máis natural.

Non traduzas identificadores, comandos, nomes de APIs, nomes de ficheiro nin termos que
formen parte literal dunha ferramenta.

## 6. Código e terminal

O código debe ensinar unha idea concreta; evita exemplos artificialmente longos. Patrón
recomendado:

1. presentar a idea;
2. amosar o código mínimo;
3. explicar as liñas non evidentes;
4. indicar o resultado ou efecto cando sexa útil;
5. introducir despois unha variante ou erro típico.

Resalta con `hl=` (sección 13.2) só as liñas que o texto comenta. Se precisas resaltar
medio bloque, divide ou simplifica o exemplo.

Nos exemplos de terminal distingue claramente a orde escrita polo usuario, a saída da
ferramenta e o erro esperado cando se mostre deliberadamente. Unha opción clara é separar
a orde (bloque `bash`) da súa saída (bloque `text`).

## 7. Escoller entre texto, táboa, diagrama e gráfico

Un recurso visual debe reducir carga cognitiva; non se engade por decoración.

| Necesidade | Recurso |
|---|---|
| Comparar propiedades, opcións, sintaxe ou resultados | Táboa |
| Fluxo, secuencia ou relación simple | Mermaid |
| Estrutura densa, arquitectura, grafo, árbore ou autómata | D2 ou Graphviz |
| Datos cuantitativos, tendencias, distribucións | Vega-Lite |
| Razoamento, matices, causas | Texto |

Non forces Mermaid cando D2 ou Graphviz representen a relación de maneira máis natural,
nin uses Vega-Lite para diagramas conceptuais.

Como orientación, un diagrama con máis de seis ou oito nodos, ou con etiquetas longas,
adoita quedar con texto pequeno. Divídeo, cambia de motor ou de orientación, ou
substitúeo por unha táboa. As etiquetas dos nodos deben ser curtas: o detalle pertence ao
texto que acompaña a figura. A sección 14.6 explica como dimensiona md2pdf os diagramas.

## 8. Uso semántico dos callouts

Cada tipo de callout ten unha función:

| Tipo | Función |
|---|---|
| `note` | Aclaración ou recordatorio |
| `tip` | Práctica recomendable ou atallo útil |
| `warning` | Risco de erro frecuente ou comportamento sorprendente |
| `danger` | Erro grave, perda de datos, seguridade ou acción difícil de reverter |
| `info` | Contexto técnico que amplía pero non interrompe o fío principal |
| `task` | Tarefa ou exercicio práctico interactivo con cadro de resposta editable |

Non convertas cada dato interesante nun callout. Varios callouts seguidos indican que parte
dese contido debe volver ao texto normal. Reserva `warning` e `danger` para situacións que
o xustifiquen. A sintaxe está na sección 12.

## 9. Tarefas, autoavaliacións e solucionarios

As tarefas avalían o que xa se ensinou: non pidas unha técnica nova sen introducila antes.
Nas tarefas prácticas:

- formula un produto ou resultado observable;
- indica só restricións que formen parte da aprendizaxe;
- pide evidencias só cando sirvan para verificar o proceso ou o resultado;
- evita pasos artificiais que só comproben que o alumnado sabe seguir unha receita;
- gradúa a dificultade desde a aplicación directa ata a integración ou o diagnóstico.

As autoavaliacións cobren conceptos relevantes, non detalles accidentais. As opcións
incorrectas deben representar erros ou confusións plausibles.

Os solucionarios docentes explican **por que** unha solución é correcta e, cando aporte
valor, sinalan erros frecuentes ou alternativas válidas. Non inclúas respostas de
solucionario nos materiais para o alumnado.

Se hai rúbrica, os seus criterios deben corresponderse con evidencias observables e evitar
descricións ambiguas.

## 10. Redacción independente do formato e accesibilidade

Non escribas «na imaxe de abaixo», «na páxina seguinte» nin «como se ve á dereita»: PDF e
HTML presentan os elementos de forma distinta. Prefire:

- «como se mostra na @fig:identificador»;
- «como resume a @tbl:identificador»;
- «no apartado [Conversión explícita](#conversion-explicita)».

Toda figura informativa (imaxe ou diagrama) leva un pé que describa o que importa; en HTML
ese pé é tamén o texto alternativo. Non dependas só da cor para distinguir estados ou
categorías.

---

# Parte II. Sintaxe e convencións de md2pdf

md2pdf usa o Markdown de Pandoc, que é **máis estrito ca GitHub** nalgúns puntos
(sección 11.1). Antes de pasar o texto a Pandoc, un preprocesador corrixe ou elimina
algunhas construcións; o que se describe aquí é o resultado final.

## 11. Estrutura do ficheiro

### 11.1 Liñas baleiras obrigatorias

Pandoc só recoñece listas, táboas, cabeceiras e citas se van **precedidas dunha liña
baleira**. Sen ela, pasan a formar parte do parágrafo anterior como texto plano:

```markdown
❌ As vantaxes son:
- Separación de responsabilidades
- Testabilidade

✅ As vantaxes son:

- Separación de responsabilidades
- Testabilidade
```

Deixa sempre unha liña baleira antes e despois de: listas, táboas, cabeceiras, citas,
bloques de código, callouts e fórmulas en bloque.

### 11.2 Front matter YAML

Ao inicio do ficheiro, para metadatos e portada:

```markdown
---
module: "Desenvolvemento web en contorno servidor"
subject: "UD3: Introdución a PHP"
activity: "A01: Estruturas de control"
---

# A01: Estruturas de control
```

| Campo | Onde aparece | Notas |
|---|---|---|
| `module` | Portada (`--titlepage`) en versaletas | Módulo profesional |
| `subject` | Portada, título principal | Unidade didáctica; en HTML, metadato `description` |
| `activity` | Portada e inicio do contido no PDF; título do elemento no paquete IMS | Actividade concreta; `subtitle` é alias |
| `school` | Portada, bloque inferior | Nome do centro |
| `course` | Portada, bloque inferior | Curso académico |
| `author` | Metadatos do PDF; cabeceira do HTML; portada se non hai `school` | Adoita ir en `metadata.yaml` |
| `keywords` | Metadatos do PDF e do HTML | Cadea separada por comas |

Regras:

- **Cada campo nunha soa liña** (`campo: valor`). O lector de metadatos non admite listas
  YAML nin valores multiliña: escribe `keywords: "PHP, DAW, Backend"`, non unha lista.
- O bloque elimínase antes de converter: ningún campo aparece como texto no corpo.
- Non uses `title`: o título sae do `# Título` (sección 11.4).

Os campos comúns a toda unha unidade (`author`, `school`, `course`, `keywords`) van nun
ficheiro de metadatos no mesmo directorio. md2pdf busca primeiro
`<prefixo>-metadata.yaml` (por exemplo `u3-metadata.yaml` para `U3A1.md`) e despois
`metadata.yaml`. O front matter do `.md` sobrescribe campo a campo:

```yaml
# metadata.yaml (compartido polos .md do directorio)
author: "Nome Apelidos"
school: "Nome do centro"
course: "Curso 2025-2026"
keywords: "PHP, DAW, Backend"
```

### 11.3 Construcións que transforma o preprocesador

O preprocesador elimina ou altera estas construcións:

- `[TOC]` e índices manuais (`## Índice` seguido dunha lista de ligazóns): o índice é
  automático. Poden conservarse na fonte cando o repositorio os esixa.
- Liñas `---` fóra do front matter e dos bloques de código: elimínanse todas, tamén dentro
  de callouts. Non uses separadores horizontais nin cabeceiras subliñadas con `---`.
- Numeración manual: `## 1.2. Título` convértese en `## Título`. Por iso **unha cabeceira
  que empece por un número seguido de espazo perde ese número** (`## 2024 en cifras` →
  «en cifras»). Reformula: `## Cifras de 2024`.

### 11.4 Título e cabeceiras

- **Un só `#` por documento**, ao inicio: é o título do documento. Todo o contido vai
  desde `##`, que é o nivel 1 da numeración.
- As seccións numéranse automaticamente na saída (1, 1.1, 1.1.1…). Na fonte, segue a convención do repositorio: md2pdf admite títulos numerados e elimina esa numeración antes de converter.
- Non saltes niveis (`##` → `####`) e non uses máis de tres niveis salvo necesidade.

Algunhas palabras nas cabeceiras engaden automaticamente un emoji, en todas as saídas:

| Palabra (con maiúscula inicial) | Emoji |
|---|---|
| `Tarefa` | 🎯 |
| `Exercicio` | ✏️ |
| `Reto` | 🏆 |
| `Exemplo` | ▶️ |

Non escribas ti o emoji. A detección busca o texto en calquera parte da cabeceira e
distingue maiúsculas: `## Exemplos de uso` recibe ▶️, e tamén **`## Retorno de valores`
recibe 🏆** porque contén «Reto». Reformula para evitalo: `## Valor de retorno`.

## 12. Callouts

### 12.1 Sintaxe

Usa divs de Pandoc cos **nomes en inglés**, que funcionan igual nas tres saídas:

```markdown
::: warning

Nunca almacenes contrasinais en texto plano.

:::
```

Deixa unha liña baleira tras a apertura (o preprocesador engádea se falta, pero é a forma
correcta). Os callouts poden conter listas, táboas e bloques de código.

Tipos e aliases:

| Tipo | Alias | Etiqueta | DOCX recoñece o alias |
|---|---|---|---|
| `note` | `nota` | Nota | Non |
| `tip` | `consello` | Consello | Si |
| `warning` | `atención`, `atencion` | Atención | Non |
| `danger` | `perigo` | Crítico | Si |
| `info` | — | Info | — |
| `task` | `tarefa`, `task-box` | Tarefa | Si |

Un alias non recoñecido en DOCX sae como texto normal, sen etiqueta. Por iso convén usar
sempre os nomes ingleses.

### 12.2 Callouts interactivos de tarefa (`task`)

Os callouts de tipo `task` (`tarefa`, `task-box`, `taskbox`) xeran áreas de resposta editables para o alumnado:
- **PDF (LuaLaTeX):** Campo interactivo de formulario PDF estándar (*AcroForm*) con `\TextField[multiline=true]`. Permite escribir, editar e gardar (`Ctrl+S`) as respostas no propio PDF con calquera visor estándar.
- **HTML5:** Elemento `<textarea class="task-box-input">` con gardado e persistencia automática en `localStorage` do navegador. En impresión preséntase como cadro delimitado limpo para escritura manual.
- **DOCX:** Encabezado `🎯 Tarefa:` en negra cun marcador de espazo de resposta.

Pódense engadir atributos como `id`, `height` (ex: `4cm`, `7em`, `120px`) e `placeholder`:

```markdown
::: {.task id="ex1" height="4cm" placeholder="Escribe aquí a túa resposta..."}

Explica a vantaxe principal de usar índices nunha base de datos relacional.
:::
```

### 12.3 Sintaxe alternativa e conversións automáticas

Tamén se converten a callout:

- A sintaxe de GitHub/Obsidian: `> [!NOTE]`, `> [!TIP]`, `> [!WARNING]`, `> [!DANGER]`,
  `> [!INFO]`, `> [!TASK]`, `> [!TAREFA]` (e os alias galegos en maiúsculas).
- **Unha cita que empece por certos emojis:** `> ⚠️ …` → `warning`, `> 💡 …` → `tip`,
  `> 📘 …` → `info`, `> 📝 …` → `note`, `> ⛔ …` → `danger`, `> 🎯 …` → `task`.

Prefire a sintaxe `:::`. Non empeces unha cita textual por un destes emojis se non queres
un callout.

## 13. Bloques de código

### 13.1 Linguaxe obrigatoria

Indica sempre a linguaxe. Un bloque sen linguaxe convértese a `text` cun aviso e, con
`--strict`, fai fallar a conversión. Usa `text` para saídas de terminal, árbores de
directorios ou calquera contido que non sexa código.

Linguaxes habituais: `php`, `html`, `css`, `javascript`, `typescript`, `bash`, `sql`,
`json`, `yaml`, `xml`, `python`, `java`, `c`, `cpp`, `markdown`, `text`.

Para mostrar un bloque de código dentro doutro (por exemplo, sintaxe Markdown), usa unha
valla exterior máis longa (catro acentos graves) que a interior.

### 13.2 Resaltado de liñas (PDF e HTML)

````markdown
```php {hl="3,5"}
public function store(Request $request)
{
    $validated = $request->validate([
        'nome'  => 'required|max:255',
        'email' => 'required|email',
    ]);
}
```
````

Formatos válidos: `"3"`, `"1,3,5"`, `"2-6"`, `"1,3,7-9"`. DOCX ignora o resaltado, así que
o texto non debe depender só del: nomea tamén o elemento («a regra de `email`…»).

### 13.3 Pés e referencias de código: non soportados

Os bloques de código non levan pé nin se poden referenciar. Unha liña `: Título` tras o
bloque aparece literalmente no documento, e `@lst:…` non se resolve. Introduce o bloque
no parágrafo anterior e, se hai que referirse a el máis adiante, cita o apartado cunha
ligazón interna (sección 17.2).

### 13.4 Emojis dentro do código

No PDF, os emojis dentro de bloques de código substitúense por texto (`✅` → `[OK]`,
`⚠️` → `[!]`…). Evítaos no código salvo que formen parte do exemplo.

### 13.5 Bloques de terminal e ordes de consola

Para ordes e sesións de consola (`bash`, `sh`, `powershell`, `zsh`, `console`, `cmd`, etc.), indica sempre a linguaxe específica no bloque fenced (` ```bash `). `md2pdf` aplica automaticamente un fondo e bordo sutilmente diferenciados para que o alumnado distinga claramente os comandos do sistema do código fonte de aplicacións (como PHP ou Python).

Non inclúas símbolos artificiais de prompt (`$`, `>`, `#`, `>_`) nin caracteres manuais ao inicio das liñas de comando salvo que sexa indispensable diferenciar entrada e saída. Isto garante que o alumnado poida copiar e pegar as ordes directamente no terminal sen provocar erros de sintaxe (`command not found`).

### 13.6 Bloques de código compactos para listados longos

Para listados longos (clases completas, ficheiros de configuración extensos ou saídas de consola volumosas), engade a clase `{.compact}` (ou `.compacto`):

````markdown
```python {.compact}
class RepositorioAlumnos:
    def __init__(self, conexion):
        self.conexion = conexion
    # listado longo...
```
````

Isto activa unha tipografía máis compacta (10 pt con interliñado de 13 pt) que amplía a capacidade horizontal a ~77 columnas e reduce a altura vertical, evitando quebras de liña `↪` innecesarias. Tamén é combinable con resaltado (`{.compact hl="3,5"}`) ou configurábel globalmente mediante o metadato `code-compact-threshold: 25` no front matter.

## 14. Diagramas e gráficos

### 14.1 Regras comúns

md2pdf renderiza os bloques `mermaid`, `d2`, `dot`/`graphviz` e `vega-lite`/`vegalite`
antes de converter. Para numeralos, citalos e darlles texto alternativo, usa a forma con
atributos:

````markdown
```{.mermaid #fig:fluxo-login caption="Fluxo de autenticación"}
flowchart LR
  A[Formulario] --> B{Credenciais válidas?}
  B -->|Si| C[Panel]
  B -->|Non| A
```

Como mostra a @fig:fluxo-login, o formulario volve mostrarse se a validación falla.
````

Atributos admitidos por todos: `#id` (ou `id=`), `caption`, `width` e `height`, con
unidades `%`, `px`, `pt`, `cm`, `mm` ou `in`.

- **Todo diagrama informativo debe levar `caption`.** Sen el, o HTML xera un aviso de
  imaxe sen texto alternativo e `--strict` fai fallar a conversión.
- O pé é texto literal (non admite Markdown). Non escribas «Figura N.» nin no pé nin na
  referencia: a numeración é automática.
- Indica só `width` ou só `height`; os dous xuntos poden deformar a imaxe. Normalmente
  non precisas ningún (sección 14.6).
- Un atributo ou valor non admitido deixa o bloque como código e emite un aviso.
- Un diagrama por bloque.

Se falta o renderizador ou a sintaxe do diagrama é incorrecta, o bloque queda como código
fonte e emítese un aviso; con `--strict`, a conversión falla.

### 14.2 Mermaid

Admite os tipos habituais: `flowchart`, `sequenceDiagram`, `classDiagram`,
`stateDiagram`, `erDiagram`, `gantt`, `pie`, `mindmap`…

- Etiquetas curtas; para partir unha etiqueta usa `<br/>`: `A[Verificar<br/>contorna]`.
- Sintaxe estándar, sen extensións exclusivas de Mermaid Live Editor.
- Non admite os atributos `layout` nin `theme`.

### 14.3 D2

Adecuado para arquitecturas e diagramas conceptuais. Atributos propios:
`layout=dagre|elk|tala` e `theme=<número>` (identificador numérico de tema de D2).

````markdown
```{.d2 #fig:arquitectura layout=elk caption="Arquitectura da aplicación"}
cliente -> servidor: HTTP
servidor -> datos: SQL
```
````

Non uses iconas nin imaxes externas: non se descargan nin se empaquetan.

### 14.4 Graphviz

Bloques `dot` ou `graphviz` (son equivalentes). Adecuado para grafos, árbores e
autómatas. Atributo propio: `layout=dot|neato|fdp|sfdp|circo|twopi|osage|patchwork`.

````markdown
```{.dot #fig:automata caption="Autómata que recoñece números pares"}
digraph {
    rankdir=LR;
    q0 -> q1 [label="1"];
    q1 -> q0 [label="1"];
}
```
````

### 14.5 Vega-Lite

Gráficos de datos estáticos (sen interacción nin tooltips). Restricións:

- O contido é **JSON estrito**: sen comentarios nin comas finais.
- Os datos van **inline** en `data.values` ou `datasets`. Non se admiten `url`, `href` nin
  marcas `image`, nin campos de datos con eses nomes.
- Tema e estilos van no propio JSON (`config`); non se admiten `layout` nin `theme`.
- `width`/`height` do JSON controlan a composición; os atributos do bloque, o tamaño final.

````markdown
```{.vega-lite #fig:tempos width=85% caption="Distribución dos tempos de resposta"}
{
  "data": {"values": [{"tempo": 12}, {"tempo": 15}, {"tempo": 15},
                      {"tempo": 18}, {"tempo": 22}, {"tempo": 25}]},
  "mark": "bar",
  "encoding": {
    "x": {"field": "tempo", "type": "quantitative", "bin": {"maxbins": 5},
          "title": "Tempo (ms)"},
    "y": {"aggregate": "count", "title": "Frecuencia"}
  }
}
```
````

Unha regresión (`"transform": [{"regression": …}]`) é un axuste aos datos, non unha
predición validada: preséntaa como tal no texto.

### 14.6 Tamaño e lexibilidade

Sen `width` nin `height`, md2pdf escala cada diagrama para que o seu texto quede a
12 pt no PDF (elixido conscientemente para achegarse aos 13 pt do corpo do texto sen desbordar
as marxes en A4) e a `.96rem` en HTML. Mide a letra real do diagrama xerado, en Source Sans 3 en
Graphviz e Mermaid. Non escribas `fontsize` nin `fontname` no diagrama: teñen prioridade. Consecuencias:

- Un diagrama moi alto (moitos niveis en vertical) ou moi ancho (moitos nodos en
  horizontal) redúcese, e o seu texto tamén.
- Se o texto estimado queda máis dun 10 % por debaixo dese tamaño, md2pdf avisa (só no PDF e se PyMuPDF
  está instalado). O aviso non detén a conversión.
- A solución adoita ser dividir o diagrama, acurtar etiquetas ou cambiar a orientación
  (`LR`/`TB`); reducir `width` empeora a lexibilidade.

### 14.7 Valores por documento

Pódense fixar valores por defecto no front matter ou en `metadata.yaml` (require PyYAML):

```yaml
diagrams:
  d2:
    layout: elk
  graphviz:
    layout: dot
  vega-lite:
    width: 85%
```

Prioridade: atributo do bloque > front matter > `metadata.yaml` > valor predeterminado.

## 15. Táboas

```markdown
| Método | Ruta | Descrición |
|--------|------|------------|
| GET | `/users` | Lista os usuarios |
| POST | `/users` | Crea un usuario |

: Rutas do recurso usuarios {#tbl:rutas}
```

- O pé (`: Texto {#tbl:id}`) vai tras a táboa, separado por unha liña baleira; permite
  citala con `@tbl:rutas`.
- Os anchos das columnas calcúlanse polo **contido** das celas: escribe sempre os `---`
  da mesma lonxitude. Unha táboa que cabe sen partir liñas queda co seu ancho natural e
  centrada; unha táboa con columnas baleiras para encher ocupa toda a liña. Só se hai
  que forzar anchos concretos, guións de lonxitude distinta fixan anchos proporcionais.
- Evita cadeas longas sen espazos nas celas (URLs, *namespaces* completos): forzan a
  columna. Abrevia (`UserAuthenticationController`) e deixa o nome completo no texto.
- Evita celas con varios parágrafos: a táboa resume e o texto desenvolve.
- Nunha columna só de números con algún decimal, o PDF aliña as unidades e o separador
  decimal. Escribe só o número na cela (`3.5`, non `3.5 s` nin `` `3.5` ``) e centra a
  columna con `|:-:|` se o queres centrado.
- No PDF, as táboas de ata 6 filas non se parten entre páxinas; as máis longas pártense
  repetindo a cabeceira nun estilo sutil (cursiva, peso normal e ton suave). As primeiras
  4 filas e a penúltima protéxense contra orfas. Prefire varias táboas curtas, unha
  por concepto, a unha táboa xigante, e pon as filas máis importantes ao inicio.
- Salto de liña dentro dunha cela: `<br>` (PDF e HTML; DOCX ignórao). Non uses barra
  invertida nin dobre espazo.

```markdown
| Opción | Valores |
|--------|---------|
| `visibility` | `public`<br>`protected`<br>`private` |
```

## 16. Imaxes e figuras

### 16.1 Figura con pé

O texto entre corchetes é o pé numerado e, en HTML, o texto alternativo:

```markdown
![Arquitectura MVC de Laravel](imaxes/mvc-laravel.png){#fig:mvc width=80%}

A @fig:mvc mostra como o controlador separa o modelo da vista.
```

- Toda imaxe informativa leva pé. `![](imaxe.png)` sen texto xera un aviso en HTML e un
  fallo con `--strict`.
- Unha imaxe puramente decorativa márcase con `{.decorative}`: `![](logo.png){.decorative}`.
- Non escribas pés manuais do tipo `*Figura 3. …*` baixo a imaxe; son un formato herdado.
- As rutas son relativas ao ficheiro `.md`. En HTML e IMS as imaxes quedan incrustadas.

### 16.2 Tamaño e imaxes grandes

::: danger

**Imaxes PNG/JPG de máis de ~800 px de ancho** ou **PDF vectoriais** sen ancho explícito
poden **bloquear LuaLaTeX indefinidamente**, sen erro nin saída. Engade sempre
`{width=...}` a estas imaxes:

```markdown
![Diagrama de despregamento](img/despregamento.png){width=100%}
```

:::

As imaxes nunca superan o ancho do texto.

### 16.3 Posición

No PDF as figuras aparecen **exactamente onde se escriben**; non flotan. Coloca a imaxe
despois do parágrafo que a introduce e non intentes controlar a posición con comandos
LaTeX.

## 17. Referencias e ligazóns

### 17.1 Figuras e táboas

- `@fig:id` para figuras (imaxes e diagramas); `@tbl:id` ou `@tab:id` para táboas.
- Con maiúscula inicial (`@Fig:id`, `@Tbl:id`) escríbese «Figura»/«Táboa»; en minúscula,
  «figura»/«táboa». Úsaa ao comezo de oración.
- Resólvense no PDF e no HTML (onde son ligazóns). **En DOCX non se resolven e aparece o
  texto `@fig:id` literal**; se o destino principal é DOCX, nomea a figura no texto.
- En HTML, unha referencia sen destino xera un aviso e fai fallar `--strict`.

### 17.2 Seccións: ligazóns internas

`@sec:`, `@eq:` e `@lst:` **non se resolven**: aparecen literalmente. Para remitir a un
apartado usa unha ligazón interna ao seu identificador:

```markdown
## Conversión explícita {#conversion-explicita}

…

Revisa o apartado [Conversión explícita](#conversion-explicita).
```

Se a cabeceira non ten `{#id}`, Pandoc xera un automaticamente: minúsculas, espazos
convertidos en guións, sen signos de puntuación, **sen o número da sección** e
conservando as letras acentuadas (`## Conversións de tipo` → `#conversións-de-tipo`).
A eliminación da numeración **non reescribe os destinos das ligazóns**. Por exemplo,
`## 1. Conversións` xera `#conversións`, mentres que unha ligazón a
`#1-conversións` conserva ese destino e queda rota na saída. O índice manual non
presenta ese problema porque se elimina e se xera de novo.

Para remisións no corpo ou entre documentos, usa un identificador explícito na
cabeceira e ese mesmo identificador na ligazón:

```markdown
## 1. Conversións {#conversion-explicita}

Revisa [Conversións](#conversion-explicita).
```

Isto funciona tamén cunha ligazón a outro documento como
`A5_Operadores.md#conversion-explicita`. Non cambies só o destino da ligazón:
a cabeceira de destino debe declarar ese identificador. Para identificar seccións
novas, prefire nomes descritivos sen numeración nin acentos. En HTML, `--strict`
detecta destinos internos inexistentes; revisa tamén as ligazóns entre documentos
na saída final.

### 17.3 Ligazóns externas

```markdown
[Manual de PHP](https://www.php.net/manual/es/)

<https://www.php.net/manual/es/>
```

Inclúe sempre `https://` ou `http://`. Un URL entre acentos graves é código, non unha
ligazón.

### 17.4 Ligazóns entre documentos e recursos

Entre actividades da mesma unidade, liga o ficheiro Markdown cunha ruta relativa:

```markdown
Continúa en [Conversións de tipo](U1A5_Operadores.md#conversións-de-tipo).
```

Ao empaquetar en IMS, a ligazón reescríbese cara ao HTML correspondente (sección 19). Os
ficheiros locais ligados (código de partida, PDF, ZIP) inclúense no paquete.

## 18. Outros elementos

### 18.1 Listas

- Liña baleira antes da lista (sección 11.1).
- Sublistas sangradas ata o texto do elemento pai (dous espazos tras `-`, tres tras
  `1.`); máximo dous niveis.
- Listas numeradas para pasos con orde («Paso a paso»): `md2pdf` resalta automaticamente
  os números en negra coa cor corporativa (`heading-section`) e engade separación vertical
  adicional (`itemsep=0.5em`) para que pasos de varias liñas non se confundan cos contiguos.
- Viñetas para o resto de enumeracións sen orde estrita, que manteñen espazamento compacto.

### 18.2 Listas de definición

Para glosarios, parámetros ou propiedades:

```markdown
`app/`
:   Directorio principal da aplicación.

`routes/`
:   Definición das rutas. Os ficheiros principais son `web.php` e `api.php`.
```

### 18.3 Énfase e código en liña

- **Negra** para termos clave; *cursiva* para títulos de obras e termos noutra lingua;
  `código en liña` para funcións, variables, ficheiros e comandos.
- O código en liña amósase por defecto en tipografía monoespazada coa cor temática sen fondo.
  Opcionalmente pódese activar o fondo tipo «píldora» con `--inline-pill` (`#F0F2F5` en día,
  `#EDE8DC` en noite, transparente en impresión). As rutas longas (`/etc/php/...`) e expresións con
  operadores rompen automaticamente de liña se chegan á marxe dereita. Fóra das táboas, o código
  de ata 20 caracteres non se parte nunca: `$c ? $a : $b` pasa enteiro á liña seguinte.
- O código en liña admite barras invertidas (`\n`, `\t`, `\\`), til, circunflexo e
  letras acentuadas, tamén nas táboas. Escríbeos literalmente entre acentos graves;
  o filtro escápaos para LaTeX. Non engadas escapes LaTeX á fonte Markdown.
  Usa un bloque de código cando a lonxitude ou o contexto o fagan máis lexíbel.

### 18.4 Citas

As citas (`>`) úsanse para texto citado, non para avisos, que van en callouts. Lembra que
unha cita que empeza por certos emojis convértese en callout (sección 12.2).

### 18.5 Emojis

No PDF convértense en iconas vectoriais só estes emojis: ⚠️ 💡 📘 ❌ ✅ ✓ 🔴 🐛 🖥️ 🌐 ▶️
⏹ 📝 🔒 🔑 📂 📁 🚀 ⚙️ 🎯 💻 ✏️ 🏆 ⛔. Outros poden non verse no PDF. Usa como máximo
un por parágrafo e non os uses como substituto de callouts.

### 18.6 Notas ao pé

```markdown
Laravel usa Eloquent[^eloquent] como capa de acceso a datos.

[^eloquent]: Eloquent implementa o patrón Active Record.
```

### 18.7 Ecuacións

En liña, `$O(n \log n)$`; en bloque:

```markdown
$$
\bar{x} = \frac{1}{n} \sum_{i=1}^{n} x_i
$$
```

As ecuacións non se poden referenciar: non engadas `{#eq:…}` (aparece como texto) nin
`@eq:…`. Refírete a elas no texto («a fórmula da media anterior»).

## 19. Moodle e paquetes IMS

Para unha actividade individual abonda co HTML autocontido (`-e html`). Para unha unidade
ou conxunto de actividades:

```bash
md2pdf U1/ --ims U1-moodle.zip --ims-title "UD1. Introdución á programación"
```

O que afecta á redacción:

- **Orde:** ao pasar un directorio, os ficheiros ordénanse de forma natural (`U1A2` antes
  que `U1A10`). Nomea os ficheiros para que esa orde sexa a da unidade.
- **Título de cada elemento da navegación:** `activity` → primeiro `#` → nome do ficheiro.
  Dálle a cada documento un `activity` curto e distintivo.
- **Ligazóns entre documentos:** relativas ao `.md` (sección 17.4). Unha ligazón a un `.md`
  non incluído no paquete produce un aviso e, con `--strict`, impide xerar o ZIP.
- **Recursos ligados:** cópianse ao cartafol `recursos/` do paquete. Se o ficheiro non
  existe, avísase e, con `--strict`, non se xera o ZIP.
- Cada HTML é autocontido: CSS, imaxes e diagramas van incrustados.
- Non escribas instrucións que dependan dunha páxina física ou da posición na pantalla.

---

# Parte III. Validación e entrega

## 20. Validación automática e `--strict`

En cada conversión, md2pdf comproba o Markdown e informa en stderr de:

- marca BOM ao inicio do ficheiro;
- front matter sen pechar ou que chega ata un `---` do corpo;
- bloques de código sen linguaxe ou sen pechar;
- callouts sen liña baleira tras a apertura, sen pechar ou con `:::` de peche soltos;
- máis dunha cabeceira `#`.

Ademais: erros de renderizado de diagramas; en HTML, IDs duplicados, ligazóns internas
rotas, referencias `@fig:`/`@tbl:` sen destino e imaxes sen texto alternativo; en IMS,
ligazóns a Markdown non incluídos e recursos inexistentes.

Sen opcións, estes problemas son avisos e a conversión continúa (os diagramas fallidos
quedan como código). Con `--strict`, calquera deles aborta a conversión cun código de
saída distinto de cero. Os avisos de tamaño de texto dos diagramas non abortan.

```bash
md2pdf documento.md --strict
md2pdf documento.md -e html --strict
```

Non hai modo de só comprobar sen converter.

## 21. Erros de LaTeX e causa probable

Se a compilación do PDF falla a pesar das comprobacións:

| Mensaxe LaTeX | Causa probable |
|---|---|
| `Extra }, or forgotten $` | Callout sen `:::` de peche |
| `Undefined control sequence` | Bloque de código sen pechar que «tragou» un callout ou cabeceira |
| `Missing $ inserted` | Carácter especial (`_`, `^`, `$`, `&`) fóra de código ou fórmula |
| `File ended while scanning` | Bloque de código aberto que nunca se pecha |
| `Paragraph ended before \@makecol` | Callout malformado xunto cun bloque sen pechar |
| LuaLaTeX non remata, sen erro | Imaxe grande ou PDF vectorial sen `{width=...}` (sección 16.2) |

## 22. Lista de comprobación antes de entregar

Contido e pedagoxía:

- [ ] A progresión respecta os prerrequisitos e a planificación da unidade.
- [ ] Non hai repeticións sen función pedagóxica nin contidos adiantados en exceso.
- [ ] Non se inventaron correspondencias con RA/CA.
- [ ] Os exemplos son mínimos, coherentes e, cando corresponda, executables.
- [ ] Cada táboa ou diagrama é a representación máis clara do que mostra.
- [ ] Os callouts teñen función semántica; `warning` e `danger`, xustificados.
- [ ] Os materiais do alumnado non conteñen solucións.

Sintaxe:

- [ ] Front matter con valores dunha liña; `activity` cando o proxecto o use.
- [ ] Un só `#`; numeración e índice da fonte segundo as normas do repositorio;
      ningunha cabeceira contén «Reto» sen querer nin un número inicial que deba
      conservarse como parte do título.
- [ ] Sen `---` no corpo; `[TOC]` e os índices manuais, se existen, serán substituídos
      polo índice automático da saída.
- [ ] Liña baleira antes de cada lista, táboa, cabeceira, cita e bloque.
- [ ] Todos os bloques de código teñen linguaxe; `hl=` só nas liñas comentadas; `{.compact}` se o listado é longo.
- [ ] Callouts con nomes ingleses e liña baleira tras a apertura.
- [ ] Todos os diagramas e imaxes informativas teñen pé; as decorativas, `{.decorative}`.
- [ ] Imaxes grandes ou PDF con `{width=...}`.
- [ ] Referencias con `@fig:`/`@tbl:` e ligazóns internas; nada de `@sec:`, `@eq:`, `@lst:`
      nin posicións («abaixo», «á dereita»).
- [ ] Código en liña escrito literalmente, sen escapes LaTeX engadidos.
- [ ] Remisións no corpo con identificadores explícitos coincidentes no destino;
      non reutilizar as áncoras numeradas do índice manual sen declaralas.
- [ ] Ligazóns externas con `https://`; ligazóns entre actividades relativas ao `.md`.

Verificación:

- [ ] Executar `md2pdf` e revisar todos os avisos.
- [ ] Para a entrega final, `--strict` (e `-e html --strict` se se publica en Moodle).
- [ ] Revisar visualmente as figuras: a validación non garante que sexan lexibles.
