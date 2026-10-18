local p = {}

function p.main(frame)
    -- 1. Нативное получение аргументов
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

    if max_idx == 0 then return "" end

    local tabber = mw.html.create('div'):addClass('tabber wds-tabber')
    local wrapper = tabber:tag('div'):addClass('wds-tabs__wrapper')
    local labels = wrapper:tag('ul'):addClass('wds-tabs')

    local is_first_tab = true

    -- 2. Идём по аргументам с шагом 2 (заголовок, содержимое)
    for i = 1, max_idx, 2 do
        local label = mw.text.trim(args[i] or "")
        local content = mw.text.trim(args[i + 1] or "")

        if label ~= "" then
            local tab_li = labels:tag('li')
                :addClass('wds-tabs__tab')
                :attr({
                    ['data-hash'] = mw.uri.anchorEncode(label),
                    ['data-text'] = label
                })

            local tab_content = tabber:tag('div')
                :addClass('wds-tab__content')

            if is_first_tab then
                tab_li:addClass('wds-is-current')
                tab_content:addClass('wds-is-current')
                is_first_tab = false
            end

            tab_li:tag('div')
                :addClass('wds-tabs__tab-label')
                :wikitext('[[##|', label, ']]')

            tab_content:wikitext('\n', content, '\n')
        end
    end

    if is_first_tab then return "" end

    return tostring(tabber)
end

return p
