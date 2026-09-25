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
-- Ancho mínimo por palabras: ningunha columna debe ser máis estreita que a
-- palabra máis longa sen espazos das súas celas, ou LaTeX divídea con guión.
-- Anchos (pt) medidos en \small co corpo de 13 pt: Source Serif 4 no corpo
-- e Source Sans 3 negra na cabeceira. As letras con til miden o mesmo ca sen
-- ela; o resto de caracteres conta OTHER_PT. A Source Code Pro, coa escala
-- MatchLowercase que lle pon md2pdf.latex, dá MONO_PT por carácter. O
-- espazo entre palabras mide SPACE_PT; con texto aliñado á esquerda TeX case
-- nunca o encolle, e prefire levar a palabra á liña seguinte.
local SERIF_PT = {
  ["a"]=6.04, ["b"]=6.84, ["c"]=5.79, ["d"]=6.73, ["e"]=6.05, ["f"]=4.20,
  ["g"]=6.14, ["h"]=7.13, ["i"]=3.54, ["j"]=3.29, ["k"]=6.49, ["l"]=3.54,
  ["m"]=10.69, ["n"]=7.19, ["o"]=6.51, ["p"]=6.92, ["q"]=6.61, ["r"]=5.02,
  ["s"]=5.15, ["t"]=3.86, ["u"]=6.92, ["v"]=5.99, ["w"]=9.06, ["x"]=6.24,
  ["y"]=6.07, ["z"]=5.41, ["A"]=7.88, ["B"]=7.46, ["C"]=7.49, ["D"]=8.42,
  ["E"]=7.15, ["F"]=6.87, ["G"]=8.09, ["H"]=9.35, ["I"]=4.40, ["J"]=4.44,
  ["K"]=7.91, ["L"]=7.07, ["M"]=10.70, ["N"]=8.72, ["O"]=8.39, ["P"]=6.99,
  ["Q"]=8.39, ["R"]=7.72, ["S"]=6.07, ["T"]=7.17, ["U"]=8.62, ["V"]=8.00,
  ["W"]=11.41, ["X"]=7.69, ["Y"]=7.51, ["Z"]=6.54, ["0"]=5.93, ["1"]=5.93,
  ["2"]=5.93, ["3"]=5.93, ["4"]=5.93, ["5"]=5.93, ["6"]=5.93, ["7"]=5.93,
  ["8"]=5.93, ["9"]=5.93, ["."]=3.56, [","]=3.56, [";"]=3.56, [":"]=3.56,
  ["-"]=3.70, ["_"]=6.07, ["("]=4.02, [")"]=4.02, ["/"]=3.91, ["'"]=2.51,
}
local SANS_BOLD_PT = {
  ["a"]=6.25, ["b"]=6.80, ["c"]=5.54, ["d"]=6.80, ["e"]=6.14, ["f"]=4.05,
  ["g"]=6.33, ["h"]=6.77, ["i"]=3.27, ["j"]=3.30, ["k"]=6.50, ["l"]=3.39,
  ["m"]=10.17, ["n"]=6.79, ["o"]=6.58, ["p"]=6.80, ["q"]=6.80, ["r"]=4.72,
  ["s"]=5.26, ["t"]=4.54, ["u"]=6.74, ["v"]=6.20, ["w"]=9.21, ["x"]=6.10,
  ["y"]=6.18, ["z"]=5.46, ["A"]=6.80, ["B"]=7.18, ["C"]=6.90, ["D"]=7.53,
  ["E"]=6.50, ["F"]=6.22, ["G"]=7.57, ["H"]=8.00, ["I"]=3.57, ["J"]=6.04,
  ["K"]=7.28, ["L"]=6.14, ["M"]=9.04, ["N"]=7.89, ["O"]=8.11, ["P"]=7.07,
  ["Q"]=8.11, ["R"]=7.27, ["S"]=6.60, ["T"]=6.60, ["U"]=7.89, ["V"]=6.60,
  ["W"]=9.64, ["X"]=6.73, ["Y"]=6.23, ["Z"]=6.42, ["0"]=6.26, ["1"]=6.26,
  ["2"]=6.26, ["3"]=6.26, ["4"]=6.26, ["5"]=6.26, ["6"]=6.26, ["7"]=6.26,
  ["8"]=6.26, ["9"]=6.26, ["."]=3.56, [","]=3.56, [";"]=3.56, [":"]=3.56,
  ["-"]=3.94, ["_"]=5.93, ["("]=4.08, [")"]=4.08, ["/"]=4.02, ["'"]=3.56,
}
local OTHER_PT = 6.4
local SPACE_PT = 2.76
local MONO_PT = 6.96
local STRONG_FACTOR = 1.08
local WORD_MARGIN = 1.03
-- Pandoc reparte (\linewidth - 2(n-1)\tabcolsep) entre as n columnas.
local LINE_PT = 483.7     -- \linewidth en A4 con marxes de 20 mm
local TABCOLSEP_PT = 6
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
-- Letra base das letras latinas con til ou diacrítico (Latin-1).
local BASE_LETTER = {}
for code, base in pairs({
  [0xC0] = "AAAAAA", [0xC7] = "C", [0xC8] = "EEEE", [0xCC] = "IIII",
  [0xD1] = "N", [0xD2] = "OOOOO", [0xD9] = "UUUU", [0xDD] = "Y",
  [0xE0] = "aaaaaa", [0xE7] = "c", [0xE8] = "eeee", [0xEC] = "iiii",
  [0xF1] = "n", [0xF2] = "ooooo", [0xF9] = "uuuu", [0xFD] = "y",
}) do
  for k = 1, #base do BASE_LETTER[code + k - 1] = base:sub(k, k) end
