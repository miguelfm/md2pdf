# Installing md2pdf on Windows 11

This guide covers the PDF, HTML, and DOCX conversion environment on Windows 11. HTML and DOCX do not require LaTeX, but the assisted scripts below install a full PDF-capable environment.

## Assisted installation

The scripts live in [scripts/windows/](../scripts/windows/). They do not require a particular checkout path or directory name. Run the following commands from the cloned repository's root.

Requirements: Windows 11, PowerShell, Chocolatey, and internet access. The scripts use winget for Pandoc and SumatraPDF when available, otherwise Chocolatey. TeX Live is installed through Chocolatey, and TeX packages through `tlmgr`. Python and Node.js are installed when missing from `PATH`. TeX Live can take considerable time and several GB of disk space.

### Step 1: software and fonts, as administrator

From a **normal PowerShell** in the repository root:

```powershell
$systemScript = (Resolve-Path .\scripts\windows\01-system.ps1).Path
Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -NoExit -File `"$systemScript`""
```

Accept Windows' UAC prompt, supplying administrator credentials if requested. A separate elevated PowerShell window runs the script and stays open for you to inspect the result. Wait for completion before step 2.

If the script reports that an administrator PowerShell is required, the terminal is not elevated. `-ExecutionPolicy Bypass` permits this script in that process; **it does not grant administrator privileges**. Use the `Start-Process ... -Verb RunAs` command above. No permanent execution-policy change or UAC disabling is needed.

Alternatively, open **Terminal (Admin)** from Windows+X, change into the checkout, and run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\01-system.ps1
```

The script installs dependencies and TeX packages, downloads official Adobe/JetBrains release ZIPs, and installs static Source Serif 4, Source Sans 3, Source Code Pro, and JetBrains Mono fonts for all users. Downloads remain under `scripts/windows/fonts/`.

**Current font selection:** md2pdf uses Source Code Pro for monospaced text. JetBrains Mono is installed by the script too, but is not selected automatically by the current code.

### Step 2: user configuration and checks, without administrator privileges

