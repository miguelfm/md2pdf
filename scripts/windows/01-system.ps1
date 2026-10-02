# Run in PowerShell as Administrator. Re-runnable; stops on errors.
$ErrorActionPreference = 'Stop'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if (-not ([Security.Principal.WindowsPrincipal]$identity).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Executa este script nun PowerShell como Administrador. Consulta docs/INSTALL_WINDOWS.md: instalacion semiautomatica, paso 1 (Start-Process -Verb RunAs).'
}
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
function Invoke-Checked([string]$Command, [string[]]$Arguments) {
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Command fallou: $LASTEXITCODE" }
}
function Refresh-Path {
    $env:PATH = [Environment]::GetEnvironmentVariable('PATH','Machine') + ';' + [Environment]::GetEnvironmentVariable('PATH','User')
    $texBins = @(Get-ChildItem 'C:\texlive\*\bin\windows' -Directory -ErrorAction SilentlyContinue | Sort-Object FullName -Descending)
    if ($texBins.Count) { $env:PATH = $texBins[0].FullName + ';' + $env:PATH }
}
Refresh-Path
if (-not (Get-Command choco.exe -ErrorAction SilentlyContinue)) { throw 'Chocolatey non esta instalado.' }
foreach ($item in @(
    @{Command='pandoc.exe'; Winget='JohnMacFarlane.Pandoc'; Choco='pandoc'},
    @{Command='SumatraPDF.exe'; Winget='SumatraPDF.SumatraPDF'; Choco='sumatrapdf'}
)) {
    if (-not (Get-Command $item.Command -ErrorAction SilentlyContinue)) {
        if (Get-Command winget.exe -ErrorAction SilentlyContinue) {
            & winget.exe install --id $item.Winget --exact --source winget --silent --accept-package-agreements --accept-source-agreements
            if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne -1978335189) { throw "winget fallou: $LASTEXITCODE" }
        } else {
            Invoke-Checked 'choco.exe' @('install',$item.Choco,'-y','--no-progress')
        }
    }
}
if (-not (Get-Command python.exe -ErrorAction SilentlyContinue)) {
    Invoke-Checked 'choco.exe' @('install','vcredist140','python','-y','--no-progress')
}
if (-not (Get-Command node.exe -ErrorAction SilentlyContinue)) {
    Invoke-Checked 'choco.exe' @('install','nodejs-lts','-y','--no-progress')
}
if (-not (Get-Command lualatex.exe -ErrorAction SilentlyContinue)) {
    Write-Host 'Instalando TeX Live. Pode tardar bastante e ocupar varios GB.'
    Invoke-Checked 'choco.exe' @('install','texlive','-y','--no-progress')
}
Refresh-Path
if (-not (Get-Command tlmgr -ErrorAction SilentlyContinue)) { throw 'Non se atopa tlmgr. Abre outro terminal e executa de novo este script.' }
Invoke-Checked 'tlmgr' @('update','--self')
$packages = ('fontspec tcolorbox fontawesome5 fvextra needspace etoolbox microtype csquotes koma-script geometry hyperref graphicx fancyvrb babel babel-spanish babel-english babel-galician hyphen-spanish hyphen-english hyphen-galician footnotebackref footnotehyper mdwtools zref luatexbase luaotfload unicode-math amsmath tools booktabs longtable caption float xcolor environ trimspaces ly1 mweights footmisc pagecolor mdframed setspace lineno fancyhdr lastpage eso-pic stix2-otf framed selnolig pdfcol tikzfill adjustbox titling colortbl multirow enumitem polyglossia tagpdf xurl listings').Split(' ')
Invoke-Checked 'tlmgr' (@('install') + $packages + @('ragged2e'))

# Download official release archives; install static fonts for all users.
$downloads = Join-Path $PSScriptRoot 'fonts'
New-Item -ItemType Directory -Path $downloads -Force | Out-Null
foreach ($repo in @('adobe-fonts/source-serif','adobe-fonts/source-sans','adobe-fonts/source-code-pro','JetBrains/JetBrainsMono')) {
    $release = Invoke-RestMethod "https://api.github.com/repos/$repo/releases/latest" -Headers @{'User-Agent'='md2pdf-windows-setup'}
    $archives = @($release.assets | Where-Object { $_.name -match '\.zip$' -and $_.name -notmatch '(?i)(woff|variable|\bVF\b)' })
    $asset = $archives | Where-Object { $_.name -match '(?i)TTF' } | Select-Object -First 1
    if (-not $asset) { $asset = $archives | Where-Object { $_.name -match '(?i)OTF' } | Select-Object -First 1 }
    if (-not $asset) { $asset = $archives | Select-Object -First 1 }
    if (-not $asset) { throw "Non se atopou un ZIP de fontes en $repo" }
    $archive = Join-Path $downloads $asset.name
    Invoke-WebRequest $asset.browser_download_url -OutFile $archive -UseBasicParsing
    $expanded = Join-Path $downloads (($repo -replace '/','-') + '-' + $release.id)
    Expand-Archive -LiteralPath $archive -DestinationPath $expanded -Force
    $fonts = @(Get-ChildItem $expanded -Recurse -File | Where-Object { $_.Extension -in '.ttf','.otf' -and $_.FullName -notmatch '(?i)(variable|[\\/]VF[\\/]|\[)' })
    if (-not $fonts.Count) { throw "Non se atoparon fontes estaticas en $archive" }
    foreach ($font in $fonts) {
        Copy-Item -LiteralPath $font.FullName -Destination (Join-Path "$env:WINDIR\Fonts" $font.Name) -Force
        $suffix = if ($font.Extension -eq '.ttf') { 'TrueType' } else { 'OpenType' }
        New-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts' -Name "$($font.BaseName) ($suffix)" -Value $font.Name -PropertyType String -Force | Out-Null
    }
    Write-Host "Instaladas $($fonts.Count) fontes: $repo ($($release.tag_name))"
}
Write-Host 'Software e fontes instalados. Abre PowerShell normal e executa 02-user.ps1.'