end
local function text_pt(text, font)
  local pt = 0
  for _, code in utf8.codes(text) do
    local c = code < 128 and string.char(code) or BASE_LETTER[code]
    pt = pt + (c and font[c] or OTHER_PT)
  end
  return pt
end
local function is_letter(code)
  return (code < 128 and string.char(code):match("%a") ~= nil) or code >= 0xC0
end
-- Palabras dunha cela, liña a liña (un <br> empeza liña nova). Unha palabra
-- acaba nun espazo, salto de liña ou tras un guión explícito; o código en
-- liña e as URL van á parte. Cada palabra leva o seu ancho (pt), se vai tras
-- un espazo e dous anchos para o mínimo da columna:
--   need  o que obriga a axustar a táboa;
--   full  o que se lle dá á columna cando se axusta.
-- TeX só divide palabras con polo menos HYPHEN_MIN_LETTERS letras seguidas,
-- e a esas súmaselles WORD_MARGIN. As que non pode dividir («CA1.8»,
-- «/etc/php/8.5/cli/php.ini») non se parten: como moito invaden o espazo
-- entre columnas (2\tabcolsep = 12 pt), así que só obrigan a axustar se
-- invadirían máis de OVERFLOW_PT. O código e as URL contan ata o seu
-- primeiro punto de corte.
local HYPHEN_MIN_LETTERS = 4
local OVERFLOW_PT = 8
local function cell_lines(inlines, font)
  local lines, line = {}, {}
  local cur, run, maxrun, space = 0, 0, 0, false
  local function push(word)
    word.space = space
    table.insert(line, word)
    space = false
  end
  local function close()
    if cur > 0 then
      if maxrun < HYPHEN_MIN_LETTERS then
        push({ pt = cur, need = cur - OVERFLOW_PT, full = cur })
      else
        push({ pt = cur, need = cur * WORD_MARGIN, full = cur * WORD_MARGIN })
      end
    end
    cur, run, maxrun = 0, 0, 0
  end
  local function walk(list, factor)
    for _, inline in ipairs(list) do
      local t = inline.t
      if t == "Str" then
        for _, code in utf8.codes(inline.text) do
          local c = utf8.char(code)
          cur = cur + text_pt(c, font) * factor
          if is_letter(code) then
            run = run + 1
            if run > maxrun then maxrun = run end
          else
            run = 0
          end
          if c == "-" then close() end
        end
      elseif t == "Space" or t == "SoftBreak" then
        close()
        space = true
      elseif t == "LineBreak" or t == "RawInline" then
        close()
        table.insert(lines, line)
        line, space = {}, false
      elseif t == "Code" then
        close()
        local min = unbreakable_len(inline.text) * MONO_PT
        push({ pt = utf8.len(inline.text) * MONO_PT, need = min, full = min })
      elseif t == "Link" and (inline.classes:includes("uri")
          or inline.classes:includes("email")) then
        close()
        local text = pandoc.utils.stringify(inline.content)
        local min = longest_segment(text) * OTHER_PT
        push({ pt = text_pt(text, font), need = min, full = min })
      elseif t == "Math" or t == "Note" then
        close()
      elseif t == "Strong" then
        walk(inline.content, factor * STRONG_FACTOR)
      elseif inline.content then
        walk(inline.content, factor)
      end
    end
  end
  walk(inlines, 1)
  close()
  table.insert(lines, line)
  return lines
