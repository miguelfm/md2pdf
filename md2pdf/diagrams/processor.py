"""Procesamento nunha soa pasada; nunca renderiza exemplos dentro doutras vallas."""
import json
import os
import re
import shlex
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .base import RenderContext
from .common import (DIAGRAM_CLASS, FORMAT_BY_ENGINE, TARGET_FONT_PT, TEXTWIDTH_PT, cache_dir,
                     content_hash, image_block, width_attr)
from .validation import validate_output, pdf_font_warning, validation_warning
from .renderers import RENDERERS

FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})([^\r\n]*)$')
LAYOUTS = {
    'd2': {'dagre', 'elk', 'tala'},
    'graphviz': {'dot', 'neato', 'fdp', 'sfdp', 'circo', 'twopi', 'osage', 'patchwork'},
}
DIMENSION = re.compile(r'(?:\d+(?:\.\d+)?|\.\d+)(?:%|px|pt|cm|mm|in)')
IDENTIFIER = re.compile(r'[A-Za-z][\w:.-]*')

@dataclass
class DiagramStats:
    new: dict[str, int] = field(default_factory=dict)
    cached: dict[str, int] = field(default_factory=dict)
    errors: dict[str, list[str]] = field(default_factory=dict)
    warnings: dict[str, list[str]] = field(default_factory=dict)

def renderer_fingerprint(executable, root, name):
    """Invalida a caché cando cambia o lanzador ou a configuración de Chromium.

    Non detecta actualizacións internas que deixen o lanzador idéntico.
    """
    path = Path(executable).resolve()
    try:
        stat = path.stat()
        identity = [str(path), stat.st_size, stat.st_mtime_ns]
    except OSError:
        identity = [str(path)]
    config = root / 'puppeteer-config.json'
    if name == 'mermaid':
        default = '{"args":["--no-sandbox","--disable-setuid-sandbox"]}'
        identity.append(config.read_text() if config.exists() else default)
    return json.dumps(identity)

def fenced_blocks(text):
    """Devolve límites e info de vallas completas, incluídas as non gráficas."""
    lines = text.splitlines(keepends=True)
    offset = 0
    opening = None
    for line in lines:
        clean = line.rstrip('\r\n')
        if opening is None:
            match = FENCE.match(clean)
            if match:
                fence, info = match.groups()
                if fence[0] == '`' and '`' in info:
                    offset += len(line)
                    continue
                opening = (offset, offset + len(line), fence, info.strip())
        else:
            start, body_start, fence, info = opening
            if re.fullmatch(r' {0,3}' + re.escape(fence[0]) +
                            '{' + str(len(fence)) + r',}[ \t]*', clean):
                body = text[body_start:offset]
                if body.endswith('\n'):
                    body = body[:-1]
                    if body.endswith('\r'):
                        body = body[:-1]
                yield start, offset + len(line), info, body
                opening = None
        offset += len(line)

def parse_info(info, registry):
    if info.startswith('{') and info.endswith('}'):
        tokens = shlex.split(info[1:-1])
        languages = [token[1:] for token in tokens if token.startswith('.')]
        language = next((name for name in languages if name in registry), None)
    else:
        tokens = shlex.split(info)
        language = tokens.pop(0) if tokens else None
    if language not in registry:
        return None, {}
    options = {}
    for token in tokens:
        if token.startswith('.'):
            continue
        if token.startswith('#'):
            options['id'] = token[1:]
        elif '=' in token:
            key, value = token.split('=', 1)
            options[key] = value
        elif token != language:
            raise ValueError(f'atributo non recoñecido: {token}')
    return registry[language], options

def validate(name, options):
    allowed = {'width', 'height', 'caption', 'id'}
    if name in LAYOUTS:
        allowed.add('layout')
    if name == 'd2':
        allowed.add('theme')
    for key, value in options.items():
        if key not in allowed:
            raise ValueError(f'opción non admitida para {name}: {key}')
        if not isinstance(value, (str, int, float)) or isinstance(value, bool):
            raise ValueError(f'valor incorrecto de {key}')
        value = str(value)
        options[key] = value
        if key == 'layout' and value not in LAYOUTS[name]:
            raise ValueError(f'layout non admitido: {value}')
        if key == 'theme' and not re.fullmatch(r'\d{1,4}', value):
            raise ValueError('theme debe ser un identificador numérico de D2')
        if key in {'width', 'height'}:
            if not DIMENSION.fullmatch(value) or float(re.match(r'[\d.]+', value)[0]) <= 0:
                raise ValueError(f'dimensión incorrecta: {key}={value}')
        if key == 'id' and not IDENTIFIER.fullmatch(value):
            raise ValueError('identificador de figura incorrecto')
    return options

