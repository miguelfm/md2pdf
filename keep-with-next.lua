-- keep-with-next.lua — Manter un parágrafo de entrada co bloque que presenta.
-- Só na saída LaTeX. Un parágrafo de entrada remata en dous puntos e vai xusto
-- antes dun bloque de código ou dunha lista. Sen protección, se o bloque non
-- cabe ao pé da páxina, o parágrafo queda só e o bloque pasa á seguinte:
-- keep-code.lua fai indivisíbeis os bloques curtos, e as listas empezan cunha
-- penalización que favorece o salto.
--
-- O filtro reserva antes do parágrafo, con \Needspace, as liñas estimadas do
-- parágrafo e do comezo do bloque:
--   - bloque de código de ata code-keep-lines liñas: todas as súas liñas;
--   - bloque máis longo: as primeiras MIN_CODE_LINES;
--   - lista: as liñas estimadas do primeiro elemento, como moito MAX_ITEM_LINES.
-- Se a reserva non cabe, o salto vai antes do parágrafo. As táboas trátaas
-- small-table.lua coa mesma regra, porque xa calcula a súa altura.
--
-- Se o parágrafo vai despois dunha ou máis cabeceiras, a reserva vai antes da
-- primeira, como en small-table.lua: entre a cabeceira e o parágrafo,
-- \Needspace deixaría un punto de corte.
--
-- keep-with-next: false nos metadatos desactiva o filtro.

local CHARS_PER_LINE = 85      -- texto do corpo en A4, con marxe
local CODE_PADDING = 2         -- marco e separación do bloque de código
local MIN_CODE_LINES = 4       -- comezo dun bloque que pode partirse
local LIST_GAP = 1             -- separación antes da lista
local MAX_ITEM_LINES = 4
local LINES_PER_EXTRA_HEADER = 3
local DIAGRAM_CLASSES = { mermaid = true, dot = true, d2 = true,
                          ['vega-lite'] = true, vegalite = true }

local enabled = true
local keep_lines = 12

local function read_meta(meta)
  local value = meta['keep-with-next']
  if type(value) == 'boolean' then
    enabled = value
  elseif value ~= nil then
    enabled = pandoc.utils.stringify(value) ~= 'false'
  end
  local keep = meta['code-keep-lines']
  if keep ~= nil then
    keep_lines = tonumber(pandoc.utils.stringify(keep)) or 12
  end
  return meta
end

local function text_lines(text, width)
  local chars = utf8.len(text) or #text
  return math.max(1, math.ceil(chars / width))
end

-- Un parágrafo (ou o texto dun elemento de lista compacta) que remata en «:».
local function is_lead_in(block)
  if block.t ~= 'Para' and block.t ~= 'Plain' then return false end
  -- O texto enteiro, para recoñecer tamén «**Erros habituais:**».
  return pandoc.utils.stringify(block):match(':%s*$') ~= nil
end

local function is_diagram(block)
  for _, class in ipairs(block.classes) do
    if DIAGRAM_CLASSES[class] then return true end
  end
  return false
end

-- Liñas que hai que reservar para o comezo do bloque, ou nil se non se protexe.
local function next_lines(block)
  if block.t == 'CodeBlock' then
    if is_diagram(block) then return nil end
    local lines = 1
    for _ in block.text:gmatch('\n') do lines = lines + 1 end
    if keep_lines <= 0 or lines > keep_lines then
      lines = math.min(lines, MIN_CODE_LINES)
    end
    return lines + CODE_PADDING
  end
  if block.t == 'BulletList' or block.t == 'OrderedList' then
    local first = block.content[1]
    if not first or not first[1] then return LIST_GAP + 1 end
    local text = pandoc.utils.stringify(first[1])
    return LIST_GAP + math.min(text_lines(text, CHARS_PER_LINE - 5),
                               MAX_ITEM_LINES)
  end
  return nil
end

local function insert_needspace(out, needed)
  local pos = #out + 1
  while pos > 1 and out[pos - 1].t == 'Header' do
    pos = pos - 1
    needed = needed + LINES_PER_EXTRA_HEADER
  end
  out:insert(pos, pandoc.RawBlock('latex',
    string.format('\\Needspace{%d\\baselineskip}', needed)))
end

local function blocks(list)
  if not enabled or not FORMAT:match('latex') then return nil end
  local out = pandoc.List:new()
  for i, block in ipairs(list) do
    local nxt = list[i + 1]
    if nxt and is_lead_in(block) then
      local lines = next_lines(nxt)
      if lines then
        insert_needspace(out, text_lines(pandoc.utils.stringify(block),
                                         CHARS_PER_LINE) + lines)
      end
    end
    out:insert(block)
  end
  return out
end

return {
  { Meta = read_meta },
  { Blocks = blocks },
}
