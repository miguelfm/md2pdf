"""
assets.py — Busca de ficheiros de activos (templates, filtros Lua, temas…)
e verificación de dependencias externas.

Todos os activos búscanse en dous lugares por orde:
  1. INSTALL_DIR  (~/.local/share/md2pdf/ en Linux)
  2. Directorio de traballo actual (CWD) — útil en desenvolvemento
"""

import shutil
import sys
from pathlib import Path

from .config import INSTALL_DIR, TEMPLATE_NAMES, _pandoc_template_dirs


# ── Utilidade interna ─────────────────────────────────────────

def _find_asset(name: str) -> Path | None:
    """Busca un ficheiro de activo en INSTALL_DIR e no CWD."""
    for directory in (INSTALL_DIR, Path.cwd()):
        candidate = directory / name
        if candidate.exists():
            return candidate
    return None


# ── Templates ─────────────────────────────────────────────────

def find_template(engine: str) -> Path | None:
    """
    Busca o template Pandoc para o motor indicado.

    Orde de busca:
      1. INSTALL_DIR
      2. CWD
      3. Directorios de templates de Pandoc (~/.local/share/pandoc/templates…)
    """
    template_name = TEMPLATE_NAMES[engine]
    if template_name is None:
        return None     # DOCX non usa template

    found = _find_asset(template_name)
    if found:
        return found

    for d in _pandoc_template_dirs():
        candidate = d / template_name
        if candidate.exists():
            return candidate

    return None


# ── Ficheiros de activos individuais ─────────────────────────

def _find_preamble() -> Path | None:
    """Busca o ficheiro md2pdf-preamble.tex de personalizacións LaTeX."""
    return _find_asset('md2pdf-preamble.tex')


def _find_highlight_theme() -> Path | None:
    """Busca o tema de resaltado drake-jb.theme."""
    return _find_asset('drake-jb.theme')


def _find_lua_filter() -> Path | None:
    """Busca o filtro Lua para auto-dimensionar columnas de táboas."""
    return _find_asset('auto-table-widths.lua')


def _find_small_table_filter() -> Path | None:
    """Busca o filtro Lua para converter táboas pequenas a tabular."""
    return _find_asset('small-table.lua')


def _find_callouts_filter() -> Path | None:
    """Busca o filtro Lua para callouts (tcolorbox) en PDF."""
    return _find_asset('callouts.lua')


def _find_callouts_docx_filter() -> Path | None:
    """Busca o filtro Lua para callouts en DOCX."""
    return _find_asset('callouts-docx.lua')


def _find_hl_lines_filter() -> Path | None:
    """Busca o filtro Lua para resaltado de liñas (hl-lines.lua)."""
    return _find_asset('hl-lines.lua')


def _find_br_filter() -> Path | None:
    """Busca o filtro Lua para converter <br> a \\newline{} en LaTeX (br.lua)."""
    return _find_asset('br.lua')



def _find_html_css() -> Path | None:
    """Busca a folla de estilo principal da saída HTML."""
    return _find_asset('md2pdf.css')


def _find_html_filter() -> Path | None:
    """Busca o filtro Lua de semántica específica da saída HTML."""
    return _find_asset('html.lua')

def _find_docx_reference() -> Path | None:
    """Busca o ficheiro reference.docx para estilos DOCX."""
    return _find_asset('reference.docx')


# ── Resaltado ────────────────────────────────────────────────

def resolve_highlight(highlight_arg: str) -> str:
    """
    Resolve o estilo de resaltado:
      - 'auto' (defecto): busca drake-jb.theme; se non existe usa pygments
      - calquera outro valor: respéctase tal cal
    """
    if highlight_arg != 'auto':
        return highlight_arg
    theme = _find_highlight_theme()
    return str(theme) if theme else 'pygments'


# ── Dependencias externas ─────────────────────────────────────

def check_dependencies(engine: str) -> None:
    """Verifica que pandoc e o motor indicado están instalados no sistema."""
    required = ['pandoc']
    if engine == 'lualatex':
        required.append('lualatex')

    missing = [cmd for cmd in required if shutil.which(cmd) is None]
    if not missing:
        return

    print(f"\n  ERRO: Non se atopan: {', '.join(missing)}", file=sys.stderr)
    print('', file=sys.stderr)
    if engine == 'lualatex':
        print('  Instalación (LuaLaTeX):', file=sys.stderr)
        print('    Arch:    sudo pacman -S pandoc texlive texlive-latexextra',
              file=sys.stderr)
        print('    Windows: Instalar MiKTeX + Pandoc', file=sys.stderr)
    else:
        label = 'HTML' if engine == 'html' else 'DOCX'
        print(f'  Instalación ({label}):', file=sys.stderr)
        print('    Arch:    sudo pacman -S pandoc', file=sys.stderr)
        print('    Windows: winget install JohnMacFarlane.Pandoc', file=sys.stderr)
    sys.exit(1)
