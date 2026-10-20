-- keep-code.lua — Manter xuntos os bloques curtos só na saída LaTeX.
-- code-keep-lines: máximo de liñas de fonte (incluídas as baleiras).
-- Por defecto 12; 0 desactiva a protección. Como en compact-code.lua,
-- os metadatos procésanse antes dos bloques e consérvase o CodeBlock
-- para os filtros seguintes e para o resaltado do escritor de Pandoc.

local threshold = 12

local function get_meta(meta)
  local value = meta['code-keep-lines']
  if value ~= nil then
    threshold = tonumber(pandoc.utils.stringify(value)) or 12
  end
  return meta
end

local function process_codeblock(block)
  if not FORMAT:match('latex') or threshold <= 0 then return nil end

  local lines = 1
  for _ in block.text:gmatch('\n') do
    lines = lines + 1
  end
  if lines > threshold then return nil end

  return {
    pandoc.RawBlock('latex', '\\begin{KeepCodeBlock}'),
    block,
    pandoc.RawBlock('latex', '\\end{KeepCodeBlock}')
  }
end

return {
  { Meta = get_meta },
  { CodeBlock = process_codeblock }
}
