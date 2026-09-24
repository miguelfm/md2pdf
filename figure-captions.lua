-- figure-captions.lua — xestiona figuras e táboas con identificador e resolve @fig: e @tbl:
local stringify = pandoc.utils.stringify
local function paragrafo_con_imaxe(bloque)
  if bloque == nil or bloque.t ~= "Para" or #bloque.content == 0 then return false end
  return bloque.content[1].t == "Image"
end
local function paragrafo_de_pe(bloque)
  if bloque == nil or bloque.t ~= "Para" or #bloque.content == 0 then return false end
  if bloque.content[1].t ~= "Emph" then return false end
  return stringify(bloque.content[1]):match("^Figura%s+%d+%.") ~= nil
end
local function raw_block(bloque)
  return bloque ~= nil and bloque.t == "RawBlock"
end
local function sen_numero(inlinas)
  if #inlinas < 4 then return inlinas end
  local a, b, c, d = inlinas[1], inlinas[2], inlinas[3], inlinas[4]
  if a.t == "Str" and a.text == "Figura"
     and b.t == "Space"
     and c.t == "Str" and c.text:match("^%d+%.$")
     and d.t == "Space" then
    return { table.unpack(inlinas, 5) }
  end
  return inlinas
end
local function obter_id_e_limpar(b_imaxe, pe)
  local imaxe = b_imaxe.content[1]
  local id = ""
  if imaxe.identifier and imaxe.identifier ~= "" then
    id = imaxe.identifier
  end
  if id == "" and #b_imaxe.content > 1 then
    for j = 2, #b_imaxe.content do
      local inl = b_imaxe.content[j]
      if inl.t == "Str" then
        local m = inl.text:match("{#(fig:[%w%-_:]+)}") or inl.text:match("{#([%w%-_:]+)}")
        if m then id = m; break end
      elseif inl.t == "Span" and inl.identifier and inl.identifier ~= "" then
        id = inl.identifier; break
      end
    end
  end
  local inlinas = pe.content[1].content
  for j = #inlinas, 1, -1 do
    local inl = inlinas[j]
    if inl.t == "Str" then
      local m = inl.text:match("{#(fig:[%w%-_:]+)}") or inl.text:match("{#([%w%-_:]+)}")
      if m then
        if id == "" then id = m end
        local novo = inl.text:gsub("%s*{#[%w%-_:]+}%s*", "")
        if novo == "" then
          table.remove(inlinas, j)
          if j > 1 and inlinas[j - 1].t == "Space" then table.remove(inlinas, j - 1) end
        else
          inlinas[j] = pandoc.Str(novo)
        end
        break
      end
    elseif inl.t == "Span" and inl.identifier and inl.identifier ~= "" then
      if id == "" then id = inl.identifier end
      table.remove(inlinas, j)
      for k = #inl.content, 1, -1 do table.insert(inlinas, j, inl.content[k]) end
      break
    end
  end
  if id == "" and #pe.content > 1 then
    for j = 2, #pe.content do
      local inl = pe.content[j]
      if inl.t == "Str" then
        local m = inl.text:match("{#(fig:[%w%-_:]+)}") or inl.text:match("{#([%w%-_:]+)}")
        if m then id = m; break end
      elseif inl.t == "Span" and inl.identifier and inl.identifier ~= "" then
        id = inl.identifier; break
      end
    end
  end
  return id, inlinas
end
local function figura(b_imaxe, pe)
  local imaxe = b_imaxe.content[1]
  local id, inlinas = obter_id_e_limpar(b_imaxe, pe)
  if FORMAT:match("latex") or FORMAT:match("html") then
    -- En PDF e HTML a numeración xérase automaticamente; retiramos a
    -- numeración manual dos pés herdados para evitar duplicados.
    inlinas = sen_numero(inlinas)
  end
  local corpo = pandoc.Blocks({ pandoc.Plain(inlinas) })
  local caption = pandoc.Caption and pandoc.Caption(corpo) or { long = corpo }
  local attr = pandoc.Attr(id, {}, {})
  -- O identificador vive na Figure; se tamén quedase na imaxe, en HTML
  -- sairía dúas veces (<figure id> e <img id>) e a ligazón sería ambigua.
  if id ~= '' and imaxe.identifier == id then imaxe.identifier = '' end
  return pandoc.Figure({ pandoc.Plain({ imaxe }) }, caption, attr)
