-- terminal-blocks.lua — Diferenciación visual de bloques de código de terminal
--
-- Aplica un estilo de fondo sutilmente diferenciado aos bloques de código
-- que representan ordes de terminal ou consola (bash, sh, zsh, powershell, etc.)
-- fronte a ficheiros de código de linguaxes de programación (php, python, etc.),
-- sen engadir símbolos de prompt nin caracteres adicionais para evitar que o
-- alumnado os copie por erro ao executar os comandos.
--
-- Saída LaTeX:
--   Envolve o bloque nunha contorna TerminalBlock que redefine localmente
--   code-bg e code-border.
--
-- Saída HTML:
--   Engade a clase 'terminal' ao CodeBlock para estilizalo con CSS.
--
-- Desactivación:
--   Pódese desactivar con 'terminal-blocks: false' ou 'terminal-style: false'
--   no front matter YAML ou nos metadatos de Pandoc.

local TERMINAL_CLASSES = {
  bash = true,
  sh = true,
  shell = true,
  zsh = true,
  console = true,
  terminal = true,
  powershell = true,
  posh = true,
  pwsh = true,
  cmd = true,
  bat = true,
  batch = true,
  fish = true,
  dos = true,
  ksh = true,
  csh = true,
  tcsh = true,
}

local function is_terminal(block)
  for _, cls in ipairs(block.classes or {}) do
    if TERMINAL_CLASSES[cls:lower()] then
      return true
    end
  end
  return false
end

local enabled = true

local function get_meta(meta)
  if not meta then return meta end
  local val = meta['terminal-blocks']
  if val == nil then val = meta['terminal-style'] end
  if val ~= nil then
    enabled = pandoc.utils.stringify(val):lower() ~= 'false'
  end
  return meta
end

local function process_codeblock(block)
  if not enabled then return nil end
  if not is_terminal(block) then return nil end

  if not block.classes:includes('terminal') then
    block.classes:insert('terminal')
  end

  if FORMAT:match('latex') then
    return {
      pandoc.RawBlock('latex', '\\begin{TerminalBlock}'),
      block,
      pandoc.RawBlock('latex', '\\end{TerminalBlock}')
    }
  end

  return block
end

return {
  { Meta = get_meta },
  { CodeBlock = process_codeblock }
}
