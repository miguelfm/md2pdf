"""
engines/lualatex.py — Comando Pandoc para o motor LuaLaTeX.

Inclúe:
  - build_lualatex_cmd(): construción do comando principal
  - Xeradores de snippets LaTeX temporais (portada, modo impresión, modo nocturno)
  - Utilidades LaTeX internas (_tex_escape, _temp_tex_file)
"""

import tempfile
from pathlib import Path

from ..config import (
    INSTALL_DIR,
    _detect_font,
    _pandoc_highlight_flag,
    _pandoc_template_dirs,
    _to_polyglossia,
)
from ..assets import (
    _find_callouts_filter,
    _find_hl_lines_filter,
    _find_br_filter,
    _find_lua_filter,
    _find_preamble,
    _find_small_table_filter,
)


# ── Utilidades LaTeX ──────────────────────────────────────────

def _tex_escape(text: str) -> str:
    """Escapa caracteres especiais LaTeX nun texto plano."""
    replacements = [
        ('\\', '\\textbackslash{}'),
        ('{',  '\\{'),
        ('}',  '\\}'),
        ('$',  '\\$'),
        ('&',  '\\&'),
        ('%',  '\\%'),
        ('#',  '\\#'),
        ('^',  '\\textasciicircum{}'),
        ('_',  '\\_'),
        ('~',  '\\textasciitilde{}'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _temp_tex_file(content: str) -> str:
    """Crea un ficheiro .tex temporal co contido dado. Devolve a ruta."""
    tmp = tempfile.NamedTemporaryFile(
        mode='w', suffix='.tex', encoding='utf-8', delete=False,
    )
    tmp.write(content)
    tmp.close()
    return tmp.name


# ── Xeradores de snippets LaTeX ───────────────────────────────

def _build_activity_label(activity: str, print_mode: bool,
                           night_mode: bool = False) -> str:
    """
    Xera LaTeX para o identificador da actividade (etiqueta centralizada).
    Úsase en dous sitios:
      - como -B sen titlepage: antes do TOC
      - como bloque raw no corpo: antes do primeiro ## en ambos modos
    """
    if print_mode:
        color = 'black'
    else:
        color = 'heading-section'
    act = _tex_escape(activity)
    return (
        '\\begin{center}\n'
        f'  \\sbox0{{\\LARGE\\bfseries\\sffamily {act}}}\n'
        '  {\\color{heading-section}\\rule{\\wd0}{0.4pt}}\\par\n'
        '  \\vspace{0.35em}\n'
        f'  {{\\LARGE\\bfseries\\sffamily\\color{{{color}}}{act}\\par}}\n'
        '  \\vspace{0.25em}\n'
        '  {\\color{heading-section}\\rule{\\wd0}{0.4pt}}\\par\n'
        '\\end{center}\n'
        '\\vspace{0.3em}\n'
    )


def _build_titlepage_snippet(meta: dict, print_mode: bool,
                              night_mode: bool = False,
                              front_author: bool = False) -> str:
    """
    Xera LaTeX para a portada (Opción D: tipografía pura, aliñado esquerda).
    """
    if print_mode:
        c_mod, c_title, c_sub, c_foot = (
            'black!45', 'black', 'black!75', 'black!50')
    elif night_mode:
        c_mod, c_title, c_sub, c_foot = (
            'night-fg', 'night-link', 'night-inline', 'night-fg')
    else:
        c_mod, c_title, c_sub, c_foot = (
            'black!45', 'blue!55!black', 'blue!40!black', 'black!50')

    mod    = _tex_escape(meta.get('module',   ''))
    subj   = _tex_escape(meta.get('subject',  ''))
    act    = _tex_escape(meta.get('activity', ''))
    school = _tex_escape(meta.get('school',   ''))
    auth   = _tex_escape(meta.get('author',   ''))
    crs    = _tex_escape(meta.get('course',   ''))
    inst       = school or auth
    extra_auth = auth if (school and front_author) else ''

    lines = ['\\begin{titlepage}\n', '\\raggedright\n',
             '\\vspace*{0.28\\textheight}\n']
    if mod:
        lines += [f'{{\\small\\sffamily\\color{{{c_mod}}}{mod}\\par}}\n',
                  '\\vspace{1.8em}\n']
    if subj:
        lines.append(
            f'{{\\Huge\\bfseries\\sffamily\\color{{{c_title}}}{subj}\\par}}\n')
    if act:
        lines += ['\\vspace{0.6em}\n',
                  f'{{\\Large\\sffamily\\color{{{c_sub}}}{act}\\par}}\n']
    lines.append('\\vfill\n')
    if inst or crs:
        lines.append('\\begin{flushright}\n')
        if inst:
            lines.append(f'{{\\normalsize\\sffamily {inst}\\par}}\n')
        if extra_auth:
            lines += ['\\vspace{0.2em}\n',
                      f'{{\\small\\sffamily\\color{{{c_foot}}}{extra_auth}\\par}}\n']
        if crs:
            lines += ['\\vspace{0.3em}\n',
                      f'{{\\small\\sffamily\\color{{{c_foot}}}{crs}\\par}}\n']
        lines.append('\\end{flushright}\n')
    lines += ['\\vspace{1.2cm}\n', '\\end{titlepage}\n']
    return ''.join(lines)


def _build_print_preamble_snippet() -> str:
    """
    Xera un ficheiro .tex temporal con overrides para modo impresión.
    Elimina fondos de cor en bloques de código, código en liña e callouts.
    Devolve a ruta ao ficheiro temporal.
    """
    snippet = r"""% ── Modo impresión: eliminar fondos e cores ──────────────
% Sobreescribe as definicións de md2pdf-preamble.tex
\definecolor{code-bg}{RGB}{255,255,255}
\definecolor{code-border}{RGB}{180,180,180}
\definecolor{inline-fg}{RGB}{0,0,0}
% Callouts: fondo branco, borde gris
\AtBeginDocument{%
  \tcbset{
    md2pdf-callout/.style={
      colback=white,
      colframe=black!55,
    }
  }%
}
"""
    return _temp_tex_file(snippet)


def _build_night_preamble_snippet() -> str:
    """
    Xera un ficheiro .tex temporal con overrides para modo nocturno.
    Paleta cálida sepia/laranxa: ideal para lectura nocturna sen fatiga visual.
      F5F0E8: crema cálido (fondo)      2C1A0E: marrón escuro (texto)
      EDE8DC: crema escuro (código)     D4C8B0: beige (borde código)
      7A4F2E: marrón medio (inline)     8B6347: laranxa apagado (ligazóns)
    Devolve a ruta ao ficheiro temporal.
    """
    snippet = (
        "% ── Modo nocturno: paleta cálida sen azul ────────────────────────────\n"
        "% F5F0E8: crema cálido (fondo xeral)     2C1A0E: marrón escuro (texto)\n"
        "% EDE8DC: crema escuro (fondo código)    D4C8B0: beige (borde código)\n"
        "% 7A4F2E: marrón medio (código en liña)  8B6347: laranxa apagado (ligazóns)\n"
        "\\definecolor{night-bg}{HTML}{F5F0E8}\n"
        "\\definecolor{night-fg}{HTML}{2C1A0E}\n"
        "\\definecolor{night-code-bg}{HTML}{EDE8DC}\n"
        "\\definecolor{night-code-border}{HTML}{D4C8B0}\n"
        "\\definecolor{night-inline}{HTML}{7A4F2E}\n"
        "\\definecolor{night-link}{HTML}{8B6347}\n"
        "\\definecolor{night-icon-alert}{HTML}{A0522D}\n"
        "\\definecolor{night-icon-muted}{HTML}{9E8872}\n"
        "% Fondo e cor global do documento\n"
        "\\pagecolor{night-bg}\n"
        "\\color{night-fg}\n"
        "\\AtBeginEnvironment{titlepage}{\\pagecolor{night-bg}\\color{night-fg}}\n"
        "\\AfterEndEnvironment{titlepage}{\\pagecolor{night-bg}\\color{night-fg}}\n"
        "% Sobreescribir cores de código do preámbulo\n"
        "\\definecolor{code-bg}{HTML}{EDE8DC}\n"
        "\\definecolor{code-border}{HTML}{D4C8B0}\n"
        "\\definecolor{inline-fg}{HTML}{7A4F2E}\n"
        "% Iconas: paleta cálida sen azul nin verde\n"
        "\\renewcommand{\\iconwarning}{{\\color{night-icon-alert}\\faExclamationTriangle}}\n"
        "\\renewcommand{\\icontip}{{\\color{night-link}\\faLightbulb}}\n"
        "\\renewcommand{\\iconinfo}{{\\color{night-link}\\faInfoCircle}}\n"
        "\\renewcommand{\\iconerror}{{\\color{night-icon-alert}\\faTimesCircle}}\n"
        "\\renewcommand{\\iconok}{{\\color{night-link}\\faCheckCircle}}\n"
        "\\renewcommand{\\iconbug}{{\\color{night-icon-alert}\\faBug}}\n"
        "\\renewcommand{\\iconglobe}{{\\color{night-link}\\faGlobe}}\n"
        "\\renewcommand{\\icondesktop}{{\\color{night-icon-muted}\\faDesktop}}\n"
        "\\renewcommand{\\iconplay}{{\\color{night-link}\\scalebox{0.9}{\\faIcon[regular]{play-circle}}}}\n"
        "\\renewcommand{\\iconstop}{{\\color{night-icon-alert}\\faStop}}\n"
        "\\renewcommand{\\iconnote}{{\\color{night-link}\\faEdit}}\n"
        "\\renewcommand{\\iconlock}{{\\color{night-icon-muted}\\faLock}}\n"
        "\\renewcommand{\\iconkey}{{\\color{night-inline}\\faKey}}\n"
        "\\renewcommand{\\iconfolder}{{\\color{night-inline}\\faFolderOpen}}\n"
        "\\renewcommand{\\iconrocket}{{\\color{night-link}\\faRocket}}\n"
        "\\renewcommand{\\icongear}{{\\color{night-icon-muted}\\faCog}}\n"
        "\\renewcommand{\\icontarget}{{\\color{night-link}\\scalebox{0.9}{\\faTasks}}}\n"
        "\\renewcommand{\\iconpc}{{\\color{night-icon-muted}\\faLaptop}}\n"
        "\\renewcommand{\\iconcheck}{{\\color{night-link}\\faCheck}}\n"
        "\\renewcommand{\\iconpencil}{{\\color{night-inline}\\scalebox{0.9}{\\faIcon{pencil-alt}}}}\n"
        "\\renewcommand{\\icontrophy}{{\\color{night-inline}\\scalebox{0.9}{\\faTrophy}}}\n"
        "\\renewcommand{\\iconban}{{\\color{night-icon-alert}\\faBan}}\n"
        "% Callouts, ligazóns e cores configurables ao comezo do documento\n"
        "\\AtBeginDocument{%\n"
        "  \\hypersetup{linkcolor=night-link,urlcolor=night-link,citecolor=night-link}%\n"
        "  \\tcbset{md2pdf-callout/.style={colback=night-code-bg,colframe=night-link}}%\n"
        "}\n"
        "% Sobrescribir cores configurables do preámbulo\n"
        "\\renewcommand{\\toctitlecolor}{night-link}\n"
        "\\renewcommand{\\titlebodycolor}{night-link}\n"
        "\\renewcommand{\\tablestripecolor}{night-code-bg}\n"
        "\\renewcommand{\\tablebasecolor}{night-bg}\n"
        "% Cabeceiras: tonos tostado ámbar sobre fondo sepia\n"
        "\\definecolor{heading-section}{HTML}{6B3A1F}\n"
        "\\definecolor{heading-subsection}{HTML}{8B5230}\n"
        "\\definecolor{heading-subsubsection}{HTML}{A86A42}\n"
    )
    return _temp_tex_file(snippet)


# ── Comando principal ─────────────────────────────────────────

def build_lualatex_cmd(
    tmp_path: str,
    output_path: str,
    template: Path,
    toc: bool,
    toc_depth: int,
    section_numbering: str,
    lang: str,
    papersize: str,
    highlight: str,
    listings: bool = False,
    titlepage: bool = False,
    callouts: bool = True,
    author: str | None = None,
    keywords: str | None = None,
    subject: str | None = None,
    print_mode: bool = False,
    **kwargs,
) -> list[str]:
    """Constrúe o comando Pandoc para LuaLaTeX con template propio."""
    night_mode: bool = kwargs.get('night_mode', False)
    decimal_align: bool = kwargs.get('decimal_align', True)

    # Se o template está nun directorio de Pandoc, usar só o nome base
    template_arg = str(template)
    for pandoc_dir in _pandoc_template_dirs():
        if template.parent == pandoc_dir:
            template_arg = template.stem
            break

    cmd = [
        'pandoc', tmp_path,
        '-o', output_path,
        '--pdf-engine=lualatex',
        f'--template={template_arg}',
        '-s',
        '--shift-heading-level-by=-1',
        '-V', f'lang={_to_polyglossia(lang)}',
        '-V', 'babel-otherlangs=english,spanish',
        '-V', f'papersize={papersize}',
        '-V', 'fontsize=13pt',
        '-V', f'mainfont={_detect_font("main")}',
        '-V', f'sansfont={_detect_font("sans")}',
        '-V', f'monofont={_detect_font("mono")}',
        '-V', r'mainfontoptions=Numbers=OldStyle,Ligatures=TeX',
        '-V', r'monofontoptions=Scale=0.85,Ligatures=NoCommon',
        '-V', 'geometry=top=12mm,bottom=14mm,left=20mm,right=20mm,footskip=7mm',
        '-V', 'colorlinks=true',
        '-V', 'linkcolor=' + ('black' if print_mode else 'blue!60!black'),
        '-V', 'urlcolor=' + ('black' if print_mode else 'blue!70!black'),
    ]

    # TOC: toc-own-page engade \clearpage despois da táboa de contidos.
    # toc-roman: calquera contido previo á primeira sección (TOC, prefacio…)
    # vai en numeración romana; a primeira sección resetea a 1 en árabe.
    # Non depende de titlepage: a portada está fóra da numeración de todas formas.
    if toc:
        cmd.extend(['-V', 'toc-own-page=true'])
        cmd.extend(['-V', 'toc-roman=true'])

    # Preámbulo personalizado
    preamble = _find_preamble()
    if preamble:
        cmd.extend(['-H', str(preamble)])

    # Snippets de modo (aplícanse despois do preámbulo para sobrescribir cores)
    if print_mode:
        cmd.extend(['-H', _build_print_preamble_snippet()])
    if night_mode:
        cmd.extend(['-H', _build_night_preamble_snippet()])

    if listings:
        cmd.append('--listings')
    else:
        cmd.extend([f'{_pandoc_highlight_flag()}={highlight}'])

    if toc:
        cmd.extend(['--toc', f'--toc-depth={toc_depth}'])

    if section_numbering:
        cmd.append('--number-sections')

    # Filtros Lua (orde importante: anchos → táboas pequenas → callouts → br → hl-lines)
    # Nota: Mermaid xa NON se procesa como filtro Lua aquí: faise no preprocesado
    # Python (md2pdf/mermaid.py) antes de chamar a Pandoc, para evitar problemas
    # de Chromium colgando cando se executa anidado dentro de Lua/Pandoc.
    lua_filter = _find_lua_filter()
    if lua_filter:
        cmd.extend(['--lua-filter', str(lua_filter)])
        if not decimal_align:
            # auto-table-widths.lua le a opción dos metadatos, onde tamén
            # a pode poñer o front matter
            cmd.extend(['--metadata', 'decimal-align=false'])

    small_table = _find_small_table_filter()
    if small_table:
        cmd.extend(['--lua-filter', str(small_table)])

    if callouts:
        callouts_filter = _find_callouts_filter()
        if callouts_filter:
            cmd.extend(['--lua-filter', str(callouts_filter)])

    br_filter = _find_br_filter()
    if br_filter:
        cmd.extend(['--lua-filter', str(br_filter)])

    hl_filter = _find_hl_lines_filter()
    if hl_filter:
        cmd.extend(['--lua-filter', str(hl_filter)])

    # Pés de figura. Vai ao final: traballa sobre a secuencia de bloques que
    # deixa o preprocesado de mermaid (raw + imaxe + raw + parágrafo do pé),
    # e os filtros anteriores non a tocan. Converte esa secuencia nunha figura
    # con \caption, que é o que activa o captionsetup de md2pdf-preamble.tex.
    figure_captions = INSTALL_DIR / 'figure-captions.lua'
    if figure_captions.exists():
        cmd.extend(['--lua-filter', str(figure_captions)])

    # Metadatos
    if author:
        cmd.extend(['--metadata', f'author={author}'])
    if keywords:
        cmd.extend(['--metadata', f'keywords={keywords}'])
    if subject:
        cmd.extend(['-V', f'subject={subject}'])

    return cmd
