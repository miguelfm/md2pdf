"""
__main__.py — Punto de entrada CLI para md2pdf.

Uso:
    python -m md2pdf documento.md
    python -m md2pdf documento.md -e docx
    python -m md2pdf documento.md -e html
    md2pdf documento.md           # se o wrapper está en PATH
"""

import argparse
import sys
import time
from pathlib import Path

from .config    import ENGINES, DEFAULT_ENGINE, TEMPLATE_NAMES, OUTPUT_EXTENSIONS
from .assets    import check_dependencies, find_template
from .converter import convert_one, collect_files
from .metadata  import _find_metadata_file
from .ims       import build_ims_package


_EPILOG = """\
Exemplos:
  md2pdf apuntes.md                          # LuaLaTeX con template propio (por defecto)
  md2pdf apuntes.md -e docx                  # Word (.docx)
  md2pdf apuntes.md -e html                  # HTML5 autocontido
  md2pdf apuntes.md --listings               # LaTeX con paquete listings
  md2pdf apuntes.md --print                  # Modo impresión (sen cores)
  md2pdf apuntes.md --serif                  # Modo serif no corpo (ideal para papel)
  md2pdf apuntes.md --night                  # Modo nocturno (paleta sepia)
  md2pdf apuntes.md -o saida.pdf
  md2pdf *.md
  md2pdf docs/ --no-toc
  md2pdf apuntes.md --titlepage
  md2pdf apuntes.md --watch                  # Recompilar automaticamente ao gardar
  md2pdf apuntes.md --plain                  # Sen TOC, título estilizado nin etiqueta
  md2pdf U1/ --ims U1-moodle.zip             # Paquete IMS para Moodle
"""


def _get_mtimes(paths: list[Path]) -> dict[Path, float]:
    """Devolve un dict {ruta: mtime} para os ficheiros que existen."""
    result = {}
    for p in paths:
        try:
            result[p] = p.stat().st_mtime
        except OSError:
            pass
    return result


def _watch_files(md_files: list[Path]) -> list[Path]:
    """
    Devolve a lista de ficheiros a vixiar para un conxunto de .md:
    os propios .md + metadata.yml asociados (se existen).
    """
    watched = list(md_files)
    seen = set(md_files)
    for f in md_files:
        meta = _find_metadata_file(f)
        if meta and meta not in seen:
            watched.append(meta)
            seen.add(meta)
    return watched


def _run_conversion(files: list[Path], args, template, section_numbering: str,
                    out_ext: str) -> tuple[int, int]:
    """Executa a conversión de todos os ficheiros. Devolve (ok, fail)."""
    ok = fail = 0
    for f in files:
        out = Path(args.output) if args.output else f.with_suffix(out_ext)
        success = convert_one(
            input_path=f,
            output_path=out,
            template=template,
            engine=args.engine,
            toc=not args.no_toc,
            toc_depth=args.toc_depth,
            section_numbering=section_numbering,
            lang=args.lang,
            papersize=args.paper,
            highlight=args.highlight,
            listings=args.listings,
            titlepage=args.titlepage,
            callouts=not args.no_callouts,
            decimal_align=not args.no_decimal_align,
            terminal_blocks=not args.no_terminal_blocks,
            no_metadata=args.no_metadata,
            print_mode=args.print_mode,
            night_mode=args.night_mode,
            serif=args.serif,
            inline_pill=args.inline_pill,
            plain=args.plain,
            strict=args.strict,
            debug=args.debug,
        )
        if success:
            ok += 1
        else:
            fail += 1
    return ok, fail


def _watch_loop(files: list[Path], args, template,
                section_numbering: str, out_ext: str) -> None:
    """
    Bucle de vixilancia por polling (stdlib, sen dependencias externas).
    Comproba os mtime cada segundo; recompila se detecta cambios.
    """
    watched = _watch_files(files)
    mtimes  = _get_mtimes(watched)

    names = ', '.join(p.name for p in watched)
    print(f'  👁  Vixiando: {names}')
    print('  Ctrl+C para saír.\n')

    try:
        while True:
            time.sleep(1)

            # Detectar ficheiros novos (p.ex. metadata.yml creado despois)
            current_watched = _watch_files(files)
            new_files = [p for p in current_watched if p not in mtimes]
            if new_files:
                for p in new_files:
                    try:
                        mtimes[p] = p.stat().st_mtime
                    except OSError:
                        pass
                names = ', '.join(p.name for p in _watch_files(files))
                print(f'  👁  Vixiando: {names}')

            # Comprobar cambios de mtime
            new_mtimes = _get_mtimes(list(mtimes.keys()))
            changed = [p for p, t in new_mtimes.items() if mtimes.get(p) != t]

            if changed:
                changed_names = ', '.join(p.name for p in changed)
                print(f'  ↻  Cambio detectado en: {changed_names}')
                print()
                ok, fail = _run_conversion(files, args, template,
                                           section_numbering, out_ext)
                print()
                if len(files) > 1:
                    msg = f'  ✓ {ok} convertidos'
                    if fail:
                        msg += f', ✗ {fail} con erros'
                    print(msg)
                print()
                mtimes = _get_mtimes(list(mtimes.keys()))

    except KeyboardInterrupt:
        print('\n  Vixilancia detida.\n')


