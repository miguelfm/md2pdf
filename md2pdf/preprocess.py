"""
preprocess.py — Preprocesamento do Markdown antes de pasalo a Pandoc.

Operacións:
  - Eliminar YAML front matter (xa extraído por metadata.py)
  - Converter callouts "> [!TYPE]" e emojis á sintaxe ":::type" de Pandoc
  - Eliminar separadores --- entre seccións
  - Eliminar numeración manual das cabeceiras
  - Engadir emojis automáticos en cabeceiras (Tarefa, Exercicio…)
  - Substituír emojis unicode por comandos LaTeX vectoriais (só lualatex)
  - Garantir liña baleira tras aperturas de callout
"""

import re
import sys
import uuid
from pathlib import Path

from .lint import linguaxe_do_bloque
from .config import (
    CALLOUT_BLOCKQUOTE_TYPES,
    CALLOUT_EMOJI_MAP,
    HEADING_ADMONITIONS,
)


# ── Mapeamentos de emojis ─────────────────────────────────────

# Emojis → comandos LaTeX fontawesome5 (só para lualatex)
_EMOJI_TO_LATEX: dict[str, str] = {
    '⚠️':  r'\iconwarning{}',
    '⚠':   r'\iconwarning{}',
    '💡':  r'\icontip{}',
    '📘':  r'\iconinfo{}',
    '❌':  r'\iconerror{}',
    '✅':  r'\iconok{}',
    '✓':   r'\iconcheck{}',
    '🔴':  r'\iconerror{}',
    '🐛':  r'\iconbug{}',
    '🖥️':  r'\icondesktop{}',
    '🖥':   r'\icondesktop{}',
    '🌐':  r'\iconglobe{}',
    '▶️':  r'\iconplay{}',
    '⏹':   r'\iconstop{}',
    '📝':  r'\iconnote{}',
    '🔒':  r'\iconlock{}',
    '🔑':  r'\iconkey{}',
    '📂':  r'\iconfolder{}',
    '📁':  r'\iconfolder{}',
    '🚀':  r'\iconrocket{}',
    '⚙️':  r'\icongear{}',
    '⚙':   r'\icongear{}',
    '🎯':  r'\icontarget{}',
    '💻':  r'\iconpc{}',
    '✏️':  r'\iconpencil{}',
    '✏':   r'\iconpencil{}',
    '🏆':  r'\icontrophy{}',
    '⛔':  r'\iconban{}',
}
# Ordenados por lonxitude descendente para evitar substitucións parciais
_EMOJI_SORTED = sorted(_EMOJI_TO_LATEX.keys(), key=len, reverse=True)

# Emojis → texto plano para dentro de bloques de código (verbatim)
_EMOJI_TO_TEXT: dict[str, str] = {
    '⚠️': '[!]', '⚠': '[!]',
    '💡': '(i)', '📘': '(i)',
    '❌': '[X]', '✅': '[OK]', '✓': '[OK]',
    '🔴': '(!)', '🐛': '[bug]',
    '🖥️': '[PC]', '🖥': '[PC]',
    '🌐': '[Web]', '▶️': '[>]', '⏹': '[stop]',
    '📝': '[nota]', '🔒': '[lock]', '🔑': '[key]',
    '📂': '[dir]', '📁': '[dir]',
    '🚀': '[!]', '⚙️': '[cfg]', '⚙': '[cfg]',
    '🎯': '[obj]', '💻': '[PC]',
    '✏️': '[ex]', '✏': '[ex]',
    '🏆': '[reto]',
    '⛔': '[NO]',
}
_EMOJI_TEXT_SORTED = sorted(_EMOJI_TO_TEXT.keys(), key=len, reverse=True)
_EMOJI_TEXT_PATTERN = '|'.join(re.escape(e) for e in _EMOJI_TEXT_SORTED)


# ── Funcións privadas ─────────────────────────────────────────

def _strip_front_matter(text: str) -> str:
    """
    Elimina o bloque YAML front matter do inicio do ficheiro Markdown.
    O front matter xa foi procesado por metadata.py; se non se elimina
    aquí, as liñas YAML aparecerían como texto plano no PDF.
    """
    m = re.match(r'(?s)^---\s*\n.*?\n(?:---|\.\.\.)\s*\n', text)
    return text[m.end():] if m else text


