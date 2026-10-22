-- small-table.lua
-- Xestión avanzada da paxinación de táboas:
--   1. Táboas pequenas (≤ THRESHOLD filas): convértense a tabular + \Needspace
--      para garantir que son indivisibles e nunca rompen entre páxinas.
--   2. Táboas grandes (> THRESHOLD filas ou con pé): mantéñense como longtable
--      con dúas melloras esenciais para a lectura:
--      - Estratexia A (evitar orfas e viúvas): as primeiras 4 filas e a
--        penúltima fila protéxense con \\* para impedir cortes prematuros
--        (1-3 filas) na primeira páxina ou deixar 1 soa fila na última.
--      - Estratexia B (cabeceira repetida sutil): se a táboa continúa
--        na seguinte páxina, a cabeceira de columnas repítese de maneira
--        sutil (cursiva, peso normal e tonalidade suave de cor), sen engadir
--        filas adicionais de texto nin pés de páxina que saturen a páxina.
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

local function make_subtle_head(head_str)
  -- Cabeceiras con formato de auto-table-widths: cambiamos a negriña e a cor
  -- forte de sección por peso normal, cursiva e unha tonalidade máis suave (65%).
  local res = head_str:gsub('\\textsf{\\bfseries\\color{heading%-section}{}', '\\textsf{\\mdseries\\itshape\\color{heading-section!65}{}')
  if res ~= head_str then
    return res
  end
  -- Se tiña \textbf ou \bfseries sen cor heading-section
  res = head_str:gsub('\\textbf{', '\\textit{'):gsub('\\bfseries', '\\mdseries\\itshape')
  if res ~= head_str then
    return res
  end
  -- Cabeceira en texto plano (ex. sen auto-table-widths): estilar cela a cela
  local out = {}
  for line in (head_str .. '\n'):gmatch('([^\n]*)\n') do
    if line:find('&') and (line:find('\\\\') or line:find('\\tabularnewline')) then
      local term = line:find('\\tabularnewline') and '\\tabularnewline' or '\\\\'
      local p = line:find(term, 1, true)
      local row_content = line:sub(1, p - 1)
      local row_end = line:sub(p)
      local parts = {}
      for cell in (row_content .. '&'):gmatch('(.-)&') do
        local tr = cell:gsub('^%s+', ''):gsub('%s+$', '')
        table.insert(parts, string.format('\\textsf{\\mdseries\\itshape\\color{heading-section!65}{%s}}', tr))
      end
      table.insert(out, table.concat(parts, ' & ') .. row_end)
    else
      table.insert(out, line)
    end
  end
  return table.concat(out, '\n')
end

local function enhance_longtable(latex, num_cols, total_rows, lang)

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
  local firsthead_pos, firsthead_end = head_part:find('\\endfirsthead')
  if firsthead_pos then
    -- Táboa con caption: Pandoc xa xerou \endfirsthead
    local first_part = head_part:sub(1, firsthead_pos - 1)
    local second_part = head_part:sub(firsthead_end + 1)
    local subtle_second = make_subtle_head(second_part)
    new_head = first_part .. '\\endfirsthead\n' .. subtle_second .. '\\endhead'
  else
    -- Táboa sen caption: cabeceira repetida sutil
    local trimmed_head = head_part:gsub('^%s+', ''):gsub('%s+$', '')
    local subtle_trimmed = make_subtle_head(trimmed_head)
    new_head = '\n' .. trimmed_head .. '\n\\endfirsthead\n' .. subtle_trimmed .. '\n\\endhead'
  end

  -- Non se engade \endfoot: a táboa parte limpamente sen fila de pé na páxina anterior
  -- («continúa na seguinte páxina…»), aforrando espazo vertical e evitando cortes prematuros.

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

-- Altura estimada do primeiro bloque indivisible dunha longtable, para
-- reservala antes dun título que a precede. Sen esa reserva, o título queda só
-- ao final da páxina: \longtable desactiva \if@nobreak, \LT@start deixa un
-- \penalty\z@ despois do título, e se a cabeceira e as filas protexidas con
-- \\* non caben, LaTeX corta entre o título e a táboa.
--
-- As medidas son as do modelo por defecto (A4, marxes de 22 mm, corpo de
-- 13 pt e táboas en \small con arraystretch 1.5), en \baselineskip do corpo
-- (18,8 pt): unha fila dunha liña ocupa 25,7 pt e cada liña máis, 17,1 pt.
-- Desde a última liña do texto anterior ata a cabeceira da táboa van uns
-- 98 pt. Cada carácter da cela ocupa de media uns 5 pt. É unha estimación: se
-- se pasa, o título salta antes do necesario.
local TEXT_WIDTH_PT = 470
local TABCOLSEP_PT = 6
local CHAR_WIDTH_PT = 5.0
local HEADING_LINES = 5
local ROW_LINES = 1.4
local EXTRA_LINE = 0.9
local CAPTION_LINES = 1.5

-- Liñas dunha cela: repártense as palabras enteiras no ancho da columna,
-- porque auto-table-widths axusta as columnas estreitas á palabra máis longa.
-- O ancho de cada p{} é a súa fracción de \linewidth menos os \tabcolsep
-- entre columnas.
-- auto-table-widths converte o código das celas en LaTeX en bruto, que
-- stringify descarta. Para medilo quítanse as ordes e as chaves.
local function latex_text(s)
  s = s:gsub('\\discretionary%b{}%b{}%b{}', '')
  s = s:gsub('\\[%a@]+%*?', '')
  return (s:gsub('[{}]', ''))