end
local function process_blocks(bloques)
  local saida = pandoc.Blocks({})
  local i = 1
  while i <= #bloques do
    local b = bloques[i]
    if raw_block(b)
       and paragrafo_con_imaxe(bloques[i + 1])
       and raw_block(bloques[i + 2])
       and bloques[i + 2].format == b.format
       and paragrafo_de_pe(bloques[i + 3]) then
      saida:insert(figura(bloques[i + 1], bloques[i + 3]))
      i = i + 4
    elseif paragrafo_con_imaxe(b) and paragrafo_de_pe(bloques[i + 1]) then
      saida:insert(figura(b, bloques[i + 1]))
      i = i + 2
    else
      saida:insert(b)
      i = i + 1
    end
  end
  return saida
end
local function process_table(tbl)
  local id = tbl.identifier or ""
  local long_blocks = nil
  if tbl.caption then
    if tbl.caption.long then
      long_blocks = tbl.caption.long
    elseif #tbl.caption > 0 and tbl.caption[1].t then
      long_blocks = tbl.caption
    end
  end
  if long_blocks and #long_blocks > 0 then
    local last_block = long_blocks[#long_blocks]
    if last_block and last_block.content then
      local inlinas = last_block.content
      for j = #inlinas, 1, -1 do
        local inl = inlinas[j]
        if inl.t == "Str" then
          local m = inl.text:match("{#([Tt][ba][lb]:[%w%-_:]+)}") or inl.text:match("{#([%w%-_:]+)}")
          if m and (m:match("^[Tt]bl:") or m:match("^[Tt]ab:")) then
            if id == "" then id = m end
            local novo = inl.text:gsub("%s*{#[%w%-_:]+}%s*", "")
            if novo == "" then
              table.remove(inlinas, j)
              if j > 1 and inlinas[j - 1].t == "Space" then table.remove(inlinas, j - 1) end
            else
              inlinas[j] = pandoc.Str(novo)
            end
            break
          end
        elseif inl.t == "Span" and inl.identifier and (inl.identifier:match("^[Tt]bl:") or inl.identifier:match("^[Tt]ab:")) then
          if id == "" then id = inl.identifier end
          table.remove(inlinas, j)
          for k = #inl.content, 1, -1 do table.insert(inlinas, j, inl.content[k]) end
          break
        end
      end
    end
  end
  if id ~= "" then tbl.identifier = id end
  return tbl
end
local function is_crossref(id)
  return id:match("^[Ff]ig:") or id:match("^[Tt]bl:") or id:match("^[Tt]ab:")
end
local function ref_label(id)
  if id:match("^[Ff]ig:") then
    return id:match("^Fig:") and "Figura" or "figura"
  elseif id:match("^[Tt]bl:") or id:match("^[Tt]ab:") then
    return (id:match("^Tbl:") or id:match("^Tab:")) and "Táboa" or "táboa"
  end
  return ""
end
local function process_cite(el)
  if not FORMAT:match("latex") then return nil end
  local has_ref = false
  for _, c in ipairs(el.citations) do
    if is_crossref(c.id) then has_ref = true; break end
  end
  if not has_ref then return nil end
  local res = {}
  local is_bracketed = (#el.citations > 0 and el.citations[1].mode == "NormalCitation")
  if is_bracketed then table.insert(res, pandoc.Str("(")) end
  for i, c in ipairs(el.citations) do
    if is_crossref(c.id) then
      local nome = ref_label(c.id)
      -- @Fig:x / @Tbl:x só cambian a palabra; a etiqueta segue sendo fig:x / tbl:x
      local label = (c.id:gsub("^%u", string.lower))
      local raw = "\\hyperref[" .. label .. "]{" .. nome .. "~\\ref*{" .. label .. "}}"
      if c.prefix and #c.prefix > 0 then
        for _, p in ipairs(c.prefix) do table.insert(res, p) end
        table.insert(res, pandoc.Space())
      end
      table.insert(res, pandoc.RawInline("latex", raw))
      if c.suffix and #c.suffix > 0 then
        table.insert(res, pandoc.Space())
        for _, s in ipairs(c.suffix) do table.insert(res, s) end
      end
    else
      table.insert(res, pandoc.Str("@" .. c.id))
    end
    if i < #el.citations then
      table.insert(res, pandoc.Str(","))
      table.insert(res, pandoc.Space())
    end
  end
  if is_bracketed then table.insert(res, pandoc.Str(")")) end
  return res
end
return {
  { Table = process_table },
  { Blocks = process_blocks },
  { Cite = process_cite },
}
