# Instalación de md2pdf en Windows 11

Guía completa para instalar e configurar o contorno de conversión Markdown → PDF en Windows 11.

## Instalación semiautomática (scripts do repositorio)

Os scripts están en [`scripts/windows/`](../scripts/windows/). Non precisan
que o repositorio estea nunha ruta concreta nin que o cartafol se chame `md2pdf`.
Executa os comandos seguintes desde a raíz do repositorio clonado.

Requisitos: Windows 11, PowerShell, Chocolatey instalado e conexión a internet.
Se winget está dispoñible úsase para Pandoc e SumatraPDF; en caso contrario
úsase Chocolatey. TeX Live instálase con Chocolatey e os seus paquetes con
`tlmgr`. Python e Node.js instálanse se non se atopan no PATH. A instalación
de TeX Live pode tardar bastante e ocupar varios GB.

### Paso 1: software e fontes, como administrador

Desde **PowerShell normal**, situado na raíz do repositorio:

```powershell
$systemScript = (Resolve-Path .\scripts\windows\01-system.ps1).Path
Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -NoExit -File `"$systemScript`""
```

Windows mostrará a solicitude de control de contas de usuario (UAC).
Acéptaa, ou introduce as credenciais de administrador se as solicita.
Abrirase unha nova xanela de PowerShell elevada que executará o script.
Espera a que remate antes de iniciar o paso 2. A xanela queda aberta para
poder ler os erros ou a mensaxe final.

**Se aparece «Executa este script nun PowerShell como Administrador»**, o
terminal non está elevado. `-ExecutionPolicy Bypass` permite executar este
script nese proceso, pero **non concede permisos de administrador**. Usa
o comando `Start-Process ... -Verb RunAs` anterior. Non é preciso cambiar
a política de execución permanentemente nin desactivar UAC.

Alternativa: abre «Terminal (Administrador)» desde Windows + X, entra no
repositorio con `cd` e executa:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\01-system.ps1
```

O script instala as dependencias e os paquetes TeX necesarios, descarga
os ZIP das publicacións oficiais de Adobe e JetBrains e instala as fontes
estáticas para todos os usuarios: Source Serif 4, Source Sans 3, Source Code
Pro e JetBrains Mono. As descargas quedan en `scripts/windows/fonts/`.
O código actual selecciona Source Code Pro para o texto monoespaciado;
JetBrains Mono queda instalada tamén, pero non é seleccionada automaticamente.

### Paso 2: configuración do usuario e probas, sen administrador

