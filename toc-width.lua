-- Axuste do TOC de md2pdf. As medicións non escriben nin envían caixas ao PDF.
local M = {active_entry=nil, enabled=false, previous=nil}
local glyph, hlist, vlist, disc = node.id('glyph'), node.id('hlist'), node.id('vlist'), node.id('disc')
local attr = luatexbase.new_attribute('md2pdf_toc_role')
tex.sprint('\\attributedef\\mdpdfTocRole=' .. attr .. '\\relax')
local glyph_cache = {}

local function glyph_text(n)
  local properties = node.getproperty(n)
  if properties and type(properties.glyph_info)=='string' then
    return properties.glyph_info
  end
  glyph_cache[n.font] = glyph_cache[n.font] or {}
  local cache = glyph_cache[n.font]
  if cache[n.char] then return cache[n.char] end
  local character = font.getfont(n.font).characters[n.char]
  local mapping = character and character.tounicode
  local result = ''
  if type(mapping) == 'string' then
    local high
    for hex in mapping:gmatch('%x%x%x%x') do
      local code = tonumber(hex,16)
      if code >= 0xD800 and code <= 0xDBFF then high = code
      else
        if high then code = 0x10000+(high-0xD800)*0x400+(code-0xDC00); high=nil end
        result = result .. utf8.char(code)
      end
    end
  elseif n.char <= 0x10FFFF then result = utf8.char(n.char)
  else return nil end
  cache[n.char] = result
  return result
end

local function advance(parent, head, stop)
  if not head then return 0 end
  if parent then
    if stop then return node.rangedimensions(parent, head, stop) end
    return node.rangedimensions(parent, head)
  end
  if stop then return node.dimensions(head, stop) end
  return node.dimensions(head)
end

