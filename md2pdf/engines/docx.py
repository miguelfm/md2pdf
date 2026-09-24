"""
engines/docx.py — Comando Pandoc para saída DOCX (Word).
"""

from pathlib import Path

from ..assets import (
    _find_callouts_docx_filter,
    _find_docx_reference,
    _find_lua_filter,
)


def build_docx_cmd(
    tmp_path: str,
    output_path: str,
    toc: bool,
    toc_depth: int,
    section_numbering: str,
    lang: str,
    callouts: bool = True,
    author: str | None = None,
    keywords: str | None = None,
    **kwargs,
) -> list[str]:
    """Constrúe o comando Pandoc para saída DOCX (Word)."""
    cmd = [
        'pandoc', tmp_path,
        '-o', output_path,
        '-s',
        '--shift-heading-level-by=-1',
    ]

    if toc:
        cmd.extend(['--toc', f'--toc-depth={toc_depth}'])
    if section_numbering:
        cmd.append('--number-sections')

    ref_doc = _find_docx_reference()
    if ref_doc:
        cmd.extend(['--reference-doc', str(ref_doc)])

    if callouts:
        callouts_docx = _find_callouts_docx_filter()
        if callouts_docx:
            cmd.extend(['--lua-filter', str(callouts_docx)])

    lua_filter = _find_lua_filter()
    if lua_filter:
        cmd.extend(['--lua-filter', str(lua_filter)])

    if author:
        cmd.extend(['--metadata', f'author={author}'])

    return cmd
