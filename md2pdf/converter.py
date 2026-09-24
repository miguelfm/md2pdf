"""
converter.py — Conversión de ficheiros Markdown a PDF/DOCX/HTML.

Función principal: convert_one()
Utilidade: collect_files()
"""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from .assets    import resolve_highlight
from .lint      import lint_md
from .diagrams  import process_diagrams
from .diagrams.settings import load_diagram_defaults
from .metadata  import (_extract_md_metadata, _find_metadata_file,
                         _load_metadata_file)
from .preprocess import preprocess_md
from .html_validation import validate_html
from .engines.lualatex import (build_lualatex_cmd, _build_activity_label,
                                _build_titlepage_snippet, _temp_tex_file)
from .engines.docx     import build_docx_cmd
from .engines.html     import build_html_cmd


def _natural_key(path: Path) -> list:
    """Orde natural: «U1A2» vai antes que «U1A10» (a alfabética poñíaos ao revés)."""
    return [int(part) if part.isdigit() else part.casefold()
            for part in re.split(r'(\d+)', path.name)]


def collect_files(paths: list[str]) -> list[Path]:
    """Recolle ficheiros .md desde rutas (ficheiros ou directorios)."""
    files: list[Path] = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            files.extend(sorted(path.glob('*.md'), key=_natural_key))
        elif path.is_file() and path.suffix == '.md':
            files.append(path)
        elif path.is_file():
            print(f'  Aviso: {path.name} non é un ficheiro .md, ignorado.',
                  file=sys.stderr)
        else:
            print(f'  Aviso: {p} non existe, ignorado.', file=sys.stderr)
    return files


def _format_size(size: int) -> str:
    """Formatea un tamaño en bytes a cadea lexible."""
    if size < 1024:
        return f'{size} B'
    if size < 1024 * 1024:
        return f'{size / 1024:.0f} KB'
    return f'{size / (1024 * 1024):.1f} MB'


def _extract_latex_errors(stderr: str) -> list[str]:
    """
    Extrae as mensaxes de erro relevantes do stderr de LuaLaTeX.
    Inclúe liñas de contexto (l.NNN comando) tras cada !.
    """
    lines    = stderr.splitlines()
    relevant = []
    for i, line in enumerate(lines):
        if (line.startswith('!') or 'Error' in line or 'error' in line
                or 'not found' in line or 'Missing' in line):
            relevant.append(line)
            # Liñas de contexto: l.NNN e a seguinte
            for j in (i + 1, i + 2):
                if j < len(lines) and lines[j].strip():
                    relevant.append('    ' + lines[j])
    return relevant or lines[-20:]


def _report_diagram(name: str, new_count: int, cached_count: int,
                    errors: list[str]) -> None:
    """Imprime o resumo do procesado dun tipo de diagrama."""
    total = new_count + cached_count
    if total > 0:
        word = 'diagrama procesado' if total == 1 else 'diagramas procesados'
        if new_count and cached_count:
            new_w = 'novo' if new_count == 1 else 'novos'
            detail = f' ({new_count} {new_w}, {cached_count} da caché)'
        elif cached_count and not new_count:
            detail = ' (todos da caché)'
        else:
            detail = ''
        print(f'    📊 {name}: {total} {word}{detail}')
    for err in errors:
        print(f'    ⚠  {name}: {err}', file=sys.stderr)


