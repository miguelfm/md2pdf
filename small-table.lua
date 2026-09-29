-- small-table.lua
-- Xestión avanzada da paxinación de táboas:
--   1. Táboas pequenas (≤ THRESHOLD filas): convértense a tabular + \Needspace
--      para garantir que son indivisibles e nunca rompen entre páxinas.
--   2. Táboas grandes (> THRESHOLD filas ou con pé): mantéñense como longtable
--      con dúas melloras esenciais para a lectura:
--      - Estratexia A (evitar orfas e viúvas): as primeiras 4 filas e a
--        penúltima fila protéxense con \\* para impedir cortes prematuros
--        (1-3 filas) na primeira páxina ou deixar 1 soa fila na última.
--      - Estratexia B (cabeceiras e pés de continuidade): se a táboa continúa
--        na seguinte páxina, a primeira páxina inclúe un pé discreto
--        «(continúa na seguinte páxina…)» e as páxinas seguintes amosan
--        «(continúa da páxina anterior)» antes dos nomes de columna.
--
-- PROBLEMA ORIXINAL:
--   longtable usa dúas pasadas para xestionar saltos de páxina.
--   Calquera \Needspace externo desincroniza ese mecanismo e produce
--   cabeceiras duplicadas (a cabeceira repítese na páxina seguinte
--   cando a táboa non necesitaba partir).
--
-- SOLUCIÓN:
--   Só táboas que con certeza caben nunha páxina (≤ THRESHOLD filas)
--   se converten a tabular + \Needspace. O resto mantense como longtable
--   e parte naturalmente entre páxinas sen problemas.
--
-- THRESHOLD conservador (6):
--   Unha páxina A4 con fonte 11pt ten ~45 liñas útiles.
--   Con celas dunha soa liña, 6 filas + cabeceira = ~7 liñas (~16% páxina).
--   Celas con texto longo poden dobrar ou triplicar a altura real,
--   así que 6 filas é un límite seguro para garantir que a táboa cabe.
--   Táboas de 7+ filas quedan como longtable e parten se é necesario.
--
-- O zebra striping xestiónao \AtBeginEnvironment{tabular/longtable}
-- da preamble (non este filtro).

local THRESHOLD = 6
local MIN_FIRST_ROWS = 4

local doc_lang = 'gl'

local function read_meta(meta)
  if meta.lang then
    doc_lang = pandoc.utils.stringify(meta.lang):lower()
  end
end

local function count_body_rows(tbl)
  local n = 0
  for _, body in ipairs(tbl.bodies) do
    n = n + #body.body
  end
  return n
end

local function get_continuation_strings(lang)
  if lang and lang:match('^es') then
    return "(continúa de la página anterior)", "(continúa en la siguiente página…)"
  elseif lang and lang:match('^en') then
    return "(continued from previous page)", "(continued on next page…)"
  else
    return "(continúa da páxina anterior)", "(continúa na seguinte páxina…)"
  end
end

