"""Empaquetado IMS Content Package 1.1.4 para publicar HTML de md2pdf en Moodle.

O empaquetador non é un motor de renderizado novo: reutiliza ``engine='html'``
para cada Markdown, xera ``imsmanifest.xml`` e crea un ZIP autocontido.
"""

from __future__ import annotations

import hashlib
import html as html_lib
import os
import re
import tempfile
import unicodedata
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, replace
from pathlib import Path

from .converter import convert_one
from .metadata import _extract_md_metadata, _find_metadata_file, _load_metadata_file


IMS_NS = 'http://www.imsglobal.org/xsd/imscp_v1p1'
XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'
SCHEMA_LOCATION = (
    'http://www.imsglobal.org/xsd/imscp_v1p1 '
    'http://www.imsglobal.org/xsd/imscp_v1p1.xsd'
)

# Os ficheiros locais enlazados (ZIP de partida, PDF, código...) cópianse aquí
# dentro do paquete; os HTML van na raíz.
ASSET_DIR = 'recursos'

ET.register_namespace('', IMS_NS)
ET.register_namespace('xsi', XSI_NS)


@dataclass(frozen=True)
class ImsItem:
    source: Path
    html_name: str
    title: str
    files: tuple[str, ...] = ()   # recursos do paquete que usa este HTML


def _q(tag: str) -> str:
    return f'{{{IMS_NS}}}{tag}'


def _first_h1(text: str) -> str | None:
    """Obtén o primeiro H1 ATX fóra de bloques fenced."""
    in_fence = False
    fence_char = ''
    fence_len = 0
    for line in text.splitlines():
        fm = re.match(r'^\s*(`{3,}|~{3,})', line)
        if fm:
            marker = fm.group(1)
            if not in_fence:
                in_fence = True
                fence_char = marker[0]
                fence_len = len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_len:
                in_fence = False
            continue
        if in_fence:
            continue
        m = re.match(r'^#(?!#)\s+(.+?)\s*$', line)
        if m:
            title = re.sub(r'\s+\{[^}]*\}\s*$', '', m.group(1)).strip()
            return title or None
    return None


def _item_title(path: Path, no_metadata: bool = False) -> str:
    """Título curto para a navegación IMS.

    Prioridade: ``activity`` → ``title`` → primeiro H1 → nome do ficheiro.
    Isto encaixa cos materiais docentes de md2pdf, onde ``activity`` adoita ser
    a etiqueta máis compacta para un menú de navegación.
    """
    text = path.read_text(encoding='utf-8-sig')
    meta: dict[str, str] = {}
    if not no_metadata:
        fm = _extract_md_metadata(text)
        meta_file = _find_metadata_file(path)
        if meta_file:
            meta = {**_load_metadata_file(meta_file), **fm}
        else:
            meta = fm

    return (meta.get('activity') or meta.get('title') or _first_h1(text)
            or path.stem)


def _slug(stem: str) -> str:
    normalized = unicodedata.normalize('NFKD', stem)
    ascii_name = normalized.encode('ascii', 'ignore').decode('ascii')
    slug = re.sub(r'[^A-Za-z0-9._-]+', '_', ascii_name).strip('._-')
    return slug or 'documento'


def _build_items(files: list[Path], no_metadata: bool = False) -> list[ImsItem]:
    used: set[str] = set()
    items: list[ImsItem] = []
    for source in files:
        base = _slug(source.stem)
        candidate = f'{base}.html'
        counter = 2
        while candidate.lower() in used:
            candidate = f'{base}-{counter}.html'
            counter += 1
        used.add(candidate.lower())
        items.append(ImsItem(
            source=source.resolve(),
            html_name=candidate,
            title=_item_title(source, no_metadata=no_metadata),
        ))
    return items


