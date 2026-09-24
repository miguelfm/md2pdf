-- br.lua
-- Converte <br> e <br/> (RawInline HTML) a \newline{} en saída LaTeX.
--
-- Pandoc parsea <br> en celas de táboa como RawInline('html','<br>')
-- pero o escritor LaTeX non o converte a nada, resultando en que o
-- salto de liña desaparece no PDF.
--
-- Uso: pandoc ... --lua-filter br.lua
-- Só afecta á saída LaTeX; outros formatos (HTML, DOCX) ignoran este filtro.

function RawInline(el)
  if el.format == 'html' and el.text:match('^<br%s*/?%s*>$') then
    return pandoc.RawInline('latex', '\\newline{}')
  end
end