Open a new **normal PowerShell under your usual account**, change into the checkout, and run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\02-user.ps1 -WithMermaid
```

Omit `-WithMermaid` if you do not need Mermaid diagrams. The script:

- Creates `scripts/windows/.venv/` and installs PyMuPDF, Pillow, PyYAML, vl-convert-python, and pypdf there.
- Installs Mermaid CLI through npm when requested.
- Sets `PYTHONUTF8=1` and adds required user PATH entries without copying the system PATH or duplicating existing entries.
- Updates LuaLaTeX's font cache and checks all four font families.
- Runs `install-md2pdf.py` with the virtual environment's interpreter, pinning it in `%LOCALAPPDATA%\md2pdf\md2pdf.cmd`.
- Converts `scripts/windows/proba.md` into PDF, HTML, and DOCX, and checks that the PDF has pages and extractable text.

This step rejects elevated terminals to avoid configuring the wrong account. Do not move or delete `.venv` after installation: the launcher depends on it. If you move the checkout, repeat step 2 in its new location. Downloads, the environment, and generated smoke documents are excluded by `scripts/windows/.gitignore`.

### Verify and troubleshoot the scripts

After both scripts finish successfully, open another terminal:

```powershell
md2pdf --help
md2pdf document.md --lang en
```

The generated smoke outputs are `scripts/windows/proba.pdf`, `proba.html`, and `proba.docx`. Open the PDF and inspect its appearance as well.

The final step-2 check opens the PDF with PyMuPDF, checks pages and the text `Windows`, and reports `PDF verificado: N paxinas` (the current script message is Galician). Python `-c` code uses single-quoted literals to survive Windows PowerShell quoting. Older revisions could lose double quotes and raise `SyntaxError: unterminated string literal` even after generating the documents. Update the checkout and repeat step 2 if you encounter that old error.

Scripts stop on errors and can be rerun after correction. Reopen the terminal if a newly installed command is missing. Extra TeX detection searches `C:\texlive\*\bin\windows`; add a different installation's executable directory to PATH yourself.

For download failures, check network/proxy access to GitHub, Chocolatey, and CTAN. If an official font archive changes structure and the script cannot locate static files, use the manual font steps below.

D2 and Graphviz are not installed by these scripts; they are only needed for their respective diagram blocks.

## Manual installation

The following steps explain the components individually. They are an alternative to the assisted setup.

### 1. Base software

In **PowerShell as Administrator**:

```powershell
choco install pandoc vcredist140 python sumatrapdf -y
```

`vcredist140` supplies the Visual C++ runtime used by the Python installation. SumatraPDF is useful for previewing because it can reload a regenerated PDF without holding a blocking file lock.

### 2. TeX Live

In an administrator PowerShell:

```powershell
choco install texlive -y
```

Installation can take 15–30 minutes or longer depending on downloads and package selection. Inspect Task Manager for `install-tl`/TeX Live processes if it appears idle. Reopen the terminal afterward and verify:

```powershell
lualatex --version
tlmgr --version
```

### 3. TeX packages

Run system-wide TeX package installation from an administrator PowerShell. Collection installation is more comprehensive; exact download/disk sizes depend on the current distribution.

```powershell
tlmgr install collection-luatex collection-latexextra collection-fontsextra collection-fontsrecommended collection-latexrecommended collection-langspanish
```

Additional packages that may be needed:

```powershell
tlmgr install babel-galician hyphen-galician babel-english footnotebackref footnotehyper mdwtools zref luatexbase koma-script tcolorbox fontawesome5 fvextra needspace stix2-otf framed selnolig pdfcol tikzfill adjustbox titling colortbl setspace ragged2e
```

For a more selective installation, the existing project dependency list is:

```powershell
tlmgr install fontspec tcolorbox fontawesome5 fvextra needspace etoolbox microtype csquotes koma-script geometry hyperref graphicx fancyvrb babel babel-spanish babel-english babel-galician hyphen-spanish hyphen-english hyphen-galician footnotebackref footnotehyper mdwtools zref luatexbase luaotfload unicode-math amsmath tools booktabs longtable caption float xcolor environ trimspaces ly1 mweights footmisc pagecolor mdframed setspace lineno fancyhdr lastpage eso-pic stix2-otf framed selnolig pdfcol tikzfill adjustbox titling colortbl array multirow enumitem polyglossia tagpdf ragged2e
```

For a missing `xxx.sty`, search its owning package and install it:

```powershell
tlmgr search --file xxx.sty
tlmgr install package-name
```

To inspect or update installed packages:

```powershell
tlmgr update --list
tlmgr update --all
```

### 4. Node.js and Mermaid CLI — optional

Mermaid CLI (`mmdc`) renders Mermaid fences. Without it, blocks remain code with a warning; strict mode fails. To install, use administrator PowerShell for Node.js:

```powershell
choco install nodejs-lts -y
```

Reopen a normal terminal, then install the user-facing renderer:

```powershell
npm install -g @mermaid-js/mermaid-cli
mmdc --version
```

Puppeteer/Chromium download and first-run behavior depend on the installed Mermaid package. Rendering can require a substantial browser download. Cached diagrams are stored under `%TEMP%\md2pdf-mermaid\`.

### 5. Fonts

Install static fonts **for all users** so LuaLaTeX can find them. Download Source Serif 4, Source Sans 3, and Source Code Pro:

```powershell
Start-Process "https://fonts.google.com/specimen/Source+Serif+4"
Start-Process "https://fonts.google.com/specimen/Source+Sans+3"
Start-Process "https://fonts.google.com/specimen/Source+Code+Pro"
```

JetBrains Mono is optional for custom font configurations:

```powershell
Start-Process "https://www.jetbrains.com/lp/mono/"
```

Extract each ZIP, select the static `.ttf` files (often in `static/`; JetBrains uses `fonts/ttf/`), then choose **Show more options → Install for all users**. Avoid assuming variable-font files at the archive root are the static set. Windows Settings → Personalization → Fonts offers another installation interface; confirm that the intended all-user installation is available to LuaLaTeX.

An administrator PowerShell alternative, with paths adjusted to your extracted archives:

```powershell
$downloads = "$env:USERPROFILE\Downloads"

