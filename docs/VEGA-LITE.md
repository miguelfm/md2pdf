# Gráficos Vega-Lite

Instala a dependencia opcional no mesmo Python que executa md2pdf:

```bash
python -m pip install "vl-convert-python>=1.7,<2"
```

En Arch Linux, se o Python está xestionado polo sistema, usa un contorno virtual.
Non uses --break-system-packages. O lanzador de md2pdf debe executar o Python
dese contorno. Tamén podes activar o contorno e executar python md2pdf_runner.py.
En Windows, instala a dependencia co mesmo python/py que empregas para md2pdf.

Probado con vl-convert-python 1.9.0.post1. Non require Node nin navegador.
A dependencia só se comproba cando aparece un bloque Vega-Lite.
A API utilizada é a de https://github.com/vega/vl-convert .

## Sintaxe

Bloques vega-lite ou vegalite, con JSON estrito dentro; sen comentarios nin
comas finais. Admítense width, height, caption e #identificador, igual ca nos
outros diagramas. O tema e estilos defínense no JSON (config), non no atributo
theme de D2. layout tampouco se aplica a Vega-Lite.

Consulta exemplos-vega-lite.md para histogramas, puntos con regresión e sectores.
A regresión do exemplo é un axuste aos datos, non unha predición validada.

Saídas activas: PDF para LuaLaTeX, PNG para DOCX e SVG para HTML5. Son gráficos estáticos:
non conservan tooltips nin interacción. As fontes deben estar instaladas.
As medidas width/height do JSON controlan a composición; os atributos Markdown
controlan o tamaño final no documento.

## Metadatos opcionais

```yaml
diagrams:
  vega-lite:
    width: 85%
```

Requírese PyYAML só para estes metadatos. A configuración do bloque ten prioridade.

## Datos e seguridade

Esta primeira versión admite datos inline en data.values ou datasets.
Non admite url/href nin marcas image, mesmo aniñados; a comprobación é
conservadora e tamén rexeita campos de datos con eses nomes.
$schema pode indicarse, pero non se descarga. Non se cargan CSV/JSON externos.
O renderizador recibe allowed_base_urls=[] para bloquear recursos externos.
Non se executa código Python procedente do documento.

A conversión ocorre nun subproceso cun timeout de 60 segundos. Isto non é unha
sandbox de memoria/CPU: usa documentos de confianza.
Se falta a dependencia, o JSON é incorrecto ou a conversión falla, o bloque
mantense como código e emítese un aviso. Un fallo non publica saídas parciais.
A caché inclúe a versión instalada de vl-convert-python.

## Verificación

python -m unittest discover -s tests -v

As probas reais de PDF/SVG/PNG sáltanse se vl-convert-python non está instalado.
As probas anteriores de Mermaid, D2 e Graphviz seguen incluídas.

