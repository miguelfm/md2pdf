"""Worker interno. Non avalía código Python achegado polo documento."""
import json
import sys
from pathlib import Path


def main():
    import vl_convert as vlc
    args = sys.argv[1:]
    positional = []
    options = {}
    for arg in args:
        if arg.startswith('--theme='):
            options['theme'] = arg.split('=', 1)[1]
        elif not arg.startswith('--'):
            positional.append(arg)
    source, output, fmt = positional
    spec = json.loads(Path(source).read_text(encoding='utf-8'))
    converter = {
        'svg': vlc.vegalite_to_svg,
        'pdf': vlc.vegalite_to_pdf,
        'png': vlc.vegalite_to_png,
    }[fmt]
    # Lista baleira: ningunha orixe externa permitida.
    kwargs = {
        'allowed_base_urls': [],
        'config': {'font': 'Source Sans 3, sans-serif'},
    }
    theme = options.get('theme')
    if theme and theme not in ('default', 'none'):
        kwargs['theme'] = theme
    result = converter(spec, **kwargs)
    if isinstance(result, str):
        Path(output).write_text(result, encoding='utf-8')
    else:
        Path(output).write_bytes(result)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)

