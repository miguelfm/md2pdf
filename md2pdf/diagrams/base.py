"""Definicións base e protocolo de renderizadores de diagramas."""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class RenderContext:
    """Contexto de execución para a xeración dun diagrama."""
    cache_dir: Path
    output_format: str
    timeout: int = 60
    options: dict[str, str] = field(default_factory=dict)
    source_dir: Path | None = None


class Renderer(Protocol):
    """Protocolo formal para calquera motor de renderizado de diagramas."""
    name: str
    languages: tuple[str, ...]
    executable_names: tuple[str, ...]
    render_tag: str
    font_px: float
    boolean_flags: frozenset[str]
    allowed_options: frozenset[str]
    render_option_keys: frozenset[str]

    def missing_message(self, count: int) -> str: ...
    def cache_tag(self) -> str: ...
    def find_executable(self) -> str | None: ...
    def font_px_for(self, fmt: str) -> float: ...
    def validate_option(self, key: str, value: Any) -> str: ...
    def filter_render_options(self, options: dict[str, str]) -> dict[str, str]: ...
    def render(self, executable: str, context: RenderContext,
               content: str, output_path: Path) -> str: ...


@dataclass(frozen=True)
class BaseRenderer:
    """Clase base con comportamentos predeterminados para renderizadores."""
    name: str = ''
    languages: tuple[str, ...] = ()
    executable_names: tuple[str, ...] = ()
    render_tag: str = 'v1'
    font_px: float = 16.0
    boolean_flags: frozenset[str] = field(default_factory=frozenset)
    allowed_options: frozenset[str] = field(default_factory=frozenset)
    render_option_keys: frozenset[str] = field(default_factory=frozenset)

    def missing_message(self, count: int) -> str:
        word = 'diagrama' if count == 1 else 'diagramas'
        return f'{count} {word} {self.name} pero non está instalado'

    def cache_tag(self) -> str:
        return self.render_tag

    def find_executable(self, which_fn=None) -> str | None:
        fn = which_fn or shutil.which
        for name in self.executable_names:
            found = fn(name)
            if found:
                return found
        return None

    def font_px_for(self, fmt: str) -> float:
        return self.font_px

    def validate_option(self, key: str, value: Any) -> str:
        """Valida e normaliza unha opción específica deste renderizador.

        Lanza ValueError se a opción ou valor non son válidos.
        """
        raise ValueError(f'opción non admitida para {self.name}: {key}')

    def filter_render_options(self, options: dict[str, str]) -> dict[str, str]:
        """Extrae só as opcións que afectan ao renderizado e polo tanto á chave de caché."""
        return {k: v for k, v in options.items() if k in self.render_option_keys}