def convert_one(
    input_path: Path,
    output_path: Path,
    template: Path | None,
    engine: str = 'lualatex',
    toc: bool = True,
    toc_depth: int = 3,
    section_numbering: str = '1.1.',
    lang: str = 'gl',
    papersize: str = 'a4',
    highlight: str = 'auto',
    listings: bool = False,
    titlepage: bool = False,
    callouts: bool = True,
    no_metadata: bool = False,
    print_mode: bool = False,
    night_mode: bool = False,
    front_author: bool = False,
    plain: bool = False,
    strict: bool = False,
    debug: bool = False,
) -> bool:
    """Converte un ficheiro .md ao formato do motor indicado. Devolve True se ten éxito."""

    highlight = resolve_highlight(highlight)

    # ── Modo plain: desactivar TOC, numeración, portada ──
    if plain:
        toc = False
        section_numbering = ''
        titlepage = False

    engine_label    = {'lualatex': 'LuaLaTeX', 'docx': 'DOCX', 'html': 'HTML5'}.get(engine, engine)
    highlight_label = (Path(highlight).stem
                       if ('/' in highlight or '\\' in highlight)
                       else highlight)
    print_label = ' 🖨 impresión' if print_mode else ''

    if engine == 'docx':
        print(f'  📄 {input_path.name} → {output_path.name}  [DOCX]')
    elif engine == 'html':
        print(f'  📄 {input_path.name} → {output_path.name}'
              f'  [HTML5, {highlight_label}]')
    else:
        print(f'  📄 {input_path.name} → {output_path.name}'
              f'  [{engine_label}, {highlight_label}{print_label}]')

    # ── Ler ficheiro ──────────────────────────────────────────
    # utf-8-sig le igual un ficheiro con BOM ou sen el, e elimina a marca
    text = input_path.read_text(encoding='utf-8-sig')

    # ── Lint ──────────────────────────────────────────────────
    lint_issues = lint_md(text)
    if lint_issues:
        label = '✗ ERRO' if strict else '⚠  Aviso'
        print(f'  {label}: {len(lint_issues)} problema(s) detectado(s) en '
              f'{input_path.name}:', file=sys.stderr)
        for issue in lint_issues:
            print(f'    • {issue}', file=sys.stderr)
        if strict:
            print('  Abortando por --strict. Corrixe os problemas e volve '
                  'a tentar.', file=sys.stderr)
            return False

    # ── Metadatos ─────────────────────────────────────────────
    md_meta: dict = {}
    meta_file: Path | None = None
    fm_meta: dict = {}
    if not no_metadata:
        fm_meta   = _extract_md_metadata(text)
        meta_file = _find_metadata_file(input_path)
        if meta_file:
            yaml_meta = _load_metadata_file(meta_file)
            print(f'    📋 Metadatos: {meta_file.name}')
            md_meta = {**yaml_meta, **fm_meta}
        else:
            md_meta = fm_meta

    # ── Preprocesamento ───────────────────────────────────────
    processed = preprocess_md(text, engine, callouts=callouts)

    # ── Diagramas: render directo desde Python antes de chamar a Pandoc
    try:
        diagram_defaults = ({} if no_metadata else
                            load_diagram_defaults(text, meta_file))
    except ValueError as error:
        print(f'  ✗ ERRO: {error}', file=sys.stderr)
        return False
    processed, diagram_stats = process_diagrams(
        processed, engine, defaults=diagram_defaults,
        source_dir=input_path.resolve().parent)
    labels = {'mermaid': 'Mermaid', 'd2': 'D2', 'graphviz': 'Graphviz',
              'vega-lite': 'Vega-Lite'}
    for name in diagram_stats.errors:
        _report_diagram(labels.get(name, name), diagram_stats.new[name],
                        diagram_stats.cached[name], diagram_stats.errors[name])
        for warning in diagram_stats.warnings.get(name, []):
            print(f'    ⚠  {labels.get(name, name)}: {warning}', file=sys.stderr)
    diagram_failed = any(diagram_stats.errors.values())
    if strict and diagram_failed:
        print('  ✗ Abortando por --strict: fallou a integración de gráficos.', file=sys.stderr)
        return False

    # ── Ficheiro temporal ─────────────────────────────────────
    tmp = tempfile.NamedTemporaryFile(
        mode='w', suffix='.md', encoding='utf-8', delete=False,
    )
    extra_tmp_files: list[str] = []
    print_snippet_path: str | None = None

    try:
        tmp.write(processed)
        tmp.close()

        # ── Construír comando Pandoc ──────────────────────────
        build_fn = {
            'lualatex': build_lualatex_cmd,
            'docx':     build_docx_cmd,
            'html':     build_html_cmd,
        }[engine]

        cmd = build_fn(
            tmp_path=tmp.name,
            output_path=str(output_path),
            template=template,
            toc=toc,
            toc_depth=toc_depth,
            section_numbering=section_numbering,
            lang=lang,
            papersize=papersize,
            highlight=highlight,
            listings=listings,
            titlepage=titlepage,
            callouts=callouts,
            author=md_meta.get('author'),
            keywords=md_meta.get('keywords'),
            subject=md_meta.get('subject') or None,
            print_mode=print_mode,
            night_mode=night_mode,
            plain_mode=plain,
            title=md_meta.get('title'),
            activity=md_meta.get('activity'),
            source_dir=str(input_path.resolve().parent),
        )

        # Gardar ruta do snippet de impresión para limpeza
        if print_mode and engine == 'lualatex':
            h_indices = [i for i, v in enumerate(cmd) if v == '-H']
            if h_indices:
                print_snippet_path = cmd[h_indices[-1] + 1]

        # ── Portada e etiqueta de actividade (só lualatex) ────
        if engine == 'lualatex':
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
                h1_match = re.search(r'^#(?!#)\s+\S.*$', processed,
                                     re.MULTILINE)
                if h1_match:
                    # Extraer título do h1 se non vén de metadatos
                    if not md_meta.get('title'):
                        h1_text = re.sub(r'^#\s+', '', h1_match.group(0))
                        md_meta['title'] = h1_text.strip()
                    processed = (processed[:h1_match.start()]
                                 + processed[h1_match.end():])
                    with open(tmp.name, 'w', encoding='utf-8') as f_upd:
                        f_upd.write(processed)
                # Pasar título como metadato para pdftitle
                title_val = md_meta.get('title', '')
                if title_val:
                    cmd.extend(['--metadata', f'title={title_val}'])

            if titlepage:
                if not has_title:
                    print(f'  ✗ ERRO: non se pode xerar portada sen título. '
                          f'Engade un # Título ou title: no YAML front matter.',
                          file=sys.stderr)
                    return False
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
                raw_block = '```{=latex}\n' + act_latex + '```\n\n'
                m2 = re.search(r'^##\s', processed, re.MULTILINE)
                if m2:
                    processed = (processed[:m2.start()]
                                 + raw_block
                                 + processed[m2.start():])
                else:
                    processed = processed + '\n' + raw_block
                with open(tmp.name, 'w', encoding='utf-8') as f_upd:
                    f_upd.write(processed)

        # ── Debug ─────────────────────────────────────────────
        if debug:
            import shlex
            print('\n  [DEBUG] Comando pandoc:')
            print('  ' + ' '.join(shlex.quote(str(c)) for c in cmd))
            if engine == 'lualatex':
                debug_dir = input_path.parent / 'md2pdf_debug'
                debug_dir.mkdir(exist_ok=True)
                for i, c in enumerate(cmd):
                    if c in ('-H', '-B', '-A') and i + 1 < len(cmd):
                        src = Path(cmd[i + 1])
                        if src.exists():
                            dst = (debug_dir
                                   / f'{c[1]}_{src.suffix.lstrip(".")}{i}.tex')
                            dst.write_bytes(src.read_bytes())
                            print(f'  [DEBUG] {c} → {dst}')
                            print(f'  [DEBUG] contido:')
                            print(src.read_text(encoding='utf-8',
                                                errors='replace'))
                            print()

        # ── Executar ──────────────────────────────────────────
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            cwd=str(input_path.parent),
        )

        if result.returncode != 0:
            print(f'  ✗ ERRO ao converter {input_path.name}:',
                  file=sys.stderr)
            stderr = result.stderr or ''
            if engine == 'lualatex':
                errors = _extract_latex_errors(stderr)
                for line in errors[:25]:
                    print(f'    {line}', file=sys.stderr)
            else:
                for line in stderr.strip().splitlines()[:15]:
                    print(f'    {line}', file=sys.stderr)
            return False

        # ── Validación da saída HTML ───────────────────────────
        if engine == 'html':
            html_issues = validate_html(output_path)
            if html_issues:
                for issue in html_issues:
                    print(f'    ⚠  HTML: {issue}', file=sys.stderr)
                if strict:
                    try:
                        output_path.unlink()
                    except OSError:
                        pass
                    print('  ✗ Abortando por --strict: a saída HTML non pasa '
                          'a validación estrutural/accesible.', file=sys.stderr)
                    return False

        size = output_path.stat().st_size
        print(f'  ✓ Xerado: {output_path.name} ({_format_size(size)})')
        if diagram_failed:
            print('  ⚠ Documento xerado con gráficos sen renderizar; revisa os avisos '
                  'ou usa --strict para impedir esta saída.', file=sys.stderr)
        return True

    finally:
        # Limpeza de ficheiros temporais
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
        for p in extra_tmp_files:
            try:
                os.unlink(p)
            except OSError:
                pass
        if print_snippet_path is not None:
            try:
                os.unlink(print_snippet_path)
            except OSError:
                pass
