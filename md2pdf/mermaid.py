"""Compatibilidade coa API histórica de renderizado Mermaid."""
from .diagrams.processor import process_diagrams
from .diagrams.renderers import MermaidRenderer

def process_mermaid(text: str, engine: str) -> tuple[str, int, int, list[str]]:
    """Procesa Mermaid conservando a sinatura pública anterior."""
    processed, stats = process_diagrams(text, engine, (MermaidRenderer(),))
    return (processed, stats.new.get('mermaid', 0),
            stats.cached.get('mermaid', 0), stats.errors.get('mermaid', []))
