"""
config.py — Constantes globais e utilidades de configuración.

Non ten dependencias internas; todos os demais módulos importan deste.
"""

import os
import subprocess
import sys
from pathlib import Path


# ── Motores e extensións ──────────────────────────────────────
ENGINES = ('lualatex', 'docx', 'html')
DEFAULT_ENGINE = 'lualatex'

TEMPLATE_NAMES = {
    'lualatex': 'md2pdf.latex',
    'docx':     None,   # DOCX usa reference.docx, non template
    'html':     'md2pdf.html',
}

OUTPUT_EXTENSIONS = {
    'lualatex': '.pdf',
    'docx':     '.docx',
    'html':     '.html',
}

# ── Directorio de instalación ────────────────────────────────
# Os activos (templates, filtros Lua, preamble.tex…) instálanse no directorio
# PAI do paquete md2pdf/.  Durante o desenvolvemento, o PAI é o directorio raíz
# do repositorio, onde tamén están os activos.
#   ~/.local/share/md2pdf/          ← INSTALL_DIR
#     md2pdf/                       ← este paquete
#       config.py                   ← __file__
#     md2pdf.latex
#     auto-table-widths.lua
#     …
INSTALL_DIR: Path = Path(__file__).resolve().parent.parent


# ── Fontes con fallback ───────────────────────────────────────
# Por defecto o corpo do texto é sans-serif (Source Sans 3) para máxima
# lexibilidade en pantalla e coherencia técnica con código e diagramas.
# O modo serif (Source Serif 4) está dispoñible coa opción --serif (ideal para papel).
FONT_CANDIDATES: dict[str, list[str]] = {
    'main':  ['Source Sans 3', 'Source Sans Pro', 'Source Sans'],
    'serif': ['Source Serif 4', 'Source Serif Pro', 'Source Serif'],
    'sans':  ['Source Sans 3', 'Source Sans Pro', 'Source Sans'],
    'mono':  ['Source Code Pro'],
}

_font_cache: dict[str, str] = {}


def _detect_font(role: str) -> str:
    """Detecta cal dos nomes candidatos de fonte está dispoñible no sistema."""
    if role in _font_cache:
        return _font_cache[role]

    for name in FONT_CANDIDATES.get(role, []):
        try:
            result = subprocess.run(
                ['luaotfload-tool', f'--find={name}'],
                capture_output=True, text=True, timeout=10,
            )
            if 'found!' in result.stdout.lower():
                _font_cache[role] = name
                return name
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    fallback = FONT_CANDIDATES.get(role, ['sans' if role != 'serif' else 'serif'])[0]
    _font_cache[role] = fallback
    return fallback


# ── Admonitions automáticos en cabeceiras ────────────────────
# Engade un emoji ao inicio das cabeceiras que coincidan co patrón.
HEADING_ADMONITIONS: dict[str, str] = {
    'Tarefa':    '🎯',
    'Exercicio': '✏️',
    'Reto':      '🏆',
    'Exemplo':   '▶️',
}


# ── Callouts ─────────────────────────────────────────────────
# Conversión de sintaxe GitHub/Obsidian "> [!TYPE]" á sintaxe Pandoc ":::type"
CALLOUT_BLOCKQUOTE_TYPES: dict[str, str] = {
    'NOTE':     'note',
    'NOTA':     'note',
    'TIP':      'tip',
    'CONSELLO': 'consello',
    'WARNING':  'warning',
    'ATENCIÓN': 'warning',
    'ATENCION': 'warning',
    'DANGER':   'danger',
    'PERIGO':   'perigo',
    'INFO':     'info',
}

# Emojis ao inicio dun blockquote que indican un callout.
# A orde importa: emojis con variante (️) antes da versión simple.
CALLOUT_EMOJI_MAP: list[tuple[str, str]] = [
    ('⚠️',  'warning'),
    ('⚠',   'warning'),
    ('💡',  'tip'),
    ('📘',  'info'),
    ('📝',  'note'),
    ('⛔',  'danger'),
]


# ── Polyglossia ───────────────────────────────────────────────
# polyglossia usa nomes completos, non códigos ISO 639-1
_POLYGLOSSIA_LANG: dict[str, str] = {
    'gl': 'galician',
    'es': 'spanish',
    'en': 'english',
    'pt': 'portuguese',
    'fr': 'french',
    'de': 'german',
    'it': 'italian',
    'ca': 'catalan',
    'eu': 'basque',
}


def _to_polyglossia(lang: str) -> str:
    """Converte un código ISO 639-1 ao nome de lingua para polyglossia."""
    return _POLYGLOSSIA_LANG.get(lang.lower(), lang)


# ── Pandoc ────────────────────────────────────────────────────

def _pandoc_highlight_flag() -> str:
    """Devolve o flag para o estilo de resaltado de Pandoc."""
    return '--highlight-style'


def _pandoc_template_dirs() -> list[Path]:
    """Devolve os directorios de templates de Pandoc segundo a plataforma."""
    dirs: list[Path] = []
    if sys.platform == 'win32':
        appdata = os.environ.get('APPDATA', '')
        if appdata:
            dirs.append(Path(appdata) / 'pandoc' / 'templates')
    else:
        dirs.append(Path.home() / '.local' / 'share' / 'pandoc' / 'templates')
        dirs.append(Path.home() / '.pandoc' / 'templates')
    return dirs
