"""Adaptador opcional vl-convert-python; conversión illada cun timeout."""
import importlib.util
import importlib.metadata
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VegaLiteRenderer:
    name: str = 'vega-lite'
    languages: tuple[str, ...] = ('vega-lite', 'vegalite')
    executable_names: tuple[str, ...] = ()
    render_tag: str = 'v1-inline'
    font_px: float = 10.0

    def find_executable(self):
        return sys.executable if importlib.util.find_spec('vl_convert') else None

    def cache_tag(self):
        try:
            return self.render_tag + ':' + importlib.metadata.version('vl-convert-python')
        except importlib.metadata.PackageNotFoundError:
            return self.render_tag

    def missing_message(self, count):
        return (f'{count} gráfico(s) Vega-Lite pero falta vl-convert-python. '
                'Instala no Python de md2pdf: python -m pip install '
                '"vl-convert-python>=1.7,<2"')

    def render(self, executable, context, content, output_path):
        try:
            spec = json.loads(content)
            validate_spec(spec)
        except (ValueError, RecursionError) as error:
            return f'Vega-Lite: {error}'
        source = output_path.with_suffix('.vl.json')
        try:
            source.write_text(json.dumps(spec, ensure_ascii=False), encoding='utf-8')
            worker = Path(__file__).with_name('vegalite_worker.py')
            result = subprocess.run(
                [executable, str(worker), str(source), str(output_path),
                 context.output_format],
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

