# Paquetes IMS para Moodle

`md2pdf` pode agrupar varios documentos Markdown nun **IMS Content Package** para Moodle. Non é un cuarto motor de renderizado: cada `.md` convértese primeiro co motor HTML5 autocontido e despois empaquétanse os HTML xunto cun `imsmanifest.xml` nun ZIP.

```bash
md2pdf U1/ --ims U1-moodle.zip
md2pdf U1/*.md --ims U1-moodle.zip --ims-title "UD1. Introdución á programación"
```

O ZIP resultante ten unha estrutura semellante a:

```text
U1-moodle.zip
├── imsmanifest.xml
├── U1A1_Introducion.html
├── U1A2_Execucion.html
└── U1A3_....html
```

Os HTML seguen sendo autocontidos: CSS, imaxes e diagramas SVG quedan embebidos. O manifesto só necesita declarar cada HTML como recurso `webcontent`.

## Navegación e orde

A orde dos elementos IMS é exactamente a orde dos ficheiros recollidos por `md2pdf`. Ao pasar un directorio, `collect_files()` usa **orde natural**: `U1A2` vai antes que `U1A10` (coa orde alfabética simple quedaría `U1A1`, `U1A10`, `U1A2`). Se pasas os ficheiros un a un, respéctase a orde da liña de comandos.

O título de cada elemento de navegación obténse nesta orde:

1. `activity` dos metadatos;
2. `title` dos metadatos;
3. primeiro `# H1` do Markdown;
4. nome do ficheiro.

O título global do paquete é o nome do ZIP sen extensión. Pódese substituír con `--ims-title`.

## Ligazóns entre documentos

Se un documento do paquete enlaza outro Markdown tamén incluído:

```markdown
[Seguinte actividade](U1A2_Execucion.md#o-caso-de-java)
```

`md2pdf` reescribe automaticamente a ligazón para que apunte ao HTML do paquete. O fragmento (`#o-caso-de-java`) é o identificador que Pandoc xera para a cabeceira `## O caso de Java`: non inclúe o número da sección.

Resultado:

```html
<a href="U1A2_Execucion.html#o-caso-de-java">...</a>
```

As ligazóns locais a `.md` que non forman parte do paquete producen un aviso. Con `--strict` impiden xerar o ZIP, para evitar publicar un paquete con navegación rota.

## Recursos enlazados

As ligazóns a outros ficheiros locais (código de partida, PDF, ZIP de exercicios…) inclúense no paquete dentro de `recursos/` e a ligazón reescríbese para apuntar alí:

```markdown
Descarga o [código de partida](recursos/exercicio.zip).
```

```text
U1-moodle.zip
├── imsmanifest.xml
├── U1A1_Introducion.html
└── recursos/
    └── exercicio.zip
```

Cada ficheiro engádese unha soa vez aínda que o enlacen varios documentos, e declárase como `<file>` no recurso IMS que o usa. Se dous ficheiros distintos teñen o mesmo nome, o segundo recibe un sufixo (`exercicio-2.zip`).

Se a ligazón apunta a un ficheiro que non existe, `md2pdf` avisa e deixa a ligazón tal cal; con `--strict` non se xera o ZIP. As imaxes non pasan por aquí: xa van incrustadas no HTML.

## Opcións HTML compatibles

O empaquetado IMS reutiliza a saída HTML, polo que admite:

- `--no-toc`;
- `--no-number`;
- `--no-callouts`;
- `--no-metadata`;
- `--night`;
- `--print`;
- `--plain`;
- `--strict`;
- `--toc-depth`;
- `--lang`;
- `--highlight`;
- `--template` (template HTML).

`--titlepage` non aplica ao paquete IMS. `--watch` non está implementado neste modo. `-o/--output` tampouco se usa: o destino indícase directamente en `--ims`.

## Importación en Moodle

No curso Moodle, engade un recurso **IMS content package / Paquete de contido IMS** e carga o ZIP xerado. Moodle usa a organización declarada no `imsmanifest.xml` para presentar os recursos e a súa navegación.

O paquete segue IMS Content Packaging 1.1.4 e coloca obrigatoriamente `imsmanifest.xml` na raíz do ZIP.
