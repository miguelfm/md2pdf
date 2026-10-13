-- compact-code.lua — Bloques de código compactos para listados longos
--
-- Aplica un formato tipográfico máis compacto (letra de 10 pt e interliñado
-- de 1,30x) a bloques de código seleccionados, mantendo a configuración
-- pedagóxica por defecto máis folgada (10,8 pt con 1,43x) no resto do documento.
--
-- Sintaxe en Markdown:
--   ```python {.compact}
--   código longo aquí...
--   ```
--   ou con atributo:
--   ```python {compact=true}
--   código longo aquí...
--   ```
--   ou en galego:
--   ```python {.compacto}
--   ...
--   ```
--
-- Limiar automático opcional:
--   Pódese activar no front matter YAML ou en metadatos de Pandoc:
--     code-compact-threshold: 25
--   Calquera bloque que teña 25 liñas ou máis compactarase de xeito automático.
--   Por defecto o limiar é 0 (desactivado: só manual).
--
-- Desactivación global:
--   Pódese desactivar con 'code-compact: false' ou 'compact-code: false'.
--
-- Saída LaTeX:
--   Envolve o bloque nunha contorna CompactBlock que redefine localmente
--   o estilo md2pdf-code-font de tcolorbox.
--
-- Saída HTML:
--   Engade a clase 'compact' ao CodeBlock para estilizalo con CSS.
--

local threshold = 0
local enabled = true

local function get_meta(meta)
  if not meta then return meta end

  local val = meta['code-compact']
  if val == nil then val = meta['compact-code'] end
  if val ~= nil then
    enabled = pandoc.utils.stringify(val):lower() ~= 'false'
  end

  local th = meta['code-compact-threshold']
  if th == nil then th = meta['compact-threshold'] end
  if th ~= nil then
    threshold = tonumber(pandoc.utils.stringify(th)) or 0
  end

  return meta
end

local function count_lines(text)
  local count = 1
  for _ in text:gmatch('\n') do
    count = count + 1
  end
  return count
end

local function is_compact(block)
  -- 1. Atributo explícito: compact=true / compact / compact="1"
  local attr = block.attributes['compact']
  if attr ~= nil then
    local s = pandoc.utils.stringify(attr):lower()
    if s ~= 'false' and s ~= '0' then
      return true
    elseif s == 'false' or s == '0' then
      return false
    end
  end

  -- 2. Clase explícita: .compact ou .compacto
  for _, cls in ipairs(block.classes or {}) do
    local l = cls:lower()
    if l == 'compact' or l == 'compacto' then
      return true
    end
  end

  -- 3. Limiar automático por liñas
  if threshold > 0 and count_lines(block.text) >= threshold then
    return true
  end

  return false
end

local function process_codeblock(block)
  if not enabled then return nil end
  if not is_compact(block) then return nil end

  if not block.classes:includes('compact') then
    block.classes:insert('compact')
  end

  if FORMAT:match('latex') then
    return {
      pandoc.RawBlock('latex', '\\begin{CompactBlock}'),
      block,
      pandoc.RawBlock('latex', '\\end{CompactBlock}')
    }
  end

  return block
end

return {
  { Meta = get_meta },
  { CodeBlock = process_codeblock }
}