def _convert_callout_blockquotes(lines: list[str]) -> list[str]:
    """
    Converte bloques de callout á sintaxe de divs Pandoc (:::type).

    Soporta dous formatos de entrada:

    1. Sintaxe GitHub/Obsidian:
        > [!NOTE]
        > Texto do callout.

    2. Blockquotes con emoji ao inicio:
        > 💡 **Recomendación:** Texto.

    Saída (para ambos):
        ::: tip

        Texto do callout.
        :::
    """
    result   = []
    i        = 0
    re_start = re.compile(r'^>\s*\[!([\w\u00C0-\u024F-]+)\](?:\s+(.*?))?\s*$')

    def _detect_emoji_callout(line: str) -> tuple[str | None, str | None]:
        content = line.lstrip('> ').lstrip()
        for emoji, callout_type in CALLOUT_EMOJI_MAP:
            if content.startswith(emoji):
                return callout_type, content[len(emoji):].lstrip()
        return None, None

    while i < len(lines):
        line = lines[i]

        # Formato 1: > [!TYPE] ou > [!TYPE] Título opcional
        m = re_start.match(line)
        if m:
            div_cls = CALLOUT_BLOCKQUOTE_TYPES.get(m.group(1).upper())
            if div_cls:
                opt_title = m.group(2)
                content = []
                if opt_title and opt_title.strip():
                    content.extend([f'**{opt_title.strip()}**', ''])
                i += 1
                while i < len(lines) and lines[i].startswith('>'):
                    content.append(lines[i][1:].lstrip())
                    i += 1
                result.extend([f'::: {div_cls}', '', *content, ':::', ''])
                continue

        # Formato 2: > 💡 **Texto**
        if line.startswith('>'):
            callout_type, first_text = _detect_emoji_callout(line)
            if callout_type:
                content = []
                if first_text:
                    content.append(first_text)
                i += 1
                while i < len(lines) and lines[i].startswith('>'):
                    content.append(lines[i][1:].lstrip())
                    i += 1
                result.extend([f'::: {callout_type}', '', *content, ':::', ''])
                continue

        result.append(line)
        i += 1

    return result


# ── API pública ───────────────────────────────────────────────

def preprocess_md(text: str, engine: str = 'lualatex',
                  callouts: bool = True) -> str:
    """Protexe as vallas gráficas e de exemplos antes das transformacións."""
    from .diagrams.processor import fenced_blocks
    protected = {}
    for start, stop, info, body in reversed(list(fenced_blocks(text))):
        opener = text[start:].splitlines()[0].lstrip()
        if (opener.startswith(('````', '~~~')) or
                re.search(r'(?<![\w-])(?:mermaid|d2|dot|graphviz|vega-lite|vegalite)(?![\w-])', info)):
            token = 'MD2PDFPROTECTED' + uuid.uuid4().hex
            protected[token] = text[start:stop].rstrip('\r\n')
            text = text[:start] + token + '\n' + text[stop:]
    text = _preprocess_md(text, engine, callouts)
    for token, original in protected.items():
        text = text.replace(token, original)
    return text


