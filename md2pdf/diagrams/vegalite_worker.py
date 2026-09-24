"""Worker interno. Non avalía código Python achegado polo documento."""
import json
import sys
from pathlib import Path


def main():
    import vl_convert as vlc
    source, output, fmt = sys.argv[1:]
    spec = json.loads(Path(source).read_text(encoding='utf-8'))
    converter = {
        'svg': vlc.vegalite_to_svg,
        'pdf': vlc.vegalite_to_pdf,
        'png': vlc.vegalite_to_png,
    }[fmt]
    # Lista baleira: ningunha orixe externa permitida.
    result = converter(spec, allowed_base_urls=[])
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

