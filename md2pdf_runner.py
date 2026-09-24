#!/usr/bin/env python3
"""
md2pdf_runner.py — Wrapper de entrada para instalacións en Linux/Windows.

O instalador copia este ficheiro a ~/.local/bin/md2pdf (Linux)
ou crea un .bat equivalente (Windows).

Engade INSTALL_DIR ao sys.path para que o paquete md2pdf/ sexa importable,
independentemente de se está instalado como paquete do sistema ou non.
"""

import sys
from pathlib import Path

# INSTALL_DIR determinado polo instalador en tempo de instalación.
# O wrapper está en ~/.local/bin/md2pdf; o paquete en ~/.local/share/md2pdf/
_BIN_DIR     = Path(__file__).resolve().parent           # ~/.local/bin
_INSTALL_DIR = _BIN_DIR.parent / 'share' / 'md2pdf'     # ~/.local/share/md2pdf

if _INSTALL_DIR.exists():
    sys.path.insert(0, str(_INSTALL_DIR))
else:
    # Fallback: directorio do propio wrapper (útil en desenvolvemento)
    sys.path.insert(0, str(_BIN_DIR))

from md2pdf.__main__ import main  # noqa: E402

if __name__ == '__main__':
    main()
