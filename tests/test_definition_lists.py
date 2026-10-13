import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('pandoc'), 'pandoc non instalado')
class DefinitionListTests(unittest.TestCase):
    def render_html(self, markdown: str) -> str:
        result = subprocess.run(
            ['pandoc', '-f', 'markdown', '-t', 'html',
             f'--lua-filter={ROOT / "term-pairs.lua"}'],
            input=markdown, text=True, capture_output=True, cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_pair_lists_become_definitions_without_changing_other_lists(self):
        html = self.render_html('''\
API
:   Interface curta.

Un termo longo que necesita outra liña
:   Explicación que continúa.

Texto separador.

- **CPU**: Procesador.
- **Memoria principal:** Datos en uso.

Outro texto.

- Primeiro elemento ordinario.
- Segundo elemento ordinario.

1. Primeiro elemento numerado.
2. Segundo elemento numerado.
''')
        self.assertEqual(html.count('<dl>'), 2)
        self.assertIn('<dt>CPU</dt>', html)
        self.assertIn('<dd>\nProcesador.\n</dd>', html)
        self.assertEqual(html.count('<ul>'), 1)
        self.assertEqual(html.count('<ol type="1">'), 1)

    def test_mixed_bullet_list_remains_ordinary(self):
        html = self.render_html('''\
- **API**: Interface.
- Un elemento sen par termo–explicación.
''')
        self.assertNotIn('<dl>', html)
        self.assertIn('<ul>', html)


if __name__ == '__main__':
    unittest.main()
