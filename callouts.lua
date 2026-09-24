--[[
callouts.lua — Filtro Pandoc Lua para callouts en LuaLaTeX
==========================================================
Converte divs con clase callout en bloques tcolorbox con cor e etiqueta.

Sintaxe no Markdown:
    ::: note
    Lembra que `session_start()` debe ir antes de calquera saída HTML.
    :::

    ::: warning
    Nunca almacenes contrasinais en texto plano.
    :::

    ::: tip
    Usa `password_needs_rehash()` para migrar algoritmos antigos.
    :::

    ::: danger
    Sen `session_regenerate_id(true)` o sistema é vulnerable.
    :::

Tamén se acepta a sintaxe GitHub/Obsidian (convertida en preprocesamento):
    > [!NOTE]
    > Contido da nota.

Tipos dispoñibles (insensible a maiúsculas/minúsculas):
    note / nota       → azul    — información xeral
    tip  / consello   → verde   — boas prácticas, consellos
    warning / atención / atencion → laranxa — precaución
    danger / perigo   → vermello — erros críticos, seguridade
    info              → cian    — dato técnico de referencia

Require tcolorbox no preámbulo LaTeX (md2pdf-preamble.tex):
    \usepackage{tcolorbox}
    \tcbuselibrary{skins,breakable}
--]]

-- Paleta apagada/elegante (cores con nome para compatibilidade con \color{})
-- Os valores RGB defínense en colordefs e úsanse polo nome en colframe/colback/\color
local CALLOUT_STYLES = {
    note      = { label = 'Nota',     colorname = 'calloutNoteFrame',
                  backdef  = '\\definecolor{calloutNoteBack}{RGB}{220,232,248}',
                  framedef = '\\definecolor{calloutNoteFrame}{RGB}{42,98,160}',
                  colback  = 'calloutNoteBack',  colframe = 'calloutNoteFrame' },
    nota      = { label = 'Nota',     colorname = 'calloutNoteFrame',
                  backdef  = '\\definecolor{calloutNoteBack}{RGB}{220,232,248}',
                  framedef = '\\definecolor{calloutNoteFrame}{RGB}{42,98,160}',
                  colback  = 'calloutNoteBack',  colframe = 'calloutNoteFrame' },
    tip       = { label = 'Consello', colorname = 'calloutTipFrame',
                  backdef  = '\\definecolor{calloutTipBack}{RGB}{215,238,218}',
                  framedef = '\\definecolor{calloutTipFrame}{RGB}{34,120,60}',
                  colback  = 'calloutTipBack',   colframe = 'calloutTipFrame' },
    consello  = { label = 'Consello', colorname = 'calloutTipFrame',
                  backdef  = '\\definecolor{calloutTipBack}{RGB}{215,238,218}',
                  framedef = '\\definecolor{calloutTipFrame}{RGB}{34,120,60}',
                  colback  = 'calloutTipBack',   colframe = 'calloutTipFrame' },
    warning   = { label = 'Atención', colorname = 'calloutWarnFrame',
                  backdef  = '\\definecolor{calloutWarnBack}{RGB}{248,232,190}',
                  framedef = '\\definecolor{calloutWarnFrame}{RGB}{170,100,10}',
                  colback  = 'calloutWarnBack',  colframe = 'calloutWarnFrame' },
    atencion  = { label = 'Atención', colorname = 'calloutWarnFrame',
                  backdef  = '\\definecolor{calloutWarnBack}{RGB}{248,232,190}',
                  framedef = '\\definecolor{calloutWarnFrame}{RGB}{170,100,10}',
                  colback  = 'calloutWarnBack',  colframe = 'calloutWarnFrame' },
    danger    = { label = 'Crítico',  colorname = 'calloutDangerFrame',
                  backdef  = '\\definecolor{calloutDangerBack}{RGB}{252,218,218}',
                  framedef = '\\definecolor{calloutDangerFrame}{RGB}{192,30,30}',
                  colback  = 'calloutDangerBack', colframe = 'calloutDangerFrame' },
    perigo    = { label = 'Crítico',  colorname = 'calloutDangerFrame',
                  backdef  = '\\definecolor{calloutDangerBack}{RGB}{252,218,218}',
                  framedef = '\\definecolor{calloutDangerFrame}{RGB}{192,30,30}',
                  colback  = 'calloutDangerBack', colframe = 'calloutDangerFrame' },
    info      = { label = 'Info',     colorname = 'calloutInfoFrame',
                  backdef  = '\\definecolor{calloutInfoBack}{RGB}{205,232,237}',
                  framedef = '\\definecolor{calloutInfoFrame}{RGB}{20,110,130}',
                  colback  = 'calloutInfoBack',  colframe = 'calloutInfoFrame' },
}

-- Normaliza o nome da clase para o lookup: atención/Atención → atencion.
-- string.lower só coñece ASCII e %a non recoñece os bytes UTF-8 de «ó»,
-- así que o acento hai que substituílo ANTES de filtrar.
local function normalize(s)
    return (s:lower()
             :gsub('ó', 'o'):gsub('Ó', 'o')
             :gsub('[^%a_]', ''))
end

function Div(el)
    for _, cls in ipairs(el.classes) do
        local key   = normalize(cls)
        local style = CALLOUT_STYLES[key]
        if style then
            local before = pandoc.RawBlock('latex',
                -- Gancho para --print/--night: se o preámbulo non o define
                -- (uso do filtro fóra de md2pdf), créase baleiro.
                '\\pgfkeysifdefined{/tcb/md2pdf-callout/.@cmd}{}' ..
                '{\\tcbset{md2pdf-callout/.style={}}}\n' ..
                style.backdef .. '\n' .. style.framedef .. '\n' ..
                string.format(
                    '\\Needspace{5\\baselineskip}' ..
                    '\\begin{tcolorbox}[enhanced, blanker, ' ..
                    'colframe=%s, colback=%s, ' ..
                    'borderline west={3pt}{0pt}{tcbcolframe}, ' ..
                    'left=10pt, right=6pt, top=5pt, bottom=5pt, ' ..
                    'breakable, ' ..
                    'lines before break=3, ' ..
                    'enlargepage flexible=\\baselineskip, ' ..
                    'before upper={\\textbf{\\color{tcbcolframe}%s}\\par\\smallskip}, ' ..
                    -- Ao final para que --print/--night (lualatex.py) poidan sobrescribir colframe
                    'md2pdf-callout]',
                    style.colframe, style.colback, style.label
                )
            )
            local after = pandoc.RawBlock('latex', '\\end{tcolorbox}')

            local blocks = {}
            table.insert(blocks, before)
            for _, b in ipairs(el.content) do
                table.insert(blocks, b)
            end
            table.insert(blocks, after)
            return blocks
        end
    end
end