Abre unha nova xanela de **PowerShell normal co teu usuario habitual**, entra
na raíz do repositorio e executa:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\02-user.ps1 -WithMermaid
```

Podes omitir `-WithMermaid` se non precisas diagramas Mermaid. O script:

- Crea un contorno Python en `scripts/windows/.venv/` e instala PyMuPDF,
  Pillow, PyYAML, vl-convert-python e pypdf nel.
- Instala Mermaid CLI con npm se se especifica `-WithMermaid`.
- Configura `PYTHONUTF8=1` e engade as rutas necesarias ao PATH do usuario
  sen copiar o PATH do sistema nin duplicar as entradas existentes.
- Actualiza a caché de LuaLaTeX e comproba as catro familias tipográficas.
- Executa `install-md2pdf.py` co Python do contorno, que queda fixado no
  lanzador `%LOCALAPPDATA%\md2pdf\md2pdf.cmd`.
- Converte `scripts/windows/proba.md` a PDF, HTML e DOCX e comproba que o
  PDF ten páxinas e texto extraíble.

Este paso rexeita un terminal elevado para evitar configurar o usuario
equivocado. Non borres nin movas `.venv` despois de instalar: o lanzador
depende dese intérprete. Se moves o repositorio, repite o paso 2 na nova ruta.
Os ficheiros descargados, o contorno e os documentos de proba están excluídos
de Git mediante `scripts/windows/.gitignore`.

### Verificación e resolución de erros

Cando ambos os scripts rematen correctamente, abre outro terminal:

```powershell
md2pdf --help
md2pdf documento.md
```

Os documentos de proba quedan en `scripts/windows/proba.pdf`, `proba.html`
e `proba.docx`. Abre o PDF para comprobar tamén a súa aparencia.

A comprobación final de `02-user.ps1` abre o PDF con PyMuPDF, verifica que
ten páxinas e que o texto extraído contén `Windows`, e mostra
`PDF verificado: N paxinas`. O código pasado a Python con `-c` usa literais
con comiñas simples para conservar as cadeas ao atravesar Windows PowerShell.
As versións anteriores podían perder as comiñas dobres e fallar con
`SyntaxError: unterminated string literal` aínda que os documentos xa estivesen
xerados. Se atopas ese erro, actualiza o repositorio e repite o paso 2.

Os scripts detéñense ante erros e poden executarse de novo tras corrixilos.
Se non se atopa un comando recentemente instalado, abre outro terminal e
repíteo. A detección adicional de TeX Live busca `C:\texlive\*\bin\windows`;
se usas outra ruta, engade o seu directorio de executables ao PATH.
Se fallan as descargas, comproba a conexión, o proxy e o acceso a GitHub,
Chocolatey e CTAN. Se o ZIP dunha publicación cambia e o script non atopa
fontes estáticas, usa a instalación manual de fontes descrita máis abaixo.

A guía manual seguinte explica cada compoñente con máis detalle. Os scripts
non instalan D2 nin Graphviz; esas ferramentas só son necesarias se usas
os seus respectivos bloques de diagramas.


## Requisitos previos

- Windows 11
- Chocolatey instalado (https://chocolatey.org/install)
- Conexión a internet


## 1. Instalar software base

Todos estes comandos en **PowerShell como Administrador** (Windows + X → "Terminal (Administrador)", ou desde PowerShell: `Start-Process powershell -Verb RunAs`):

```powershell
choco install pandoc -y
choco install python -y
choco install sumatrapdf -y
```

Ou nun só comando:

```
choco install pandoc vcredist140 python sumatrapdf -y
```

SumatraPDF é o visor de PDF recomendado: non bloquea os ficheiros, permitindo rexenerar o PDF sen pechar o visor. Ademais actualiza a vista automaticamente ao rexenerar. 

**Nota:** vcredist140 é necesario para instalar python.


## 2. Instalar TeX Live

En **PowerShell como Administrador**:

```powershell
choco install texlive -y
```

A instalación pode tardar **15-30 minutos**. É normal que pareza conxelada — está descargando e instalando paquetes. Podes verificar que segue activo no Task Manager (Ctrl+Shift+Esc) buscando procesos de `install-tl` ou `texlive`.

**Pechar e abrir un novo terminal** despois da instalación.

Verificar:

```powershell
lualatex --version
tlmgr --version
```


## 3. Instalar paquetes de TeX Live

En **PowerShell como Administrador**:

### Opción A: Coleccións (recomendada, máis segura, ~2GB)

```powershell
tlmgr install collection-luatex collection-latexextra collection-fontsextra collection-fontsrecommended collection-latexrecommended collection-langspanish
```

Paquetes adicionais que poderían faltar:

```powershell
tlmgr install babel-galician hyphen-galician babel-english footnotebackref footnotehyper mdwtools zref luatexbase koma-script tcolorbox fontawesome5 fvextra needspace stix2-otf framed selnolig pdfcol tikzfill adjustbox titling colortbl setspace
```

### Opción B: Paquetes individuais (instalación mínima, ~500MB)

```powershell
tlmgr install fontspec tcolorbox fontawesome5 fvextra needspace etoolbox microtype csquotes koma-script geometry hyperref graphicx fancyvrb babel babel-spanish babel-english babel-galician hyphen-spanish hyphen-english hyphen-galician footnotebackref footnotehyper mdwtools zref luatexbase luaotfload unicode-math amsmath tools booktabs longtable caption float xcolor environ trimspaces ly1 mweights footmisc pagecolor mdframed setspace lineno fancyhdr lastpage eso-pic stix2-otf framed selnolig pdfcol tikzfill adjustbox titling colortbl array multirow enumitem polyglossia tagpdf
```

### Se falta algún paquete

Ao compilar, se aparece un erro `File 'xxx.sty' not found`, podes buscalo e instalalo:

```powershell
tlmgr search --file xxx.sty
tlmgr install nome-do-paquete
```

### Actualizar paquetes

```powershell
# Ver que hai dispoñible
tlmgr update --list

# Actualizar todo
tlmgr update --all
```


## 4. Instalar Node.js e Mermaid CLI (opcional)

Mermaid CLI (`mmdc`) renderiza os bloques ` ```mermaid ` do Markdown como diagramas vectoriais incrustados no PDF. É **opcional**: sen el, os bloques mermaid renderízanse como código fonte e emítese un aviso. Se vas usar diagramas, instálao:

En **PowerShell como Administrador**:

```powershell
choco install nodejs-lts -y
```

**Pechar e abrir un novo terminal** para que o PATH de Node.js estea dispoñible.

