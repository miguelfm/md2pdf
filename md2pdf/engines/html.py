"""engines/html.py — Comando Pandoc para saída HTML5 autocontida."""

from pathlib import Path

from ..assets import (
    _find_html_css,
    _find_html_filter,
    _find_term_pairs_filter,
    _find_terminal_blocks_filter,
)
from ..config import INSTALL_DIR


def build_html_cmd(
    tmp_path: str,
    output_path: str,
    template: Path,
    toc: bool,
    toc_depth: int,
    section_numbering: str,
    lang: str,
    highlight: str,
    callouts: bool = True,
    author: str | None = None,
    keywords: str | None = None,
    subject: str | None = None,
    title: str | None = None,
    activity: str | None = None,
    print_mode: bool = False,
    night_mode: bool = False,
    plain_mode: bool = False,
    serif_mode: bool = False,
    source_dir: str | None = None,
    **kwargs,
) -> list[str]:
    """Constrúe o comando Pandoc para un HTML5 autocontido e responsive."""
    cmd = [
        'pandoc', tmp_path,
        '-o', output_path,
        '--to=html5',
        '--standalone',
        '--embed-resources',
        '--section-divs',
        '--shift-heading-level-by=-1',
        '--mathml',
        f'--template={template}',
        '-V', f'lang={lang}',
        f'--highlight-style={highlight}',
    ]

    css = _find_html_css()
    if css:
        cmd.extend(['--css', str(css)])

    term_pairs = _find_term_pairs_filter()
    if term_pairs:
        cmd.extend(['--lua-filter', str(term_pairs)])

    # Primeiro normalizamos os pés de figura herdados (imaxe seguida de
    # ``*Figura N. ...*``) á representación Figure de Pandoc. O filtro HTML
    # engade despois a numeración e resolve as referencias internas.
    figure_captions = INSTALL_DIR / 'figure-captions.lua'
    if figure_captions.exists():
        cmd.extend(['--lua-filter', str(figure_captions)])

    terminal_blocks: bool = kwargs.get('terminal_blocks', True)
    terminal_filter = _find_terminal_blocks_filter()
    if terminal_filter:
        cmd.extend(['--lua-filter', str(terminal_filter)])
        if not terminal_blocks:
            cmd.extend(['--metadata', 'terminal-blocks=false'])

    html_filter = _find_html_filter()
    if html_filter:
        cmd.extend(['--lua-filter', str(html_filter)])

    if source_dir:
        cmd.append(f'--resource-path={source_dir}')

    if toc:
        cmd.extend(['--toc', f'--toc-depth={toc_depth}'])
    if section_numbering:
        cmd.append('--number-sections')

    # Variables de presentación usadas polo template/CSS.
    if print_mode:
        cmd.extend(['-V', 'print-mode=true'])
    if night_mode:
        cmd.extend(['-V', 'night-mode=true'])
    if plain_mode:
        cmd.extend(['-V', 'plain-mode=true'])
    if serif_mode:
        cmd.extend(['-V', 'serif-mode=true'])

    # O filtro HTML consulta esta marca para respectar --no-callouts.
    cmd.extend(['--metadata', f'md2pdf-callouts={str(callouts).lower()}'])

    # Metadatos extraídos do front matter e metadata.yml.
    for key, value in (
        ('title', title),
        ('author', author),
        ('keywords', keywords),
        ('subject', subject),
        ('activity', activity),
    ):
        if value:
            cmd.extend(['--metadata', f'{key}={value}'])

    return cmd
