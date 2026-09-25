import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


@unittest.skipUnless(shutil.which('pandoc'), 'pandoc non está instalado')
class SmallTablePaginationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.filter = cls.root / 'small-table.lua'

    def render_latex(self, markdown: str) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / 'test.md'
            src.write_text(markdown, encoding='utf-8')
            result = subprocess.run(
                ['pandoc', str(src), '-t', 'latex',
                 f'--lua-filter={self.filter}'],
                cwd=self.root,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_header_plus_small_table_reserves_space_before_header(self):
        latex = self.render_latex('''\
### 2.2 Aritméticos

| Operador | Operación | Exemplo | Resultado |
|---|---|---|---|
| `+` | Suma | `7 + 2` | `9` |
| `-` | Resta | `7 - 2` | `5` |
| `*` | Produto | `7 * 2` | `14` |
| `/` | División | `7 / 2` | `3` |
| `%` | Resto | `7 % 2` | `1` |
''')
        reserve = r'\Needspace{10\baselineskip}'
        header = r'\subsubsection{2.2 Aritméticos}'
        table = r'\noindent\begin{tabular}'

        self.assertIn(reserve, latex)
        self.assertIn(header, latex)
        self.assertIn(table, latex)
        self.assertLess(latex.index(reserve), latex.index(header))
        self.assertLess(latex.index(header), latex.index(table))
        between = latex[latex.index(header):latex.index(table)]
        self.assertNotIn(r'\Needspace', between)

    def test_consecutive_headers_reserve_space_before_the_first(self):
        latex = self.render_latex('''\
## 5. Operadores

### 5.1 Aritméticos

| Operador | Operación | Exemplo | Resultado |
|---|---|---|---|
| `+` | Suma | `7 + 2` | `9` |
| `-` | Resta | `7 - 2` | `5` |
''')
        # 2 filas + 5, máis 3 pola cabeceira anterior.
        reserve = r'\Needspace{10\baselineskip}'
        section = r'\subsection{5. Operadores}'
        subsection = r'\subsubsection{5.1 Aritméticos}'
        self.assertIn(reserve, latex)
        self.assertLess(latex.index(reserve), latex.index(section))
        between = latex[latex.index(section):latex.index(r'\begin{tabular}')]
        self.assertNotIn(r'\Needspace', between)
        self.assertIn(subsection, between)

    def test_standalone_small_table_keeps_its_own_needspace(self):
        latex = self.render_latex('''\
Texto anterior.

| A | B |
|---|---|
| 1 | 2 |
| 3 | 4 |
''')
        reserve = r'\Needspace{7\baselineskip}'
        table = r'\noindent\begin{tabular}'
        self.assertIn(reserve, latex)
        self.assertLess(latex.index(reserve), latex.index(table))

    def test_large_table_remains_longtable(self):
        rows = '\n'.join(f'| {i} | {i} |' for i in range(1, 8))
        latex = self.render_latex(
            '### Táboa grande\n\n| A | B |\n|---|---|\n' + rows + '\n'
        )
        self.assertIn(r'\begin{longtable}', latex)
        self.assertNotIn(r'\noindent\begin{tabular}', latex)


if __name__ == '__main__':
    unittest.main()