Despois, en calquera terminal (xa non hai que ser Administrador):

```powershell
npm install -g @mermaid-js/mermaid-cli
```

Verificar:

```powershell
mmdc --version
```

A primeira vez que se execute `mmdc`, Puppeteer descarga Chromium (~150MB). Pode tardar uns minutos en iniciarse a primeira renderización; as seguintes serán rápidas. md2pdf cachea os diagramas xerados en `%TEMP%\md2pdf-mermaid\`, polo que un mesmo diagrama só se renderiza unha vez.


## 5. Instalar fontes

As fontes deben instalarse **para todos os usuarios** para que LuaLaTeX as atope.

### 5.1. Descargar

Abrir estes enlaces no navegador (descarga automática de ZIPs):

```powershell
Start-Process "https://fonts.google.com/download?family=Source+Serif+4"
Start-Process "https://fonts.google.com/download?family=Source+Sans+3"
Start-Process "https://fonts.google.com/download?family=Source+Code+Pro"
```

JetBrains Mono (fonte monoespaciada principal) ten instalador propio:

```powershell
Start-Process "https://www.jetbrains.com/lp/mono/"
```

Descargar o ZIP desde a páxina, descomprimir e instalar os `.ttf` da carpeta `fonts/ttf/`.

### 5.2. Instalar

Para cada ZIP descargado:

1. Descomprimir o ZIP
2. Entrar no cartafol **`static`** (ignorar os ficheiros da raíz, que son variable fonts)
3. Seleccionar todos os `.ttf` (`Ctrl+A`)
4. `Shift + clic dereito` → **"Mostrar más opciones"** → **"Instalar para todos los usuarios"**

Alternativa: arrastar os `.ttf` a **Configuración → Personalización → Fuentes**.

Alternativa por PowerShell (en **PowerShell como Administrador**, axustar rutas):

```powershell
$downloads = "$env:USERPROFILE\Downloads"

Get-ChildItem "$downloads\Source_Serif_4\static", "$downloads\Source_Sans_3\static", "$downloads\Source_Code_Pro\static", "$downloads\JetBrainsMono\fonts\ttf" -Filter "*.ttf" -ErrorAction SilentlyContinue | ForEach-Object {
    Copy-Item $_.FullName "C:\Windows\Fonts\" -Force
    New-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts" -Name "$($_.BaseName) (TrueType)" -Value $_.Name -PropertyType String -Force | Out-Null
    Write-Host "  ✓ $($_.Name)"
}
```

Nota: os nomes dos cartafoles poden variar. Verificar con `dir "$downloads\Source*"` e `dir "$downloads\JetBrains*"`.

### 5.3. Actualizar caché de fontes e verificar

```powershell
luaotfload-tool --update --force
luaotfload-tool --find="Source Serif 4"
luaotfload-tool --find="Source Sans 3"
luaotfload-tool --find="JetBrains Mono"
luaotfload-tool --find="Source Code Pro"
```

Cada un debe responder `Font "..." found!`. Se algún non se atopa, verificar que se instalou para todos os usuarios e executar `luaotfload-tool --update --force` de novo.

O paquete md2pdf detecta automaticamente as fontes dispoñibles: usa `JetBrains Mono` como monoespaciada principal (con fallback a `Source Code Pro`), e `Source Sans 3` ou `Source Sans Pro` como sans-serif.


## 6. Verificar o contorno

```powershell
echo '# Test' | pandoc --pdf-engine=lualatex -V "mainfont=Source Serif 4" -V "sansfont=Source Sans 3" -V "monofont=JetBrains Mono" -V fontsize=13pt -s -o test.pdf 2>&1
```

Se xera `test.pdf` sen erros, o contorno está correctamente configurado.


## 7. Instalar md2pdf

### 7.1. Preparar ficheiros

Colocar os ficheiros do proxecto nun directorio (por exemplo `C:\Users\TeuUsuario\Projects\md2pdf\`):

```
md2pdf\                    ← paquete Python (directorio)
    __init__.py
    __main__.py
    config.py
    assets.py
    metadata.py
    preprocess.py
    lint.py
    converter.py
    engines\
        lualatex.py
        docx.py
        html.py
