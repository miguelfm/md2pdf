-- html.lua — Adaptacións semánticas para a saída HTML de md2pdf.
--
-- Mantén o Markdown como fonte común e deixa a presentación ao CSS:
--   * callouts ::: tip / warning / ... → divs con clases semánticas
--   * numeración de figuras e táboas
--   * referencias @fig: / @tbl: / @tab: → ligazóns internas
--   * extracción de {#tbl:...} cando Pandoc o deixa dentro do caption
--
-- O resaltado de liñas hl="..." non precisa transformación aquí: Pandoc
-- conserva o atributo como data-hl e md2pdf.html aplícao despois con JS.

local stringify = pandoc.utils.stringify

local CALL_OUTS = {
  note = { label = 'Nota', kind = 'note' },
  nota = { label = 'Nota', kind = 'note' },
  tip = { label = 'Consello', kind = 'tip' },
  consello = { label = 'Consello', kind = 'tip' },
  warning = { label = 'Atención', kind = 'warning' },
  ['atención'] = { label = 'Atención', kind = 'warning' },
  atencion = { label = 'Atención', kind = 'warning' },
  danger = { label = 'Crítico', kind = 'danger' },
  perigo = { label = 'Crítico', kind = 'danger' },
  info = { label = 'Info', kind = 'info' },
}

local figure_no = 0
local table_no = 0
local callout_no = 0
local refs = {}

local function has_class(el, wanted)
  for _, cls in ipairs(el.classes or {}) do
    if cls == wanted then return true end
  end
  return false
end

local function callouts_enabled(meta)
  local value = meta['md2pdf-callouts']
  if value == nil then return true end
  return stringify(value):lower() ~= 'false'
end

local function transform_callout(div)
  if has_class(div, 'callout') then return div end

  local style = nil
  for _, cls in ipairs(div.classes) do
    -- ::: Nota / ::: Atención: string.lower só baixa ASCII, abonda aquí
    -- porque os acentos das claves xa van en minúscula.
    local key = cls:lower()
    if CALL_OUTS[key] then
      style = CALL_OUTS[key]
      break
    end
  end
  if not style then return nil end

  callout_no = callout_no + 1
  div.classes:insert('callout')
  div.classes:insert('callout-' .. style.kind)
  div.attributes['role'] = 'note'

  local title_id
  if div.identifier and div.identifier ~= '' then
    title_id = div.identifier .. '-title'
  else
    title_id = 'md2pdf-callout-' .. tostring(callout_no) .. '-title'
  end
  div.attributes['aria-labelledby'] = title_id

  local title = pandoc.Div(
    { pandoc.Plain({ pandoc.Str(style.label) }) },
    pandoc.Attr(title_id, { 'callout-title' })
  )
  div.content:insert(1, title)
  return div
end

local function caption_blocks(caption)
  if not caption then return nil end
  if caption.long then return caption.long end
  -- Compatibilidade con versións de Pandoc onde Caption se comporta como lista.
  if #caption > 0 and caption[1] and caption[1].t then return caption end
  return nil
end

local function remove_table_id_from_caption(tbl)
  local id = tbl.identifier or ''
  local blocks = caption_blocks(tbl.caption)
  if not blocks or #blocks == 0 then return id end

  local last = blocks[#blocks]
  if not last or not last.content then return id end

  for j = #last.content, 1, -1 do
    local inl = last.content[j]
    if inl.t == 'Str' then
      local found = inl.text:match('{#([Tt][ba][lb]:[%w%-_:]+)}')
      if found then
        if id == '' then id = found end
        local cleaned = inl.text:gsub('%s*{#[%w%-_:]+}%s*', '')
        if cleaned == '' then
          table.remove(last.content, j)
          if j > 1 and last.content[j - 1].t == 'Space' then
            table.remove(last.content, j - 1)
          end
        else
          last.content[j] = pandoc.Str(cleaned)
        end
        break
      end
    elseif inl.t == 'Span' and inl.identifier and
           (inl.identifier:match('^[Tt]bl:') or inl.identifier:match('^[Tt]ab:')) then
      if id == '' then id = inl.identifier end
      table.remove(last.content, j)
      for k = #inl.content, 1, -1 do
        table.insert(last.content, j, inl.content[k])
      end
      break
    end
  end

  if id ~= '' then tbl.identifier = id end
  return id
end

local function caption_has_label(blocks)
  if not blocks or #blocks == 0 then return false end
  local first = blocks[1]
  if not first or not first.content or #first.content == 0 then return false end
  local inl = first.content[1]
  return inl.t == 'Span' and has_class(inl, 'caption-label')
end

local function add_caption_label(caption, noun, number)
  local blocks = caption_blocks(caption)
  if not blocks or #blocks == 0 or caption_has_label(blocks) then return end

  local first = blocks[1]
  if not first.content then return end

  local original = pandoc.List()
  for _, inl in ipairs(first.content) do original:insert(inl) end

  first.content = pandoc.Inlines({
    pandoc.Span(
      { pandoc.Str(noun .. ' ' .. tostring(number) .. '.') },
      pandoc.Attr('', { 'caption-label' })
    ),
    pandoc.Space(),
    pandoc.Span(original, pandoc.Attr('', { 'caption-text' })),
  })
end

local function register_ref(id, kind, number)
  if not id or id == '' then return end
  local canonical = id:sub(1, 1):lower() .. id:sub(2)
  refs[canonical] = { target = id, kind = kind, number = number }

  -- tbl: e tab: son alias para a mesma familia de referencias.
  local suffix = canonical:match('^[Tt]bl:(.+)$')
  if suffix then refs['tab:' .. suffix] = refs[canonical] end
  suffix = canonical:match('^[Tt]ab:(.+)$')
  if suffix then refs['tbl:' .. suffix] = refs[canonical] end
end


local function fill_empty_figure_alt(fig, description)
  if not description or description == '' then return fig end
  return fig:walk({
    Image = function(img)
      if stringify(img.caption or {}) == '' then
        img.caption = pandoc.Inlines({ pandoc.Str(description) })
      end
      if not img.attributes['role'] or img.attributes['role'] == '' then
        img.attributes['role'] = 'img'
      end
      if not img.attributes['aria-label'] or img.attributes['aria-label'] == '' then
        img.attributes['aria-label'] = description
      end
      return img
    end
  })
end

local function transform_figure(fig)
  local blocks = caption_blocks(fig.caption)
  if blocks and #blocks > 0 and stringify(blocks) ~= '' then
    local description = stringify(blocks)
    fig = fill_empty_figure_alt(fig, description)
    figure_no = figure_no + 1
    add_caption_label(fig.caption, 'Figura', figure_no)
    register_ref(fig.identifier, 'figure', figure_no)
  elseif fig.identifier and fig.identifier ~= '' then
    -- Unha figura sen caption pode seguir sendo destino dunha ligazón, pero non
    -- inventamos un número que non se amosa.
    refs[fig.identifier] = { target = fig.identifier, kind = 'figure', number = nil }
  end
  return fig
end

local function transform_table(tbl)
  local id = remove_table_id_from_caption(tbl)
  local blocks = caption_blocks(tbl.caption)
  if blocks and #blocks > 0 and stringify(blocks) ~= '' then
    table_no = table_no + 1
    add_caption_label(tbl.caption, 'Táboa', table_no)
    register_ref(id, 'table', table_no)
  elseif id ~= '' then
    refs[id] = { target = id, kind = 'table', number = nil }
  end

  -- O scroll horizontal pertence ao contedor, non ao elemento <table>.
  -- Así consérvase a semántica nativa da táboa e obtense un comportamento
  -- responsive limpo en pantallas estreitas.
  return pandoc.Div({ tbl }, pandoc.Attr('', { 'table-wrapper' }))
end

local function is_crossref(id)
  return id:match('^[Ff]ig:') or id:match('^[Tt]bl:') or id:match('^[Tt]ab:')
end

local function canonical_ref(id)
  return id:sub(1, 1):lower() .. id:sub(2)
end

local function ref_word(id, kind)
  local upper = id:sub(1, 1):match('%u') ~= nil
  if kind == 'figure' then return upper and 'Figura' or 'figura' end
  return upper and 'Táboa' or 'táboa'
end

local function append_inlines(out, values)
  if not values then return end
  for _, value in ipairs(values) do out:insert(value) end
end

local function transform_cite(el)
  if #el.citations == 0 then return nil end
  for _, citation in ipairs(el.citations) do
    if not is_crossref(citation.id) then return nil end
  end

  local out = pandoc.Inlines({})
  local bracketed = el.citations[1].mode == 'NormalCitation'
  if bracketed then out:insert(pandoc.Str('(')) end

  for index, citation in ipairs(el.citations) do
    local data = refs[canonical_ref(citation.id)]
    if not data then
      -- A referencia queda visible e marcada semanticamente para que a
      -- validación posterior poida avisar (e --strict poida abortar).
      out:insert(pandoc.Span(
        { pandoc.Str('@' .. citation.id) },
        pandoc.Attr('', { 'broken-crossref' }, { ['data-ref'] = citation.id })
      ))
    else
      if citation.prefix and #citation.prefix > 0 then
        append_inlines(out, citation.prefix)
        out:insert(pandoc.Space())
      end

      local label = ref_word(citation.id, data.kind)
      if data.number then label = label .. ' ' .. tostring(data.number) end
      out:insert(pandoc.Link(
        { pandoc.Str(label) },
        '#' .. data.target,
        '',
        pandoc.Attr('', { 'crossref' })
      ))

      if citation.suffix and #citation.suffix > 0 then
        out:insert(pandoc.Space())
        append_inlines(out, citation.suffix)
      end
    end

    if index < #el.citations then
      out:insert(pandoc.Str(','))
      out:insert(pandoc.Space())
    end
  end

  if bracketed then out:insert(pandoc.Str(')')) end
  return out
end

function Pandoc(doc)
  figure_no, table_no, callout_no, refs = 0, 0, 0, {}
  local use_callouts = callouts_enabled(doc.meta)

  doc = doc:walk({
    Div = use_callouts and transform_callout or nil,
    Figure = transform_figure,
    Table = transform_table,
  })
  doc = doc:walk({ Cite = transform_cite })
  return doc
end