def build_manifest(items: list[ImsItem], package_title: str) -> bytes:
    """Constrúe un ``imsmanifest.xml`` IMS Content Packaging 1.1.4."""
    digest = hashlib.sha1(
        ('|'.join(item.html_name for item in items) + '|' + package_title)
        .encode('utf-8')
    ).hexdigest()[:12].upper()

    manifest = ET.Element(_q('manifest'), {
        'identifier': f'MANIFEST-{digest}',
        'version': '1EdTech CP 1.1.4',
        f'{{{XSI_NS}}}schemaLocation': SCHEMA_LOCATION,
    })

    metadata = ET.SubElement(manifest, _q('metadata'))
    ET.SubElement(metadata, _q('schema')).text = 'IMS Content'
    ET.SubElement(metadata, _q('schemaversion')).text = '1.1.4'

    org_id = f'ORG-{digest}'
    organizations = ET.SubElement(manifest, _q('organizations'), {
        'default': org_id,
    })
    organization = ET.SubElement(organizations, _q('organization'), {
        'identifier': org_id,
    })
    ET.SubElement(organization, _q('title')).text = package_title

    resources = ET.SubElement(manifest, _q('resources'))

    for index, item in enumerate(items, 1):
        item_id = f'ITEM-{index:04d}'
        resource_id = f'RES-{index:04d}'

        node = ET.SubElement(organization, _q('item'), {
            'identifier': item_id,
            'identifierref': resource_id,
        })
        ET.SubElement(node, _q('title')).text = item.title

        resource = ET.SubElement(resources, _q('resource'), {
            'identifier': resource_id,
            'type': 'webcontent',
            'href': item.html_name,
        })
        ET.SubElement(resource, _q('file'), {'href': item.html_name})
        for href in item.files:
            ET.SubElement(resource, _q('file'), {'href': href})

    if hasattr(ET, 'indent'):
        ET.indent(manifest, space='  ')
    return ET.tostring(manifest, encoding='utf-8', xml_declaration=True)


_HREF_RE = re.compile(r'href=(?P<q>["\'])(?P<value>.*?)(?P=q)', re.IGNORECASE)


def _asset_name(target: Path, assets: dict[Path, str]) -> str:
    """Nome estable e único dentro do paquete para un ficheiro local enlazado."""
    if target in assets:
        return assets[target]
    taken = {name.lower() for name in assets.values()}
    stem, suffix = _slug(target.stem), target.suffix.lower()
    candidate = f'{ASSET_DIR}/{stem}{suffix}'
    counter = 2
    while candidate.lower() in taken:
        candidate = f'{ASSET_DIR}/{stem}-{counter}{suffix}'
        counter += 1
    assets[target] = candidate
    return candidate


def _rewrite_markdown_links(
    html_text: str,
    source: Path,
    source_to_html: dict[Path, str],
    assets: dict[Path, str] | None = None,
    used_assets: set[str] | None = None,
) -> tuple[str, list[str]]:
    """Reescribe as ligazóns locais para que funcionen dentro do paquete.

    - ``.md`` incluídos no paquete → o seu HTML.
    - ``.md`` fóra do paquete → aviso (``--strict`` rexéitao).
    - Outros ficheiros locais (se se pasa ``assets``) → cópianse en
      ``recursos/`` e a ligazón apunta alí; se non existen, aviso.
      Sen isto, Moodle publicaría ligazóns rotas a ficheiros que non van no ZIP.
    """
    warnings: list[str] = []

    def replace(match: re.Match[str]) -> str:
        quote_char = match.group('q')
        raw = html_lib.unescape(match.group('value'))
        parsed = urllib.parse.urlsplit(raw)
        if parsed.scheme or parsed.netloc or raw.startswith('#'):
            return match.group(0)

        decoded_path = urllib.parse.unquote(parsed.path)
        if not decoded_path:
            return match.group(0)
        is_markdown = decoded_path.lower().endswith('.md')
        if not is_markdown and assets is None:
            return match.group(0)

        try:
            target = (source.parent / decoded_path).resolve()
        except OSError:
            return match.group(0)

        if not is_markdown:
            if not target.is_file():
                warning = f'{source.name}: ligazón local a un ficheiro inexistente: {raw}'
                if warning not in warnings:
                    warnings.append(warning)
                return match.group(0)
            package_name = _asset_name(target, assets)
            if used_assets is not None:
                used_assets.add(package_name)
            new_url = urllib.parse.urlunsplit((
                '', '', urllib.parse.quote(package_name), parsed.query, parsed.fragment,
            ))
            return f'href={quote_char}{html_lib.escape(new_url, quote=True)}{quote_char}'

        html_name = source_to_html.get(target)
        if html_name is None:
            warning = f'{source.name}: ligazón a Markdown fóra do paquete: {raw}'
            if warning not in warnings:
                warnings.append(warning)
            return match.group(0)

        new_url = urllib.parse.urlunsplit((
            '', '', urllib.parse.quote(html_name), parsed.query, parsed.fragment,
        ))
        escaped = html_lib.escape(new_url, quote=True)
        return f'href={quote_char}{escaped}{quote_char}'

    return _HREF_RE.sub(replace, html_text), warnings


