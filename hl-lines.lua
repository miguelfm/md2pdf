-- hl-lines.lua — Resaltado de liñas en bloques de código
--
-- Sintaxe:
--   ```php {hl="1,3,5-7"}
--   código aquí
--   ```
--
-- Funciona con LuaLaTeX + fvextra (highlightlines).
-- Nas demais saídas conserva o bloque e o atributo hl.
--
-- A cor de fondo defínese no preámbulo con:
--   \fvset{highlightcolor=<cor>}
-- Por defecto fvextra usa amarelo. Para un amarelo máis suave:
--   \colorlet{hl-line-bg}{yellow!18!white}
--   \fvset{highlightcolor=hl-line-bg}

-- ── Parsear especificación de liñas ──────────────────────────
-- Entrada:  "1, 3, 5-7, 10"
-- Saída:    "1,3,5,6,7,10"
local function parse_hl(spec)
  local nums = {}
  local seen = {}
  for part in spec:gmatch('[^,]+') do
    part = part:match('^%s*(.-)%s*$')
    local a, b = part:match('^(%d+)%s*[-–]%s*(%d+)$')  -- soporta - e –
    if a then
      for i = tonumber(a), tonumber(b) do
        if not seen[i] then seen[i] = true; table.insert(nums, i) end
      end
    else
      local n = tonumber(part)
      if n and not seen[n] then
        seen[n] = true; table.insert(nums, n)
      end
    end
  end
  table.sort(nums)
  return table.concat(nums, ',')
end

-- ── Filtro principal ──────────────────────────────────────────
function CodeBlock(block)
  if not FORMAT:match('latex') then return nil end

  local hl = block.attributes['hl']
  if not hl or hl == '' then return nil end

  local lines_str = parse_hl(hl)
  if lines_str == '' then return nil end

  -- Clonar sen o atributo hl para evitar recursión
  local clean = block:clone()
  clean.attributes['hl'] = nil

  -- Conservar o CodeBlock para que o escritor final de Pandoc xere
  -- as definicións de resaltado e aplique o tema seleccionado.
  -- \fvset{highlightlines=...} actívase só para este bloque.
  return {
    pandoc.RawBlock('latex',
      '\\fvset{highlightlines={' .. lines_str .. '}}'),
    clean,
    pandoc.RawBlock('latex', '\\fvset{highlightlines={}}')
  }
end
