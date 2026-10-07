"""Adaptadores dos CLI Mermaid, D2 e Graphviz."""
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from .base import RenderContext

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

@dataclass(frozen=True)
class MermaidRenderer:
    name: str='mermaid'; languages: tuple[str,...]=('mermaid',)
    executable_names: tuple[str,...]=('mmdc','mmdc.cmd','mmdc.exe')
    render_tag: str='v4'; font_px: float=16.0
    def missing_message(self, count):
        return f'{count} diagrama(s) mermaid pero `mmdc` non está instalado. Instala con: pacman -S mermaid-cli (Arch) ou npm install -g @mermaid-js/mermaid-cli'
    def render(self, executable, context, content, output_path):
        source, config = output_path.with_suffix('.mmd'), context.cache_dir/'puppeteer-config.json'
        if not config.exists(): config.write_text('{"args":["--no-sandbox","--disable-setuid-sandbox"]}', encoding='utf-8')
        source.write_text(content, encoding='utf-8')
        command=[executable,'-i',str(source),'-o',str(output_path),'-b','transparent','-q','--puppeteerConfigFile',str(config)]
        if context.output_format == 'pdf': command.append('--pdfFit')
        try:
            error=_run(command, context.timeout, {**os.environ,'PUPPETEER_DISABLE_HEADLESS_WARNING':'1'}, cwd=context.source_dir)
            # CLI <=11 needs --pdfFit; CLI 12 fits PDFs by default and
            # rejects that option. Retry only this specific option error.
            if (context.output_format == 'pdf' and
                    "unknown option '--pdfFit'" in error):
                error=_run(command[:-1], context.timeout,
                    {**os.environ,'PUPPETEER_DISABLE_HEADLESS_WARNING':'1'},
                    cwd=context.source_dir)
            return f'mmdc {error}' if error else ''
        finally: source.unlink(missing_ok=True)

@dataclass(frozen=True)
class D2Renderer:
    name: str='d2'; languages: tuple[str,...]=('d2',)
    executable_names: tuple[str,...]=('d2','d2.exe')
    render_tag: str='v1'; font_px: float=16.0
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
            error=_run(command + [str(source),str(output_path)],context.timeout,
                       cwd=context.source_dir)
            return f'd2 {error}' if error else ''
        finally: source.unlink(missing_ok=True)

@dataclass(frozen=True)
class GraphvizRenderer:
    name: str='graphviz'; languages: tuple[str,...]=('dot','graphviz')
    executable_names: tuple[str,...]=('dot','dot.exe')
    render_tag: str='v3'; font_px: float=10.0
    def font_px_for(self, fmt):
        # -Nfontsize=10 son PUNTOS. En PDF e PNG natural_size_px devolve px
        # (pt/0.75), así que a fonte equivalente son 13,33 px; no SVG de
        # Graphviz o viewBox xa vai en pt, polo que alí vale o valor tal cal.
        return self.font_px / 0.75 if fmt in ('pdf', 'png') else self.font_px
    def missing_message(self,count): return f'{count} diagrama(s) DOT pero `dot` non está instalado'
    def render(self, executable, context, content, output_path):
        source=output_path.with_suffix('.dot'); source.write_text(content,encoding='utf-8')
        try:
            command = [
                executable, f'-T{context.output_format}',
                '-Gmargin=0',
                '-Gfontname=sans-serif', '-Nfontname=sans-serif', '-Efontname=sans-serif',
                '-Gfontsize=11', '-Nfontsize=10', '-Efontsize=9'
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