md2pdf-preamble.tex
md2pdf.latex
md2pdf.html
md2pdf.css
html.lua
drake-jb.theme
auto-table-widths.lua
small-table.lua
br.lua
callouts.lua
callouts-docx.lua
hl-lines.lua
install-md2pdf.py
README.md
```

Se os ficheiros Lua ou o tema se descargaron con extensión alternativa, renomear:

```powershell
cd C:\Users\TeuUsuario\Projects\md2pdf
Rename-Item "drake-jb-theme.json" "drake-jb.theme" -ErrorAction SilentlyContinue
Rename-Item "auto-table-widths.lua.txt" "auto-table-widths.lua" -ErrorAction SilentlyContinue
Rename-Item "small-table.lua.txt" "small-table.lua" -ErrorAction SilentlyContinue
Rename-Item "br.lua.txt" "br.lua" -ErrorAction SilentlyContinue
Rename-Item "callouts.lua.txt" "callouts.lua" -ErrorAction SilentlyContinue
Rename-Item "callouts-docx.lua.txt" "callouts-docx.lua" -ErrorAction SilentlyContinue
Rename-Item "hl-lines.lua.txt" "hl-lines.lua" -ErrorAction SilentlyContinue
Rename-Item "html.lua.txt" "html.lua" -ErrorAction SilentlyContinue
```

### 7.2. Executar o instalador

```powershell
python install-md2pdf.py
```

### 7.3. Engadir ao PATH

Se o instalador avisa que o directorio non está no PATH, executar na consola **do teu usuario** (non como Administrador, para non modificar o PATH do usuario equivocado):

```powershell
$userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
[Environment]::SetEnvironmentVariable("PATH", "$userPath;$env:LOCALAPPDATA\md2pdf", "User")
```

**Pechar e abrir un novo terminal** para que o cambio teña efecto.

### 7.4. Verificar

```powershell
md2pdf --help
```


## 8. Probar

### 8.1. Compilar un documento

```powershell
md2pdf documento.md
```

A primeira compilación pode tardar algo máis (LuaLaTeX compila a caché de fontes). As seguintes serán rápidas.

### 8.2. Abrir co visor recomendado

```powershell
Start-Process sumatrapdf documento.pdf
```

SumatraPDF actualiza a vista automaticamente ao rexenerar o PDF con `md2pdf`.


## 9. Uso habitual

```powershell
# LuaLaTeX (por defecto, calidade máxima)
md2pdf apuntes.md

# Con portada separada
md2pdf apuntes.md --titlepage

# Sen callouts (blockquotes simples)
md2pdf apuntes.md --no-callouts

# Sen aliñamento decimal nas columnas numéricas das táboas
md2pdf apuntes.md --no-decimal-align

# Varios ficheiros
md2pdf *.md

# Nome de saída específico
md2pdf apuntes.md -o saida.pdf

# HTML5 autocontido
md2pdf apuntes.md -e html