def figure_block(output, fmt, engine, font_px, options):
    width = options.get('width')
    height = options.get('height')
    if not width and not height:
        width = width_attr(output, fmt, engine, font_px)
    if not any(key in options for key in ('height', 'caption', 'id')):
        return image_block(output, width, engine)
    attrs = []
    if options.get('id'):
        attrs.append('#' + options['id'])
    if engine == 'html':
        attrs.append('.' + DIAGRAM_CLASS)
    if width:
        attrs.append('width=' + width)
    if height:
        attrs.append('height=' + height)
    # O pé é texto literal; non permite inxectar Markdown/raw.
    caption = re.sub(r'([\\\[\]*_`{}<>!])', r'\\\1', options.get('caption', ''))
    caption = caption.replace('\n', ' ').replace('\r', ' ')
    path = output.as_posix().replace(' ', '%20').replace('>', '%3E').replace('<', '%3C')
    return '\n\n![' + caption + '](<' + path + '>){' + ' '.join(attrs) + '}\n\n'

def process_diagrams(text: str, engine: str, renderers=RENDERERS, *,
                     defaults=None, source_dir=None):
    stats = DiagramStats()
    registry = {lang: renderer for renderer in renderers for lang in renderer.languages}
    parts, end = [], 0
    counters = {}
    directory = Path(source_dir).resolve() if source_dir else None
    for start, stop, info, content in fenced_blocks(text):
        try:
            renderer, local = parse_info(info, registry)
        except ValueError as error:
            # Só reportar cabeceiras que parecen diagramas.
            if not any(re.search(r'(?<![\w-])' + re.escape(n) + r'(?![\w-])', info)
                       for n in registry):
                continue
            stats.errors.setdefault('config', []).append(str(error))
            stats.new.setdefault('config', 0)
            stats.cached.setdefault('config', 0)
            continue
        if renderer is None:
            continue
        name = renderer.name
        stats.new.setdefault(name, 0)
        stats.cached.setdefault(name, 0)
        stats.errors.setdefault(name, [])
        stats.warnings.setdefault(name, [])
        counters[name] = counters.get(name, 0) + 1
        parts.append(text[end:start])
        replacement = text[start:stop]
        try:
            if defaults is not None and not isinstance(defaults, dict):
                raise ValueError('diagrams debe ser un mapa')
            inherited = (defaults or {}).get(name, {})
            if not isinstance(inherited, dict):
                raise ValueError(f'diagrams.{name} debe ser un mapa')
            options = validate(name, {**inherited, **local})
            finder = getattr(renderer, 'find_executable', None)
            executable = (finder() if finder else next(
                (p for n in renderer.executable_names if (p := shutil.which(n))), None))
            if not executable:
                raise ValueError(renderer.missing_message(1))
            fmt = FORMAT_BY_ENGINE.get(engine, 'pdf')
            # Cada renderizador pode axustar o tamaño de fonte á unidade do
            # formato de saída (Graphviz mide en pt; Mermaid e D2 en px).
            font_px = getattr(renderer, 'font_px_for',
                              lambda _fmt: renderer.font_px)(fmt)
            if counters[name] == 1:
                warning = validation_warning(fmt)
                if warning:
                    stats.warnings[name].append(warning)
            root = cache_dir(name)
            render_options = {k: v for k, v in options.items() if k in {'layout', 'theme'}}
            # Nova xeración de caché: saídas verificadas e identidade do lanzador.
            tag = (renderer.cache_tag() if hasattr(renderer, 'cache_tag')
                   else renderer.render_tag)
            tag += '|validated-v1|' + renderer_fingerprint(executable, root, name)
            tag += json.dumps([render_options, str(directory)], sort_keys=True)
            output = root / (content_hash(content, fmt, tag) + '.' + fmt)
            # Recursos externos poden cambiar sen cambiar o bloque: non reutilizar.
            external = bool(re.search(r'@|\b(?:image|icon)\s*[:=]', content))
            cached = output.is_file() and output.stat().st_size > 0 and not external
            if cached:
                try:
                    validate_output(output, fmt)
                except ValueError as error:
                    cached = False
                    stats.warnings[name].append(
                        f'diagrama #{counters[name]}: caché inválida; rexenerando ({error})')
            if not cached:
                with tempfile.TemporaryDirectory(prefix='render-', dir=root) as temp:
                    temporary = Path(temp) / ('diagram.' + fmt)
                    context = RenderContext(root, fmt, options=render_options,
                                            source_dir=directory)
                    error = renderer.render(executable, context, content, temporary)
                    if error:
                        raise ValueError(error)
                    validate_output(temporary, fmt)
                    os.replace(temporary, output)
            if fmt == 'pdf' and 'height' not in options:
                width = options.get('width') or width_attr(output, fmt, engine, font_px)
                warning = pdf_font_warning(output, width, TEXTWIDTH_PT.get(engine, 483.7),
                                           TARGET_FONT_PT)
                if warning:
                    stats.warnings[name].append(f'diagrama #{counters[name]}: {warning}')
            replacement = figure_block(output, fmt, engine, font_px, options)
            (stats.cached if cached else stats.new)[name] += 1
        except (ValueError, OSError) as error:
            stats.errors[name].append(f'diagrama #{counters[name]}: {error}')
        parts.append(replacement)
        end = stop
    parts.append(text[end:])
    return ''.join(parts), stats