end
-- Liñas que ocupa unha cela nunha columna de width pt, enchendo cada liña
-- coas palabras que caben. Unha palabra máis ancha ca columna ocupa as liñas
-- que precise.
local function count_lines(lines, width)
  local n = 0
  for _, words in ipairs(lines) do
    local cur = 0
    n = n + 1
    for _, w in ipairs(words) do
      local add = w.pt + ((cur > 0 and w.space) and SPACE_PT or 0)
      if cur > 0 and cur + add > width then
        n = n + 1
        cur = w.pt
      else
        cur = cur + add
      end
      if cur > width then
        local extra = math.ceil(cur / width) - 1
        n = n + extra
        cur = cur - extra * width
      end
    end
  end
  return n
end
-- Altura estimada da táboa en liñas: en cada fila manda a cela máis alta.
local function table_height(rows, widths, avail)
  local h = 0
  for _, row in ipairs(rows) do
    local m = 1
    for i, lines in pairs(row) do
      local n = count_lines(lines, math.max(widths[i] * avail, 1))
      if n > m then m = n end
    end
    h = h + m
  end
  return h
end
local function analyze_cells(tbl, ncols)
  local max_lens, min_lens, word_pts, word_rows = {}, {}, {}, {}
  for i = 1, ncols do
    max_lens[i] = 1
    min_lens[i] = 0
    word_pts[i] = { need = 0, full = 0 }
  end
  local function process_words(rows, font)
    for _, row in ipairs(rows) do
      local cells = {}
      for i, cell in ipairs(row.cells) do
        if i <= ncols then
          cells[i] = {}
          for _, block in ipairs(cell.contents) do
            if block.content then
              for _, line in ipairs(cell_lines(block.content, font)) do
                table.insert(cells[i], line)
                for _, w in ipairs(line) do
                  local wp = word_pts[i]
                  if w.need > wp.need then wp.need = w.need end
                  if w.full > wp.full then wp.full = w.full end
                end
              end
            end
          end
        end
      end
      table.insert(word_rows, cells)
    end
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
    process_words(tbl.head.rows, SANS_BOLD_PT)
  end
  for _, body in ipairs(tbl.bodies) do
    process_rows(body.body)
    process_words(body.body, SERIF_PT)
  end
  return max_lens, min_lens, word_pts, word_rows
end
-- Anchos manuais: se a liña separadora dunha táboa ten guións de lonxitude
-- distinta, Pandoc xa calcula anchos relativos a partir deles. Neses casos
-- respéctanse e non se calculan automaticamente. Guións iguais (o habitual)
-- dan anchos iguais, e entón segue o cálculo automático.
-- Pandoc conta tamén os dous puntos de aliñamento: |:---:|---| dá anchos
-- distintos aínda que os guións sexan iguais. Por iso compróbase se hai algún
-- número de guións d, igual para todas as columnas, que explique os anchos
-- (ancho proporcional a d + dous puntos); se o hai, non son manuais.
local function dous_puntos(alineacion)
  if alineacion == "AlignCenter" then return 2 end
  if alineacion == "AlignLeft" or alineacion == "AlignRight" then return 1 end
  return 0
end
local function anchos_manuais(tbl)
  local ws, cs = {}, {}
  for i, colspec in ipairs(tbl.colspecs) do
    if type(colspec[2]) ~= "number" then return false end
    ws[i], cs[i] = colspec[2], dous_puntos(colspec[1])
  end
  for d = 1, 200 do
    local total = 0
    for i = 1, #ws do total = total + d + cs[i] end
    local encaixa = true
    for i = 1, #ws do
      if math.abs(ws[i] - (d + cs[i]) / total) > 0.001 then
        encaixa = false
        break
      end
    end
    if encaixa then return false end
  end
  return true