def _preprocess_md(text: str, engine: str = 'lualatex',
                  callouts: bool = True) -> str:
    """
    Limpa o Markdown antes de pasalo a Pandoc.

    Xestiona calquera tipo de índice:
      - Manual (## Índice + lista de ligazóns)
      - Automático ([TOC] de Typora)
      - Sen índice

    Tamén:
      - Elimina o YAML front matter
      - Converte callouts "> [!TYPE]" á sintaxe ":::type" de Pandoc
      - Elimina separadores --- entre seccións
      - Elimina numeración manual das cabeceiras
      - Engade emojis automáticos en cabeceiras (Tarefa, Exercicio…)
      - Substitúe emojis por comandos LaTeX vectoriais (só lualatex)
      - NON toca o contido dentro de bloques de código
    """
    text = _strip_front_matter(text)

    # Normalizar fenced divs con atributos directos tipo '::: task-box{...}' a '::: {.task-box ...}'
    text = re.sub(r'^:::\s+([\w-]+)\s*\{([^}]+)\}', r'::: {.\1 \2}', text, flags=re.MULTILINE)

    if callouts:
        text = '\n'.join(_convert_callout_blockquotes(text.splitlines()))

    lines = text.splitlines()
    result: list[str] = []
    in_code = False
    in_toc  = False

    re_numbered_heading = re.compile(r'^(#+)\s+\d+(?:\.\d+)*\.?\s+(.*)')
    re_toc_numbered     = re.compile(r'^\s*\d+\.\s*\[.*\]\(#')
    re_toc_bulleted     = re.compile(r'^\s*[-*+]\s*\[.*\]\(#')

    emoji_pattern      = '|'.join(re.escape(e) for e in _EMOJI_SORTED)

    for line in lines:
        stripped = line.strip()

        # ── Bloques de código ──────────────────────────────────
        if stripped.startswith('```'):
            if not in_code:
                marker    = re.match(r'`+', stripped).group(0)
                lang_part = stripped[len(marker):].strip()
                if not linguaxe_do_bloque(lang_part):
                    indent = line[: len(line) - len(line.lstrip())]
                    if lang_part.startswith('{'):
                        # Bloque con atributos pero sen clase: engádese .text
                        # e consérvanse o identificador e o resto.
                        line = f"{indent}{marker}{{.text {lang_part[1:].lstrip()}"
                    else:
                        line = f"{indent}{marker}text"
                    print('  ⚠  Auto-fixado: bloque de código sen linguaxe → text',
                          file=sys.stderr)
            in_code = not in_code
            result.append(line)
            continue

        if in_code:
            if engine == 'lualatex' and _EMOJI_TEXT_PATTERN:
                line = re.sub(
                    f'({_EMOJI_TEXT_PATTERN})',
                    lambda m: _EMOJI_TO_TEXT[m.group(0)],
                    line,
                )
            result.append(line)
            continue

        # ── TOC manual ────────────────────────────────────────
        if stripped == '[TOC]':
            continue

        if stripped in ('## Índice', '## Índice de contidos',
                        '## Índice de Contidos', '## ÍNDICE'):
            in_toc = True
            continue

        if in_toc:
            if re_toc_numbered.match(line) or re_toc_bulleted.match(line):
                continue
            if stripped == '':
                continue
            if stripped == '---':
                in_toc = False
                continue
            in_toc = False

        # ── Separadores ───────────────────────────────────────
        if stripped == '---':
            continue

        # ── Numeración manual de cabeceiras ───────────────────
        m = re_numbered_heading.match(line)
        if m:
            line = f'{m.group(1)} {m.group(2)}'

        # ── Emojis automáticos en cabeceiras ──────────────────
        heading_match = re.match(r'^(#+\s+)(.*)', line)
        if heading_match and HEADING_ADMONITIONS:
            hashes       = heading_match.group(1)
            heading_text = heading_match.group(2)
            stripped_txt = re.sub(r'^[*_]+', '', heading_text)
            prefix       = stripped_txt[:5]
            has_emoji    = any(e in prefix for e in HEADING_ADMONITIONS.values())
            if not has_emoji:
                for pattern, emoji in HEADING_ADMONITIONS.items():
                    if pattern in heading_text:
                        line = f'{hashes}{emoji} {heading_text}'
                        break

        # ── Emojis → comandos LaTeX (só lualatex) ─────────────
        if engine == 'lualatex' and emoji_pattern:
            if heading_match:
                # En cabeceiras, protexer con \texorpdfstring para que
                # hyperref use cadea baleira nos bookmarks PDF en lugar
                # de tentar expandir comandos fontawesome non expandibles
                def _emoji_replace(m: re.Match) -> str:
                    cmd = _EMOJI_TO_LATEX[m.group(0)]
                    return f'`\\texorpdfstring{{{cmd}}}{{}}`{{=latex}}'
            else:
                def _emoji_replace(m: re.Match) -> str:
                    cmd = _EMOJI_TO_LATEX[m.group(0)]
                    return f'`{cmd}`{{=latex}}'
            line = re.sub(f'({emoji_pattern})', _emoji_replace, line)

        result.append(line)

    # Post-pass: garantir liña baleira tras aperturas de callout :::tipo
    # escritas directamente no .md (non xeradas polo conversor)
    re_callout_open = re.compile(r'^:::\s*(?:\{[ \t]*[.#]?[\w-]+|[\w-]+)')
    final: list[str] = []
    for idx, ln in enumerate(result):
        final.append(ln)
        if re_callout_open.match(ln.strip()):
            next_ln = result[idx + 1] if idx + 1 < len(result) else ''
            if next_ln.strip() != '':
                final.append('')

    return '\n'.join(final) + '\n'
