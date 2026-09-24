-- auto-table-widths.lua
local MAX_CELL_LEN = 60
local MAX_MBOX_LEN = 15
local BREAK_CLASS = "[,%s/%.:=%?%-_%(;]"
-- Táboas de contido curto: se ningunha cela pasa de NATURAL_MAX_CELL caracteres
-- e o ancho natural estimado non supera NATURAL_MAX_TOTAL da liña, non se fixan
-- anchos e Pandoc usa columnas l/c/r co seu ancho natural. Así unha táboa de
-- verdade ou de valores numéricos non se estira ata ocupar a liña enteira nin
-- deixa columnas estreitísimas ao lado doutras anchas.
local NATURAL_MAX_CELL = 20
local NATURAL_MAX_TOTAL = 0.85
local CHAR_WIDTH = 0.013
local estilar_cabeceira
local function content_length(inlines)
  local len = 0
  for _, inline in ipairs(inlines) do
    if inline.t == "Str" then
      len = len + #inline.text
    elseif inline.t == "Space" or inline.t == "SoftBreak" then
      len = len + 1
    elseif inline.t == "Code" then
      len = len + #inline.text * 1.05
    elseif inline.t == "Strong" or inline.t == "Emph" or inline.t == "Link" then
      len = len + content_length(inline.content)
    end
  end
  if len > MAX_CELL_LEN then len = MAX_CELL_LEN end
  return len
end
local function longest_segment(text)
  local maxlen, cur = 0, 0
  for i = 1, #text do
    if text:sub(i, i):match(BREAK_CLASS) then
      cur = cur + 1
      if cur > maxlen then maxlen = cur end
      cur = 0
    else
      cur = cur + 1
    end
  end
  if cur > maxlen then maxlen = cur end
  return maxlen
