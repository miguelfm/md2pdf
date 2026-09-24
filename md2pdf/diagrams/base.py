from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

@dataclass(frozen=True)
class RenderContext:
    cache_dir: Path
    output_format: str
    timeout: int = 60
    options: dict[str, str] = field(default_factory=dict)
    source_dir: Path | None = None

class Renderer(Protocol):
    name: str
    languages: tuple[str, ...]
    executable_names: tuple[str, ...]
    render_tag: str
    font_px: float
    def missing_message(self, count: int) -> str: ...
    def render(self, executable: str, context: RenderContext,
               content: str, output_path: Path) -> str: ...