# Word / LibreOffice
md2pdf apuntes.md -e docx
```


## 10. Resolución de problemas

### "No counter 'none' defined"

Erro de compatibilidade entre Pandoc 3.8+ e `longtable` v4.24+. Pandoc xera `\newcounter{none}` para táboas sen numeración pero longtable non o define previamente. O template `md2pdf.latex` inclúe a corrección; asegúrate de ter a versión actualizada instalada:

```powershell
Copy-Item md2pdf.latex "$env:LOCALAPPDATA\md2pdf\md2pdf.latex"
```

### Caracteres especiais non se mostran / `UnicodeEncodeError`

A consola de Windows usa por defecto a codificación `cp1252` que non soporta caracteres Unicode como `→`. Engadir esta variable de entorno de forma permanente:

```powershell
[Environment]::SetEnvironmentVariable("PYTHONUTF8", "1", "User")
```

Pechar e abrir un novo terminal para que teña efecto.

### "File 'xxx.sty' not found"

Se falta `ragged2e.sty` (requirido polo preámbulo de md2pdf), executa nun
PowerShell como administrador:

```powershell
tlmgr install ragged2e
```

Buscar e instalar o paquete que falta:

```powershell
tlmgr search --file xxx.sty
tlmgr install nome-do-paquete
```

### "Font 'Source ...' not found"

Reinstalar as fontes para todos os usuarios e actualizar a caché:

```powershell
luaotfload-tool --update --force
luaotfload-tool --find="Source Serif 4"
```

### "Permission denied" ao xerar o PDF

O ficheiro PDF está aberto nalgún visor que bloquea ficheiros (Acrobat, Edge). Pechar o visor ou usar SumatraPDF que non bloquea.

### "Error producing PDF" pero o PDF existe

Ás veces LuaLaTeX xera avisos (warnings) que Pandoc interpreta como erros. Verificar:

```powershell
Test-Path documento.pdf
```

Se existe e ten tamaño > 0, é válido. Os avisos `Missing character` significan que hai emojis no Markdown que non están no mapeamento do script.

### "TeX capacity exceeded" ou compilación colgada indefinidamente

En LuaLaTeX con `polyglossia` e `fontspec`, a redefinición de `p{}` mediante `\newcolumntype{p}[1]{...p{#1}}` causa recursión infinita. Non usar esta construción en `md2pdf-preamble.tex`. O aliñamento superior das celas está xestionado polo filtro `auto-table-widths.lua` con `\leavevmode\strut`, que non require redefinir `p{}`.

### "Undefined control sequence"

O preámbulo (`md2pdf-preamble.tex`) non se está aplicando. Reinstalar:

```powershell
cd C:\Users\TeuUsuario\Projects\md2pdf
python install-md2pdf.py
```

### PowerShell non atopa `lualatex` / `tlmgr` / outro comando

Pechar e abrir un **novo terminal**. Tras instalar software, o PATH actualízase só en novos terminais.

### `curl` dá erro de parámetro `-L`

PowerShell ten un alias `curl` → `Invoke-WebRequest`. Usar `curl.exe`:

```powershell
curl.exe -L -o ficheiro.zip "https://..."
```

### "Unknown option 'galician'" en babel

Instalar soporte de galego para LaTeX:

```powershell
tlmgr install babel-galician hyphen-galician
```

### Executar comandos como Administrador

Moitas operacións de TeX Live e instalación de fontes requiren admin:

- Windows + X → **"Terminal (Administrador)"**
- Ou desde PowerShell normal: `Start-Process powershell -Verb RunAs`
- O título da xanela debe dicir **"Administrador"**

### Ver historial de paquetes instalados

```powershell
Get-History | Where-Object { $_.CommandLine -like "tlmgr install*" }
```

### Actualizar todo o software

```powershell
# Chocolatey (Pandoc, Python, SumatraPDF)
choco upgrade all -y

# TeX Live
tlmgr update --all
```


## 11. Diferenzas con Linux (Arch)

| Aspecto | Arch Linux | Windows 11 |
|---|---|---|
| Xestor de paquetes | `pacman` | `choco` + `tlmgr` |
| TeX Live | `pacman -S texlive texlive-*` | `choco install texlive` + `tlmgr install ...` |
| Mermaid CLI (opcional) | `pacman -S mermaid-cli` | `choco install nodejs-lts` + `npm install -g @mermaid-js/mermaid-cli` |
| Fontes do sistema | `pacman -S adobe-source-*-fonts ttf-jetbrains-mono` | Descarga manual desde Google Fonts + jetbrains.com |
| Fonte sans-serif | `Source Sans 3` ou `Source Sans Pro` (auto-detectado) | `Source Sans 3` (auto-detectado) |
| Fonte monoespaciada | `JetBrains Mono` (fallback: `Source Code Pro`) | `JetBrains Mono` (fallback: `Source Code Pro`) |
| Fontes matemáticas | `pacman -S otf-stix` | `tlmgr install stix2-otf` |
| Visor PDF | Okular / Zathura / Evince | SumatraPDF |
| Shell | Fish / Bash | PowerShell |
| Admin para instalar | `sudo` | PowerShell como Administrador |
| Instalación md2pdf | `~/.local/bin/md2pdf` | `%LOCALAPPDATA%\md2pdf\md2pdf.cmd` |
| Alias de curl | Non hai conflito | `curl` = Invoke-WebRequest; usar `curl.exe` |


## 12. Nota sobre MiKTeX

Esta guía usa **TeX Live** en vez de MiKTeX. MiKTeX require que un administrador faga un "check for updates" antes de poder compilar, e este paso pode ser problemático en contornos con permisos restrinxidos. TeX Live non ten este requisito e funciona de forma máis predicible, similar á experiencia en Linux.

## Outros gráficos e comprobacións de fiabilidade

Ademais de Mermaid, md2pdf admite D2, Graphviz (dot) e Vega-Lite. D2 e dot
deben estar no PATH. Os compoñentes Python opcionais instálanse co mesmo
Python usado polo instalador:

```powershell
python -m pip install PyMuPDF Pillow PyYAML "vl-convert-python>=1.7,<2"
python install-md2pdf.py
```

O instalador informa dos compoñentes detectados e fixa ese intérprete no
lanzador .cmd. Se cambias de Python, reinstala md2pdf. Consulta DIAGRAMAS.md
para os niveis de validación, a caché e `--strict`; VEGA-LITE.md describe
as restricións de datos. A caché danada rexenérase automaticamente.