local function walk(head, parent, offset, result)
  if not head then return end
  for n in node.traverse(head) do
    local x = offset + advance(parent, head, n)
    if n.id == glyph then
      local role = node.has_attribute(n, attr)
      local width = advance(parent, head, n.next) - advance(parent, head, n)
      if role == 1 then
        result.font_size = result.font_size or font.getfont(n.font).size
        result.right = math.max(result.right, x + width)
        result.left = math.min(result.left, x)
        local text = glyph_text(n)
        if not text then result.unsupported=true; text='?' end
        result.text[#result.text + 1] = text
      elseif role == 2 then
        result.page_left = math.min(result.page_left, x)
        result.page_right = math.max(result.page_right, x + width)
      end
    elseif n.id == hlist then
      walk(n.head, n, x, result)
    elseif n.id == disc and n.replace then
      walk(n.replace, nil, x, result)
    elseif n.id == vlist then
      -- Non se extrapola unha medición horizontal a fórmulas verticais.
      result.unsupported = true
    elseif n.id == node.id('dir') and n.dir~='TLT' then
      result.unsupported = true
    end
  end
end

local digest = require('md5').sumhexa
local function toc_text()
  local name = tex.jobname .. '.toc'
  local directory = os.getenv('TEXMFOUTPUT')
  local paths = {directory and directory .. '/' .. name or name, name, kpse.find_file(name)}
  for _,path in ipairs(paths) do
    if path then
      local file = io.open(path,'rb')
      if file then local text=file:read('*a'); file:close(); return text end
    end
  end
  return nil
end

local function hash(text) return text and digest(text) or 'none' end
local function warning(message)
  tex.sprint('\\csname @latex@warning@no@line\\endcsname{md2pdf TOC: '..message..'}')
end
local function reject(reason)
  M.current.valid=false
  M.current.reasons[reason]=true
  if not M.exhaustive then tex.setcount('global','mdpdfTocSkip',1) end
end
local function subset(values,allowed)
  for value in pairs(values) do if not allowed[value] then return false end end
  return true
end

function M.restore(raw,key,width,fixed)
  M.previous={raw=raw,key=key,width=width,fixed=fixed==1}
end

function M.start(body,reference,gap)
  M.body=body; M.reference=reference; M.gap=gap
  M.read_hash=hash(toc_text()); M.rendered=true
  M.baseline={}; M.selected=nil; M.key=nil; M.trials=0; M.expected=0
  M.unsupported=false; M.reason=nil; M.cached=false
  M.force_fixed=M.previous and M.previous.fixed or false
  if M.previous and M.previous.raw~=M.read_hash then
    M.force_fixed=true; M.reason='references changed; keeping reference width'
  end
  tex.setcount('global','mdpdfTocSolved',0)
end

function M.unsupported_source() M.unsupported=true end
function M.begin_candidate(width,phase)
  M.current={width=width,phase=phase,entries={},reasons={},valid=true}
  M.exhaustive=phase~='search'
  tex.setcount('global','mdpdfTocSkip',0)
  M.trials=M.trials+1
end

function M.measure(head,entry)
  local rows,breaks,texts,consumed={}, {}, {}, 0
  local overflow,unsupported=0,false
  for n in node.traverse(head) do
    if n.id==hlist then
      local row={left=math.huge,right=-math.huge,page_left=math.huge,page_right=-math.huge,text={}}
      walk(n.head,n,(n.shift or 0)-(M.body-M.current.width)/2,row)
      if row.right>-math.huge or row.page_left<math.huge then
        row.text=table.concat(row.text); rows[#rows+1]=row; texts[#texts+1]=row.text
        overflow=math.max(overflow,row.right-M.current.width,row.page_right-M.current.width,-row.left)
        unsupported=unsupported or row.unsupported
        local tail=utf8.offset(row.text,-1)
        local char=tail and utf8.codepoint(row.text,tail) or 0
        local hyphen=char==45 or char==173
        consumed=consumed+(utf8.len(row.text) or 0)-(hyphen and 1 or 0)
        if hyphen then breaks[consumed]=true end
      end
    end
  end
  if #rows==0 then return end
  -- Algúns comandos compoñen fragmentos auxiliares do título. Só o
  -- parágrafo que tamén leva a páxina é a entrada completa do índice.
  local has_page=false
  for _,row in ipairs(rows) do if row.page_left<math.huge then has_page=true end end
  if not has_page then return end
  for index,row in ipairs(rows) do
    if index<#rows then overflow=math.max(overflow,row.right-(M.current.width-M.rightindent)) end
  end
  local last=rows[#rows]
  local gap=last.page_left<math.huge and last.right>-math.huge and last.page_left-last.right or -1
  local value={lines=#rows,gap=gap,text=table.concat(texts,'|'),breaks=breaks}
  if M.current.entries[entry] then reject('nested entry paragraphs') end
  M.current.entries[entry]=value
  if unsupported then reject('unsupported entry content') end
  if overflow>tex.sp('0.05mm') then reject('overflow') end
  if gap<M.gap then reject('insufficient page-number gap') end
  if M.current.phase~='baseline' then
    local base=M.baseline[entry]
    if not base then reject('missing reference entry')
    else
      if value.lines>base.lines then reject('additional lines') end
      if not subset(breaks,base.breaks) then reject('new hyphenation') end
    end
  end
end

function M.end_candidate(expected)
  local current=M.current
  local count=0; for _ in pairs(current.entries) do count=count+1 end
  if current.valid and count~=expected then reject('missing entries') end
  if current.phase=='baseline' then
    M.baseline=current.entries; M.expected=expected
    M.baseline_reasons=current.reasons
    if current.reasons['unsupported entry content'] then M.unsupported=true end
    local parts={M.read_hash,M.body,M.reference,M.gap,M.rightindent}
    for i=1,expected do
      local value=current.entries[i]
      if not value then M.unsupported=true
      else parts[#parts+1]=value.text..':'..value.lines..':'..math.floor(value.gap+0.5) end
    end
    M.key=digest(table.concat(parts,';'))
  elseif current.phase=='search' then
    if current.valid and not M.selected then
      M.selected=current.width; M.selected_entries=current.entries
      tex.setcount('global','mdpdfTocSolved',1)
    end
  elseif current.phase=='verify' then
    local expected_values=M.selected_entries
    if expected_values then
      for id,value in pairs(current.entries) do
        local before=expected_values[id]
        if not before or before.lines~=value.lines or before.text~=value.text or math.abs(before.gap-value.gap)>2 then
          reject('nonrepeatable measurement')
        end
      end
    end
    if not current.valid then
      M.selected=nil; M.force_fixed=true; M.reason='verification failed; keeping reference width'
    end
  end
end

function M.can_search()
  return not M.force_fixed and not M.unsupported and M.expected>0
end
function M.try_cached()
  local old=M.previous
  if M.can_search() and old and old.key==M.key and old.width>0 and old.width<=M.reference then
    tex.dimen.mdpdfTocWidth=old.width
    M.cached=true
    return true
  end
  return false
end
function M.grid_width(index) return tex.sp(tostring(index/2)..'mm') end
function M.grid_steps() return math.floor(M.reference/tex.sp('0.5mm')) end

function M.choose()
  if M.unsupported then M.reason='unsupported TOC structure; keeping reference width' end
  if not M.selected and M.expected>0 and not M.reason then
    local reasons={}
    for reason in pairs(M.baseline_reasons or {}) do reasons[#reasons+1]=reason end
    table.sort(reasons)
    M.reason='no admissible width; keeping reference width'
    if #reasons>0 then M.reason=M.reason..' ('..table.concat(reasons,', ')..')' end
  end
  tex.dimen.mdpdfTocWidth=M.selected or M.reference
end

function M.complete()
  local width=M.selected or M.reference
  local fixed=(M.force_fixed or M.unsupported or (not M.selected and M.expected>0)) and 1 or 0
  if M.expected>0 and M.read_hash~='none' then
    tex.sprint('\\mdpdfTocWriteCache{'..M.read_hash..'}{'..M.key..'}{'..width..'}{'..fixed..'}')
  end
  if M.reason then warning(M.reason) end
  texio.write_nl('log',string.format('md2pdf-toc width_mm=%.3f reference_mm=%.3f entries=%d trials=%d cached=%s fallback=%d',
    width/tex.sp('1mm'),M.reference/tex.sp('1mm'),M.expected or 0,M.trials,tostring(M.cached),fixed))
end

function M.check_end()
  if M.rendered and hash(toc_text())~=M.read_hash then
    warning('MD2PDF_TOC_UNSTABLE; Rerun LaTeX')
  end
end

luatexbase.add_to_callback('post_linebreak_filter',function(head)
  if M.active_entry then M.measure(head,M.active_entry) end
  return head
end,'md2pdf.toc.width')
return M
