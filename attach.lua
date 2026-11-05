-- attach.lua — Ficheiros adxuntos cunha ligazón no texto
--
-- Sintaxe: unha ligazón local coa clase attach.
--   [`code/A8/DuplicateCost.java`](code/A8/DuplicateCost.java){.attach}
--
-- LuaLaTeX: o ficheiro vai dentro do PDF (attachfile2) e o texto da
-- ligazón, seguido dunha icona de clip, abre ou garda o adxunto nos
-- visores que o admiten. O visor amosa só o nome do ficheiro, sen a
-- ruta. O tipo MIME dedúcese da extensión; mimetype=... cámbiao.
-- HTML: ligazón normal ao ficheiro, co atributo download.
-- DOCX e as demais saídas: ligazón normal.
--
-- A ruta é relativa ao directorio de traballo, que é o do documento.
-- Un ficheiro que non existe ou un URL detén a conversión, para que
-- ningún PDF saia cunha ligazón que non leva nada.

local TEXT_EXTENSIONS = {
  c = true, conf = true, cpp = true, css = true, csv = true, gift = true,
  h = true, html = true, ini = true, java = true, js = true, json = true,
  kt = true, md = true, php = true, properties = true, ps1 = true,
  py = true, sh = true, sql = true, ts = true, txt = true, xml = true,
  yaml = true, yml = true,
}

local function basename(target)
  return target:match('([^/\\]+)$') or target
end

local function exists(target)
  local file = io.open(target, 'rb')
  if file then
    file:close()
    return true
  end
  return false
end

-- Os valores van entre chaves nas opcións de attachfile2: as chaves, as
-- barras e os comentarios do nome romperían a lista.
local function option_value(text)
  return (text:gsub('[{}\\%%]', ''))
end

-- O nome que ve o visor pasa por \pdfstringdef: sen escapar, LaTeX le o
-- _ dun nome de entrega como subíndice e quítao.
local PDFSTRING_ESCAPES = {
  ['_'] = '\\_', ['#'] = '\\#', ['&'] = '\\&', ['$'] = '\\$',
  ['~'] = '\\textasciitilde{}', ['^'] = '\\textasciicircum{}',
}

local function pdfstring_value(text)
  return (option_value(text):gsub('[_#&$~^]', PDFSTRING_ESCAPES))
end

local function mimetype(link, name)
  local explicit = link.attributes['mimetype']
  if explicit and explicit ~= '' then
    return explicit
  end
  local extension = (name:match('%.([%w]+)$') or ''):lower()
  return TEXT_EXTENSIONS[extension] and 'text/plain'
    or 'application/octet-stream'
end

function Link(link)
  if not link.classes:includes('attach') then
    return nil
  end
  local target = link.target
  if target:match('^%a[%w+.-]*:') then
    error('attach.lua: o adxunto ten que ser un ficheiro local, non '
      .. target)
  end
  if not exists(target) then
    error('attach.lua: non existe o ficheiro adxunto ' .. target)
  end
  local name = basename(target)

  if FORMAT:match('latex') then
    local options = string.format(
      'mimetype=%s,ucfilespec={%s},description={%s}',
      option_value(mimetype(link, name)), pdfstring_value(name),
      pdfstring_value(name))
    -- \mdattachfile está no preámbulo: o texto da ligazón e a icona
    local inlines = {
      pandoc.RawInline('latex',
        '\\mdattachfile{' .. options .. '}{' .. target .. '}{'),
    }
    for _, inline in ipairs(link.content) do
      table.insert(inlines, inline)
    end
    table.insert(inlines, pandoc.RawInline('latex', '}'))
    return inlines
  end

  link.classes = link.classes:filter(function(c) return c ~= 'attach' end)
  link.attributes['mimetype'] = nil
  if FORMAT:match('html') then
    link.attributes['download'] = name
  end
  return link
end
