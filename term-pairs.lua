-- Converte listas homoxéneas de «**termo**: explicación» en listas de
-- definicións. As listas ordinarias e as numeradas conservan a súa semántica.

local function pair(item)
  local first = item[1]
  if not first or (first.t ~= 'Plain' and first.t ~= 'Para') then return nil end
  local inlines = first.content
  if not inlines[1] or inlines[1].t ~= 'Strong' then return nil end

  local term = {}
  for _, inline in ipairs(inlines[1].content) do term[#term + 1] = inline end
  local last = term[#term]
  local attached = last and last.t == 'Str' and last.text:sub(-1) == ':'
  if attached then
    if last.text == ':' then
      term[#term] = nil
    else
      term[#term] = pandoc.Str(last.text:sub(1, -2))
    end
  end
  if #term == 0 then return nil end

  local i = 2
  if not attached then
    while inlines[i] and inlines[i].t == 'Space' do i = i + 1 end
    local separator = inlines[i]
    if not separator or separator.t ~= 'Str' or
       (separator.text ~= ':' and separator.text ~= '—' and separator.text ~= '–') then
      return nil
    end
    i = i + 1
  end
  while inlines[i] and inlines[i].t == 'Space' do i = i + 1 end

  local body = {}
  local rest = {}
  for j = i, #inlines do rest[#rest + 1] = inlines[j] end
  if #rest > 0 then
    body[1] = first.t == 'Para' and pandoc.Para(rest) or pandoc.Plain(rest)
  end
  for j = 2, #item do body[#body + 1] = item[j] end
  if #body == 0 then return nil end
  return { term, { body } }
end

function BulletList(list)
  if #list.content < 2 then return nil end
  local pairs = {}
  for _, item in ipairs(list.content) do
    local found = pair(item)
    if not found then return nil end
    pairs[#pairs + 1] = found
  end
  return pandoc.DefinitionList(pairs)
end
