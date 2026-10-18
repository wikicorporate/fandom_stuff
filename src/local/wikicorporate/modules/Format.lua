local p = {}
local tabli = mw.loadData('Модуль:Format/Данные')

function p.e(frame)
    local args = frame:getParent().args
    if not args[1] and frame.args[1] then 
        args = frame.args 
    end
    
    local formats_raw = args[1] or ""
    local text = args[2] or ""
    
    if formats_raw == "" or text == "" then 
        return text 
    end
    
    -- Разделяем запрошенные форматы по запятой, точке с запятой или плюсу
    local formats = mw.text.split(formats_raw, "[,;+%s]+")
    
    -- Накладываем форматы на текст последовательно
    for _, fmt in ipairs(formats) do
        local clean_fmt = mw.ustring.upper(mw.text.trim(fmt))
        local format_pattern = tabli[clean_fmt]
        
        if format_pattern then
            -- Безопасная замена: анонимная функция защищает от краша из-за знаков % в тексте
            text = format_pattern:gsub("%$1", function() return text end)
        end
    end
    
    return text
end

return p