end

local function cell_text(cell)
  return pandoc.utils.stringify(cell.contents:walk({
    RawInline = function(raw)
      if raw.format:match('latex') then return pandoc.Str(latex_text(raw.text)) end
    end,
  }))
end

local function cell_lines(cell, width, ncols)
  -- Columnas de ancho natural: o texto non parte.
  if type(width) ~= 'number' or width <= 0 then return 1 end
  local avail = width * (TEXT_WIDTH_PT - 2 * TABCOLSEP_PT * (ncols - 1))
  local per_line = math.max(1, math.floor(avail / CHAR_WIDTH_PT))
  local lines, used = 1, 0
  for word in cell_text(cell):gmatch('%S+') do
    local len = utf8.len(word) or #word
    if used == 0 then
      used = len
    elseif used + 1 + len <= per_line then
      used = used + 1 + len
    else
      lines = lines + 1
      used = len
    end
  end
  return lines
end

local function row_lines(row, colspecs)
  local k = 1
  for j, cell in ipairs(row.cells) do
    local spec = colspecs[j]
    k = math.max(k, cell_lines(cell, spec and spec[2], #colspecs))
  end
  return ROW_LINES + EXTRA_LINE * (k - 1)
end

local function first_chunk_lines(tbl)
  -- enhance_longtable protexe con \\* as primeiras min_first filas, así que o
  -- primeiro corte posible vén despois da fila min_first + 1.
  local total = count_body_rows(tbl)
  local min_first = math.min(MIN_FIRST_ROWS, math.max(1, total - 2))
  local chunk = math.min(total, min_first + 1)
  local lines = HEADING_LINES
  if tbl.caption and tbl.caption.long and #tbl.caption.long > 0 then
    lines = lines + CAPTION_LINES
  end
  for _, row in ipairs(tbl.head.rows) do
    lines = lines + row_lines(row, tbl.colspecs)
  end
  local n = 0
  for _, body in ipairs(tbl.bodies) do
    for _, row in ipairs(body.body) do
      if n >= chunk then break end
      lines = lines + row_lines(row, tbl.colspecs)
      n = n + 1
    end
  end
  return math.ceil(lines)
end

-- Parágrafo de entrada: remata en «:» e presenta a táboa seguinte. Como en
-- keep-with-next.lua, que trata os bloques de código e as listas, a reserva
-- vai antes do parágrafo e inclúe as súas liñas estimadas.
local LEAD_IN_CHARS_PER_LINE = 85
local LEAD_IN_GAP = 2

local function is_lead_in(block)
  if not block or (block.t ~= 'Para' and block.t ~= 'Plain') then
    return false
  end
  -- O texto enteiro, para recoñecer tamén «**Erros habituais:**».
  return pandoc.utils.stringify(block):match(':%s*$') ~= nil
end

local function lead_in_lines(block)
  local text = pandoc.utils.stringify(block)
  local chars = utf8.len(text) or #text
  return math.max(1, math.ceil(chars / LEAD_IN_CHARS_PER_LINE))
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
--
-- Se a táboa é grande, segue como longtable, e a reserva antes do Header cobre
-- só o primeiro bloque indivisible (first_chunk_lines). Esta reserva vai antes
-- do título, non entre o título e a táboa, que é onde se desincronizaría a
-- longtable.
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
      elseif FORMAT:match('latex') then
        insert_needspace(out, first_chunk_lines(next_block))
        out:insert(current)
        out:insert(convert_large_table(next_block))
        i = i + 2
        goto continue
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
      elseif FORMAT:match('latex') then
        insert_needspace(out, first_chunk_lines(tbl))
        out:insert(current)
        out:insert(next_block)
        out:insert(convert_large_table(tbl))
        out:insert(blocks[i + 3])
        i = i + 4
        goto continue
      end
    end

    -- Parágrafo de entrada + Table, coa táboa directa ou envolvida polo
    -- centrado de auto-table-widths.lua. A reserva vai antes do parágrafo
    -- (e das cabeceiras que o precedan), non entre o parágrafo e a táboa:
    -- alí deixaría o corte que se quere evitar e desincronizaría a longtable.
    if FORMAT:match('latex') and is_lead_in(current) and next_block then
      local wrapped = is_centering_prefix(next_block)
        and blocks[i + 2] and blocks[i + 2].t == 'Table'
        and is_group_suffix(blocks[i + 3])
      local tbl = next_block.t == 'Table' and next_block
        or (wrapped and blocks[i + 2]) or nil
      if tbl then
        local para = lead_in_lines(current)
        local convertible, nrows = is_small_convertible_table(tbl)
        local converted, needed
        if convertible then
          converted = convert_small_table(tbl, nrows + 5, false)
          needed = nrows + 5 + para
        else
          converted = convert_large_table(tbl)
          -- HEADING_LINES estima a cabeceira; dun parágrafo quedan dúas liñas
          -- de separación antes da táboa.
          needed = first_chunk_lines(tbl) - HEADING_LINES + LEAD_IN_GAP + para
        end
        if converted then
          insert_needspace(out, needed)
          out:insert(current)
          if wrapped then
            out:insert(next_block)
            out:insert(converted)
            out:insert(blocks[i + 3])
            i = i + 4
          else
            out:insert(converted)
            i = i + 2
          end
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