local function enhance_longtable(latex, num_cols, total_rows, lang)
  local str_prev, str_next = get_continuation_strings(lang)

  local b_start, b_end = latex:find('\\begin{longtable}')
  if not b_start then return latex end

  -- Atopamos peche da definición de columnas de \begin{longtable}...{...}
  local col_open = latex:find('{', b_end)
  if not col_open then return latex end

  local depth = 1
  local idx = col_open + 1
  while depth > 0 and idx <= #latex do
    local c = latex:sub(idx, idx)
    if c == '{' then depth = depth + 1
    elseif c == '}' then depth = depth - 1 end
    idx = idx + 1
  end
  local col_close = idx - 1

  local before_head = latex:sub(1, col_close)
  local rest = latex:sub(col_close + 1)

  local endhead_pos, endhead_end = rest:find('\\endhead')
  if not endhead_pos then return latex end

  local head_part = rest:sub(1, endhead_pos - 1)
  local after_endhead = rest:sub(endhead_end + 1)

  local new_head = ''
  local cont_prev_line = string.format('\\multicolumn{%d}{r}{\\footnotesize\\textcolor{gray}{\\textit{%s}}} \\\\ \\addlinespace[2pt]', num_cols, str_prev)
  local cont_next_foot = string.format('\\midrule\\noalign{}\n\\multicolumn{%d}{r}{\\footnotesize\\textcolor{gray}{\\textit{%s}}} \\\\\n\\endfoot', num_cols, str_next)

  local firsthead_pos, firsthead_end = head_part:find('\\endfirsthead')
  if firsthead_pos then
    -- Táboa con caption: Pandoc xa xerou \endfirsthead
    local first_part = head_part:sub(1, firsthead_pos - 1)
    local second_part = head_part:sub(firsthead_end + 1)
    new_head = first_part .. '\\endfirsthead\n' .. cont_prev_line .. '\n' .. second_part .. '\\endhead'
  else
    -- Táboa sen caption: duplicamos cabeceira co aviso de continuación
    local trimmed_head = head_part:gsub('^%s+', ''):gsub('%s+$', '')
    new_head = '\n' .. trimmed_head .. '\n\\endfirsthead\n' .. cont_prev_line .. '\n' .. trimmed_head .. '\n\\endhead'
  end

  if not after_endhead:find('\\endfoot') then
    new_head = new_head .. '\n' .. cont_next_foot
  end

  -- Estratexia A: Protexer as primeiras filas con \\* (mínimo antes de romper)
  -- e a penúltima fila (evitar viúvas).
  local endlastfoot_pos, endlastfoot_end = after_endhead:find('\\endlastfoot')
  local foot_part = ''
  local body_part = after_endhead
  if endlastfoot_end then
    foot_part = after_endhead:sub(1, endlastfoot_end)
    body_part = after_endhead:sub(endlastfoot_end + 1)
  end

  local min_first = math.min(MIN_FIRST_ROWS, math.max(1, (total_rows or 4) - 2))
  local penult = (total_rows and total_rows >= 6) and (total_rows - 1) or nil
  local row_idx = 0
  local lines = {}

  for line in (body_part .. '\n'):gmatch('([^\n]*)\n') do
    local l = line
    if l:match('\\\\%s*$') and not l:match('\\\\%*%s*$') then
      row_idx = row_idx + 1
      if row_idx <= min_first or (penult and row_idx == penult) then
        l = l:gsub('\\\\(%s*)$', '\\\\*%1')
      end
    end
    table.insert(lines, l)
  end
  local enhanced_body = table.concat(lines, '\n')

  return before_head .. new_head .. foot_part .. enhanced_body
end

local function longtable_to_tabular(latex, needed_lines, include_needspace)
  local state   = 'start'
  local head    = {}
  local foot    = {}
  local body    = {}
  local colspec = nil

  for line in (latex .. '\n'):gmatch('([^\n]*)\n') do
    if state == 'start' then
      local cs = line:match('\\begin{longtable}%b[]{(.+)}')
              or line:match('\\begin{longtable}{(.+)}')
      if cs then
        colspec = cs
        state   = 'head'
      end
    elseif state == 'head' then
      if line:match('\\endhead') then
        state = 'foot'
      else
        table.insert(head, line)
      end
    elseif state == 'foot' then
      if line:match('\\endlastfoot') then
        state = 'body'
      elseif line:match('%S') then
        table.insert(foot, line)
      end
    elseif state == 'body' then
      if line:match('\\end{longtable}') then
        state = 'done'
      else
        table.insert(body, line)
      end
    end
  end

  if not colspec then return nil end

  local out = {}
  if include_needspace then
    table.insert(out, string.format('\\Needspace{%d\\baselineskip}', needed_lines))
  end
  table.insert(out, string.format('\\noindent\\begin{tabular}{%s}', colspec))
  for _, l in ipairs(head)  do table.insert(out, l) end
  for _, l in ipairs(body)  do table.insert(out, l) end
  for _, l in ipairs(foot)  do table.insert(out, l) end
  table.insert(out, '\\end{tabular}')
  return table.concat(out, '\n')
end