Get-ChildItem "$downloads\Source_Serif_4\static", "$downloads\Source_Sans_3\static", "$downloads\Source_Code_Pro\static", "$downloads\JetBrainsMono\fonts\ttf" -Filter "*.ttf" -ErrorAction SilentlyContinue | ForEach-Object {
    Copy-Item $_.FullName "C:\Windows\Fonts\" -Force
    New-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts" -Name "$($_.BaseName) (TrueType)" -Value $_.Name -PropertyType String -Force | Out-Null
    Write-Host "Installed $($_.Name)"
}
```

Archive directory names can differ. Inspect them before using the command. Refresh LuaLaTeX's cache:

```powershell
luaotfload-tool --update --force
luaotfload-tool --find="Source Serif 4"
luaotfload-tool --find="Source Sans 3"
luaotfload-tool --find="Source Code Pro"
```

Each lookup should report a found font. md2pdf prefers Source Sans 3 / Source Sans Pro for sans, Source Serif 4 / Source Serif Pro for serif, and currently selects Source Code Pro for mono. STIX Two Math is provided by the TeX `stix2-otf` package.

### 6. Check the environment

```powershell
echo '# Test' | pandoc --pdf-engine=lualatex -V "mainfont=Source Serif 4" -V "sansfont=Source Sans 3" -V "monofont=Source Code Pro" -V fontsize=13pt -s -o test.pdf 2>&1
```

A successful conversion checks the basic Pandoc/LuaLaTeX/font setup. It is not a full test of every md2pdf filter.

### 7. Install md2pdf

Keep the **complete checkout**, including the `md2pdf/` package, templates, preamble, theme, syntax definition, Lua filters, and installer. Copying a selected subset can omit new assets. For example:

```powershell
cd C:\Users\YourUser\Projects\md2pdf
python install-md2pdf.py
```

Use the Python environment containing the optional libraries you intend to use. If files were downloaded individually with unwanted `.txt` extensions, restore their repository names before installing; cloning or extracting a repository ZIP avoids that problem.

If prompted, add the launcher directory to the **current user's** PATH in a normal PowerShell:

```powershell
$userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
$launcherPath = "$env:LOCALAPPDATA\md2pdf"
if (($userPath -split ';') -notcontains $launcherPath) {
    [Environment]::SetEnvironmentVariable("PATH", "$userPath;$launcherPath", "User")
}
```

Reopen the terminal:

```powershell
md2pdf --help
```

### 8. Convert and preview

```powershell
md2pdf document.md --lang en
Start-Process sumatrapdf document.pdf
```

The first compilation can be slower while LuaLaTeX builds font caches. SumatraPDF can refresh the view when the file is regenerated.

### 9. Everyday use

```powershell
# Default PDF
md2pdf notes.md --lang en

# Separate PDF title page
md2pdf notes.md --lang en --titlepage

# Disable callouts or decimal alignment
md2pdf notes.md --lang en --no-callouts
md2pdf notes.md --lang en --no-decimal-align

# Multiple files or an explicit output
md2pdf *.md --lang en
md2pdf notes.md --lang en -o output.pdf

