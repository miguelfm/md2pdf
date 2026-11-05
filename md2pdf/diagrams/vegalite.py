"""Adaptador opcional vl-convert-python; conversión illada cun timeout."""
from __future__ import annotations

import importlib.metadata
import importlib.util
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .base import BaseRenderer, RenderContext

VEGA_THEMES = frozenset({
    'carbong10', 'carbong100', 'carbong90', 'carbonwhite',
    'dark', 'excel', 'fivethirtyeight', 'ggplot2', 'googlecharts',
    'latimes', 'powerbi', 'quartz', 'urbaninstitute', 'vox',
    'default', 'none',
})


@dataclass(frozen=True)
class VegaLiteRenderer(BaseRenderer):
    name: str = 'vega-lite'
    languages: tuple[str, ...] = ('vega-lite', 'vegalite')
    executable_names: tuple[str, ...] = ()
    # v3: a fonte por defecto vai entre aspas (vegalite_worker.py); as
    # gráficas da caché anterior estaban en Times New Roman.
    render_tag: str = 'v3-inline'
    font_px: float = 10.0
    boolean_flags: frozenset[str] = field(default_factory=frozenset)
    allowed_options: frozenset[str] = field(default_factory=lambda: frozenset({'theme'}))
    render_option_keys: frozenset[str] = field(default_factory=lambda: frozenset({'theme'}))

    def find_executable(self, which_fn=None) -> str | None:
        return sys.executable if importlib.util.find_spec('vl_convert') else None

    def cache_tag(self) -> str:
        try:
            return self.render_tag + ':' + importlib.metadata.version('vl-convert-python')
        except importlib.metadata.PackageNotFoundError:
            return self.render_tag

    def missing_message(self, count: int) -> str:
        return (f'{count} gráfico(s) Vega-Lite pero falta vl-convert-python. '
                'Instala no Python de md2pdf: python -m pip install '
                '"vl-convert-python>=1.7,<2"')

    def validate_option(self, key: str, value: Any) -> str:
        if key not in self.allowed_options:
            raise ValueError(f'opción non admitida para {self.name}: {key}')
        if not isinstance(value, (str, int, float)) or isinstance(value, bool):
            raise ValueError(f'valor incorrecto de {key}')
        val = str(value)
        if key == 'theme' and val not in VEGA_THEMES:
            raise ValueError(f'tema de Vega-Lite non admitido: {val}')
        return val

    def render(self, executable: str, context: RenderContext,
               content: str, output_path: Path) -> str:
        try:
            spec = json.loads(content)
            validate_spec(spec)
        except (ValueError, RecursionError) as error:
            return f'Vega-Lite: {error}'
        source = output_path.with_suffix('.vl.json')
        try:
            source.write_text(json.dumps(spec, ensure_ascii=False), encoding='utf-8')
            worker = Path(__file__).with_name('vegalite_worker.py')
            command = [executable, str(worker), str(source), str(output_path),
                       context.output_format]
            if 'theme' in context.options:
                command.append('--theme=' + context.options['theme'])
            result = subprocess.run(
                command,
                stdin=subprocess.DEVNULL, capture_output=True, text=True,
                timeout=context.timeout, cwd=context.source_dir)
            if result.returncode:
                return 'Vega-Lite: ' + (result.stderr or result.stdout).strip()[:500]
            return ''
        except subprocess.TimeoutExpired:
            return f'Vega-Lite: timeout de {context.timeout}s'
        except OSError as error:
            return f'Vega-Lite: {error}'
        finally:
            source.unlink(missing_ok=True)


def validate_spec(spec):
    if not isinstance(spec, dict):
        raise ValueError('a especificación debe ser un obxecto JSON')
    # Primeira versión deliberadamente autocontida: evita I/O externo.
    # $schema é unha etiqueta; non se descarga.
    def visit(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {'url', 'href'}:
                    raise ValueError('usa datos inline (data.values/datasets); '
                                     'url e href non están admitidos')
                if key == 'mark' and (child == 'image' or
                        isinstance(child, dict) and child.get('type') == 'image'):
                    raise ValueError('as marcas image non están admitidas')
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(spec)

