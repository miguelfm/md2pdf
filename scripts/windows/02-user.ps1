# Run as your normal Windows user AFTER 01-system.ps1.
param([switch]$WithMermaid)
$ErrorActionPreference = 'Stop'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if (([Security.Principal.WindowsPrincipal]$identity).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Executa este script no PowerShell normal do teu usuario, sen administrador.'
}
function Invoke-Checked([string]$Command, [string[]]$Arguments) {
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Command fallou: $LASTEXITCODE" }
}
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
if (-not (Test-Path (Join-Path $repo 'install-md2pdf.py'))) { throw "Non se atopa o repositorio: $repo" }
$env:PATH = [Environment]::GetEnvironmentVariable('PATH','Machine') + ';' + [Environment]::GetEnvironmentVariable('PATH','User')
$texBins = @(Get-ChildItem 'C:\texlive\*\bin\windows' -Directory -ErrorAction SilentlyContinue | Sort-Object FullName -Descending)
$pathsToAdd = @((Join-Path $env:LOCALAPPDATA 'md2pdf'))
if ($texBins.Count) { $pathsToAdd += $texBins[0].FullName }
$userPath = [Environment]::GetEnvironmentVariable('PATH','User')
$entries = @($userPath -split ';' | Where-Object { $_ })
foreach ($path in $pathsToAdd) { if ($entries -notcontains $path) { $entries += $path } }
[Environment]::SetEnvironmentVariable('PATH',($entries -join ';'),'User')
$env:PATH = ($pathsToAdd -join ';') + ';' + $env:PATH
[Environment]::SetEnvironmentVariable('PYTHONUTF8','1','User')
$env:PYTHONUTF8 = '1'
foreach ($cmd in @('python.exe','pandoc.exe','lualatex.exe','luaotfload-tool')) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { throw "Falta $cmd. Executa primeiro 01-system.ps1." }
}
$venv = Join-Path $PSScriptRoot '.venv'
if (-not (Test-Path "$venv\Scripts\python.exe")) { Invoke-Checked 'python.exe' @('-m','venv',$venv) }
$python = Join-Path $venv 'Scripts\python.exe'
Invoke-Checked $python @('-m','pip','install','PyMuPDF','Pillow','PyYAML','vl-convert-python>=1.7,<2','pypdf')
if ($WithMermaid) {
    Invoke-Checked 'npm.cmd' @('install','-g','@mermaid-js/mermaid-cli')
    $npmPrefix = (& npm.cmd config get prefix | Select-Object -Last 1).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Non se puido obter o prefixo npm.' }
    if ($entries -notcontains $npmPrefix) {
        $entries += $npmPrefix
        [Environment]::SetEnvironmentVariable('PATH',($entries -join ';'),'User')
    }
    $env:PATH = $npmPrefix + ';' + $env:PATH
    Invoke-Checked 'mmdc.cmd' @('--version')
}
Invoke-Checked 'luaotfload-tool' @('--update','--force')
foreach ($font in @('Source Serif 4','Source Sans 3','Source Code Pro','JetBrains Mono')) {
    $result = & luaotfload-tool "--find=$font" 2>&1
    $result | Out-Host
    if ($LASTEXITCODE -ne 0 -or ($result -join "`n") -notmatch '(?i)found!') { throw "Non se atopa a fonte: $font" }
}
Invoke-Checked $python @((Join-Path $repo 'install-md2pdf.py'))
$launcher = Join-Path $env:LOCALAPPDATA 'md2pdf\md2pdf.cmd'
Invoke-Checked $launcher @('--help')
$sample = Join-Path $PSScriptRoot 'proba.md'
foreach ($format in @('lualatex','html','docx')) {
    $ext = @{lualatex='pdf';html='html';docx='docx'}[$format]
    $output = Join-Path $PSScriptRoot "proba.$ext"
    Invoke-Checked $launcher @($sample,'-e',$format,'-o',$output)
    if (-not (Test-Path $output) -or (Get-Item $output).Length -eq 0) { throw "Non se xerou $output" }
}
Invoke-Checked $python @('-c','import pymupdf,sys; d=pymupdf.open(sys.argv[1]); assert len(d)>0; assert "Windows" in "".join(p.get_text() for p in d); print("PDF verificado:",len(d),"paxinas")',(Join-Path $PSScriptRoot 'proba.pdf'))
Write-Host 'Instalacion e probas completadas. Abre outro terminal para usar md2pdf desde calquera cartafol.'