end
local function unbreakable_len(code_text)
  local has_break = code_text:match("[/\\%.:=%?%-_]") ~= nil
  if (#code_text <= 8) or (#code_text <= MAX_MBOX_LEN and not has_break) then
    return #code_text
  end
  return longest_segment(code_text)
end
local function longest_code(inlines)
  local maxlen = 0
  for _, inline in ipairs(inlines) do
    if inline.t == "Code" then
      local len = unbreakable_len(inline.text)
      if len > maxlen then maxlen = len end
    end
  end
  return maxlen
end
local function analyze_cells(tbl, ncols)
  local max_lens, min_lens = {}, {}
  for i = 1, ncols do
    max_lens[i] = 1
    min_lens[i] = 0
  end
  local function process_rows(rows)
    for _, row in ipairs(rows) do
      for i, cell in ipairs(row.cells) do
        if i <= ncols then
          for _, block in ipairs(cell.contents) do
            if block.content then
              local len = content_length(block.content)
              if len > max_lens[i] then max_lens[i] = len end
              local mlen = longest_code(block.content)
              if mlen > min_lens[i] then min_lens[i] = mlen end
            end
          end
        end
      end
    end
  end
  if tbl.head and tbl.head.rows then
    for _, row in ipairs(tbl.head.rows) do
      for i, cell in ipairs(row.cells) do
        if i <= ncols then
          for _, block in ipairs(cell.contents) do
            if block.content then
              for _, inline in ipairs(block.content) do
                if inline.t == "Str" then
                  local wlen = #inline.text
                  if wlen > min_lens[i] then min_lens[i] = wlen end
                end
              end
            end
          end
        end
      end
    end
    process_rows(tbl.head.rows)
  end
  for _, body in ipairs(tbl.bodies) do
    process_rows(body.body)
  end
  return max_lens, min_lens
end
function Table(tbl)
  local ncols = #tbl.colspecs
  if ncols == 0 then return tbl end
  local max_lens, min_lens = analyze_cells(tbl, ncols)
  local natural, estimado = true, 0
  for i = 1, ncols do
    if max_lens[i] > NATURAL_MAX_CELL then natural = false end
    estimado = estimado + max_lens[i] * CHAR_WIDTH + 0.02
  end
  if natural and estimado <= NATURAL_MAX_TOTAL then
    estilar_cabeceira(tbl)
    -- Unha táboa co seu ancho natural non ocupa a liña enteira, así que se
    -- centra. Faise localmente, porque o preámbulo pode ter \LTleft a cero
    -- para que as táboas de ancho completo empecen na marxe.
    -- \LTleft/\LTright centran o longtable; \centering centra o tabular
    -- no que small-table.lua converte as táboas de ata 6 filas.
    if FORMAT:match("latex") then
      return {
        pandoc.RawBlock("latex",
          "\\begingroup\\centering\\setlength{\\LTleft}{\\fill}\\setlength{\\LTright}{\\fill}"),
        tbl,
        pandoc.RawBlock("latex", "\\par\\endgroup"),
      }
    end
    return tbl
  end
  local total = 0
  for i = 1, ncols do total = total + max_lens[i] end
  if total == 0 then return tbl end
  local char_width = CHAR_WIDTH
  local min_widths = {}
  for i = 1, ncols do
    min_widths[i] = min_lens[i] * char_width + 0.03
  end
  local widths = {}
  for i = 1, ncols do widths[i] = max_lens[i] / total end
  local clamped = {}
  local clamped_sum = 0
  local changed = true
  while changed do
    changed = false
    local unclamped_total = 0
    for i = 1, ncols do
      if not clamped[i] then
        unclamped_total = unclamped_total + max_lens[i]
      end
    end
    local rem = 1.0 - clamped_sum
    for i = 1, ncols do
      if not clamped[i] then
        local w = (unclamped_total > 0 and rem > 0)
          and (rem * (max_lens[i] / unclamped_total))
          or (1.0 / ncols)
        if w < min_widths[i] and min_widths[i] <= 0.6 then
          clamped[i] = true
          clamped_sum = clamped_sum + min_widths[i]
          widths[i] = min_widths[i]
          changed = true
          break
        else
          widths[i] = w
        end
      end
    end
  end
  local final_sum = 0
  for i = 1, ncols do final_sum = final_sum + widths[i] end
  if final_sum > 0 and math.abs(final_sum - 1.0) > 0.001 then
    for i = 1, ncols do widths[i] = widths[i] / final_sum end
  end
  for i, colspec in ipairs(tbl.colspecs) do colspec[2] = widths[i] end
  estilar_cabeceira(tbl)
  return tbl
end

estilar_cabeceira = function(tbl)
  -- Só LaTeX: noutros formatos (DOCX) o RawInline descártase e o único
  -- efecto sería perder o **negro** que escribise o usuario na cabeceira.
  if not FORMAT:match("latex") then return end
  if tbl.head and tbl.head.rows then
    for _, row in ipairs(tbl.head.rows) do
      for _, cell in ipairs(row.cells) do
        for _, block in ipairs(cell.contents) do
          if block.t == "Para" or block.t == "Plain" then
            local new_inlines = {}
            table.insert(new_inlines, pandoc.RawInline("latex",
              "\\textsf{\\bfseries\\color{heading-section}{}"))
            for _, inline in ipairs(block.content) do
              if inline.t == "Strong" then
                for _, inner in ipairs(inline.content) do
                  table.insert(new_inlines, inner)
                end
              else
                table.insert(new_inlines, inline)
              end
            end
            table.insert(new_inlines, pandoc.RawInline("latex", "}"))
            block.content = new_inlines
          end
        end
      end
    end
  end
end
local ESCAPES = {
  ["\\"] = "\\textbackslash{}", ["{"]  = "\\{", ["}"]  = "\\}",
  ["$"]  = "\\$", ["&"]  = "\\&", ["#"]  = "\\#", ["_"]  = "\\_",
  ["%"]  = "\\%", ["~"]  = "\\char126{}", ["^"]  = "\\textasciicircum{}",
}
local function escape(s)
  return (s:gsub("[\\{}$&#_%%~^]", ESCAPES))
end
local function add_op_breaks(s)
  s = s:gsub("(%\\&%\\&)", "%1\\allowbreak{}")
  s = s:gsub("(%|%|)",     "%1\\allowbreak{}")
  s = s:gsub("(%()",       "%1\\allowbreak{}")
  s = s:gsub("(%;)",       "%1\\allowbreak{}")
  s = s:gsub("(,)",        "%1\\allowbreak{}")
  return s
end
local function add_path_breaks(s)
  s = s:gsub("://", "\1")
  s = s:gsub("(\\_)",         "%1\\discretionary{}{}{}")
  s = s:gsub("([/%.:=%?%-])", "%1\\discretionary{}{}{}")
  s = s:gsub("\1", "://\\discretionary{}{}{}")
  return s
end
local function code_to_mbox(el)
  if not FORMAT:match("latex") then return nil end
  local text = el.text
  local has_break = text:match("[/\\%.:=%?%-_]") ~= nil
  if (#text <= 8) or (#text <= MAX_MBOX_LEN and not has_break) then
    return pandoc.RawInline("latex",
      "\\leavevmode\\strut\\allowbreak\\mbox{\\texttt{" .. escape(text) .. "}}")
  end
  local esc = add_path_breaks(add_op_breaks(escape(text)))
  return pandoc.RawInline("latex", "\\leavevmode\\strut\\texttt{" .. esc .. "}")
end
return {
  { Table = Table },
  { Code = code_to_mbox },
}
