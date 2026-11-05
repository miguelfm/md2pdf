"""
engines/lualatex.py — Comando Pandoc para o motor LuaLaTeX.

Inclúe:
  - build_lualatex_cmd(): construción do comando principal
  - Xeradores de snippets LaTeX temporais (portada, modo impresión, modo nocturno)
  - Utilidades LaTeX internas (_tex_escape, _temp_tex_file)
"""

import re
import sys
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
    _find_compact_code_filter,
    _find_keep_code_filter,
    _find_attach_filter,
    _find_keep_with_next_filter,
    _find_hl_lines_filter,
    _find_javadoc_syntax,
    _find_terminal_blocks_filter,
    _find_br_filter,
    _find_lua_filter,
    _find_preamble,
    _find_small_table_filter,
    _find_term_pairs_filter,
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
        ('\N{NO-BREAK SPACE}', '~'),
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
    Insírese como bloque raw no corpo, antes do primeiro ##, con portada
    ou sen ela.
    """
    if print_mode:
        color = 'black'
    else:
        color = 'heading-section'
    act = _tex_escape(activity)
    return (
        '\\begin{center}\n'
        f'  \\sbox0{{\\LARGE\\bfseries\\sffamily {act}}}\n'
        # Unha etiqueta que non cabe nunha liña pártese ao compoñela;
        # as raias quedan no ancho da liña, non no da etiqueta enteira.
        '  \\ifdim\\wd0>\\linewidth\\sbox0{\\hbox to\\linewidth{}}\\fi\n'
        '  {\\color{heading-section}\\rule{\\wd0}{0.4pt}}\\par\n'
        '  \\vspace{0.35em}\n'
        f'  {{\\LARGE\\bfseries\\sffamily\\color{{{color}}}{act}\\par}}\n'
        '  \\vspace{0.25em}\n'
        '  {\\color{heading-section}\\rule{\\wd0}{0.4pt}}\\par\n'
        '\\end{center}\n'
        '\\vspace{0.3em}\n'
    )


# Reserva antes do rótulo de actividade. O rótulo ocupa unhas seis liñas base
# desde o texto anterior, e a cabeceira que o segue reserva outras oito
# (\section, no preámbulo). Sen a reserva, un rótulo ao pé da páxina quedaba
# só: a cabeceira non collía e pasaba á seguinte. A marca permite que
# keep-with-next.lua e small-table.lua leven as súas reservas por riba del.
ACTIVITY_LABEL_MARK = '% md2pdf:activity-label'
ACTIVITY_LABEL_LINES = 6
SECTION_RESERVE_LINES = 8


def _activity_label_block(act_latex: str, before_section: bool) -> str:
    """Bloque LaTeX en bruto do rótulo, coa súa reserva, para o Markdown."""
    lines = ACTIVITY_LABEL_LINES + (SECTION_RESERVE_LINES if before_section else 0)
    return ('```{=latex}\n' + ACTIVITY_LABEL_MARK + '\n'
            + f'\\Needspace{{{lines}\\baselineskip}}\n'
            + act_latex + '```\n\n')


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
\definecolor{terminal-bg}{HTML}{F2F2F2}
\definecolor{terminal-border}{RGB}{140,140,140}
\definecolor{inline-bg}{RGB}{255,255,255}
\definecolor{inline-fg}{RGB}{0,0,0}
\definecolor{heading-section}{RGB}{0,0,0}
% Callouts: fondo branco, borde gris; código en liña transparente
\renewcommand{\mdpdftaskborder}{0.55 0.55 0.55}
\renewcommand{\mdpdftaskbg}{1 1 1}
\AtBeginDocument{%
  \tcbset{
    md2pdf-callout/.style={
      colback=white,
      colframe=black!55,
    },
    md2pdf-inline-style/.style={
      blankest,
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
        "\\definecolor{terminal-bg}{HTML}{E2DDD0}\n"
        "\\definecolor{terminal-border}{HTML}{C5B99E}\n"
        "\\definecolor{inline-bg}{HTML}{EDE8DC}\n"
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
        "% Formularios e caixas de tarefas\n"
        "\\renewcommand{\\mdpdftaskborder}{0.83 0.78 0.69}\n"
        "\\renewcommand{\\mdpdftaskbg}{0.93 0.91 0.86}\n"
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
    titlepage: bool = False,
    callouts: bool = True,
    author: str | None = None,
    keywords: str | None = None,
    subject: str | None = None,
    print_mode: bool = False,
    serif: bool = False,
    **kwargs,
) -> list[str]:
    """Constrúe o comando Pandoc para LuaLaTeX con template propio."""
    night_mode: bool = kwargs.get('night_mode', False)
    decimal_align: bool = kwargs.get('decimal_align', True)
    terminal_blocks: bool = kwargs.get('terminal_blocks', True)
    body_font: str = 'serif' if serif or kwargs.get('body_font') == 'serif' else 'sans'
    main_font: str = _detect_font('serif') if body_font == 'serif' else _detect_font('main')

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
        '-V', f'mainfont={main_font}',
        '-V', f'sansfont={_detect_font("sans")}',
        '-V', f'monofont={_detect_font("mono")}',
        '-V', f'bodyfont={body_font}',
        '-M', f'body-font={body_font}',
        '-V', r'mainfontoptions=Numbers=OldStyle,Ligatures=TeX',
        '-V', r'monofontoptions=Scale=0.85,Ligatures=NoCommon',
        '-V', 'geometry=top=14mm,bottom=16mm,left=22mm,right=22mm,footskip=7mm',
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
    if kwargs.get('inline_pill', False):
        cmd.extend(['-H', _temp_tex_file(r'\mdpdfinlinepilltrue')])

    cmd.extend([f'{_pandoc_highlight_flag()}={highlight}'])
    # Sintaxe Javadoc corrixida: sen ela, os tiles dos comentarios /** */
    # saen co estilo de comentario no medio de palabras en texto normal.
    javadoc_syntax = _find_javadoc_syntax()
    if javadoc_syntax:
        cmd.append(f'--syntax-definition={javadoc_syntax}')

    if toc:
        cmd.extend(['--toc', f'--toc-depth={toc_depth}'])

    if section_numbering:
        cmd.append('--number-sections')

    # Primeiro normalizamos as listas de pares; logo aplicamos os filtros
    # de táboas, callouts e código.
    term_pairs = _find_term_pairs_filter()
    if term_pairs:
        cmd.extend(['--lua-filter', str(term_pairs)])

    # Filtros Lua: anchos → táboas pequenas → parágrafos de entrada → callouts
    # → br → terminal → compact-code → keep-code → hl-lines.
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

    # Antes de callouts: os parágrafos e os bloques de dentro dun callout
    # aínda son elementos de Pandoc, non LaTeX en bruto.
    keep_with_next = _find_keep_with_next_filter()
    if keep_with_next:
        cmd.extend(['--lua-filter', str(keep_with_next)])
        # Como code-keep-lines: o preprocesamento elimina o front matter.
        keep_with_next_value = kwargs.get('keep_with_next')
        if keep_with_next_value is not None:
            keep_with_next_value = str(keep_with_next_value).split('#', 1)[0]
            keep_with_next_value = keep_with_next_value.strip().strip('\'"')
            cmd.extend(['--metadata', f'keep-with-next={keep_with_next_value}'])

    if callouts:
        callouts_filter = _find_callouts_filter()
        if callouts_filter:
            cmd.extend(['--lua-filter', str(callouts_filter)])

    br_filter = _find_br_filter()
    if br_filter:
        cmd.extend(['--lua-filter', str(br_filter)])

    terminal_filter = _find_terminal_blocks_filter()
    if terminal_filter:
        cmd.extend(['--lua-filter', str(terminal_filter)])
        if not terminal_blocks:
            cmd.extend(['--metadata', 'terminal-blocks=false'])

    compact_filter = _find_compact_code_filter()
    if compact_filter:
        cmd.extend(['--lua-filter', str(compact_filter)])

    keep_filter = _find_keep_code_filter()
    if keep_filter:
        cmd.extend(['--lua-filter', str(keep_filter)])
        # O preprocesamento elimina o front matter: transportar o valor
        # combinado de metadata.yaml e do documento, incluído o cero.
        code_keep_lines = kwargs.get('code_keep_lines')
        if code_keep_lines is not None:
            # Os lectores YAML sinxelos conservan os comentarios en liña.
            code_keep_lines = str(code_keep_lines).split('#', 1)[0].strip().strip('\'"')
            cmd.extend(['--metadata', f'code-keep-lines={code_keep_lines}'])

    hl_filter = _find_hl_lines_filter()
    if hl_filter:
        cmd.extend(['--lua-filter', str(hl_filter)])

    # Ficheiros adxuntos: despois das reservas de keep-with-next e
    # small-table, que miden o texto da ligazón antes de que sexa LaTeX.
    attach_filter = _find_attach_filter()
    if attach_filter:
        cmd.extend(['--lua-filter', str(attach_filter)])

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


def prepare_lualatex_extras(
    cmd: list[str],
    processed: str,
    tmp_path: str,
    md_meta: dict,
    input_path: Path,
    titlepage: bool = False,
    plain: bool = False,
    print_mode: bool = False,
    night_mode: bool = False,
    front_author: bool = False,
    debug: bool = False,
    fm_meta: dict | None = None,
    meta_file: Path | None = None,
) -> tuple[str, list[str], bool]:
    """Prepara os snippets e axustes de Markdown/LaTeX específicos de LuaLaTeX.

    Devolve:
        (processed_actualizado, extra_tmp_files, éxito)
    """
    activity_val = md_meta.get('activity', '')

    # Detectar se hai título (front matter, metadata.yaml ou primeiro # h1)
    # O regex ^#(?!#) asegura que só coincide con h1, non con ## ou ###
    has_title = bool(md_meta.get('title') or
                     re.search(r'^#(?!#)\s+\S', processed, re.MULTILINE))
    if not has_title:
        print(f'  ⚠  Aviso: non se detectou título en '
              f'{input_path.name} (engade un # Título ou '
              f'title: no YAML front matter)',
              file=sys.stderr)

    # ── Modo plain: eliminar o # título do corpo ──────
    # Con --shift-heading-level-by=-1 pandoc converte o primeiro
    # # h1 a nivel 0, que se renderiza como \part{} no corpo.
    # En modo plain eliminámolo para que non apareza; o título
    # segue dispoñible nos metadatos PDF vía --metadata.
    if plain and has_title:
        h1_match = re.search(r'^#(?!#)\s+\S.*$', processed, re.MULTILINE)
        if h1_match:
            # Extraer título do h1 se non vén de metadatos
            if not md_meta.get('title'):
                h1_text = re.sub(r'^#\s+', '', h1_match.group(0))
                md_meta['title'] = h1_text.strip()
            processed = (processed[:h1_match.start()]
                         + processed[h1_match.end():])
            with open(tmp_path, 'w', encoding='utf-8') as f_upd:
                f_upd.write(processed)
        # Pasar título como metadato para pdftitle
        title_val = md_meta.get('title', '')
        if title_val:
            cmd.extend(['--metadata', f'title={title_val}'])

    extra_tmp_files: list[str] = []

    if titlepage:
        if not has_title:
            print('  ✗ ERRO: non se pode xerar portada sen título. '
                  'Engade un # Título ou title: no YAML front matter.',
                  file=sys.stderr)
            return processed, extra_tmp_files, False
        if debug:
            print('  [DEBUG] fm_meta (front matter):', fm_meta)
            print('  [DEBUG] meta_file:',
                  str(meta_file) if meta_file else 'NONE')
            print('  [DEBUG] md_meta completo:', md_meta)
        tp_content = _build_titlepage_snippet(
            md_meta, print_mode, night_mode=night_mode,
            front_author=front_author,
        )
        tp_path = _temp_tex_file(tp_content)
        extra_tmp_files.append(tp_path)
        cmd.extend(['-B', tp_path])
    elif not plain:
        # Sen portada: título estilizado antes do TOC (só se hai título)
        if has_title:
            if print_mode:
                title_color = 'black'
            elif night_mode:
                title_color = 'night-link'
            else:
                title_color = 'blue!45!black'
            b_lines = [
                '\\makeatletter',
                '\\begin{center}',
                f'  {{\\LARGE\\bfseries\\sffamily'
                f'\\color{{{title_color}}}\\@title\\par}}',
                '\\end{center}',
                '\\vskip 0.6em',
                '\\makeatother',
            ]
            b_path = _temp_tex_file('\n'.join(b_lines) + '\n')
            extra_tmp_files.append(b_path)
            cmd.extend(['-B', b_path])

    # Etiqueta de actividade inxectada no corpo antes do primeiro ##
    if activity_val and not plain:
        act_latex = _build_activity_label(
            activity_val, print_mode, night_mode=night_mode)
        m2 = re.search(r'^##\s', processed, re.MULTILINE)
        if m2:
            processed = (processed[:m2.start()]
                         + _activity_label_block(act_latex, True)
                         + processed[m2.start():])
        else:
            processed = (processed + '\n'
                         + _activity_label_block(act_latex, False))
        with open(tmp_path, 'w', encoding='utf-8') as f_upd:
            f_upd.write(processed)

    return processed, extra_tmp_files, True

