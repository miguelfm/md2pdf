"""Configuración opcional de diagramas; PyYAML só se require ao usala."""
import re

def load_diagram_defaults(text, metadata_file=None):
    sources = []
    if metadata_file:
        sources.append(metadata_file.read_text(encoding='utf-8-sig'))
    match = re.match(r'^---[ \t]*\r?\n(.*?)\r?\n(?:---|\.\.\.)[ \t]*(?:\r?\n|$)',
                     text, re.DOTALL)
    if match:
        sources.append(match.group(1))
    defaults = {}
    for source in sources:
        if not re.search(r'^diagrams\s*:', source, re.MULTILINE):
            continue
        try:
            import yaml
        except ImportError as error:
            raise ValueError('Os metadatos diagrams requiren PyYAML: python -m pip install PyYAML') from error
        try:
            document = yaml.safe_load(source)
        except yaml.YAMLError as error:
            raise ValueError(f'YAML de diagramas incorrecto: {error}') from error
        if not isinstance(document, dict):
            raise ValueError('Os metadatos deben ser un mapa YAML')
        config = document.get('diagrams', {})
        if not isinstance(config, dict):
            raise ValueError('diagrams debe ser un mapa YAML')
        for name, options in config.items():
            if name not in {'mermaid', 'd2', 'graphviz', 'dot', 'vega-lite', 'vegalite'} or not isinstance(options, dict):
                raise ValueError(f'Configuración de diagramas incorrecta: {name}')
            name = 'graphviz' if name == 'dot' else name
            name = 'vega-lite' if name == 'vegalite' else name
            defaults[name] = {**defaults.get(name, {}), **options}
    return defaults
