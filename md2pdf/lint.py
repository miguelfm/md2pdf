"""
lint.py — Validación previa do Markdown antes de procesalo.

Detecta problemas estruturais que causarían erros en Pandoc/LaTeX:
  - Marca BOM ao inicio do ficheiro
  - Front matter YAML sen pechar, ou que chega ata un --- do corpo
  - Bloques de código sen linguaxe especificada
  - Bloques de código non pechados
  - Callouts :::tipo sen liña baleira a continuación
  - Callouts non pechados
  - ::: de peche sen callout aberto
  - Múltiples cabeceiras de nivel 1 (#)

O front matter pechado non xera aviso, porque o material leva sempre
metadatos. As súas liñas quedan fóra das comprobacións do corpo.

Os bloques de código seguen a regra de CommonMark: o peche usa o mesmo
carácter ca a apertura, polo menos a mesma lonxitude e ningún texto detrás.
Así, un bloque de catro acentos graves pode conter outro de tres.
"""

import re

RE_FM_OPEN = re.compile(r'---[ \t]*\r?\n')
RE_FM_BLOCK = re.compile(
    r'(?s)---[ \t]*\r?\n(?:.*?\r?\n)?(?:---|\.\.\.)[ \t]*(?:\r?\n|\Z)'
)
RE_FENCE = re.compile(r'^(`{3,}|~{3,})(.*)$')
# Primeira clase dun bloque de atributos: {.java}, {#id .java}, { .java }
RE_CLASE = re.compile(r'(?:^\{|\s)\.([\w+-]+)(?=[\s}])')
RE_CALLOUT_OPEN = re.compile(r'^:::\s*(?:\{[ \t]*[.#]?([\w-]+)|([\w-]+))')
RE_CALLOUT_CLOSE = re.compile(r'^:::$')
RE_H1 = re.compile(r'^#\s+\S')
# Liñas que non se esperan dentro dos metadatos. Un «# » só pode ser un
# comentario YAML, así que non se conta.
RE_MARKDOWN_IN_FM = re.compile(r'^(?:#{2,6}\s+\S|`{3,}|~{3,}|:::)')


def linguaxe_do_bloque(info: str) -> str:
    """
    Linguaxe dun bloque de código a partir do seu texto de información.

    Pandoc admite dúas formas: a curta, ```java, e a de atributos,
    ```{.java #id caption="..."}, na que a linguaxe é a primeira clase.
    Devolve a cadea baleira se non hai linguaxe en ningunha das dúas.
    """
    info = info.strip()
    if not info:
        return ''
    if info.startswith('{'):
        m = RE_CLASE.search(info)
        return m.group(1) if m else ''
    return re.split(r'[\s{]', info)[0]


def lint_md(text: str) -> list[str]:
    """
    Valida un ficheiro Markdown e devolve unha lista de avisos.
    Non modifica o texto.
    """
    issues: list[str] = []

    # ── BOM ───────────────────────────────────────────────────
    if text.startswith('\ufeff'):
        issues.append(
            'liña 1: o ficheiro empeza cunha marca BOM '
            '(gardalo en UTF-8 sen BOM; o front matter pode non recoñecerse)'
        )
        text = text[1:]

    lines = text.splitlines()

    # ── YAML front matter ─────────────────────────────────────
    fm_lines = 0
    m_fm = RE_FM_BLOCK.match(text)
    if m_fm:
        fm_lines = len(m_fm.group(0).splitlines())
        body_like = [
            n for n, fm_line in enumerate(lines[1:fm_lines - 1], 2)
            if RE_MARKDOWN_IN_FM.match(fm_line.strip())
        ]
        if body_like:
            issues.append(
                f'liñas 1-{fm_lines}: o front matter contén liñas de Markdown '
                f'(a primeira na liña {body_like[0]}); probablemente falta o '
                f'peche e o bloque chega ata un --- do corpo'
            )
    elif RE_FM_OPEN.match(text):
        issues.append(
            'liña 1: front matter YAML sen pechar '
            '(falta a liña --- ou ... de peche)'
        )

    fence_char = ''
    fence_len = 0
    code_open_line: int | None = None
    callout_stack: list[int] = []    # liñas onde abriu cada callout
    h1_lines: list[int] = []

    for i, line in enumerate(lines, 1):
        if i <= fm_lines:
            continue

        stripped = line.strip()
        m_fence = RE_FENCE.match(stripped)

        # ── Bloques de código ──────────────────────────────────
        if fence_char:
            if (m_fence
                    and m_fence.group(1)[0] == fence_char
                    and len(m_fence.group(1)) >= fence_len
                    and not m_fence.group(2).strip()):
                fence_char = ''
                fence_len = 0
                code_open_line = None
            continue

        if m_fence:
            marker, info = m_fence.group(1), m_fence.group(2).strip()
            # Con acentos graves, o texto de información non pode conter
            # outro acento grave: esa liña non abre un bloque
            if not (marker[0] == '`' and '`' in info):
                if not linguaxe_do_bloque(info):
                    issues.append(
                        f'liña {i}: bloque de código sen linguaxe '
                        f'(usar `text` para saídas planas)'
                    )
                fence_char = marker[0]
                fence_len = len(marker)
                code_open_line = i
                continue

        # ── Callouts ───────────────────────────────────────────
        m_open = RE_CALLOUT_OPEN.match(stripped)
        if m_open:
            callout_stack.append(i)
            next_line = lines[i] if i < len(lines) else ''
            callout_type = m_open.group(1) or m_open.group(2)
            if next_line.strip() != '':
                issues.append(
                    f'liña {i}: callout `:::{callout_type}` sen liña '
                    f'baleira a continuación '
                    f'(LaTeX fallará con «Extra }}, or forgotten $»)'
                )
            continue

        if RE_CALLOUT_CLOSE.match(stripped):
            if callout_stack:
                callout_stack.pop()
            else:
                issues.append(
                    f'liña {i}: `:::` de peche sen callout aberto '
                    f'correspondente'
                )
            continue

        # ── Cabeceiras de nivel 1 ──────────────────────────────
        if RE_H1.match(line):
            h1_lines.append(i)

    # ── Comprobacións ao final do ficheiro ────────────────────
    if fence_char and code_open_line is not None:
        issues.append(
            f'liña {code_open_line}: bloque de código aberto pero nunca '
            f'pechado (falta {fence_char * fence_len} de peche)'
        )

    for open_line in callout_stack:
        issues.append(
            f'liña {open_line}: callout aberto pero nunca pechado '
            f'(falta ::: de peche)'
        )

    if len(h1_lines) > 1:
        issues.append(
            f'múltiples cabeceiras de nivel 1 (#) nas liñas: '
            f'{", ".join(map(str, h1_lines))} '
            f'(só debe haber un # Título ao inicio)'
        )

    return issues