local function is_small_convertible_table(tbl)
  -- Táboas con pé: quedan como longtable. \caption e \label só funcionan
  -- alí; dentro dun tabular fóra de float, \caption dá «\caption outside
  -- float». Ademais, figure-captions.lua (que corre despois) necesita ver a
  -- táboa como Table para extraer o {#tbl:…} do pé.
  if tbl.caption and tbl.caption.long and #tbl.caption.long > 0 then
    return false
  end

  local nrows = count_body_rows(tbl)
  return nrows <= THRESHOLD, nrows
end

local function convert_small_table(tbl, needed_lines, include_needspace)
  local latex = pandoc.write(pandoc.Pandoc({tbl}), 'latex')
  local result = longtable_to_tabular(latex, needed_lines, include_needspace)
  if not result then return nil end
  return pandoc.RawBlock('latex', result)
end

local function convert_large_table(tbl)
  if not FORMAT:match('latex') then return tbl end
  local latex = pandoc.write(pandoc.Pandoc({tbl}), 'latex')
  local num_cols = #tbl.colspecs
  if num_cols == 0 then num_cols = 1 end
  local nrows = count_body_rows(tbl)
  local enhanced = enhance_longtable(latex, num_cols, nrows, doc_lang)
  return pandoc.RawBlock('latex', enhanced)
end

-- Trátase a secuencia de bloques, non cada Table illadamente, porque unha táboa
-- pequena situada xusto despois dunha cabeceira debe reservar espazo ANTES da
-- cabeceira. Se a reserva se introduce entre ambos, pode ocorrer isto:
--
--   cabeceira          <- cabe porque pasa o \Needspace propio da sección
--   [salto de páxina]  <- o \Needspace da táboa xa non cabe
--   táboa
--
-- Para Header + Table consecutivos, a reserva conxunta colócase antes do Header
-- e a táboa convértese a tabular sen un segundo \needspace. As táboas pequenas
-- que non seguen inmediatamente a unha cabeceira conservan o comportamento
-- anterior.
local function is_centering_prefix(block)
  return block
    and block.t == 'RawBlock'
    and block.format == 'latex'
    and block.text:match('^\\begingroup\\centering\\setlength{\\LTleft}{\\fill}\\setlength{\\LTright}{\\fill}%s*$')
end

local function is_group_suffix(block)
  return block
    and block.t == 'RawBlock'
    and block.format == 'latex'
    and block.text:match('^\\par\\endgroup%s*$')
end

-- Cabeceiras consecutivas (sección + subsección + táboa): a reserva ponse
-- antes da primeira cabeceira da serie, sumando tres liñas por cada cabeceira
-- anterior. Se se puxese só antes da última, o salto quedaría entre elas.
local LINES_PER_EXTRA_HEADER = 3

local function insert_needspace(out, needed)
  local pos = #out + 1
  while pos > 1 and out[pos - 1].t == 'Header' do
    pos = pos - 1
    needed = needed + LINES_PER_EXTRA_HEADER
  end
  out:insert(pos, pandoc.RawBlock('latex',
    string.format('\\Needspace{%d\\baselineskip}', needed)))
end

function Blocks(blocks)
  local out = pandoc.List:new()
  local i = 1

  while i <= #blocks do
    local current = blocks[i]
    local next_block = blocks[i + 1]

    -- Caso directo: Header + Table.
    if current.t == 'Header' and next_block and next_block.t == 'Table' then
      local convertible, nrows = is_small_convertible_table(next_block)
      if convertible then
        local needed = nrows + 5
        local converted = convert_small_table(next_block, needed, false)
        if converted then
          insert_needspace(out, needed)
          out:insert(current)
          out:insert(converted)
          i = i + 2
          goto continue
        end
      end
    end

    -- auto-table-widths.lua envolve as táboas de ancho natural en
    --   \\begingroup...  Table  \\endgroup
    -- polo que Header e Table deixan de ser adxacentes cando este filtro corre.
    -- Trátase ese envoltorio como transparente para a decisión de paxinación.
    if current.t == 'Header'
       and is_centering_prefix(next_block)
       and blocks[i + 2] and blocks[i + 2].t == 'Table'
       and is_group_suffix(blocks[i + 3]) then
      local tbl = blocks[i + 2]
      local convertible, nrows = is_small_convertible_table(tbl)
      if convertible then
        local needed = nrows + 5
        local converted = convert_small_table(tbl, needed, false)
        if converted then
          insert_needspace(out, needed)
          out:insert(current)
          out:insert(next_block)
          out:insert(converted)
          out:insert(blocks[i + 3])
          i = i + 4
          goto continue
        end
      end
    end

    if current.t == 'Table' then
      local convertible, nrows = is_small_convertible_table(current)
      if convertible then
        local needed = nrows + 5
        local converted = convert_small_table(current, needed, true)
        if converted then
          out:insert(converted)
          i = i + 1
          goto continue
        end
      else
        local enhanced = convert_large_table(current)
        out:insert(enhanced)
        i = i + 1
        goto continue
      end
    end

    -- Táboas de ancho natural grandes / con caption envolvidas en begingroup...endgroup
    if is_centering_prefix(current)
       and next_block and next_block.t == 'Table'
       and blocks[i + 2] and is_group_suffix(blocks[i + 2]) then
      local tbl = next_block
      local convertible, _ = is_small_convertible_table(tbl)
      if not convertible then
        local enhanced = convert_large_table(tbl)
        out:insert(current)
        out:insert(enhanced)
        out:insert(blocks[i + 2])
        i = i + 3
        goto continue
      end
    end

    out:insert(current)
    i = i + 1

    ::continue::
  end

  return out
end

return {
  { Meta = read_meta },
  { Blocks = Blocks },
}
