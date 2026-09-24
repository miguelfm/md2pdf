-- callouts-docx.lua
-- Converte divs callout (:::note, :::tip, etc.) a bloques de texto con
-- prefixo bold para saída DOCX. En DOCX non hai tcolorbox nin estilos de cor,
-- así que usamos un marcador textual claro.
--
-- Resultado visual en Word:
--   📝 Nota:
--   Texto do callout aquí.
--
-- Para un aspecto máis elaborado, define un estilo "Callout" en reference.docx
-- e descomenta a liña de CustomStyle abaixo.

local CALLOUT_LABELS = {
    note     = "📝 Nota:",
    tip      = "💡 Consello:",
    warning  = "⚠️ Atención:",
    danger   = "⛔ Perigo:",
    info     = "ℹ️ Información:",
    -- Aliases en galego
    consello = "💡 Consello:",
    perigo   = "⛔ Perigo:",
}

function Div(el)
    for cls, label in pairs(CALLOUT_LABELS) do
        if el.classes:includes(cls) then
            -- Parágrafo de cabeceira con texto bold
            local header = pandoc.Para({
                pandoc.Strong({ pandoc.Str(label) })
            })
            -- Montar: cabeceira + contido orixinal
            local blocks = { header }
            for _, block in ipairs(el.content) do
                table.insert(blocks, block)
            end
            -- Separador visual despois do callout (liña baleira implícita)
            return blocks
        end
    end
end
