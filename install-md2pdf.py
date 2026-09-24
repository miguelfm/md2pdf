#!/usr/bin/env python3
"""
install-md2pdf.py — Instalador de md2pdf para Linux e Windows.

Uso:
    python install-md2pdf.py           # Instalar
    python install-md2pdf.py --remove  # Desinstalar

Onde instala (Linux):
    ~/.local/bin/md2pdf                              (executábel wrapper)
    ~/.local/share/md2pdf/md2pdf/                    (paquete Python)
    ~/.local/share/md2pdf/md2pdf.latex               (template LuaLaTeX)
    ~/.local/share/md2pdf/md2pdf-preamble.tex        (preámbulo LaTeX)
    ~/.local/share/md2pdf/md2pdf.html                 (template HTML5)
    ~/.local/share/md2pdf/md2pdf.css                  (estilos HTML)
    ~/.local/share/md2pdf/html.lua                    (semántica HTML)
    ~/.local/share/md2pdf/drake-jb.theme             (cores de resaltado)
    ~/.local/share/md2pdf/auto-table-widths.lua      (filtro Lua táboas)
    ~/.local/share/md2pdf/small-table.lua            (filtro Lua táboas pequenas)
    ~/.local/share/md2pdf/callouts.lua               (filtro Lua callouts PDF)
    ~/.local/share/md2pdf/callouts-docx.lua          (filtro Lua callouts DOCX)
    ~/.local/share/md2pdf/hl-lines.lua               (filtro Lua resaltado liñas)
    ~/.local/share/md2pdf/br.lua                     (filtro Lua <br> → salto de liña)
    ~/.local/share/md2pdf/figure-captions.lua        (filtro Lua pés e referencias de figuras)
    ~/.local/share/md2pdf/reference.docx             (estilos DOCX, opcional)
"""

import argparse
import importlib.util
import os
import shlex
import shutil
import stat
import subprocess
import sys
from pathlib import Path


# Activos obrigatorios
DATA_FILES_REQUIRED = [
    'md2pdf.latex',
    'md2pdf-preamble.tex',
    'auto-table-widths.lua',
    'md2pdf.html',
    'md2pdf.css',
    'html.lua',
]

# Activos opcionais: copiados se existen, saltados silenciosamente se non
DATA_FILES_OPTIONAL = [
    'drake-jb.theme',
    'small-table.lua',
    'callouts.lua',
    'callouts-docx.lua',
    'hl-lines.lua',
    'br.lua',
    'figure-captions.lua',
    'reference.docx',
]

PACKAGE_DIR = 'md2pdf'

# Ficheiros de versións anteriores que xa non forman parte do proxecto.
# Elimínanse durante unha actualización para evitar restos que suxiran soporte
# para motores ou pipelines retirados.
LEGACY_FILES = [
    'drake-jb-pandoc.typ',
    'mermaid.lua',
]


def get_install_dirs() -> tuple[Path, Path]:
    """Devolve (bin_dir, data_dir) segundo o SO."""
    if sys.platform == 'win32':
        base = Path(os.environ.get('LOCALAPPDATA',
                                    Path.home() / 'AppData' / 'Local'))
        install_dir = base / 'md2pdf'
        return install_dir, install_dir
    else:
        return (Path.home() / '.local' / 'bin',
                Path.home() / '.local' / 'share' / 'md2pdf')


def find_source_dir() -> Path:
    """Verifica que os ficheiros obrigatorios existen e devolve o directorio fonte."""
    script_dir = Path(__file__).resolve().parent

    missing = []
    if not (script_dir / PACKAGE_DIR).is_dir():
        missing.append(f'{PACKAGE_DIR}/')
    for f in DATA_FILES_REQUIRED:
        if not (script_dir / f).exists():
            missing.append(f)

    if missing:
        print(f'\n  ERRO: Non se atopan os seguintes ficheiros en {script_dir}:')
        for f in missing:
            print(f'    - {f}')
        print('\n  Asegúrate de executar o instalador desde o directorio')
        print('  onde están todos os ficheiros de md2pdf.')
        sys.exit(1)

    return script_dir


