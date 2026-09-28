"""
metadata.py — Extracción e carga de metadatos para os documentos.

Soporta dúas fontes de metadatos:
  1. YAML front matter do propio ficheiro .md
  2. Ficheiro YAML externo (metadata.yaml, u3-metadata.yaml…) no mesmo directorio
"""

import re
from pathlib import Path


def _extract_md_metadata(text: str) -> dict[str, str]:
    """
    Extrae metadatos do YAML front matter dun ficheiro Markdown.

    Claves recoñecidas: title, author, keywords, subject, activity,
                        module, course, school, subtitle (alias de activity),
                        decimal-align, serif, body-font, font-body.
    """
    meta: dict[str, str] = {}
    m = re.match(r'^---\s*\n(.*?)\n(?:---|\.\.\.)\s*\n', text, re.DOTALL)
    if not m:
        return meta

    yaml_block = m.group(1)
    for key in ('title', 'author', 'keywords', 'subject', 'activity',
                'module', 'course', 'school', 'subtitle', 'decimal-align',
                'serif', 'body-font', 'font-body', 'inline-pill',
                'terminal-blocks', 'terminal-style'):
        km = re.search(rf'^{key}:\s*(.+)$', yaml_block,
                       re.MULTILINE | re.IGNORECASE)
        if km:
            val = km.group(1).strip().strip('\'"')
            if val:
                meta[key] = val

    # subtitle é alias de activity
    if 'activity' not in meta and 'subtitle' in meta:
        meta['activity'] = meta.pop('subtitle')

    return meta


def _find_metadata_file(md_path: Path) -> Path | None:
    """
    Busca un ficheiro de metadatos YAML no directorio do ficheiro .md.

    Orde de prioridade:
      1. <prefixo-unidade>-metadata.yaml  (ex: u3-metadata.yaml para U3A*.md)
      2. metadata.yaml / metadata.yml xenérico

    Devolve a ruta ao primeiro que exista, ou None.
    """
    search_dir = md_path.parent

    # Ficheiro específico de unidade: u3-metadata.yaml, u4-metadata.yml…
    m = re.match(r'^(u\d+)', md_path.stem, re.IGNORECASE)
    if m:
        prefix = m.group(1).lower()
        for ext in ('yaml', 'yml'):
            candidate = search_dir / f'{prefix}-metadata.{ext}'
            if candidate.exists():
                return candidate

    # Ficheiro xenérico
    for ext in ('yaml', 'yml'):
        candidate = search_dir / f'metadata.{ext}'
        if candidate.exists():
            return candidate

    return None


def _load_metadata_file(path: Path) -> dict[str, str]:
    """Le un ficheiro YAML de metadatos sinxelo (clave: valor sen anidamento)."""
    meta: dict[str, str] = {}
    # utf-8-sig le igual un ficheiro con BOM ou sen el, e elimina a marca
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' in line:
            key, _, val = line.partition(':')
            meta[key.strip()] = val.strip().strip("'\"")
    return meta
