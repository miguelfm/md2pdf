"""tests/test_interactive_tasks.py — Probas para callouts interactivos de tarefas e AcroForms."""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import pymupdf

from md2pdf.converter import convert_one
from md2pdf.html_validation import validate_html
from md2pdf.lint import lint_md
from md2pdf.preprocess import preprocess_md

ROOT = Path(__file__).resolve().parents[1]


class PreprocessAndLintTaskTests(unittest.TestCase):
    def test_preprocess_task_blockquotes(self):
        text = "> [!TASK]\n> Responde á seguinte pregunta.\n"
        pre = preprocess_md(text)
        self.assertIn("::: task", pre)
        self.assertIn("Responde á seguinte pregunta.", pre)

        text_tarefa = "> [!TAREFA]\n> Entrega antes das 23:59.\n"
        pre_tarefa = preprocess_md(text_tarefa)
        self.assertIn("::: task", pre_tarefa)
        self.assertIn("Entrega antes das 23:59.", pre_tarefa)

    def test_preprocess_task_with_title(self):
        text = "> [!TASK] Exercicio 1: Configurar SSH\n> Xera un par de claves.\n"
        pre = preprocess_md(text)
        self.assertIn("::: task", pre)
        self.assertIn("**Exercicio 1: Configurar SSH**", pre)
        self.assertIn("Xera un par de claves.", pre)

    def test_preprocess_emoji_task(self):
        text = "> 🎯 Resolver problemas de rede\n> Comproba con ping.\n"
        pre = preprocess_md(text)
        self.assertIn("::: task", pre)
        self.assertIn("Resolver problemas de rede", pre)

    def test_preprocess_fenced_attributes_normalization(self):
        text = '::: task-box{id="t1" height="4cm"}\nContido da tarefa.\n:::\n'
        pre = preprocess_md(text)
        self.assertIn('::: {.task-box id="t1" height="4cm"}', pre)

    def test_lint_callout_detection(self):
        # Con liña en branco non hai problemas
        md_ok = '::: {.task id="t1"}\n\nEnunciado da tarefa.\n:::\n'
        issues_ok = lint_md(md_ok)
        self.assertEqual(len(issues_ok), 0)

        # Sen liña en branco detecta o erro
        md_fail = '::: {.task id="t1"}\nEnunciado sen liña baleira.\n:::\n'
        issues_fail = lint_md(md_fail)
        self.assertTrue(any('callout `:::task` sen liña' in iss for iss in issues_fail))


class HtmlInteractiveTasksTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_html_task_box_and_persistence(self):
        md_text = """---
activity: "Tarefa Interactiva"
---

# Avaliación

::: {.task id="ex1" height="5cm" placeholder="Escribe a solución..."}

Describa o procedemento realizado.
:::
"""
        md_file = self.dir_path / 'tarefa.md'
        html_file = self.dir_path / 'tarefa.html'
        md_file.write_text(md_text, encoding='utf-8')

        ok = convert_one(
            md_file,
            html_file,
            ROOT / 'md2pdf.html',
            engine='html',
            highlight=str(ROOT / 'drake-jb.theme'),
        )
        self.assertTrue(ok)
        self.assertTrue(html_file.exists())

        content = html_file.read_text(encoding='utf-8')

        # Verificación semántica do elemento callout e a textarea
        self.assertIn('callout-task', content)
        self.assertIn('role="region"', content)
        self.assertIn('class="task-box-wrapper"', content)
        self.assertIn('class="task-box-input"', content)
        self.assertIn('id="ex1-input"', content)
        self.assertIn('data-task-id="ex1"', content)
        self.assertIn('style="height: 5cm;"', content)
        self.assertIn('placeholder="Escribe a solución..."', content)

        # Verificación do script de persistencia con localStorage
        self.assertIn("localStorage.getItem(storageKey)", content)
        self.assertIn("localStorage.setItem(storageKey", content)

        # Verificación de conformidade HTML (non hai IDs duplicados)
        issues = validate_html(html_file)
        self.assertEqual(len(issues), 0, f"Erros de validación HTML: {issues}")


@unittest.skipUnless(shutil.which('lualatex'), 'lualatex non instalado')
class PdfAcroFormsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_pdf_acroform_generation_and_fill(self):
        md_text = """---
activity: "Tarefa Formulario PDF"
---

# Exercicio con formulario interactivo

::: {.task id="resposta_alumno" height="3.5cm"}

Explica brevemente o principio de funcionamento de DNS.
:::
"""
        md_file = self.dir_path / 'tarefa.md'
        pdf_file = self.dir_path / 'tarefa.pdf'
        md_file.write_text(md_text, encoding='utf-8')

        cmd = ['python3', '-m', 'md2pdf', str(md_file), '-o', str(pdf_file)]
        res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"STDOUT: {res.stdout}\nSTDERR: {res.stderr}")
        self.assertTrue(pdf_file.exists())

        # Abrir con PyMuPDF e validar o widget AcroForm
        doc = pymupdf.open(pdf_file)
        widgets = []
        for p in doc:
            widgets.extend(list(p.widgets()))
        self.assertGreaterEqual(len(widgets), 1, "Non se atoparon widgets de formulario no PDF")

        target_widget = None
        for w in widgets:
            if w.field_name == "resposta-alumno":
                target_widget = w
                break

        self.assertIsNotNone(target_widget, "Non se atopou o campo de formulario con nome 'resposta-alumno'")
        self.assertEqual(target_widget.field_type, pymupdf.PDF_WIDGET_TYPE_TEXT)

        # Encher o formulario e gardar nun novo PDF para verificar persistencia
        test_answer = "O DNS traduce nomes de dominio lexibles por humanos a enderezos IP."
        target_widget.field_value = test_answer
        target_widget.update()

        filled_pdf = self.dir_path / 'tarefa_cuberta.pdf'
        doc.save(filled_pdf)
        doc.close()

        # Recargar e verificar que o valor persiste
        doc_reloaded = pymupdf.open(filled_pdf)
        all_reloaded = []
        for p in doc_reloaded:
            all_reloaded.extend(list(p.widgets()))
        reloaded_widget = next(w for w in all_reloaded if w.field_name == "resposta-alumno")
        self.assertEqual(reloaded_widget.field_value, test_answer)
        doc_reloaded.close()


class DocxInteractiveTasksTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_docx_task_rendering(self):
        md_text = """::: task
Debuxa o diagrama da arquitectura da rede.
:::
"""
        md_file = self.dir_path / 'tarefa.md'
        docx_file = self.dir_path / 'tarefa.docx'
        md_file.write_text(md_text, encoding='utf-8')

        # Compilar a docx usando Pandoc e o filtro callouts-docx.lua
        cmd = [
            'pandoc', str(md_file),
            '--lua-filter', str(ROOT / 'callouts-docx.lua'),
            '-o', str(docx_file),
        ]
        res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"STDOUT: {res.stdout}\nSTDERR: {res.stderr}")
        self.assertTrue(docx_file.exists())