def _copy_package(source_dir: Path, data_dir: Path) -> None:
    """Copia o paquete md2pdf/ ao data_dir."""
    src = source_dir / PACKAGE_DIR
    dst = data_dir / PACKAGE_DIR
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f'  ✓ md2pdf/ → {dst}')


def _copy_data_files(source_dir: Path, data_dir: Path) -> None:
    """Copia os activos ao data_dir."""
    for f in DATA_FILES_REQUIRED:
        shutil.copy2(source_dir / f, data_dir / f)
        print(f'  ✓ {f}')
    for f in DATA_FILES_OPTIONAL:
        src = source_dir / f
        if src.exists():
            shutil.copy2(src, data_dir / f)
            print(f'  ✓ {f}')
        else:
            print(f'  ○ {f} (non atopado, saltado)')


def _make_linux_wrapper(bin_dir: Path, data_dir: Path) -> None:
    """Crea o script executábel ~/.local/bin/md2pdf."""
    dst = bin_dir / 'md2pdf'
    code = (
        'import sys\n'
        f'sys.path.insert(0, {str(data_dir)!r})\n'
        'from md2pdf.__main__ import main\n'
        "if __name__ == '__main__': main()\n"
    )
    wrapper = ('#!/bin/sh\n# md2pdf — xerado por install-md2pdf.py\nexec '
               + shlex.quote(sys.executable) + ' -c ' + shlex.quote(code) + ' "$@"\n')
    dst.write_text(wrapper, encoding='utf-8')
    dst.chmod(dst.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    print(f'  ✓ md2pdf → {dst}')


def _make_windows_wrapper(data_dir: Path) -> None:
    """Crea o wrapper .cmd para Windows."""
    runner = data_dir / 'md2pdf_runner.py'
    runner.write_text(
        '#!/usr/bin/env python3\n'
        'import sys\n'
        'from pathlib import Path\n'
        "sys.path.insert(0, str(Path(__file__).parent))\n"
        'from md2pdf.__main__ import main\n'
        "if __name__ == '__main__': main()\n",
        encoding='utf-8',
    )
    cmd = data_dir / 'md2pdf.cmd'
    cmd.write_text(f'@"{sys.executable}" "{runner}" %*\r\n', encoding='utf-8')
    print(f'  ✓ md2pdf.cmd → {cmd}')


def _check_path(bin_dir: Path) -> None:
    """Avisa se bin_dir non está no PATH."""
    if str(bin_dir) in os.environ.get('PATH', '').split(os.pathsep):
        return
    print()
    if sys.platform == 'win32':
        print(f'  ⚠ Engade este directorio ao PATH de Windows:')
        print(f'    {bin_dir}')
        print()
        print(f'  PowerShell (permanente):')
        print(f'    [Environment]::SetEnvironmentVariable("PATH", $env:PATH + ";{bin_dir}", "User")')
    else:
        print('  ⚠ Engade ~/.local/bin ao PATH (se non o tes xa):')
        shell = os.environ.get('SHELL', '')
        if 'fish' in shell:
            print('    fish_add_path ~/.local/bin')
        elif 'zsh' in shell:
            print('    echo \'export PATH="$HOME/.local/bin:$PATH"\' >> ~/.zshrc')
        else:
            print('    echo \'export PATH="$HOME/.local/bin:$PATH"\' >> ~/.bashrc')


def _remove_legacy_files(data_dir: Path) -> None:
    """Elimina activos obsoletos que puideron quedar dunha instalación previa."""
    for name in LEGACY_FILES:
        path = data_dir / name
        if path.exists():
            path.unlink()
            print(f'  ✓ Eliminado obsoleto: {name}')


def _check_dependencies(data_dir: Path) -> None:
    """Verifica dependencias externas."""
    print()
    print('  ── Dependencias ──')
    for cmd, required in [('pandoc', True), ('lualatex', False),
                          ('mmdc', False), ('d2', False), ('dot', False),
                          ('pdfcrop', False), ('pdfinfo', False)]:
        found = shutil.which(cmd) is not None
        mark = '✓' if found else ('✗ (necesario)' if required else '○ (opcional)')
        print(f'    {mark} {cmd}')
    print(f'    Python usado polo lanzador: {sys.executable}')
    for module, label in [('vl_convert', 'vl-convert-python (Vega-Lite)'),
                          ('yaml', 'PyYAML (diagrams no YAML)'),
                          ('pymupdf', 'PyMuPDF (validación visual PDF e lexibilidade)'),
                          ('PIL', 'Pillow (decodificación PNG)'),
                          ('pypdf', 'pypdf (validación PDF alternativa)')]:
        found = importlib.util.find_spec(module) is not None
        print(f'    {"✓" if found else "○ (opcional)"} {label}')
    if shutil.which('kpsewhich'):
        try:
            result = subprocess.run(['kpsewhich', 'xurl.sty'], capture_output=True,
                                    text=True, timeout=10)
            print(f'    {"✓" if result.returncode == 0 else "○ (opcional)"} xurl.sty')
        except (OSError, subprocess.TimeoutExpired):
            print('    ○ xurl.sty: non se puido comprobar')
    mark = '✓' if (data_dir / 'md2pdf.latex').exists() else '✗ (necesario para lualatex)'
    print(f'    {mark} md2pdf.latex')
    html_ok = all((data_dir / name).exists() for name in ('md2pdf.html', 'md2pdf.css', 'html.lua'))
    print(f'    {"✓" if html_ok else "✗ (necesario para HTML)"} activos HTML')


def install() -> None:
    source_dir = find_source_dir()
    bin_dir, data_dir = get_install_dirs()

    print()
    print('  ══════════════════════════════════════')
    print('  Instalación de md2pdf')
    print('  ══════════════════════════════════════')
    print()

    bin_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    _copy_package(source_dir, data_dir)
    _remove_legacy_files(data_dir)
    _copy_data_files(source_dir, data_dir)

    if sys.platform == 'win32':
        _make_windows_wrapper(data_dir)
        _check_path(data_dir)
    else:
        _make_linux_wrapper(bin_dir, data_dir)
        _check_path(bin_dir)

    _check_dependencies(data_dir)

    print()
    print('  ══════════════════════════════════════')
    print('  ✓ Instalación completa!')
    print()
    print('  Uso: md2pdf apuntes.md')
    print('       md2pdf apuntes.md -e lualatex')
    print('       md2pdf apuntes.md -e html')
    print('       md2pdf U1/ --ims U1-moodle.zip')
    print('       md2pdf --help')
    print()


def remove() -> None:
    bin_dir, data_dir = get_install_dirs()

    print()
    print('  Desinstalando md2pdf...')
    print()

    if sys.platform == 'win32':
        for f in ['md2pdf_runner.py', 'md2pdf.cmd']:
            p = data_dir / f
            if p.exists():
                p.unlink(); print(f'  ✓ Eliminado: {p}')
    else:
        p = bin_dir / 'md2pdf'
        if p.exists():
            p.unlink(); print(f'  ✓ Eliminado: {p}')

    pkg = data_dir / PACKAGE_DIR
    if pkg.exists():
        shutil.rmtree(pkg); print(f'  ✓ Eliminado: {pkg}')

    for f in DATA_FILES_REQUIRED + DATA_FILES_OPTIONAL + LEGACY_FILES:
        p = data_dir / f
        if p.exists():
            p.unlink(); print(f'  ✓ Eliminado: {p}')

    if data_dir.exists() and not any(data_dir.iterdir()):
        data_dir.rmdir(); print(f'  ✓ Eliminado directorio: {data_dir}')

    print()
    print('  ✓ Desinstalación completa.')
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description='Instalar/desinstalar md2pdf')
    parser.add_argument('--remove', action='store_true', help='Desinstalar md2pdf')
    args = parser.parse_args()
    remove() if args.remove else install()


if __name__ == '__main__':
    main()
