"""Adaptadores dos CLI Mermaid, D2 e Graphviz."""
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from .base import RenderContext
from .common import TARGET_FONT_PT

# Source Sans 3 é a sans do documento (cabeceiras das táboas). Graphviz
# (Pango) le «Source Sans 3» como familia «Source Sans» de 3 pt e cae noutra
# fonte; seguida dunha coma lese enteira. En CSS o nome vai entre aspas,
# porque un identificador non pode comezar por díxito.
DOT_FONT = 'Source Sans 3,sans-serif'
CSS_FONT = '"Source Sans 3", sans-serif'

def _run(command: list[str], timeout: int, env=None, cwd=None) -> str:
    try:
        result = subprocess.run(command, stdin=subprocess.DEVNULL,
            capture_output=True, text=True, timeout=timeout, env=env, cwd=cwd)
    except subprocess.TimeoutExpired: return f'colgouse (timeout {timeout}s)'
    except OSError as error: return f'erro ao executar: {error}'
    if result.returncode:
        detail = (result.stderr or result.stdout or '').strip()
        return f'devolveu {result.returncode}: {detail[:300]}'
    return ''

@lru_cache(maxsize=None)
def _mmdc_supports_pdf_fit(executable: str) -> bool:
    """mermaid-cli 12 retirou --pdfFit: o PDF axústase ao diagrama por defecto.
    Pregúntase á axuda unha vez por executable, para non lanzar Chromium nunha
    chamada que vai fallar. Se a axuda non responde, próbase coa opción."""
    try:
        result = subprocess.run([executable, '--help'], stdin=subprocess.DEVNULL,
                                capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return True
    return '--pdfFit' in (result.stdout + result.stderr)

@dataclass(frozen=True)
class MermaidRenderer:
    name: str='mermaid'; languages: tuple[str,...]=('mermaid',)
    executable_names: tuple[str,...]=('mmdc','mmdc.cmd','mmdc.exe')
    render_tag: str='v6'; font_px: float=16.0
    def missing_message(self, count):
        return f'{count} diagrama(s) mermaid pero `mmdc` non está instalado. Instala con: pacman -S mermaid-cli (Arch) ou npm install -g @mermaid-js/mermaid-cli'
    def render(self, executable, context, content, output_path):
        source = output_path.with_suffix('.mmd')
        mermaid_config = output_path.parent / f'{output_path.stem}-mermaid-config.json'
        config = context.cache_dir / 'puppeteer-config.json'
        if not config.exists():
            config.write_text('{"args":["--no-sandbox","--disable-setuid-sandbox"]}', encoding='utf-8')
        cfg = {
            'fontFamily': CSS_FONT,
            'fontSize': 16,
            'themeVariables': {
                'fontFamily': CSS_FONT,
                'fontSize': '16px',
            }
        }
        if 'theme' in context.options:
            cfg['theme'] = context.options['theme']
        if 'layout' in context.options:
            cfg['layout'] = context.options['layout']
        if 'look' in context.options:
            cfg['look'] = context.options['look']
        mermaid_config.write_text(json.dumps(cfg), encoding='utf-8')
        source.write_text(content, encoding='utf-8')
        command = [executable, '-i', str(source), '-o', str(output_path), '-b', 'transparent', '-q',
                   '--puppeteerConfigFile', str(config), '-c', str(mermaid_config)]
        if 'theme' in context.options:
            command.extend(['-t', context.options['theme']])
        if context.output_format == 'pdf' and _mmdc_supports_pdf_fit(executable):
            command.append('--pdfFit')
        try:
            env = {**os.environ, 'PUPPETEER_DISABLE_HEADLESS_WARNING': '1'}
            error = _run(command, context.timeout, env, cwd=context.source_dir)
            if error and '--pdfFit' in error and 'unknown option' in error:
                # Rede de seguridade se a axuda mentía ou non se puido ler.
                command.remove('--pdfFit')
                error = _run(command, context.timeout, env, cwd=context.source_dir)
            return f'mmdc {error}' if error else ''
        finally:
            source.unlink(missing_ok=True)
            mermaid_config.unlink(missing_ok=True)

@dataclass(frozen=True)
class D2Renderer:
    name: str='d2'; languages: tuple[str,...]=('d2',)
    executable_names: tuple[str,...]=('d2','d2.exe')
    render_tag: str='v2'; font_px: float=16.0
    def missing_message(self,count): return f'{count} diagrama(s) D2 pero `d2` non está instalado'
    def render(self, executable, context, content, output_path):
        if context.source_dir:
            with tempfile.NamedTemporaryFile(dir=context.source_dir,
                    prefix='.md2pdf-', suffix='.d2', delete=False) as temporary:
                source = Path(temporary.name)
        else:
            source = output_path.with_suffix('.d2')
        try:
            source.write_text(content, encoding='utf-8')
            command = [executable, '--theme=' + context.options.get('theme', '0')]
            if 'layout' in context.options:
                command.append('--layout=' + context.options['layout'])
            if context.options.get('sketch') in ('true', '1'):
                command.append('--sketch')
            if 'pad' in context.options:
                command.append('--pad=' + context.options['pad'])
            if 'dark-theme' in context.options:
                command.append('--dark-theme=' + context.options['dark-theme'])
            error=_run(command + [str(source),str(output_path)],context.timeout,
                       cwd=context.source_dir)
            return f'd2 {error}' if error else ''
        finally: source.unlink(missing_ok=True)

@dataclass(frozen=True)
class GraphvizRenderer:
    name: str='graphviz'; languages: tuple[str,...]=('dot','graphviz')
    executable_names: tuple[str,...]=('dot','dot.exe')
    render_tag: str='v5'; font_px: float=TARGET_FONT_PT
    def font_px_for(self, fmt):
        # -Nfontsize son PUNTOS. En PDF e PNG natural_size_px devolve px
        # (pt/0.75); no SVG de Graphviz o viewBox xa vai en pt, polo que alí
        # vale o valor tal cal. Renderízase xa ao tamaño final: a escala é 1
        # e as frechas e marxes non medran co texto.
        return self.font_px / 0.75 if fmt in ('pdf', 'png') else self.font_px
    def missing_message(self,count): return f'{count} diagrama(s) DOT pero `dot` non está instalado'
    def render(self, executable, context, content, output_path):
        source=output_path.with_suffix('.dot'); source.write_text(content,encoding='utf-8')
        try:
            command = [
                executable, f'-T{context.output_format}',
                '-Gmargin=0',
                f'-Gfontname={DOT_FONT}', f'-Nfontname={DOT_FONT}', f'-Efontname={DOT_FONT}',
                # Un só tamaño: a xerarquía, se fai falta, márcase con negra ou cor.
                *(f'-{kind}fontsize={TARGET_FONT_PT}' for kind in 'GNE')
            ]
            if 'layout' in context.options:
                command.append('-K' + context.options['layout'])
            error=_run(command + ['-o',str(output_path),str(source)],context.timeout,
                       cwd=context.source_dir)
            if error: return f'dot {error}'
            if context.output_format == 'pdf':
                crop = shutil.which('pdfcrop')
                if crop:
                    _run([crop, '--margins', '0 0 0 7', str(output_path), str(output_path)], context.timeout)
            return ''
        finally: source.unlink(missing_ok=True)

from .vegalite import VegaLiteRenderer

RENDERERS=(MermaidRenderer(),D2Renderer(),GraphvizRenderer(),VegaLiteRenderer())