def main() -> None:
    parser = argparse.ArgumentParser(
        prog='md2pdf',
        description='Converter Markdown a PDF/DOCX/HTML con Pandoc e empaquetar '
                    'HTML como IMS para Moodle',
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument('inputs', nargs='+',
                        help='Ficheiros .md ou directorios con .md')
    parser.add_argument('-o', '--output',
                        help='Nome do ficheiro de saída (só con 1 input)')
    parser.add_argument('-e', '--engine', choices=ENGINES,
                        default=DEFAULT_ENGINE,
                        help=f'Motor: lualatex (PDF), docx (Word), html (HTML5). '
                             f'Defecto: {DEFAULT_ENGINE}')
    parser.add_argument('--no-toc', action='store_true',
                        help='Non incluír índice de contidos')
    parser.add_argument('--no-number', action='store_true',
                        help='Non numerar as seccións')
    parser.add_argument('--titlepage', action='store_true',
                        help='Incluír portada separada (só lualatex)')
    parser.add_argument('--listings', action='store_true',
                        help='LuaLaTeX: usar paquete listings para código')
    parser.add_argument('--no-callouts', action='store_true',
                        help='Desactivar callouts')
    parser.add_argument('--no-decimal-align', action='store_true',
                        help='LuaLaTeX: non aliñar polo separador decimal as '
                             'columnas numéricas das táboas')
    parser.add_argument('--no-terminal-blocks', action='store_true',
                        help='Desactivar o fondo diferenciado para bloques de código de terminal')
    parser.add_argument('--no-metadata', action='store_true',
                        help='Non cargar metadatos de YAML nin do front matter')
    parser.add_argument('--night', action='store_true', dest='night_mode',
                        help='Modo nocturno: paleta cálida sepia (PDF/HTML)')
    parser.add_argument('--print', action='store_true', dest='print_mode',
                        help='Modo impresión: ligazóns en negro, sen fondos '
                             '(PDF/HTML)')
    parser.add_argument('--serif', action='store_true',
                        help='Usar fonte serif (Source Serif 4) no corpo do texto '
                             '(recomendado para documentos impresos en papel)')
    parser.add_argument('--inline-pill', action='store_true',
                        help='Activar fondo suave tipo píldora para o código en liña (experimental)')
    parser.add_argument('--watch', action='store_true',
                        help='Vixiar o ficheiro e recompilar automaticamente '
                             'ao detectar cambios (polling cada 1s)')
    parser.add_argument('--plain', action='store_true',
                        help='Saída simple: sen TOC, sen título estilizado, '
                             'sen etiqueta de actividade, sen numeración')
    parser.add_argument('--debug', action='store_true',
                        help='Gardar ficheiros temporais e imprimir comando pandoc')
    parser.add_argument('--strict', action='store_true',
                        help='Abortar se se detectan problemas de estrutura no MD')
    parser.add_argument('--toc-depth', type=int, default=3,
                        help='Profundidade do TOC (defecto: 3)')
    parser.add_argument('--lang', default='gl',
                        help='Idioma do documento (defecto: gl)')
    parser.add_argument('--paper', default='a4',
                        help='Tamaño de páxina (defecto: a4)')
    parser.add_argument('--highlight', default='auto',
                        help='Estilo de resaltado (defecto: auto → '
                             'drake-jb.theme se existe, senón pygments)')
    parser.add_argument('--template',
                        help='Ruta ao template (auto-detectado por defecto; '
                             'non aplica a DOCX)')
    parser.add_argument('--ims', metavar='PAQUETE.zip',
                        help='Xerar un IMS Content Package para Moodle usando '
                             'HTML5 autocontido para cada Markdown')
    parser.add_argument('--ims-title', metavar='TÍTULO',
                        help='Título da organización IMS (defecto: nome do ZIP)')

    args = parser.parse_args()

    package_mode = bool(args.ims)
    effective_engine = 'html' if package_mode else args.engine
    check_dependencies(effective_engine)

    if args.ims_title and not package_mode:
        print('ERRO: --ims-title só se pode usar xunto con --ims',
              file=sys.stderr)
        sys.exit(1)
    if package_mode and args.output:
        print('ERRO: -o/--output non se usa con --ims; indica o ZIP no propio '
              '--ims', file=sys.stderr)
        sys.exit(1)
    if package_mode and args.watch:
        print('ERRO: --watch aínda non está dispoñible no modo --ims',
              file=sys.stderr)
        sys.exit(1)
    if package_mode:
        for flag, name in [
            (args.listings, '--listings'),
            (args.titlepage, '--titlepage'),
        ]:
            if flag:
                print(f'  Aviso: {name} non aplica a IMS/HTML, ignorado.',
                      file=sys.stderr)

    # ── Avisos de opcións incompatibles con DOCX ──────────────
    if not package_mode and args.engine == 'docx':
        for flag, name in [
            (args.listings,   '--listings'),
            (args.print_mode, '--print'),
            (args.night_mode, '--night'),
            (args.titlepage,  '--titlepage'),
            (args.template,   '--template'),
        ]:
            if flag:
                print(f'  Aviso: {name} non aplica a DOCX, ignorado.',
                      file=sys.stderr)

    if not package_mode and args.engine == 'html' and args.titlepage:
        print('  Aviso: --titlepage non aplica a HTML; o título intégrase na páxina.',
              file=sys.stderr)
        args.titlepage = False

    # ── Avisos de opcións incompatibles con --plain ────────
    if args.plain:
        if args.titlepage:
            print('  Aviso: --plain é incompatible con --titlepage, '
                  '--titlepage ignorado.', file=sys.stderr)
            args.titlepage = False
        if not args.no_toc:
            # --plain implica sen TOC; avisar só se o usuario puxo --toc explícito
            # (non hai --toc explícito, pero se non puxo --no-toc avisamos igualmente)
            pass  # silencioso: --plain xa desactiva o TOC internamente

    if args.watch and args.engine == 'docx':
        print('  Aviso: --watch con DOCX é posible pero pouco útil.',
              file=sys.stderr)

    # ── Template ──────────────────────────────────────────────
    template = None
    template_engine = 'html' if package_mode else args.engine
    if template_engine != 'docx':
        if args.template:
            template = Path(args.template)
            if not template.exists():
                print(f'ERRO: Non se atopa o template: {template}',
                      file=sys.stderr)
                sys.exit(1)
        else:
            template = find_template(template_engine)
            if template is None:
                tname = TEMPLATE_NAMES[template_engine]
                print(f'\n  ERRO: Non se atopa o template: {tname}',
                      file=sys.stderr)
                if template_engine == 'lualatex':
                    print('', file=sys.stderr)
                    print('  Solución: coloca md2pdf.latex no mesmo '
                          'directorio que o paquete md2pdf/', file=sys.stderr)
                else:
                    print(f'  Coloca {tname} no mesmo directorio que o '
                          f'paquete md2pdf/', file=sys.stderr)
                sys.exit(1)

    # ── Ficheiros de entrada ──────────────────────────────────
    files = collect_files(args.inputs)
    if not files:
        print('ERRO: Non se atoparon ficheiros .md', file=sys.stderr)
        sys.exit(1)

    if args.output and len(files) > 1:
        print('ERRO: -o/--output só se pode usar cun único ficheiro de entrada',
              file=sys.stderr)
        sys.exit(1)

    # ── Empaquetado IMS para Moodle ──────────────────────────
    if package_mode:
        section_numbering = '' if args.no_number else '1.1.'
        ims_output = Path(args.ims).expanduser()
        if ims_output.suffix.lower() != '.zip':
            ims_output = ims_output.with_suffix('.zip')
        print()
        success = build_ims_package(
            files=files,
            output_path=ims_output,
            template=template,
            package_title=args.ims_title,
            toc=not args.no_toc,
            toc_depth=args.toc_depth,
            section_numbering=section_numbering,
            lang=args.lang,
            highlight=args.highlight,
            callouts=not args.no_callouts,
            no_metadata=args.no_metadata,
            print_mode=args.print_mode,
            night_mode=args.night_mode,
            plain=args.plain,
            strict=args.strict,
            debug=args.debug,
        )
        print()
        sys.exit(0 if success else 1)

    if args.watch and len(files) > 1:
        print('  Aviso: --watch con múltiples ficheiros vixía todos e '
              'recompila todos ao detectar calquera cambio.', file=sys.stderr)

    if args.listings and args.engine != 'lualatex':
        print('  Aviso: --listings só ten efecto con -e lualatex, ignorado.',
              file=sys.stderr)

    # ── Conversión inicial ────────────────────────────────────
    section_numbering = '' if args.no_number else '1.1.'
    out_ext = OUTPUT_EXTENSIONS[args.engine]

    print()
    ok, fail = _run_conversion(files, args, template, section_numbering, out_ext)
    print()

    if len(files) > 1:
        msg = f'  ✓ {ok} convertidos'
        if fail:
            msg += f', ✗ {fail} con erros'
        print(msg)
        print()

    # ── Modo watch ────────────────────────────────────────────
    if args.watch:
        _watch_loop(files, args, template, section_numbering, out_ext)
        sys.exit(0)

    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()