# Self-contained HTML and editable Word output
md2pdf notes.md --lang en -e html
md2pdf notes.md --lang en -e docx
```

The document-language default remains Galician (`gl`). `--lang en` does not translate your text or all built-in labels/messages.

## Troubleshooting

### `No counter 'none' defined`

This can occur with newer Pandoc/longtable combinations. The current `md2pdf.latex` contains the project's compatibility fix. Update the checkout and reinstall all assets:

```powershell
python install-md2pdf.py
```

### Missing special characters / `UnicodeEncodeError`

A legacy Windows console encoding such as cp1252 cannot represent every Unicode character. Enable Python UTF-8 mode for the user, then reopen the terminal:

```powershell
[Environment]::SetEnvironmentVariable("PYTHONUTF8", "1", "User")
```

### `File 'xxx.sty' not found`

Search/install the owning package with `tlmgr`; for `ragged2e.sty`:

```powershell
tlmgr install ragged2e
```

### `Font 'Source ...' not found`

Confirm an all-user static-font installation and refresh the font cache:

```powershell
luaotfload-tool --update --force
luaotfload-tool --find="Source Serif 4"
```

### `Permission denied` when writing a PDF

Some PDF viewers lock files. Close the document or use a viewer such as SumatraPDF that permits replacement.

### `Error producing PDF`, but a file exists

A nonempty file alone does **not** establish that the build is valid. Inspect the error, check that the file was freshly generated, open it, and review its pages before distributing it. A `Missing character` message can indicate unsupported emoji or unavailable glyphs.

### `TeX capacity exceeded` or a hung build

A recursive `p{}` redefinition such as `\newcolumntype{p}[1]{...p{#1}}` can loop with LuaLaTeX/fontspec/polyglossia. Do not add it to the preamble; the table filter handles top alignment.

Large raster images or vector PDFs without explicit size can also hang in the current pipeline. Give them `{width=100%}` or another suitable explicit width; see [the image guide](README.md#images-and-figures).

### `Undefined control sequence`

Check the reported command, document structure, and whether the expected preamble/filter assets are installed. Reinstall after updating the checkout. An unclosed source block can also cause misleading downstream LaTeX errors.

### PowerShell cannot find `lualatex`, `tlmgr`, or another command

Reopen the terminal after installation. If needed, add the actual installation's executable directory to PATH; the scripts search `C:\texlive\*\bin\windows`.

### `curl` rejects `-L`

Windows PowerShell may alias `curl` to `Invoke-WebRequest`. Call the native executable explicitly:

```powershell
curl.exe -L -o archive.zip "https://example.com/archive.zip"
```

### Babel reports `Unknown option 'galician'`

The default language is Galician; install its support even if you are testing the default command:

```powershell
tlmgr install babel-galician hyphen-galician
```

### Administrator operations

Use Windows+X → **Terminal (Admin)**, or `Start-Process powershell -Verb RunAs`. Font and system-wide TeX installation require elevation; user setup and the md2pdf launcher should normally run as your usual user.

To inspect the current PowerShell session's package-install commands:

```powershell
Get-History | Where-Object { $_.CommandLine -like "tlmgr install*" }
```

For deliberate maintenance, review the changes requested by your package manager:

```powershell
choco upgrade all -y
tlmgr update --all
```

## Differences from Arch Linux

| Component | Arch Linux | Windows 11 |
|---|---|---|
| Package manager | `pacman` | Chocolatey / winget; `tlmgr` for TeX |
| TeX | Distribution packages | TeX Live plus `tlmgr` |
| Mermaid | `mermaid-cli` | Node.js plus npm Mermaid CLI |
| Fonts | System font packages | Static font files installed for all users |
| Current code font | Source Code Pro | Source Code Pro |
| Math font | `otf-stix` | `stix2-otf` |
| PDF preview | Okular / Zathura / Evince | SumatraPDF |
| Launcher | `~/.local/bin/md2pdf` | `%LOCALAPPDATA%\md2pdf\md2pdf.cmd` |
| Shell | Bash / Fish / Zsh | PowerShell |
| `curl` | Usually the native executable | Use `curl.exe` to bypass the PowerShell alias |

## TeX distribution choice

The documented Windows workflow uses **TeX Live**, matching the project's tested setup. Other distributions, including MiKTeX, are not covered by these installation steps. Package names, update policies, and administrator requirements differ.

## Other renderers and validation

D2 and Graphviz executables must be on PATH when used. Install optional Python components into the same environment used by the installer:

```powershell
python -m pip install PyMuPDF Pillow PyYAML "vl-convert-python>=1.7,<2"
python install-md2pdf.py
```

The installer reports detected components and pins that interpreter in the `.cmd` launcher. Reinstall when changing Python. See [DIAGRAMS.md](DIAGRAMS.md) for validation levels, caching, and strict mode, and [VEGA-LITE.md](VEGA-LITE.md) for chart data restrictions. Damaged cache entries are regenerated automatically.
