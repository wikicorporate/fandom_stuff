local p = {}

local ok, db = pcall(mw.loadJsonData, 'MediaWiki:Custom-Интервики.json')

function p.e(frame)
    if not ok or type(db) ~= 'table' then
        return ''
    end

    local args = frame.args
    local page = args[1]
    if not page or mw.text.trim(page) == '' then
        local parent = frame:getParent()
        if parent and parent.args and parent.args[1] then
            page = parent.args[1]
        else
            page = mw.title.getCurrentTitle().text
        end
    end

    page = mw.text.trim(page or '')
    if page == '' then
        return ''
    end

    local links = db[page]
    if type(links) ~= 'table' then
        return ''
    end

    local is_main_page = (page == 'Заглавная страница')

    local langs = {}
    for lang, target in pairs(links) do
        if type(lang) == 'string' and type(target) == 'string' then
            local clean_target = mw.text.trim(target)
            if clean_target ~= '' or is_main_page then
                table.insert(langs, lang)
            end
        end
    end
    table.sort(langs)

    local res = {}
    for _, lang in ipairs(langs) do
        local clean_target = mw.text.trim(links[lang] or '')
        table.insert(res, string.format('[[%s:%s]]', lang, clean_target))
    end

    return table.concat(res, '\n')
end

return p
