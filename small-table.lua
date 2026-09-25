-- small-table.lua
-- Converte táboas moi pequenas de longtable a tabular+needspace.
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

local function count_body_rows(tbl)
  local n = 0
  for _, body in ipairs(tbl.bodies) do
    n = n + #body.body
  end
  return n
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

local function convert_table(tbl, needed_lines, include_needspace)
  local latex = pandoc.write(pandoc.Pandoc({tbl}), 'latex')
  local result = longtable_to_tabular(latex, needed_lines, include_needspace)
  if not result then return nil end
  return pandoc.RawBlock('latex', result)
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
        local converted = convert_table(next_block, needed, false)
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
        local converted = convert_table(tbl, needed, false)
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
        local converted = convert_table(current, needed, true)
        if converted then
          out:insert(converted)
          i = i + 1
          goto continue
        end
      end
    end

    out:insert(current)
    i = i + 1

    ::continue::
  end

  return out
end
