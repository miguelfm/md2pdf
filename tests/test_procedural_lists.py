"""tests/test_procedural_lists.py — Probas para listas procedementais («Paso a paso»)."""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('lualatex'), 'lualatex non instalado')
class ProceduralListsPdfTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _convert(self, md_content: str, extra_args: list[str] | None = None) -> Path:
        md_file = self.dir_path / 'doc.md'
        pdf_file = self.dir_path / 'doc.pdf'
        md_file.write_text(md_content, encoding='utf-8')
        cmd = ['python3', '-m', 'md2pdf', str(md_file), '-o', str(pdf_file)]
        if extra_args:
            cmd.extend(extra_args)
        res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"STDOUT: {res.stdout}\nSTDERR: {res.stderr}")
        self.assertTrue(pdf_file.exists())
        return pdf_file

    def test_numbers_bold_and_colored_in_pdf(self):
        md = """---
activity: "P1"
---

# Guía de pasos

1. Primeiro paso procedemental.
2. Segundo paso procedemental.
"""
        pdf = self._convert(md)
        doc = pymupdf.open(pdf)
        page = doc[1]  # páxina de contido (páxina 0 é portada/TOC)
        found_markers = {}
        for b in page.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                for s in l.get("spans", []):
                    t = s["text"].strip()
                    if t in ("1.", "2."):
                        found_markers[t] = (s["font"], hex(s["color"]))

        self.assertIn("1.", found_markers)
        self.assertIn("2.", found_markers)
        self.assertIn("Bold", found_markers["1."][0])
        self.assertEqual(found_markers["1."][1], "0x1c2f4a")
        self.assertIn("Bold", found_markers["2."][0])
        self.assertEqual(found_markers["2."][1], "0x1c2f4a")

    def test_vertical_spacing_greater_between_numbered_steps(self):
        md = """---
activity: "P2"
---

# Guía con pasos longos

1. Primeiro paso con texto longo suficiente para ocupar dúas liñas na páxina e poder medir a distancia entre liñas do mesmo paso.
2. Segundo paso que segue ao anterior.

- Elemento bullet A
- Elemento bullet B
"""
        pdf = self._convert(md)
        doc = pymupdf.open(pdf)
        page = doc[1]
        lines = []
        for b in page.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                t = "".join(s["text"] for s in l.get("spans", [])).strip()
                if t:
                    lines.append((l["bbox"][1], t))

        # Atopar liñas de paso 1 e paso 2
        y_item1_l1 = None
        y_item1_l2 = None
        y_item2_l1 = None
        y_bullet_a = None
        y_bullet_b = None

        for y, t in lines:
            if t.startswith("1. Primeiro paso"):
                y_item1_l1 = y
            elif "mesmo paso" in t:
                y_item1_l2 = y
            elif t.startswith("2. Segundo paso"):
                y_item2_l1 = y
            elif "Elemento bullet A" in t:
                y_bullet_a = y
            elif "Elemento bullet B" in t:
                y_bullet_b = y

        self.assertIsNotNone(y_item1_l1)
        self.assertIsNotNone(y_item1_l2)
        self.assertIsNotNone(y_item2_l1)
        self.assertIsNotNone(y_bullet_a)
        self.assertIsNotNone(y_bullet_b)

        intra_step_gap = y_item1_l2 - y_item1_l1
        inter_step_gap = y_item2_l1 - y_item1_l2
        bullet_gap = y_bullet_b - y_bullet_a

        # A separación entre pasos distintos debe ser maior ca a entreliña interna (~0.5em extra)
        self.assertGreater(inter_step_gap, intra_step_gap + 4.0)

        # As listas de viñetas (itemize) mantéñense compactas (sen salto de 0.5em)
        self.assertAlmostEqual(bullet_gap, intra_step_gap, delta=2.0)

    def test_night_and_print_mode_colors(self):
        md = """---
activity: "P3"
---

# Guía de modos

1. Paso de proba.
"""
        # Modo nocturno: cor ámbar/tostada (#6B3A1F)
        pdf_night = self._convert(md, extra_args=['--night'])
        doc_night = pymupdf.open(pdf_night)
        page_night = doc_night[1]
        color_night = None
        for b in page_night.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                for s in l.get("spans", []):
                    if s["text"].strip() == "1.":
                        color_night = hex(s["color"])
        self.assertEqual(color_night, "0x6b3a1f")

        # Modo impresión: negro puro (0x0)
        pdf_print = self._convert(md, extra_args=['--print'])
        doc_print = pymupdf.open(pdf_print)
        page_print = doc_print[1]
        color_print = None
        for b in page_print.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                for s in l.get("spans", []):
                    if s["text"].strip() == "1.":
                        color_print = hex(s["color"])
        self.assertEqual(color_print, "0x0")


class ProceduralListsHtmlTests(unittest.TestCase):
    def test_css_rules_present_in_md2pdf_css(self):
        css_path = ROOT / 'md2pdf.css'
        content = css_path.read_text(encoding='utf-8')
        self.assertIn('ol > li::marker', content)
        self.assertIn('color: var(--heading-1)', content)
        self.assertIn('ol > li + li', content)
        self.assertIn('margin-top: .5em', content)


if __name__ == '__main__':
    unittest.main()
