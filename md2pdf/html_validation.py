"""Validación estrutural e de accesibilidade básica da saída HTML de md2pdf."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote


class _HTMLValidator(HTMLParser):
    """Recolle destinos, ligazóns internas e problemas básicos de accesibilidade."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.duplicates: set[str] = set()
        self.internal_links: list[str] = []
        self.labelledby: list[str] = []
        self.missing_alt: list[int] = []
        self.broken_crossrefs: list[str] = []
        self.svg_without_name: list[int] = []
        self.image_count = 0
        self.svg_count = 0

    def _handle_tag(self, tag: str, attrs_list: list[tuple[str, str | None]]) -> None:
        attrs = {key: (value or '') for key, value in attrs_list}

        identifier = attrs.get('id', '').strip()
        if identifier:
            if identifier in self.ids:
                self.duplicates.add(identifier)
            self.ids.add(identifier)

        href = attrs.get('href', '').strip()
        if href.startswith('#') and len(href) > 1:
            self.internal_links.append(unquote(href[1:]))

        labelledby = attrs.get('aria-labelledby', '').strip()
        if labelledby:
            self.labelledby.extend(labelledby.split())

        classes = set(attrs.get('class', '').split())
        if 'broken-crossref' in classes:
            ref = attrs.get('data-ref', '').strip()
            self.broken_crossrefs.append(ref or '(descoñecida)')

        if tag.lower() == 'img':
            self.image_count += 1
            decorative = (
                'decorative' in classes
                or attrs.get('aria-hidden', '').lower() == 'true'
                or attrs.get('role', '').lower() in {'none', 'presentation'}
            )
            if not decorative and not attrs.get('alt', '').strip():
                self.missing_alt.append(self.image_count)

        if tag.lower() == 'svg' and attrs.get('role', '').lower() == 'img':
            self.svg_count += 1
            if not (attrs.get('aria-label', '').strip() or labelledby):
                self.svg_without_name.append(self.svg_count)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._handle_tag(tag, attrs)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._handle_tag(tag, attrs)


def validate_html(path: Path | str) -> list[str]:
    """Devolve avisos para unha saída HTML xa xerada.

    Compróbanse destinos internos, IDs duplicados, referencias ARIA e imaxes
    informativas sen texto alternativo. Unha imaxe decorativa pode marcarse con
    ``{.decorative}``, ``aria-hidden=true`` ou ``role=presentation``.
    """
    source = Path(path).read_text(encoding='utf-8', errors='replace')
    parser = _HTMLValidator()
    parser.feed(source)
    parser.close()

    issues: list[str] = []

    for identifier in sorted(parser.duplicates):
        issues.append(f'identificador HTML duplicado: #{identifier}')

    for ref in sorted(set(parser.broken_crossrefs)):
        issues.append(f'referencia cruzada sen destino: @{ref}')

    missing_targets = sorted({target for target in parser.internal_links
                              if target not in parser.ids})
    for target in missing_targets:
        issues.append(f'ligazón interna rota: #{target}')

    missing_labels = sorted({target for target in parser.labelledby
                             if target not in parser.ids})
    for target in missing_labels:
        issues.append(f'aria-labelledby apunta a un ID inexistente: #{target}')

    for number in parser.missing_alt:
        issues.append(
            f'imaxe #{number} sen texto alternativo; usa un texto entre [] '
            f'ou marca a imaxe como decorativa con {{.decorative}}'
        )

    for number in parser.svg_without_name:
        issues.append(
            f'SVG informativo #{number} sen nome accesible '
            f'(aria-label ou aria-labelledby)'
        )

    return issues