def build_ims_package(
    files: list[Path],
    output_path: Path,
    template: Path,
    *,
    package_title: str | None = None,
    toc: bool = True,
    toc_depth: int = 3,
    section_numbering: str = '1.1.',
    lang: str = 'gl',
    highlight: str = 'auto',
    callouts: bool = True,
    no_metadata: bool = False,
    print_mode: bool = False,
    night_mode: bool = False,
    plain: bool = False,
    strict: bool = False,
    debug: bool = False,
) -> bool:
    """Xera un ZIP IMS con un HTML autocontido por cada Markdown.

    A operación é atómica: se falla calquera conversión, non se publica o ZIP.
    """
    if not files:
        return False

    output_path = output_path.expanduser()
    if output_path.suffix.lower() != '.zip':
        output_path = output_path.with_suffix('.zip')
    output_path.parent.mkdir(parents=True, exist_ok=True)

    title = package_title or output_path.stem
    items = _build_items(files, no_metadata=no_metadata)
    source_to_html = {item.source: item.html_name for item in items}

    print(f'  📦 IMS: {len(items)} documento(s) → {output_path.name}')

    with tempfile.TemporaryDirectory(prefix='md2pdf-ims-') as tmpdir:
        tmpdir_path = Path(tmpdir)
        warnings: list[str] = []
        assets: dict[Path, str] = {}
        item_files: dict[str, tuple[str, ...]] = {}

        for item in items:
            html_path = tmpdir_path / item.html_name
            ok = convert_one(
                input_path=item.source,
                output_path=html_path,
                template=template,
                engine='html',
                toc=toc,
                toc_depth=toc_depth,
                section_numbering=section_numbering,
                lang=lang,
                highlight=highlight,
                listings=False,
                titlepage=False,
                callouts=callouts,
                no_metadata=no_metadata,
                print_mode=print_mode,
                night_mode=night_mode,
                plain=plain,
                strict=strict,
                debug=debug,
            )
            if not ok:
                print(f'  ✗ IMS non xerado: fallou {item.source.name}.')
                return False

            html_text = html_path.read_text(encoding='utf-8')
            used_assets: set[str] = set()
            html_text, link_warnings = _rewrite_markdown_links(
                html_text, item.source, source_to_html, assets, used_assets,
            )
            item_files[item.html_name] = tuple(sorted(used_assets))
            warnings.extend(link_warnings)
            html_path.write_text(html_text, encoding='utf-8')

        if warnings:
            for warning in warnings:
                print(f'    ⚠  IMS: {warning}')
            if strict:
                print('  ✗ IMS non xerado: hai ligazóns locais a Markdown '
                      'fóra do paquete ou a ficheiros inexistentes (--strict).')
                return False

        items = [replace(item, files=item_files.get(item.html_name, ()))
                 for item in items]
        if assets:
            print(f'    📎 IMS: {len(assets)} recurso(s) enlazado(s) incluído(s) en {ASSET_DIR}/')
        manifest = build_manifest(items, title)
        (tmpdir_path / 'imsmanifest.xml').write_bytes(manifest)

        tmp_zip = tempfile.NamedTemporaryFile(
            prefix='.md2pdf-ims-', suffix='.zip',
            dir=output_path.parent, delete=False,
        )
        tmp_zip_path = Path(tmp_zip.name)
        tmp_zip.close()
        try:
            with zipfile.ZipFile(
                tmp_zip_path, 'w', compression=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            ) as archive:
                archive.write(tmpdir_path / 'imsmanifest.xml', 'imsmanifest.xml')
                for item in items:
                    archive.write(tmpdir_path / item.html_name, item.html_name)
                for target, package_name in assets.items():
                    archive.write(target, package_name)
            os.replace(tmp_zip_path, output_path)
        finally:
            try:
                tmp_zip_path.unlink(missing_ok=True)
            except OSError:
                pass

    size = output_path.stat().st_size
    if size < 1024:
        size_label = f'{size} B'
    elif size < 1024 * 1024:
        size_label = f'{size / 1024:.0f} KB'
    else:
        size_label = f'{size / (1024 * 1024):.1f} MB'
    print(f'  ✓ Paquete IMS xerado: {output_path} ({size_label})')
    return True
