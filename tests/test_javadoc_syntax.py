import importlib.util
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYNTAX = ROOT / 'javadoc.xml'

JAVADOC = (
    '```java\n'
    '/**\n'
    ' * Saúda ao usuario. Segunda frase con ñ e ç.\n'
    ' * Usa {@code IO.println}.\n'
    ' * @param nome o nome da persoa\n'
    ' */\n'
    '```\n'
)


@unittest.skipUnless(shutil.which('pandoc'), 'pandoc non está instalado')
class JavadocSyntaxTests(unittest.TestCase):
    def render_latex(self, *extra_args: str) -> str:
        cmd = ['pandoc', '-f', 'markdown', '-t', 'latex', *extra_args]
        result = subprocess.run(
            cmd, input=JAVADOC, capture_output=True, text=True, cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_builtin_syntax_splits_accented_words(self):
        # Documenta o erro que corrixe javadoc.xml. Se deixa de fallar,
        # a versión de Pandoc xa o arranxou e o ficheiro pode retirarse.
        latex = self.render_latex()
        self.assertIn(r'\CommentTok{ú}', latex)

    def test_fixed_syntax_keeps_accented_words_as_comment(self):
        latex = self.render_latex(f'--syntax-definition={SYNTAX}')
        self.assertIn(r'\CommentTok{Saúda}', latex)
        self.assertIn(r'\CommentTok{ñ}', latex)
        self.assertNotIn(r'\NormalTok{', latex)

    def test_fixed_syntax_keeps_javadoc_tags(self):
        latex = self.render_latex(f'--syntax-definition={SYNTAX}')
        self.assertIn(r'\AnnotationTok{@param}', latex)
        self.assertIn(r'\AnnotationTok{\{@code IO.println\}}', latex)


class JavadocSyntaxInstallTests(unittest.TestCase):
    def test_installer_copies_javadoc_syntax(self):
        spec = importlib.util.spec_from_file_location(
            'install_md2pdf', ROOT / 'install-md2pdf.py',
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        files = module.DATA_FILES_REQUIRED + module.DATA_FILES_OPTIONAL
        self.assertIn('javadoc.xml', files)


if __name__ == '__main__':
    unittest.main()
