local p = {}

function p.main(frame)
    -- 1. Нативное получение аргументов (в 10 раз быстрее, чем Dev:Arguments)
    local args = frame:getParent().args
    if not args[1] and frame.args[1] then
        args = frame.args
    end
    
    -- Вычисляем максимальный индекс аргумента (защита от "дыр" в номерах)
    local max_idx = 0
    for k, _ in pairs(args) do
        if type(k) == "number" and k > max_idx then
            max_idx = k
        end
    end

    -- Если аргументов нет, ничего не выводим
    if max_idx == 0 then return "" end

    local tabber = mw.html.create('div'):addClass('tabber wds-tabber')
    local wrapper = tabber:tag('div'):addClass('wds-tabs__wrapper')
    local labels = wrapper:tag('ul'):addClass('wds-tabs')
    
    local is_first_tab = true
    
    -- 2. Идём по аргументам с шагом 2
    for i = 1, max_idx, 2 do
        -- Безопасно извлекаем заголовок и текст (очищая от случайных пробелов по краям)
        local label = mw.text.trim(args[i] or "")
        local content = mw.text.trim(args[i + 1] or "")
        
        -- Создаём вкладку только если есть заголовок
        if label ~= "" then
            local is_current = is_first_tab and 'wds-is-current' or ''
            
            labels:tag('li')
                :addClass('wds-tabs__tab ' .. is_current)
                :attr({
                    ['data-hash'] = mw.uri.anchorEncode(label), 
                    ['data-text'] = label
                })
                :tag('div')
                :addClass('wds-tabs__tab-label')
                :wikitext('[[##|', label, ']]')
            
            tabber:tag('div')
                :addClass('wds-tab__content ' .. is_current)
                :wikitext('\n', content, '\n')
                
            is_first_tab = false
        end
    end
    
    -- Защита: если переданы только пустые параметры
    if is_first_tab then return "" end
    
    return tostring(tabber)
end

return p
