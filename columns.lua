-- columns.lua — Columnas lado a lado na saída LaTeX.
--
-- Sintaxe de Pandoc, a mesma de beamer e das presentacións HTML:
--
--     :::: columns
--
--     ::: {.column width="40%"}
--
--     | Referencia | Obxecto |
--     ...
--
--     :::
--
--     ::: column
--
--     ...
--
--     :::
--
--     ::::
--
-- Pandoc só converte estes divs en columnas na saída beamer; en LaTeX deixa o
-- contido un despois do outro. O filtro pon cada columna nunha minipage
-- aliñada pola parte superior, separadas por \hfill. As columnas sen `width`
-- repártense por igual o ancho que deixan as outras, descontada a separación.
--
-- Os bloques indivisíbeis da columna non poden partir entre páxinas: a minipage
-- é unha caixa. As reservas \Needspace que small-table.lua e keep-with-next.lua
-- poñen dentro das columnas non serven alí, así que se retiran e se pon unha
-- soa antes do conxunto, coa maior delas. Se o parágrafo anterior remata en dous puntos,
-- a reserva vai antes del e súmalle as súas liñas, como en keep-with-next.lua.
--
-- Vai despois de small-table.lua e keep-with-next.lua, que xa deixaron as
-- reservas, e antes de callouts.lua.

local GAP = 0.04              -- separación entre columnas, en fracción de \linewidth
local CHARS_PER_LINE = 85     -- texto do corpo en A4, como keep-with-next.lua
local NEEDSPACE_PATTERN = '\\Needspace{(%d+)\\baselineskip}%s*'

local function is_column(block)
  return block.t == 'Div' and block.classes:includes('column')
end

local function parse_width(value)
  if not value then return nil end
  local number = value:match('^%s*([%d.]+)%s*%%%s*$')
  if number then return tonumber(number) / 100 end
  number = value:match('^%s*([%d.]+)%s*$')
  if number then
    number = tonumber(number)
    if number and number > 1 then return number / 100 end
    return number
  end
  return nil
end

-- Retira as reservas dos bloques en bruto da columna e devolve a maior.
local function strip_reserves(blocks)
  local largest = 0
  local function take(raw)
    if raw.format ~= 'latex' and raw.format ~= 'tex' then return nil end
    local text = raw.text:gsub(NEEDSPACE_PATTERN, function(lines)
      largest = math.max(largest, tonumber(lines))
      return ''
    end)
    if text:match('^%s*$') then return {} end
    raw.text = text
    return raw
  end
  local filtered = pandoc.Div(blocks):walk({ RawBlock = take })
  return filtered.content, largest
end

local function lead_in_lines(block)
  if not block or (block.t ~= 'Para' and block.t ~= 'Plain') then return nil end
  local text = pandoc.utils.stringify(block)
  if not text:match(':%s*$') then return nil end
  local chars = utf8.len(text) or #text
  return math.max(1, math.ceil(chars / CHARS_PER_LINE))
end

local function render_columns(div)
  local columns = {}
  for _, block in ipairs(div.content) do
    if is_column(block) then
      table.insert(columns, block)
    end
  end
  if #columns == 0 then return nil, 0 end

  local fixed, free = 0, 0
  local widths = {}
  for i, column in ipairs(columns) do
    local width = parse_width(column.attributes.width)
    widths[i] = width
    if width then fixed = fixed + width else free = free + 1 end
  end
  local available = 1 - GAP * (#columns - 1) - fixed
  local share = free > 0 and math.max(available / free, 0.1) or 0

  -- Pandoc separa os bloques cunha liña baleira, que entre dúas minipages
  -- remataría o parágrafo e baixaría a segunda. Por iso o peche dunha
  -- columna e a apertura da seguinte van no mesmo bloque en bruto.
  local out = pandoc.List:new()
  local reserve = 0
  for i, column in ipairs(columns) do
    local content, largest = strip_reserves(column.content)
    reserve = math.max(reserve, largest)
    local open = string.format('\\begin{minipage}[t]{%.3f\\linewidth}',
                               widths[i] or share)
    if i == 1 then
      open = '\\par\\noindent' .. open
    else
      open = '\\end{minipage}\\hfill' .. open
    end
    out:insert(pandoc.RawBlock('latex', open))
    out:extend(content)
  end
  out:insert(pandoc.RawBlock('latex', '\\end{minipage}\\par'))
  return out, reserve
end

function Blocks(blocks)
  if not FORMAT:match('latex') then return nil end
  local out = pandoc.List:new()
  local changed = false
  for _, block in ipairs(blocks) do
    local rendered, reserve = nil, 0
    if block.t == 'Div' and block.classes:includes('columns') then
      rendered, reserve = render_columns(block)
    end
    if rendered then
      changed = true
      local lead = lead_in_lines(out[#out])
      if reserve > 0 or lead then
        local pos = #out + 1
        if lead then
          reserve = reserve + lead
          pos = #out
        end
        out:insert(pos, pandoc.RawBlock('latex',
          string.format('\\Needspace{%d\\baselineskip}', reserve)))
      end
      out:extend(rendered)
    else
      out:insert(block)
    end
  end
  if changed then return out end
  return nil
end