end
-- Se os mínimos non caben xuntos, cúmprense os máis pequenos (mentres ás
-- demais columnas lles quede polo menos MIN_SHARE de media) e o resto
-- repártese entre as columnas de palabras máis longas, en proporción ao seu
-- mínimo: esas partirán a palabra, pero as outras non.
local MIN_SHARE = 0.1
local function repartir_sen_sitio(widths, floor)
  local ncols = #widths
  local order, weight, rest = {}, {}, 0
  for i = 1, ncols do
    weight[i] = floor[i] > 0 and floor[i] or widths[i]
    rest = rest + weight[i]
    if floor[i] > 0 then table.insert(order, i) end
  end
  table.sort(order, function(a, b) return floor[a] < floor[b] end)
  local fixed, used, nrest = {}, 0, ncols
  for _, i in ipairs(order) do
    if (1 - used - floor[i]) / (nrest - 1) < MIN_SHARE then break end
    fixed[i] = true
    used = used + floor[i]
    rest = rest - weight[i]
    nrest = nrest - 1
  end
  for i = 1, ncols do
    widths[i] = fixed[i] and floor[i] or (1 - used) * weight[i] / rest
  end
end
-- Ensancha as columnas máis estreitas que a súa palabra máis longa (como o
-- mínimo por cabeceira, só se non pasa do 60 %). O espazo que falta sae das
-- outras columnas punto a punto: cada vez da que menos altura engade á
-- táboa, simulando o reparto das palabras en liñas, e en empate da que máis
-- lle sobra sobre o seu propio mínimo, que adoita ser a de máis texto.
-- A estimación dos anchos pode errar nun par de puntos, así que cada columna
-- valórase LOOKAHEAD_PT máis estreita do que quedaría: unha liña xusto no
-- límite contará como partida e esa columna só cederá se non hai outra.
local LOOKAHEAD_PT = 2
local function axustar_a_palabras(widths, min_widths, word_pts, rows)
  local ncols = #widths
  local avail = LINE_PT - 2 * TABCOLSEP_PT * (ncols - 1)
  local floor, wmins, raise = {}, {}, {}
  local sum_floor, deficit = 0, 0
  for i = 1, ncols do
    local wmin = word_pts[i].full / avail
    if wmin > 0.6 then wmin = 0 end
    local hmin = min_widths[i] <= 0.6 and min_widths[i] or 0
    floor[i] = math.max(wmin, hmin)
    wmins[i] = wmin
    sum_floor = sum_floor + floor[i]
    if wmin > widths[i] and word_pts[i].need / avail > widths[i] then
      raise[i] = true
      deficit = deficit + wmin - widths[i]
    end
  end
  if deficit == 0 then return end
  if sum_floor > 1 then
    repartir_sen_sitio(widths, floor)
    return
  end
  for i = 1, ncols do
    if raise[i] then widths[i] = wmins[i] end
  end
  local step, lookahead = 1 / avail, LOOKAHEAD_PT / avail
  while deficit > 1e-9 do
    local cut = math.min(step, deficit)
    local best, best_h, best_slack
    for j = 1, ncols do
      local slack = widths[j] - floor[j]
      if slack >= cut then
        local w = widths[j]
        widths[j] = w - cut - lookahead
        local h = table_height(rows, widths, avail)
        widths[j] = w
        if not best or h < best_h or (h == best_h and slack > best_slack) then
          best, best_h, best_slack = j, h, slack
        end
      end
    end
    if not best then break end
    widths[best] = widths[best] - cut
    deficit = deficit - cut
  end
  if deficit > 1e-9 then
    local sum = 0
    for i = 1, ncols do sum = sum + widths[i] end
    for i = 1, ncols do widths[i] = widths[i] / sum end
  end
end
function Table(tbl)
  local ncols = #tbl.colspecs
  if ncols == 0 then return tbl end
  if anchos_manuais(tbl) then
    estilar_cabeceira(tbl)
    return tbl
  end
  local max_lens, min_lens, word_pts, word_rows = analyze_cells(tbl, ncols)
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
  axustar_a_palabras(widths, min_widths, word_pts, word_rows)
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
